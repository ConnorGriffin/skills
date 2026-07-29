#!/usr/bin/env python3
"""Create an isolated Git worktree for issue or branch work."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


DEFAULT_ROOT = Path(
    os.environ.get("AGENT_WORKTREE_ROOT", str(Path.home() / "worktrees"))
).expanduser()
DEFAULT_REMOTE = "origin"


class SpinError(RuntimeError):
    """A safe, user-facing worktree setup failure."""


def run(
    command: list[str],
    *,
    cwd: Optional[Path] = None,
    capture: bool = False,
    dry_run: bool = False,
) -> str:
    print("$ " + " ".join(command), flush=True)
    if dry_run:
        return ""
    options: dict[str, object] = {"text": True}
    if cwd is not None:
        options["cwd"] = str(cwd)
    if capture:
        options["stdout"] = subprocess.PIPE
        options["stderr"] = subprocess.PIPE
    try:
        completed = subprocess.run(command, check=True, **options)
    except FileNotFoundError as error:
        raise SpinError(f"required command not found: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() if capture and error.stderr else ""
        raise SpinError(detail or f"command exited {error.returncode}") from error
    return str(completed.stdout).strip() if capture else ""


def git(
    repo: Path, *arguments: str, capture: bool = False, dry_run: bool = False
) -> str:
    return run(
        ["git", "-C", str(repo), *arguments],
        capture=capture,
        dry_run=dry_run,
    )


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "task"


def safe_leaf(value: str) -> str:
    if (
        not value
        or value in {".", ".."}
        or Path(value).is_absolute()
        or "/" in value
        or "\\" in value
    ):
        raise SpinError("--name must be one safe relative directory name")
    return value


def repository_root(path: Path) -> Path:
    try:
        value = run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture=True,
        )
    except SpinError as error:
        raise SpinError(f"{path} is not a Git checkout") from error
    return Path(value).resolve()


def require_clean(repo: Path, *, dry_run: bool) -> None:
    if dry_run:
        return
    if git(repo, "status", "--short", capture=True):
        raise SpinError(f"control checkout is dirty: {repo}")


def local_branch_exists(repo: Path, branch: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "show-ref",
            "--verify",
            "--quiet",
            f"refs/heads/{branch}",
        ],
        check=False,
    )
    return result.returncode == 0


def remote_default_branch(repo: Path, remote: str) -> str:
    symbolic = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "symbolic-ref",
            "--quiet",
            "--short",
            f"refs/remotes/{remote}/HEAD",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
    )
    if symbolic.returncode == 0 and symbolic.stdout.strip():
        return symbolic.stdout.strip().removeprefix(f"{remote}/")
    for candidate in ("main", "master"):
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "show-ref",
                "--verify",
                "--quiet",
                f"refs/remotes/{remote}/{candidate}",
            ],
            check=False,
        )
        if result.returncode == 0:
            return candidate
    raise SpinError(f"cannot determine the default branch for remote {remote}")


def discover_pr_branch(repo: Path, pull_request: int) -> str:
    value = run(
        [
            "gh",
            "pr",
            "view",
            str(pull_request),
            "--json",
            "headRefName,isCrossRepository,headRepository,headRepositoryOwner",
        ],
        cwd=repo,
        capture=True,
    )
    try:
        metadata = json.loads(value)
    except json.JSONDecodeError as error:
        raise SpinError(f"could not resolve pull request #{pull_request}") from error
    branch = metadata.get("headRefName")
    if not branch:
        raise SpinError(f"could not resolve pull request #{pull_request}")
    if metadata.get("isCrossRepository"):
        owner = (metadata.get("headRepositoryOwner") or {}).get("login", "unknown")
        repository = (metadata.get("headRepository") or {}).get("name", "unknown")
        raise SpinError(
            f"pull request #{pull_request} comes from fork {owner}/{repository}; "
            "add that fork as a Git remote, fetch its head branch, then rerun with "
            f"--branch {branch}"
        )
    return str(branch)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="control checkout")
    parser.add_argument("--worktree-root", default=str(DEFAULT_ROOT))
    parser.add_argument("--remote", default=DEFAULT_REMOTE)
    parser.add_argument("--base", help="base branch for new issue work")
    parser.add_argument("--branch-prefix", default="codex")
    parser.add_argument("--issue", type=int)
    parser.add_argument("--slug")
    parser.add_argument("--pr", type=int)
    parser.add_argument("--branch")
    parser.add_argument("--name", help="worktree directory name")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()

    modes = (
        arguments.issue is not None,
        arguments.pr is not None,
        arguments.branch is not None,
    )
    if sum(modes) != 1:
        parser.error("choose exactly one of --issue, --pr, or --branch")
    if arguments.slug and arguments.issue is None:
        parser.error("--slug requires --issue")
    return arguments


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.name is not None:
            safe_leaf(arguments.name)
        repo = repository_root(Path(arguments.repo).expanduser())
        require_clean(repo, dry_run=arguments.dry_run)
        root = Path(arguments.worktree_root).expanduser().resolve()

        if arguments.issue is not None:
            git(repo, "fetch", arguments.remote, dry_run=arguments.dry_run)
            base = arguments.base or remote_default_branch(repo, arguments.remote)
            branch_slug = slugify(arguments.slug or f"issue-{arguments.issue}")
            branch = (
                f"{arguments.branch_prefix}/{arguments.issue}-{branch_slug}"
                if arguments.slug
                else f"{arguments.branch_prefix}/issue-{arguments.issue}"
            )
            task_name = safe_leaf(arguments.name or str(arguments.issue))
            start_point = f"{arguments.remote}/{base}"
            new_branch = True
        else:
            branch = arguments.branch or discover_pr_branch(repo, arguments.pr)
            task_name = safe_leaf(
                arguments.name
                or (f"pr{arguments.pr}" if arguments.pr else slugify(branch))
            )
            start_point = branch
            new_branch = not local_branch_exists(repo, branch)
            if new_branch:
                git(
                    repo,
                    "fetch",
                    arguments.remote,
                    branch,
                    dry_run=arguments.dry_run,
                )
                git(
                    repo,
                    "branch",
                    "--track",
                    branch,
                    f"{arguments.remote}/{branch}",
                    dry_run=arguments.dry_run,
                )
                new_branch = False

        destination = root / repo.name / task_name
        if not arguments.dry_run and destination.exists():
            raise SpinError(f"target already exists: {destination}")

        command = ["worktree", "add", str(destination)]
        if new_branch:
            command.extend(["-b", branch, start_point])
        else:
            command.append(branch)
        git(repo, *command, dry_run=arguments.dry_run)
    except SpinError as error:
        print(f"spin-worktree: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "repo": str(repo),
                "worktree": str(destination),
                "branch": branch,
                "dry_run": arguments.dry_run,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
