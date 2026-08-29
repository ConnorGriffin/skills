#!/usr/bin/env python3
"""Reproduce issue 259 from immutable repository history."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


CHANGE = "259-remove-unused-ticket-telemetry"
REGRESSION_COMMIT = "fe3317a81e72ec630bd30a829c2489d62bc5cb7e"


def run(
    command: list[str],
    cwd: Path,
    display_command: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    print(f"$ {' '.join(display_command or command)}")
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")
    print(f"exit={result.returncode}")
    return result


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    probe = Path(__file__).with_name("preflight_openspec.py")
    with tempfile.TemporaryDirectory(prefix="ticket-265-reproduce-") as scratch:
        fixture = Path(scratch)
        archive_path = fixture / "repo.tar"
        archived = subprocess.run(
            ["git", "archive", "--format=tar", f"--output={archive_path}", REGRESSION_COMMIT],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if archived.returncode:
            print(archived.stderr, file=sys.stderr)
            return archived.returncode
        with tarfile.open(archive_path) as bundle:
            bundle.extractall(fixture, filter="data")
        archive_path.unlink()

        version = run(["openspec", "--version"], fixture)
        validation = run(["openspec", "validate", CHANGE, "--strict"], fixture)
        before = tree_digest(fixture / "openspec")
        preflight = run(
            [sys.executable, str(probe), CHANGE, "--repo", "."],
            fixture,
            [sys.executable, "docs/scope/265-probes/preflight_openspec.py", CHANGE, "--repo", "."],
        )
        after = tree_digest(fixture / "openspec")
        print(f"source_unchanged={str(before == after).lower()}")

    return 0 if version.returncode == 0 and validation.returncode == 0 and preflight.returncode == 1 and before == after else 1


if __name__ == "__main__":
    raise SystemExit(main())
