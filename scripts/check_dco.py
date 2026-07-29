#!/usr/bin/env python3
"""Require a valid Signed-off-by trailer on every commit in a revision range."""

from __future__ import annotations

import re
import subprocess
import sys


SIGNOFF = re.compile(
    r"^Signed-off-by:\s+.+\s+<[^<>\s@]+@[^<>\s@]+>$",
    re.MULTILINE,
)


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    return completed.stdout


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: check_dco.py <base-sha> <head-sha>", file=sys.stderr)
        return 2
    base, head = sys.argv[1:]
    try:
        commits = git("rev-list", "--reverse", f"{base}..{head}").splitlines()
        missing = [
            revision
            for revision in commits
            if not SIGNOFF.search(git("show", "-s", "--format=%B", revision))
        ]
    except RuntimeError as error:
        print(f"DCO check failed: {error}", file=sys.stderr)
        return 2
    if missing:
        print(
            "Missing valid Signed-off-by trailer: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1
    print(f"DCO_OK commits={len(commits)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
