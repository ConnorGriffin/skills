#!/usr/bin/env python3
"""Executable spike for issue 265's non-mutating OpenSpec preflight."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("change")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base-ref")
    args = parser.parse_args()

    source = args.repo.resolve() / "openspec"
    if not source.is_dir():
        print(f"ticket: OpenSpec root not found: {source}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="ticket-openspec-preflight-") as scratch:
        root = Path(scratch)
        if args.base_ref:
            archive_path = root / "openspec.tar"
            exported = subprocess.run(
                ["git", "archive", "--format=tar", f"--output={archive_path}", args.base_ref, "openspec"],
                cwd=args.repo.resolve(),
                text=True,
                capture_output=True,
                check=False,
            )
            if exported.returncode:
                print(exported.stderr.strip(), file=sys.stderr)
                return exported.returncode
            with tarfile.open(archive_path) as bundle:
                bundle.extractall(root, filter="data")
            change_source = source / "changes" / args.change
            if not change_source.is_dir():
                print(f"ticket: active OpenSpec change not found: {change_source}", file=sys.stderr)
                return 2
            shutil.copytree(change_source, root / "openspec" / "changes" / args.change)
        else:
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

    if not isinstance(payload, dict):
        print("ticket: OpenSpec archive JSON must be an object", file=sys.stderr)
        return 2
    status = payload.get("status", [])
    if not isinstance(status, list) or any(not isinstance(item, dict) for item in status):
        print("ticket: OpenSpec archive status must be a list of objects", file=sys.stderr)
        return 2
    archive = payload.get("archive")
    if archive is not None and not isinstance(archive, dict):
        print("ticket: OpenSpec archive result must be an object", file=sys.stderr)
        return 2

    errors = [item for item in status if item.get("severity") == "error"]
    if archive is None or errors:
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
