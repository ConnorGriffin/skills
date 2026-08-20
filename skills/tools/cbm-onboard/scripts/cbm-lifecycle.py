#!/usr/bin/env python3
"""Shared contract checks for ephemeral Codebase Memory lifecycle scripts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


MINIMUM_VERSION = (0, 10, 8)
VERSION_PATTERN = re.compile(rb"codebase-memory-mcp (0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\n?\Z")


def fail(message: str) -> "NoReturn":
    print(message, file=sys.stderr)
    raise SystemExit(1)


def identity(target: str, *, main_checkout: bool = False) -> None:
    git_arguments = (
        ["worktree", "list", "--porcelain", "-z"]
        if main_checkout
        else ["rev-parse", "--show-toplevel"]
    )
    result = subprocess.run(
        ["git", "-C", target, *git_arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        fail(f"not a Git repository: {target}")
    if main_checkout:
        fields = result.stdout.split(b"\0")
        reported = next(
            (field[len(b"worktree ") :] for field in fields if field.startswith(b"worktree ")),
            b"",
        )
    else:
        if not result.stdout.endswith(b"\n"):
            fail(f"not a Git repository: {target}")
        reported = result.stdout[:-1]
    if not reported:
        fail(f"not a Git repository: {target}")
    if b"\n" in reported:
        fail("checkout paths containing newline bytes are unsupported")
    root = os.path.realpath(os.fsdecode(reported))
    root_bytes = os.fsencode(root)
    if b"\n" in root_bytes:
        fail("checkout paths containing newline bytes are unsupported")
    project = "cbm-onboard-v1-" + hashlib.sha256(root_bytes).hexdigest()
    json.dump({"root": root, "project": project}, sys.stdout)
    sys.stdout.write("\n")


def validate_version(path: str) -> None:
    banner = Path(path).read_bytes()
    match = VERSION_PATTERN.fullmatch(banner)
    if not match:
        fail("unsupported codebase-memory-mcp version banner")
    version = tuple(int(component) for component in match.groups())
    if version < MINIMUM_VERSION:
        fail("codebase-memory-mcp 0.10.8 or newer is required")


def validate_response(project: str, status: str, is_error: str, path: str) -> None:
    try:
        envelope = json.loads(Path(path).read_text(encoding="utf-8"))
        structured = envelope["structuredContent"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
        fail("invalid Codebase Memory JSON response")
    expected_error = is_error == "true"
    if (
        not isinstance(structured, dict)
        or structured.get("project") != project
        or structured.get("status") != status
        or envelope.get("isError") is not expected_error
    ):
        fail("Codebase Memory response did not match the requested project and status")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "identity":
        identity(sys.argv[2])
        return
    if len(sys.argv) == 4 and sys.argv[1:3] == ["identity", "--main"]:
        identity(sys.argv[3], main_checkout=True)
        return
    if len(sys.argv) == 3 and sys.argv[1] == "version":
        validate_version(sys.argv[2])
        return
    if len(sys.argv) == 6 and sys.argv[1] == "response":
        validate_response(*sys.argv[2:])
        return
    fail("usage: cbm-lifecycle.py identity [--main] PATH | version FILE | response PROJECT STATUS BOOL FILE")


if __name__ == "__main__":
    main()
