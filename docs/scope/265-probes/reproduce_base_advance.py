#!/usr/bin/env python3
"""Prove the base-ref composite catches applicability drift after branch cut."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


CHANGE = "265-preflight-openspec-rename-applicability"


def command(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def main() -> int:
    source_repo = Path(__file__).resolve().parents[3]
    probe = Path(__file__).with_name("preflight_openspec.py")
    with tempfile.TemporaryDirectory(prefix="ticket-265-base-advance-") as scratch:
        repo = Path(scratch)
        bundle_path = repo / "openspec.tar"
        exported = command(
            ["git", "archive", "--format=tar", f"--output={bundle_path}", "origin/main", "openspec"],
            source_repo,
        )
        if exported.returncode:
            print(exported.stderr, file=sys.stderr)
            return exported.returncode
        with tarfile.open(bundle_path) as bundle:
            bundle.extractall(repo, filter="data")
        bundle_path.unlink()

        for args in (
            ["git", "init", "-b", "main"],
            ["git", "config", "user.name", "Issue 265 fixture"],
            ["git", "config", "user.email", "fixture@example.invalid"],
            ["git", "add", "openspec"],
            ["git", "commit", "-m", "baseline"],
            ["git", "switch", "-c", "ticket"],
        ):
            result = command(args, repo)
            if result.returncode:
                print(result.stderr, file=sys.stderr)
                return result.returncode

        shutil.copytree(
            source_repo / "openspec" / "changes" / CHANGE,
            repo / "openspec" / "changes" / CHANGE,
        )
        for args in (["git", "add", "openspec"], ["git", "commit", "-m", "ticket delta"], ["git", "switch", "main"]):
            result = command(args, repo)
            if result.returncode:
                print(result.stderr, file=sys.stderr)
                return result.returncode

        baseline = repo / "openspec" / "specs" / "ticket-workflow" / "spec.md"
        baseline.write_text(
            baseline.read_text(encoding="utf-8").replace(
                "### Requirement: Four-verb lifecycle",
                "### Requirement: Renamed lifecycle",
                1,
            ),
            encoding="utf-8",
        )
        for args in (
            ["git", "add", str(baseline.relative_to(repo))],
            ["git", "commit", "-m", "advance baseline"],
            ["git", "switch", "ticket"],
        ):
            result = command(args, repo)
            if result.returncode:
                print(result.stderr, file=sys.stderr)
                return result.returncode

        stale = command([sys.executable, str(probe), CHANGE, "--repo", "."], repo)
        current = command(
            [sys.executable, str(probe), CHANGE, "--repo", ".", "--base-ref", "main"],
            repo,
        )
        print(f"stale_ticket_baseline_exit={stale.returncode}")
        print(stale.stdout.strip())
        print(f"current_base_composite_exit={current.returncode}")
        print(current.stderr.strip())

    return 0 if stale.returncode == 0 and current.returncode == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
