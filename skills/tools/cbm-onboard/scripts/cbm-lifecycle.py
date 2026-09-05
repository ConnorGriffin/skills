#!/usr/bin/env python3
"""Shared contract checks for ephemeral Codebase Memory lifecycle scripts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


MINIMUM_VERSION = (0, 10, 8)
VERSION_PATTERN = re.compile(rb"codebase-memory-mcp (0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\n?\Z")
# The exact response Codebase Memory gives for a project it does not hold. Only
# this signal permits indexing; anything else is a failure rather than a miss.
MISSING_PROJECT_ERROR = "project not found or not indexed"


def fail(message: str) -> "NoReturn":
    print(message, file=sys.stderr)
    raise SystemExit(1)


def physical_identity(target: str, *, main_checkout: bool = False) -> tuple[str, str]:
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
    return root, project


def identity(target: str, *, main_checkout: bool = False) -> None:
    root, project = physical_identity(target, main_checkout=main_checkout)
    json.dump({"root": root, "project": project}, sys.stdout)
    sys.stdout.write("\n")


def parsed_version(banner: bytes) -> "tuple[int, ...] | None":
    match = VERSION_PATTERN.fullmatch(banner)
    return tuple(int(component) for component in match.groups()) if match else None


def validate_version(path: str) -> None:
    version = parsed_version(Path(path).read_bytes())
    if version is None:
        fail("unsupported codebase-memory-mcp version banner")
    if version < MINIMUM_VERSION:
        fail("codebase-memory-mcp 0.10.8 or newer is required")


def read_envelope(raw: str) -> tuple[dict, object]:
    """Split one Codebase Memory response into its structured body and error flag."""

    try:
        envelope = json.loads(raw)
        structured = envelope["structuredContent"]
    except (json.JSONDecodeError, KeyError, TypeError):
        fail("invalid Codebase Memory JSON response")
    if not isinstance(structured, dict):
        fail("invalid Codebase Memory JSON response")
    return structured, envelope.get("isError")


def validate_response(project: str, status: str, is_error: str, path: str) -> None:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        fail("invalid Codebase Memory JSON response")
    structured, reported_error = read_envelope(raw)
    if (
        structured.get("project") != project
        or structured.get("status") != status
        or reported_error is not (is_error == "true")
    ):
        fail("Codebase Memory response did not match the requested project and status")


def unavailable(reason: str) -> "NoReturn":
    """Report the visible degraded mode without exposing tool output."""

    json.dump({"status": "unavailable"}, sys.stdout)
    sys.stdout.write("\n")
    print(reason, file=sys.stderr)
    raise SystemExit(2)


def unavailable_reason(diagnostic: str) -> str:
    """Turn a bounded tool failure class into safe operator guidance."""

    if (
        "active generation" in diagnostic.lower()
        or "active-generation" in diagnostic.lower()
        or "generation is active" in diagnostic.lower()
    ):
        return (
            "Codebase Memory has an active-generation conflict; wait for that generation "
            "to finish, then retry this checkout. Do not terminate unrelated sessions."
        )
    return (
        "Codebase Memory could not return a response. Verify its supported version; "
        "in a workspace-write sandbox, retry this same command with the documented "
        "local-only permission rationale."
    )


def envelope_or_unavailable(code: int, raw: str, diagnostic: str) -> tuple[dict, object]:
    """Read one tool response, distinguishing "produced nothing" from "answered wrongly".

    A nonzero exit paired with empty stdout means the binary could not operate
    at all here (for example a sandbox that blocks the daemon endpoint it
    needs) — the same degraded mode as a missing or too-old binary, reported
    as `unavailable`. A zero exit with empty stdout is still a protocol
    violation: the tool claimed success and said nothing, which is not a case
    where "no graph is available" is a safe conclusion. Non-empty stdout that
    fails to parse is always a protocol violation regardless of exit code.
    """

    if code != 0 and raw == "":
        unavailable(unavailable_reason(diagnostic))
    return read_envelope(raw)


def usable_binary() -> str:
    configured = os.environ.get("CODEBASE_MEMORY_BIN") or shutil.which("codebase-memory-mcp")
    if not configured or not os.access(configured, os.X_OK):
        unavailable("codebase-memory-mcp was not found or is not executable.")
    banner = subprocess.run(
        [configured, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    version = parsed_version(banner.stdout) if banner.returncode == 0 else None
    if version is None or version < MINIMUM_VERSION:
        unavailable("codebase-memory-mcp does not report a supported version (0.10.8 or newer).")
    return configured


def call_tool(binary: str, arguments: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(
        [binary, "cli", "--json", *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return (
        result.returncode,
        result.stdout.decode("utf-8", "replace"),
        result.stderr.decode("utf-8", "replace"),
    )


def ready_for(structured: dict, reported_error: object, project: str, root: str) -> bool:
    return (
        reported_error is False
        and structured.get("project") == project
        and structured.get("status") == "ready"
        and structured.get("root_path") == root
    )


def ensure(target: str) -> None:
    """Make the exact project for one physical checkout ready, and name it."""

    binary = usable_binary()
    root, project = physical_identity(target)

    code, raw, diagnostic = call_tool(binary, ["index_status", "--project", project])
    structured, reported_error = envelope_or_unavailable(code, raw, diagnostic)
    if code == 0:
        if not ready_for(structured, reported_error, project, root):
            fail(f"Codebase Memory did not report {project} ready for {root}")
        json.dump({"root_path": root, "project": project, "status": "ready"}, sys.stdout)
        sys.stdout.write("\n")
        return
    if code != 1 or reported_error is not True or structured.get("error") != MISSING_PROJECT_ERROR:
        fail(f"Codebase Memory index_status failed for {project}")

    code, raw, diagnostic = call_tool(
        binary,
        ["index_repository", "--repo-path", root, "--mode", "full", "--name", project],
    )
    structured, reported_error = envelope_or_unavailable(code, raw, diagnostic)
    if (
        code != 0
        or reported_error is not False
        or structured.get("project") != project
        or structured.get("status") != "indexed"
    ):
        fail(f"Codebase Memory failed to index {root} as {project}")

    # index_repository never echoes the root it indexed, so the binding is only
    # proven by asking for the project's own root afterwards.
    code, raw, diagnostic = call_tool(binary, ["index_status", "--project", project])
    structured, reported_error = envelope_or_unavailable(code, raw, diagnostic)
    if code != 0 or not ready_for(structured, reported_error, project, root):
        fail(f"Codebase Memory did not report {project} ready for {root} after indexing")
    json.dump({"root_path": root, "project": project, "status": "indexed"}, sys.stdout)
    sys.stdout.write("\n")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "identity":
        identity(sys.argv[2])
        return
    if len(sys.argv) == 4 and sys.argv[1:3] == ["identity", "--main"]:
        identity(sys.argv[3], main_checkout=True)
        return
    if len(sys.argv) == 3 and sys.argv[1] == "ensure":
        ensure(sys.argv[2])
        return
    if len(sys.argv) == 3 and sys.argv[1] == "version":
        validate_version(sys.argv[2])
        return
    if len(sys.argv) == 6 and sys.argv[1] == "response":
        validate_response(*sys.argv[2:])
        return
    fail(
        "usage: cbm-lifecycle.py identity [--main] PATH | ensure PATH"
        " | version FILE | response PROJECT STATUS BOOL FILE"
    )


if __name__ == "__main__":
    main()
