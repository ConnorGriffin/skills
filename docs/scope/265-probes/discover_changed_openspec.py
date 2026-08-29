#!/usr/bin/env python3
"""Executable spike for deriving ordinary active changes from a ticket diff."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path, PurePosixPath


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", required=True)
    args = parser.parse_args()

    result = subprocess.run(
        ["git", "diff", "--name-only", args.base, "--", "openspec/changes"],
        cwd=args.repo.resolve(),
        text=True,
        capture_output=True,
        check=True,
    )
    changes: set[str] = set()
    for line in result.stdout.splitlines():
        parts = PurePosixPath(line).parts
        if len(parts) >= 3 and parts[:2] == ("openspec", "changes") and parts[2] != "archive":
            changes.add(parts[2])
    for change in sorted(changes):
        print(change)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
