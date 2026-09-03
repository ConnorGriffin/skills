#!/usr/bin/env python3
"""Reproduce ticket 290 with public ticket commands and isolated local data."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TICKET = ROOT / "skills" / "drivers" / "ticket" / "scripts" / "ticket.py"


def run(environment: dict[str, str], *arguments: str) -> dict:
    result = subprocess.run(
        ["python3", str(TICKET), *arguments],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def rollout(path: Path, session_id: str, peak: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "timestamp": "2026-08-30T00:00:00Z",
            "type": "session_meta",
            "payload": {"id": session_id},
        },
        {
            "timestamp": "2026-08-30T00:00:01Z",
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": {"last_token_usage": {"input_tokens": peak}},
            },
        },
    ]
    path.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n")


with tempfile.TemporaryDirectory() as temporary:
    scratch = Path(temporary)
    codex_home = scratch / "codex-home"
    environment = os.environ.copy()
    environment.pop("CLAUDE_CODE_SESSION_ID", None)
    environment.pop("CODEX_SESSION_ID", None)
    environment["CODEX_HOME"] = str(codex_home)
    environment["TICKET_CLAIMS"] = str(scratch / "claims.jsonl")
    environment["CLAUDE_PROJECTS_DIR"] = str(scratch / "projects")

    archived_id = "codex-archived-290"
    rollout(
        codex_home / "archived_sessions" / f"rollout-2026-08-30-{archived_id}.jsonl",
        archived_id,
        228_055,
    )
    run(
        environment,
        "claim",
        "REPRO-290-ARCHIVED",
        "--session",
        archived_id,
        "--agent",
        "codex",
        "--verb",
        "start",
        "--role",
        "coordinator",
    )
    archived = run(environment, "scan", "REPRO-290-ARCHIVED")

    active_id = "codex-active-290"
    rollout(
        codex_home
        / "sessions"
        / "2026"
        / "08"
        / "30"
        / f"rollout-2026-08-30-{active_id}.jsonl",
        active_id,
        228_055,
    )
    run(
        environment,
        "claim",
        "REPRO-290-ACTIVE",
        "--session",
        active_id,
        "--agent",
        "codex",
        "--verb",
        "start",
        "--role",
        "coordinator",
    )
    active = run(
        environment,
        "record",
        "REPRO-290-ACTIVE",
        "--verb",
        "start",
        "--trait",
        "narrow-scope",
        "--depth",
        "full",
    )

    print(
        json.dumps(
            {
                "archived_only": {
                    "session_count": archived["session_count"],
                    "unreadable": archived["unreadable"],
                },
                "active_threshold": {
                    "peak_context": active["peak_context"],
                    "verdict": active["verdict"],
                    "reason": active["reason"],
                },
            },
            indent=2,
        )
    )
