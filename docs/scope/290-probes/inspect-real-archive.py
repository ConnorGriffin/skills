#!/usr/bin/env python3
"""Confirm Codex's real archive root and filename shape without exposing metadata."""

from __future__ import annotations

import json
import os
from pathlib import Path


codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
archive = codex_home / "archived_sessions"
has_rollout = next(archive.rglob("rollout-*.jsonl"), None) is not None
print(
    json.dumps(
        {
            "root": "archived_sessions",
            "filename_shape": "rollout-<timestamp>-<session-id>.jsonl",
            "matching_rollout_exists": has_rollout,
        },
        indent=2,
    )
)
