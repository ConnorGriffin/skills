#!/usr/bin/env python3
"""Executable spike for deriving ordinary active changes from a ticket diff."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path, PurePosixPath


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base-ref", required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    resolved = subprocess.run(
        [
            "git",
            "rev-parse",
            "--verify",
            "--end-of-options",
            f"{args.base_ref}^{{commit}}",
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if resolved.returncode:
        print(
            f"base ref does not resolve to a local commit: {args.base_ref}",
            file=sys.stderr,
        )
        return 2
    base_commit = resolved.stdout.strip()
    merge_base = subprocess.run(
        ["git", "merge-base", "HEAD", base_commit],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    result = subprocess.run(
        ["git", "diff", "--name-only", merge_base, "--", "openspec/changes"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    changes: set[str] = set()
    for line in result.stdout.splitlines():
        parts = PurePosixPath(line).parts
        active = repo / "openspec" / "changes" / parts[2] if len(parts) >= 3 else None
        if (
            active is not None
            and parts[:2] == ("openspec", "changes")
            and parts[2] != "archive"
            and active.is_dir()
        ):
            changes.add(parts[2])
    if len(changes) > 1:
        parser.error("ordinary tickets may change at most one active OpenSpec change")
    for change in sorted(changes):
        print(change)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
