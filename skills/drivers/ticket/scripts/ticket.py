#!/usr/bin/env python3
"""Context telemetry for the ticket workflow: measure what a ticket cost.

Each verb claims its own session against the ticket it is working, so the set
of sessions that worked a ticket is recorded rather than inferred. Reports
peak context per claimed session, then records the actuals so the slicing
rubric can be retuned against real numbers. Every record carries counts and labels
supplied on the command line: never a transcript excerpt, a prompt, or any
other prose from a session.
"""

from __future__ import annotations

import argparse
import json
import os
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
    running = next(
        ((name, os.environ[variable]) for name, variable in SESSION_VARIABLES if os.environ.get(variable)),
        None,
    )
    if explicit:
        if agent:
            return agent, explicit
        if running:
            return running[0], explicit
        names = " or ".join(name for name, _ in SESSION_VARIABLES)
        raise TelemetryError(f"--session needs --agent ({names}) outside a known agent")
    if agent:
        raise TelemetryError("--agent needs --session")
    if running:
        return running
    names = " or ".join(variable for _, variable in SESSION_VARIABLES)
    raise TelemetryError(f"no session id: pass --session, or run where {names} is set")


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
        if claim.get("ticket_id") == ticket_id:
            claims.append(claim)
    return claims


def append_claim(claim: dict) -> Optional[Path]:
    """Record one session against one ticket, once."""
    for existing in read_claims(claim["ticket_id"]):
        if existing.get("session_id") == claim["session_id"]:
            return None
    CLAIMS_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with CLAIMS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(claim) + "\n")
    CLAIMS_PATH.chmod(0o600)
    return CLAIMS_PATH


def transcript_for(claim: dict, projects_dir: Path) -> Optional[Path]:
    """Find one claimed session's transcript by its id, never by its contents."""
    session_id = claim.get("session_id", "")
    if not session_id:
        return None
    if claim.get("agent") == "codex":
        matches = sorted(CODEX_SESSIONS_DIR.glob(f"**/rollout-*-{session_id}.jsonl"))
    else:
        matches = sorted(projects_dir.glob(f"*/{session_id}.jsonl"))
    return matches[0] if matches else None


def claude_peaks(raw: bytes) -> tuple[Optional[str], int, int]:
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
        if entry.get("isSidechain"):
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
    path = transcript_for(claim, projects_dir)
    session = {
        "session_id": claim.get("session_id"),
        "agent": claim.get("agent"),
        "project": claim.get("project"),
        "started": claim.get("claimed_at"),
        "peak_context": 0,
        "subagent_peak": 0,
        "transcript": None,
    }
    if path is None:
        return session
    started, peak, subagent_peak = (
        codex_peaks(path.read_bytes())
        if claim.get("agent") == "codex"
        else claude_peaks(path.read_bytes())
    )
    session.update(
        started=started or session["started"],
        peak_context=peak,
        subagent_peak=subagent_peak,
        transcript=str(path),
    )
    return session


def scan(ticket_id: str, projects_dir: Path) -> dict:
    sessions = [session_cost(claim, projects_dir) for claim in read_claims(ticket_id)]
    sessions.sort(key=lambda session: session["started"] or "")
    measured = [session for session in sessions if session["transcript"]]
    return {
        "ticket_id": ticket_id,
        "session_count": len(measured),
        "claim_count": len(sessions),
        "unreadable": [
            session["session_id"] for session in sessions if not session["transcript"]
        ],
        "peak_context": max((session["peak_context"] for session in measured), default=0),
        "subagent_peak": max((session["subagent_peak"] for session in measured), default=0),
        "sessions": sessions,
    }


def verdict(actual: dict, chunked: bool, chunks: int) -> tuple[str, str]:
    """Compare the shape triage stamped against what the work actually cost.

    A flat order is judged on its own sessions only: sub-agents run on most
    tickets (review panels), so counting their context against a flat order
    would misread ordinary review overhead as work that needed slicing. On a
    chunked order the chunk builders are themselves sub-agents, so their peak
    is the work and counts.
    """
    if actual["session_count"] == 0:
        return "no-data", "no session claimed this ticket, so nothing measured it"
    own = max(session["peak_context"] for session in actual["sessions"])
    if not chunked:
        if own >= DEGRADE_PEAK:
            return (
                "under-sliced",
                f"flat order peaked at {own:,} tokens, past the {DEGRADE_PEAK:,} degradation band",
            )
        return "ok", f"peaked at {own:,} tokens across {actual['session_count']} session(s)"
    peak = max(own, actual["subagent_peak"])
    if peak >= DEGRADE_PEAK:
        return (
            "still-degraded",
            f"{chunks} chunk(s) and it still peaked at {peak:,} tokens, past the "
            f"{DEGRADE_PEAK:,} degradation band; the chunks were too big",
        )
    if chunks > 1 and peak < FLOOR_PEAK:
        return (
            "over-sliced",
            f"{chunks} chunks but nothing exceeded {peak:,} tokens; one agent would have held it",
        )
    return "ok", f"peaked at {peak:,} tokens across {chunks} chunk(s)"


def append_record(record: dict) -> Path:
    TELEMETRY_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with TELEMETRY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    TELEMETRY_PATH.chmod(0o600)
    return TELEMETRY_PATH


def command_scan(arguments: argparse.Namespace) -> int:
    ticket_id = validate_ticket_id(arguments.ticket_id)
    result = scan(ticket_id, arguments.projects_dir)
    print(json.dumps(result, indent=2))
    return 0


def command_record(arguments: argparse.Namespace) -> int:
    ticket_id = validate_ticket_id(arguments.ticket_id)
    actual = scan(ticket_id, arguments.projects_dir)
    call, reason = verdict(actual, arguments.chunked, arguments.chunks)
    record = {
        "ticket_id": ticket_id,
        "verbs": arguments.verb,
        "traits": arguments.trait,
        "depth": arguments.depth,
        "chunked": arguments.chunked,
        "chunks": arguments.chunks,
        "session_count": actual["session_count"],
        "peak_context": actual["peak_context"],
        "subagent_peak": actual["subagent_peak"],
        "session_peaks": [session["peak_context"] for session in actual["sessions"]],
        "verdict": call,
        "reason": reason,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    if call != "no-data":
        append_record(record)
    print(json.dumps(record, indent=2))
    return 0


def command_claim(arguments: argparse.Namespace) -> int:
    ticket_id = validate_ticket_id(arguments.ticket_id)
    agent, session_id = detect_session(arguments.session, arguments.agent)
    claim = {
        "ticket_id": ticket_id,
        "session_id": session_id,
        "agent": agent,
        "project": arguments.project or str(Path.cwd()),
        "claimed_at": datetime.now(timezone.utc).isoformat(),
    }
    written = append_claim(claim)
    print(json.dumps({**claim, "already_claimed": written is None}, indent=2))
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
        "--project", default=None, help="working directory to record (default: this one)"
    )
    claim_parser.set_defaults(handler=command_claim)

    scan_parser = subparsers.add_parser(
        "scan", help="report peak context per session that worked this ticket id"
    )
    add_common_flags(scan_parser)
    scan_parser.set_defaults(handler=command_scan)

    record_parser = subparsers.add_parser(
        "record", help="append this ticket's measured cost and print the verdict"
    )
    add_common_flags(record_parser)
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
