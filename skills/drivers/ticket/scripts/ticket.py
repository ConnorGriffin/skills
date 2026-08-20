#!/usr/bin/env python3
"""Context telemetry for the ticket workflow: measure what a ticket cost.

Scans this agent's own local session transcripts for a ticket id and reports
peak context per session, then records the actuals so the slicing rubric can
be retuned against real numbers. Every record carries counts and labels
supplied on the command line: never a transcript excerpt, a prompt, or any
other prose from a session.
"""

from __future__ import annotations

import argparse
import json
import os
import re
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


def transcript_files(projects_dir: Path) -> Iterator[Path]:
    if not projects_dir.exists():
        raise TelemetryError(f"no transcript directory: {projects_dir}")
    yield from sorted(projects_dir.glob("*/*.jsonl"))


def user_text(entry: dict) -> str:
    """Prose the operator typed, excluding tool results.

    A ticket id that appears only inside a tool result was read by an agent,
    not typed by the operator: that session looked at the ticket, it did not
    necessarily work it.
    """
    if entry.get("type") != "user":
        return ""
    content = entry.get("message", {}).get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return " ".join(
        str(block.get("text", ""))
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    )


def typed_reference(ticket_id: str) -> "re.Pattern[str]":
    """Match the id as a reference to the ticket, not as digits inside something else.

    A bare substring test counts any session whose prose happens to contain the
    digits: a percentage (62.67%), a hex task id, a commit sha, a line range
    (SKILL.md:8, 62-64), or another repository's pull request (dotfiles/pull/62).
    Those sessions never worked the ticket, and their peaks skew the slicing
    rubric they are recorded to calibrate. So the neighbours decide: an
    alphanumeric, underscore, hyphen, or slash on either side means the id is
    part of something longer, and a digit across a decimal point means a number.
    A sentence-final "62." still counts.
    """
    return re.compile(
        rf"(?<![0-9A-Za-z_/-])(?<!\d\.){re.escape(ticket_id)}(?![0-9A-Za-z_/-])(?!\.\d)"
    )


def scan_transcript(path: Path, ticket_id: str) -> Optional[dict]:
    raw = path.read_bytes()
    if ticket_id.encode() not in raw:
        return None

    reference = typed_reference(ticket_id)
    typed = False
    peak = 0
    subagent_peak = 0
    started = None

    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if started is None and entry.get("timestamp"):
            started = entry["timestamp"]
        if not typed and reference.search(user_text(entry)):
            typed = True
        if entry.get("type") != "assistant":
            continue
        size = context_size(entry.get("message", {}).get("usage", {}))
        if entry.get("isSidechain"):
            subagent_peak = max(subagent_peak, size)
        else:
            peak = max(peak, size)

    if not typed:
        return None
    return {
        "session_id": path.stem,
        "project": path.parent.name,
        "started": started,
        "peak_context": peak,
        "subagent_peak": subagent_peak,
    }


def scan(ticket_id: str, projects_dir: Path, project: Optional[str] = None) -> dict:
    paths = [
        path
        for path in transcript_files(projects_dir)
        if project is None or project in path.parent.name
    ]
    sessions = [
        session
        for session in (scan_transcript(path, ticket_id) for path in paths)
        if session is not None
    ]
    sessions.sort(key=lambda session: session["started"] or "")
    return {
        "ticket_id": ticket_id,
        "session_count": len(sessions),
        "peak_context": max((session["peak_context"] for session in sessions), default=0),
        "subagent_peak": max((session["subagent_peak"] for session in sessions), default=0),
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
        return "no-data", "no local transcript was typed against this ticket id"
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
    result = scan(ticket_id, arguments.projects_dir, arguments.project)
    print(json.dumps(result, indent=2))
    return 0


def command_record(arguments: argparse.Namespace) -> int:
    ticket_id = validate_ticket_id(arguments.ticket_id)
    actual = scan(ticket_id, arguments.projects_dir, arguments.project)
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


def add_common_flags(target: argparse.ArgumentParser) -> None:
    target.add_argument("ticket_id", help="ticket id to look for, exactly as typed by the operator")
    target.add_argument(
        "--project",
        default=None,
        help="restrict to transcript directories containing this substring",
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--projects-dir",
        type=lambda value: Path(value).expanduser(),
        default=PROJECTS_DIR,
        help=f"local session transcript root (default {PROJECTS_DIR})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

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
