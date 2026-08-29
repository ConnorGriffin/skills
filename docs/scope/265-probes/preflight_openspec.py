#!/usr/bin/env python3
"""Executable spike for issue 265's non-mutating OpenSpec preflight."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("change")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()

    source = args.repo.resolve() / "openspec"
    if not source.is_dir():
        print(f"ticket: OpenSpec root not found: {source}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="ticket-openspec-preflight-") as scratch:
        root = Path(scratch)
        shutil.copytree(source, root / "openspec")
        result = subprocess.run(
            ["openspec", "archive", args.change, "--json", "--yes"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        print(f"ticket: OpenSpec archive returned invalid JSON: {error}", file=sys.stderr)
        return 2

    errors = [item for item in payload.get("status", []) if item.get("severity") == "error"]
    if payload.get("archive") is None or errors:
        for item in errors:
            message = item.get("message", "OpenSpec archive preflight failed")
            print(f"ticket: {message}", file=sys.stderr)
            if item.get("code") == "archive_spec_update_failed":
                print(
                    "ticket: if this requirement was renamed, add a `## RENAMED "
                    "Requirements` mapping from its current baseline header to the "
                    "unmatched delta header; otherwise correct the MODIFIED header.",
                    file=sys.stderr,
                )
        return result.returncode or 1

    if result.returncode:
        print(result.stderr.strip() or result.stdout.strip(), file=sys.stderr)
        return result.returncode

    print(f"ticket: OpenSpec change {args.change} applies cleanly in a disposable copy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
