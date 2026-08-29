#!/usr/bin/env python3
"""Context telemetry for the ticket workflow: measure what a ticket cost.

Each verb claims its own session against the ticket it is working, so the set
of sessions that worked a ticket is recorded rather than inferred, each with the
role it played and the lifecycle verb that produced it. Reports peak context per
claimed session, then records the actuals so the slicing rubric can be retuned
against real numbers. Every record carries counts and labels supplied on the
command line: never a transcript excerpt, a prompt, or any other prose from a
session.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

PROJECTS_DIR = Path(
    os.environ.get("CLAUDE_PROJECTS_DIR", str(Path.home() / ".claude" / "projects"))
).expanduser()
TELEMETRY_PATH = Path(
    os.environ.get(
        "TICKET_TELEMETRY",
        str(Path.home() / ".config" / "ticket" / "telemetry.jsonl"),
    )
).expanduser()
CLAIMS_PATH = Path(
    os.environ.get(
        "TICKET_CLAIMS",
        str(Path.home() / ".config" / "ticket" / "claims.jsonl"),
    )
).expanduser()
CODEX_SESSIONS_DIR = Path(
    os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
).expanduser() / "sessions"

# Which environment variable carries the running session id, per agent. A verb
# that cannot read one passes --session instead.
SESSION_VARIABLES = (("claude", "CLAUDE_CODE_SESSION_ID"), ("codex", "CODEX_SESSION_ID"))

# What a claimed session was doing, so cost is attributed to the work that spent
# it. The coordinator drives the ticket, a worker builds one chunk, a reviewer
# only reviews. A claim written before roles existed is read back as `legacy`,
# which is not a guess about which of the three it was.
ROLES = ("coordinator", "worker", "reviewer")
LEGACY_ROLE = "legacy"

# Which lifecycle phase produced a claim. A claim written before verbs existed
# is read back as `legacy`; the reader never guesses from role or ordering.
VERBS = ("triage", "start", "revise", "finalize")
LEGACY_VERB = "legacy"

# A session past this peaked into the degradation band: it should have been
# sliced below this line.
DEGRADE_PEAK = 180_000
# A chunk session under this was mostly fixed overhead, not real work.
FLOOR_PEAK = 120_000


class TelemetryError(RuntimeError):
    """A safe, user-facing telemetry failure."""


def validate_ticket_id(value: str) -> str:
    if not value or any(character.isspace() for character in value):
        raise TelemetryError("ticket id must be a single token with no whitespace")
    return value


def validate_session_id(value: str) -> str:
    """A session id is pasted in from elsewhere and reaches a filesystem glob.

    An id carrying glob syntax matches transcripts the claim never named:
    `--session '*'` resolved to every transcript on the machine and reported
    their maximum as one session's peak.
    """
    if not value or any(character.isspace() for character in value):
        raise TelemetryError("session id must be a single token with no whitespace")
    forbidden = set("*?[]/\\")
    if forbidden & set(value):
        raise TelemetryError("session id must not contain glob or path characters")
    return value


def _normalize_remote(url: str) -> str:
    """Collide an ssh and an https remote for one repository to one string.

    `git@github.com:owner/repo.git` and `https://github.com/owner/repo` name
    the same repository; both fold to `github.com/owner/repo` so a claim made
    through either form resolves to the same identity.
    """
    url = url.strip()
    if url.endswith(".git"):
        url = url[: -len(".git")]
    scp_match = re.match(r"^[^/@]+@([^:]+):(.+)$", url)
    if scp_match:
        return f"{scp_match.group(1)}/{scp_match.group(2)}"
    url_match = re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://(?:[^/@]+@)?([^/]+)/(.+)$", url)
    if url_match:
        return f"{url_match.group(1)}/{url_match.group(2)}"
    return url


def resolve_repo(path: Path) -> Optional[str]:
    """Name the repository a checkout path belongs to, derived from disk.

    Never raises: a missing `git`, a path outside any checkout, or a checkout
    with no origin remote all fall through to the next step rather than
    blocking whichever claim, scan, or record call needs this. Tried in order:
    the origin remote (normalized so ssh and https collide), then the
    checkout's own toplevel path, then `None`.
    """
    try:
        remote = subprocess.run(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError:
        remote = None
    if remote is not None and remote.returncode == 0 and remote.stdout.strip():
        return _normalize_remote(remote.stdout.strip())

    try:
        toplevel = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError:
        toplevel = None
    if toplevel is not None and toplevel.returncode == 0 and toplevel.stdout.strip():
        return toplevel.stdout.strip()

    return None


def context_size(usage: dict) -> int:
    return sum(
        int(usage.get(field) or 0)
        for field in (
            "input_tokens",
            "cache_read_input_tokens",
            "cache_creation_input_tokens",
        )
    )


def detect_session(explicit: Optional[str], agent: Optional[str]) -> tuple[str, str]:
    """Name the session this verb is running in, so the claim is a fact.

    The old scan searched every transcript for the ticket id and counted the
    sessions whose operator prose contained it. That guessed at attribution and
    got it wrong in both directions: digits inside a percentage or a commit sha
    counted, while an agent-filed ticket whose id the operator never typed did
    not. The session working a ticket is known at the moment it works it, so it
    is recorded here instead.

    An agent that publishes its session id in the environment needs no flags. A
    dispatched worker whose coordinator holds the id passes both, because which
    agent wrote a session decides where its transcript lives and how its context
    is counted.
    """
    visible = [
        (name, os.environ[variable])
        for name, variable in SESSION_VARIABLES
        if os.environ.get(variable)
    ]
    names = " or ".join(name for name, _ in SESSION_VARIABLES)
    if agent and not explicit:
        raise TelemetryError("--agent needs --session")
    if agent:
        return agent, explicit
    # A Codex worker launched from a Claude session inherits that session's
    # variable, so two visible ids mean the environment cannot say which agent
    # is running. Guessing there records the coordinator's transcript against
    # the worker's ticket.
    if len(visible) > 1:
        raise TelemetryError(f"more than one agent session in the environment: pass --agent ({names})")
    if explicit:
        if visible:
            return visible[0][0], explicit
        raise TelemetryError(f"--session needs --agent ({names}) outside a known agent")
    if visible:
        return visible[0]
    variables = " or ".join(variable for _, variable in SESSION_VARIABLES)
    raise TelemetryError(f"no session id: pass --session, or run where {variables} is set")


def read_claims(ticket_id: str) -> list[dict]:
    if not CLAIMS_PATH.exists():
        return []
    claims = []
    for line in CLAIMS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            claim = json.loads(line)
        except json.JSONDecodeError:
            continue
        if claim.get("ticket_id") == ticket_id and claim.get("session_id"):
            claims.append(claim)
    return claims


def append_claim(claim: dict) -> tuple[dict, bool]:
    """Record one session against one ticket, returning authoritative state."""
    for existing in read_claims(claim["ticket_id"]):
        if existing.get("session_id") == claim["session_id"]:
            return existing, False
    CLAIMS_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with CLAIMS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(claim) + "\n")
    CLAIMS_PATH.chmod(0o600)
    return claim, True


def transcripts_for(claim: dict, projects_dir: Path) -> list[Path]:
    """Find a claimed session's transcripts by id, never by their contents.

    A resumed session writes more than one file, so this returns every match
    and the caller takes the peak across them. Picking one would report
    whichever the filesystem happened to sort first.
    """
    session_id = claim["session_id"]
    if claim.get("agent") == "codex":
        return sorted(CODEX_SESSIONS_DIR.glob(f"**/rollout-*-{session_id}.jsonl"))
    parent_sessions = projects_dir.glob(f"*/{session_id}.jsonl")
    native_workers = projects_dir.glob(f"*/*/subagents/agent-{session_id}.jsonl")
    return sorted([*parent_sessions, *native_workers])


def claude_peaks(raw: bytes, *, claimed_worker: bool = False) -> tuple[Optional[str], int, int]:
    started = None
    peak = 0
    subagent_peak = 0
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if started is None and entry.get("timestamp"):
            started = entry["timestamp"]
        if entry.get("type") != "assistant":
            continue
        size = context_size(entry.get("message", {}).get("usage", {}))
        if entry.get("isSidechain") and not claimed_worker:
            subagent_peak = max(subagent_peak, size)
        else:
            peak = max(peak, size)
    return started, peak, subagent_peak


def codex_peaks(raw: bytes) -> tuple[Optional[str], int, int]:
    """Codex reports one input total per turn, already counting its cached part.

    Summing the cached field back in would double-count it, so this is a
    maximum over one field rather than the three-field sum a Claude transcript
    needs. Codex writes no sub-agent turns into a rollout, so that peak is zero.
    """
    started = None
    peak = 0
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if started is None and entry.get("timestamp"):
            started = entry["timestamp"]
        payload = entry.get("payload", {})
        if entry.get("type") != "event_msg" or payload.get("type") != "token_count":
            continue
        usage = (payload.get("info") or {}).get("last_token_usage") or {}
        peak = max(peak, int(usage.get("input_tokens") or 0))
    return started, peak, 0


def session_cost(claim: dict, projects_dir: Path) -> dict:
    paths = transcripts_for(claim, projects_dir)
    started = None
    peak = 0
    subagent_peak = 0
    for path in paths:
        if claim.get("agent") == "codex":
            first, own, sub = codex_peaks(path.read_bytes())
        else:
            first, own, sub = claude_peaks(
                path.read_bytes(), claimed_worker=path.parent.name == "subagents"
            )
        started = min(x for x in (started, first) if x) if (started or first) else None
        peak = max(peak, own)
        subagent_peak = max(subagent_peak, sub)
    return {
        "session_id": claim["session_id"],
        "agent": claim.get("agent"),
        "role": claim.get("role") or LEGACY_ROLE,
        "verb": claim.get("verb") or LEGACY_VERB,
        "project": claim.get("project"),
        "started": started or claim.get("claimed_at"),
        "peak_context": peak,
        "subagent_peak": subagent_peak,
        "transcripts": [str(path) for path in paths],
    }


def scan(ticket_id: str, projects_dir: Path, current_repo: Optional[str]) -> dict:
    """Report peak context for this ticket id, scoped to one repository.

    A claim's `repo` was resolved once, at claim time, from the checkout it
    ran in. Reading it back here keeps two repositories' same-numbered
    tickets from merging into one measurement: a claim from another
    repository is counted but never folded in, and a claim with no
    resolvable repository (a pre-existing claim written before this field
    existed, or a resolution failure) is named rather than silently dropped
    or silently counted.
    """
    own_claims = []
    excluded = 0
    unattributable = []
    for claim in read_claims(ticket_id):
        repo = claim.get("repo")
        if repo:
            if repo == current_repo:
                own_claims.append(claim)
            else:
                excluded += 1
        else:
            unattributable.append(claim["session_id"])

    sessions = [session_cost(claim, projects_dir) for claim in own_claims]
    sessions.sort(key=lambda session: session["started"] or "")
    measured = [session for session in sessions if session["transcripts"]]

    def peaks_for(role: str) -> list[int]:
        return [session["peak_context"] for session in measured if session["role"] == role]

    def peak_for_verb(verb: str) -> int:
        return max(
            (session["peak_context"] for session in measured if session["verb"] == verb),
            default=0,
        )

    return {
        "ticket_id": ticket_id,
        "repo": current_repo,
        "session_count": len(measured),
        "claim_count": len(sessions),
        "unreadable": [
            session["session_id"] for session in sessions if not session["transcripts"]
        ],
        "excluded_claims": excluded,
        "unattributable": unattributable,
        "peak_context": max((session["peak_context"] for session in measured), default=0),
        "subagent_peak": max((session["subagent_peak"] for session in measured), default=0),
        "coordinator_peak": max(peaks_for("coordinator"), default=0),
        "worker_peaks": peaks_for("worker"),
        "reviewer_peak": max(peaks_for("reviewer"), default=0),
        "legacy_peak": max(peaks_for(LEGACY_ROLE), default=0),
        "verb_peaks": {
            verb: peak_for_verb(verb) for verb in (*VERBS, LEGACY_VERB)
        },
        "claimed_workers": len([session for session in sessions if session["role"] == "worker"]),
        "sessions": sessions,
    }


def verdict(actual: dict, chunked: bool, chunks: int) -> tuple[str, str]:
    """Compare the shape triage stamped against what the work actually cost.

    Only the sessions that built the work are evidence about how big the work
    was. Review-only sessions are overhead on every order, so their peaks are
    reported and never judged. A flat order is judged on its own peak.

    A chunked order is judged on its implementation workers' peaks alone.
    A coordinator's context grows with dispatches, returned results, review
    rounds and merges, so slicing the same work more finely can raise it while
    lowering every chunk's peak: reading it as chunk size inverts the answer.
    When every chunk worker held under the band but the coordinator did not,
    `coordination-degraded` reports that the slice was right and coordination
    was not. Incomplete worker coverage never yields `coordination-degraded`;
    it falls through to `ok` only when no earlier branch fired, because an
    unmeasured chunk could itself have crossed the band.
    `subagent_peak` cannot stand in either, because a coordinator dispatches
    review panels as sub-agents too and the transcript cannot tell the two
    apart — and per ADR 70 attribution comes from explicit claims, never from
    transcript shape. With no measured worker there is therefore no measurement
    of chunk size, which is `coordinator-only` rather than a guess.
    """
    if actual["claim_count"] == 0:
        excluded = actual.get("excluded_claims") or 0
        unattributable = actual.get("unattributable") or []
        if excluded or unattributable:
            parts = []
            if excluded:
                parts.append(f"{excluded} claim(s) from another repository")
            if unattributable:
                parts.append(f"{len(unattributable)} claim(s) with no resolvable repository")
            repo_name = actual.get("repo") or "this repository"
            return (
                "no-data",
                "this ticket had claims, but " + " and ".join(parts)
                + f", none of them from {repo_name}, so nothing measured it here",
            )
        return "no-data", "no session claimed this ticket, so nothing measured it"

    if not chunked:
        eligible = [
            session
            for session in actual["sessions"]
            if session["verb"] == "start" and session["role"] != "reviewer"
        ]
        usable = [
            session["peak_context"]
            for session in eligible
            if session["transcripts"] and session["peak_context"]
        ]
        if not usable:
            unreadable = len([session for session in eligible if not session["transcripts"]])
            zero_peak = len(
                [
                    session
                    for session in eligible
                    if session["transcripts"] and not session["peak_context"]
                ]
            )
            if eligible:
                details = []
                if unreadable:
                    unreadable_codex = len(
                        [
                            session
                            for session in eligible
                            if session["agent"] == "codex" and not session["transcripts"]
                        ]
                    )
                    if unreadable_codex:
                        details.append(
                            f"{unreadable_codex} Codex session(s) carried a start claim, "
                            "but their rollout files could not be read"
                        )
                    if unreadable > unreadable_codex:
                        details.append(
                            f"{unreadable - unreadable_codex} start claim(s) were unreadable "
                            "because their transcripts are gone"
                        )
                if zero_peak:
                    details.append(f"{zero_peak} start claim(s) recorded no usable context peak")
                reason = " and ".join(details)
            else:
                reason = (
                    "lifecycle, reviewer, or legacy claims were visible but none was an "
                    "eligible non-reviewer start claim"
                )
            return "unmeasurable", f"flat order could not be measured: {reason}"
        own = max(usable)
        if own >= DEGRADE_PEAK:
            return (
                "under-sliced",
                f"flat order execution peaked at {own:,} tokens, past the "
                f"{DEGRADE_PEAK:,} degradation band",
            )
        return "ok", f"flat order execution peaked at {own:,} tokens"

    if actual["session_count"] == 0:
        if actual["claim_count"]:
            unreadable_codex = [
                session
                for session in actual["sessions"]
                if session["agent"] == "codex" and not session["transcripts"]
            ]
            if unreadable_codex:
                return (
                    "unmeasurable",
                    f"{len(unreadable_codex)} Codex session(s) claimed this ticket, but their "
                    "rollout files could not be read, so nothing could be measured",
                )
            return (
                "unmeasurable",
                f"{actual['claim_count']} session(s) claimed this ticket and their "
                "transcripts are gone, so nothing could be measured",
            )
    judged = [session for session in actual["sessions"] if session["role"] != "reviewer"]
    own = max((session["peak_context"] for session in judged), default=0)
    worker_peaks = [peak for peak in actual["worker_peaks"] if peak]
    if not worker_peaks:
        if actual["peak_context"] == 0:
            return (
                "unmeasurable",
                f"{chunks} chunk(s), but no usable context peak was measured, so chunk size "
                "could not be measured",
            )
        measured_roles = {
            session["role"] for session in actual["sessions"] if session["transcripts"]
        }
        if measured_roles and measured_roles <= {"reviewer"}:
            shape = "only review-only sessions were measured"
        else:
            shape = f"the sessions that were measured peaked at {own:,} tokens"
        return (
            "coordinator-only",
            f"{chunks} chunk(s), but chunk size was not measured: "
            f"{actual['claimed_workers']} claim(s) carried an implementation-worker role "
            f"and 0 of them were measurable; {shape}",
        )

    peak = max(worker_peaks)
    if peak >= DEGRADE_PEAK:
        return (
            "still-degraded",
            f"{chunks} chunk(s) and the largest implementation worker still peaked at "
            f"{peak:,} tokens, past the {DEGRADE_PEAK:,} degradation band; the chunks were too big",
        )
    if chunks > 1 and peak < FLOOR_PEAK:
        # over-sliced says no chunk was big enough to need its own agent, which
        # takes a measured worker for every chunk. An unreadable or never-claimed
        # worker leaves a chunk whose cost is unknown, and an unknown chunk
        # cannot be the small one. More workers than chunks is ordinary rather
        # than suspicious: a chunk that escalates a tier claims the escalation as
        # a second worker session, so the test is coverage, not equality.
        if len(worker_peaks) >= chunks:
            return (
                "over-sliced",
                f"{chunks} chunks but no implementation worker exceeded {peak:,} tokens; "
                "one agent would have held it",
            )
        return (
            "ok",
            f"{len(worker_peaks)} of {chunks} chunk(s) measured an implementation worker, "
            f"peaking at {peak:,} tokens; too few to call it over-sliced",
        )
    if len(worker_peaks) >= chunks and actual["coordinator_peak"] >= DEGRADE_PEAK:
        return (
            "coordination-degraded",
            f"{chunks} chunk(s) and every measured implementation worker held under the "
            f"{DEGRADE_PEAK:,} degradation band, but the coordinator peaked at "
            f"{actual['coordinator_peak']:,} tokens; the slice was right while the "
            "coordinating session was not",
        )
    return "ok", f"implementation workers peaked at {peak:,} tokens across {chunks} chunk(s)"


def report_write_denial(path: Path, error: OSError) -> None:
    """Tell a sandboxed session its telemetry write was denied and how to fix it.

    A sandbox permission denial is not a workflow failure: telemetry is a
    measurement, never a gate. One line to stderr names the denied path and
    the remedy, so a rerun of the same command outside the sandbox (or with
    escalated permissions) succeeds.
    """
    print(
        f"ticket: could not write {path} ({error.strerror or error}); "
        "rerun this command outside the sandbox or with escalated permissions",
        file=sys.stderr,
    )


def append_record(record: dict) -> Path:
    TELEMETRY_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with TELEMETRY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    TELEMETRY_PATH.chmod(0o600)
    return TELEMETRY_PATH


def command_scan(arguments: argparse.Namespace) -> int:
    ticket_id = validate_ticket_id(arguments.ticket_id)
    current_repo = resolve_repo(Path(arguments.project) if arguments.project else Path.cwd())
    result = scan(ticket_id, arguments.projects_dir, current_repo)
    print(json.dumps(result, indent=2))
    return 0


def command_record(arguments: argparse.Namespace) -> int:
    ticket_id = validate_ticket_id(arguments.ticket_id)
    current_repo = resolve_repo(Path(arguments.project) if arguments.project else Path.cwd())
    actual = scan(ticket_id, arguments.projects_dir, current_repo)
    call, reason = verdict(actual, arguments.chunked, arguments.chunks)
    record = {
        "ticket_id": ticket_id,
        "verbs": arguments.verb,
        "traits": arguments.trait,
        "depth": arguments.depth,
        "chunked": arguments.chunked,
        "chunks": arguments.chunks,
        "repo": actual["repo"],
        "session_count": actual["session_count"],
        "claim_count": actual["claim_count"],
        "unreadable": actual["unreadable"],
        "excluded_claims": actual["excluded_claims"],
        "unattributable": actual["unattributable"],
        "peak_context": actual["peak_context"],
        "subagent_peak": actual["subagent_peak"],
        "coordinator_peak": actual["coordinator_peak"],
        "worker_peaks": actual["worker_peaks"],
        "reviewer_peak": actual["reviewer_peak"],
        "legacy_peak": actual["legacy_peak"],
        "verb_peaks": actual["verb_peaks"],
        "claimed_workers": actual["claimed_workers"],
        "session_peaks": [
            session["peak_context"] for session in actual["sessions"] if session["transcripts"]
        ],
        "verdict": call,
        "reason": reason,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    if call not in ("no-data", "unmeasurable"):
        try:
            append_record(record)
        except OSError as error:
            report_write_denial(TELEMETRY_PATH, error)
    print(json.dumps(record, indent=2))
    return 0


def command_claim(arguments: argparse.Namespace) -> int:
    ticket_id = validate_ticket_id(arguments.ticket_id)
    agent, session_id = detect_session(
        validate_session_id(arguments.session) if arguments.session else None,
        arguments.agent,
    )
    project = arguments.project or str(Path.cwd())
    claim = {
        "ticket_id": ticket_id,
        "session_id": session_id,
        "agent": agent,
        "role": arguments.role,
        "verb": arguments.verb,
        "project": project,
        "repo": resolve_repo(Path(project)),
        "claimed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        persisted, written = append_claim(claim)
        already_claimed = not written
        persisted_verb = persisted.get("verb") or LEGACY_VERB
        if already_claimed and persisted_verb != arguments.verb:
            print(
                "ticket telemetry: claim conflict: "
                f"persisted verb '{persisted_verb}', submitted verb '{arguments.verb}'; "
                "kept the persisted claim",
                file=sys.stderr,
            )
    except OSError as error:
        report_write_denial(CLAIMS_PATH, error)
        persisted = claim
        already_claimed = False
    print(json.dumps({**persisted, "already_claimed": already_claimed}, indent=2))
    return 0


def add_common_flags(target: argparse.ArgumentParser) -> None:
    target.add_argument("ticket_id", help="ticket id, exactly as the tracker names it")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--projects-dir",
        type=lambda value: Path(value).expanduser(),
        default=PROJECTS_DIR,
        help=f"local session transcript root (default {PROJECTS_DIR})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    claim_parser = subparsers.add_parser(
        "claim", help="record that this session is working this ticket"
    )
    add_common_flags(claim_parser)
    claim_parser.add_argument(
        "--session", default=None, help="session id, when the environment carries none"
    )
    claim_parser.add_argument(
        "--agent",
        choices=[name for name, _ in SESSION_VARIABLES],
        default=None,
        help="which agent wrote the session; needed with --session outside a known agent",
    )
    claim_parser.add_argument(
        "--role",
        choices=ROLES,
        default="coordinator",
        help="what this session is doing on the ticket (default: coordinator)",
    )
    claim_parser.add_argument(
        "--verb",
        choices=VERBS,
        required=True,
        help="ticket lifecycle verb that produced this claim",
    )
    claim_parser.add_argument(
        "--project", default=None, help="working directory to record (default: this one)"
    )
    claim_parser.set_defaults(handler=command_claim)

    scan_parser = subparsers.add_parser(
        "scan", help="report peak context per session that worked this ticket id"
    )
    add_common_flags(scan_parser)
    scan_parser.add_argument(
        "--project", default=None, help="working directory to record (default: this one)"
    )
    scan_parser.set_defaults(handler=command_scan)

    record_parser = subparsers.add_parser(
        "record", help="append this ticket's measured cost and print the verdict"
    )
    add_common_flags(record_parser)
    record_parser.add_argument(
        "--project", default=None, help="working directory to record (default: this one)"
    )
    record_parser.add_argument(
        "--verb", action="append", required=True, help="workflow verb that ran; repeatable"
    )
    record_parser.add_argument(
        "--trait",
        action="append",
        required=True,
        help="slicing rubric trait that fired; repeatable",
    )
    record_parser.add_argument("--depth", required=True, help="review depth that was stamped")
    record_parser.add_argument("--chunked", action="store_true", help="the order was chunked")
    record_parser.add_argument(
        "--chunks", type=int, default=1, help="chunk count when --chunked is set"
    )
    record_parser.set_defaults(handler=command_record)

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        return int(arguments.handler(arguments))
    except TelemetryError as error:
        print(f"ticket: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
