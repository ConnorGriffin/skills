#!/usr/bin/env python3
"""Prove fetch + base-ref composite catches applicability drift after branch cut."""

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


def require(args: list[str], cwd: Path) -> None:
    result = command(args, cwd)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)


def configure(repo: Path) -> None:
    require(["git", "config", "user.name", "Issue 265 fixture"], repo)
    require(["git", "config", "user.email", "fixture@example.invalid"], repo)


def main() -> int:
    source_repo = Path(__file__).resolve().parents[3]
    probe = Path(__file__).with_name("preflight_openspec.py")
    with tempfile.TemporaryDirectory(prefix="ticket-265-base-advance-") as scratch:
        root = Path(scratch)
        seed = root / "seed"
        remote = root / "remote.git"
        ticket = root / "ticket"
        updater = root / "updater"
        seed.mkdir()

        bundle_path = seed / "openspec.tar"
        exported = command(
            ["git", "archive", "--format=tar", f"--output={bundle_path}", "origin/main", "openspec"],
            source_repo,
        )
        if exported.returncode:
            print(exported.stderr, file=sys.stderr)
            return exported.returncode
        with tarfile.open(bundle_path) as bundle:
            bundle.extractall(seed, filter="data")
        bundle_path.unlink()

        try:
            require(["git", "init", "-b", "main"], seed)
            configure(seed)
            require(["git", "add", "openspec"], seed)
            require(["git", "commit", "-m", "baseline"], seed)
            require(["git", "init", "--bare", "--initial-branch=main", str(remote)], root)
            require(["git", "remote", "add", "origin", str(remote)], seed)
            require(["git", "push", "-u", "origin", "main"], seed)
            require(["git", "clone", str(remote), str(ticket)], root)
            require(["git", "clone", str(remote), str(updater)], root)
            configure(ticket)
            configure(updater)

            require(["git", "switch", "-c", "ticket"], ticket)
            shutil.copytree(
                source_repo / "openspec" / "changes" / CHANGE,
                ticket / "openspec" / "changes" / CHANGE,
            )
            require(["git", "add", "openspec"], ticket)
            require(["git", "commit", "-m", "ticket delta"], ticket)

            baseline = updater / "openspec" / "specs" / "ticket-workflow" / "spec.md"
            baseline.write_text(
                baseline.read_text(encoding="utf-8").replace(
                    "### Requirement: Four-verb lifecycle",
                    "### Requirement: Renamed lifecycle",
                    1,
                ),
                encoding="utf-8",
            )
            require(["git", "add", str(baseline.relative_to(updater))], updater)
            require(["git", "commit", "-m", "advance baseline"], updater)
            require(["git", "push", "origin", "main"], updater)
        except RuntimeError as error:
            print(error, file=sys.stderr)
            return 2

        stale = command(
            [sys.executable, str(probe), CHANGE, "--repo", ".", "--base-ref", "refs/remotes/origin/HEAD"],
            ticket,
        )
        fetched = command(["git", "fetch", "origin"], ticket)
        current = command(
            [sys.executable, str(probe), CHANGE, "--repo", ".", "--base-ref", "refs/remotes/origin/HEAD"],
            ticket,
        )
        print(f"before_fetch_exit={stale.returncode}")
        print(stale.stdout.strip())
        print(f"fetch_exit={fetched.returncode}")
        print(f"after_fetch_exit={current.returncode}")
        print(current.stderr.strip())

    return 0 if stale.returncode == 0 and fetched.returncode == 0 and current.returncode == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
