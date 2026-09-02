#!/usr/bin/env python3
"""Confirm Codex's archive naming contract without exposing session metadata."""

from __future__ import annotations

import json
import os
from pathlib import Path


codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
archive = codex_home / "archived_sessions"
rollouts = list(archive.rglob("rollout-*.jsonl"))


def filename_ends_with_metadata_id(path: Path) -> bool:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "session_meta":
                continue
            session_id = entry.get("payload", {}).get("id")
            return bool(session_id) and path.name.endswith(f"-{session_id}.jsonl")
    return False


print(
    json.dumps(
        {
            "root": "archived_sessions",
            "checked_at_least_one_rollout": bool(rollouts),
            "all_checked_filenames_end_with_metadata_id": bool(rollouts)
            and all(filename_ends_with_metadata_id(path) for path in rollouts),
        },
        indent=2,
    )
)
