#!/usr/bin/env python3
"""Classify a change set for the required GitHub Actions skills job."""

import argparse
import subprocess
import sys
from pathlib import Path


SAFE_ROOT_FILES = {"README.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE", "NOTICE"}


def git(repository, *arguments):
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def is_safe_path(path):
    if path in SAFE_ROOT_FILES:
        return True
    return (
        (path.startswith("docs/") or path.startswith("openspec/"))
        and path.endswith(".md")
    )


def classify(repository, event, base, head):
    if event != "pull_request":
        return True
    try:
        git(repository, "rev-parse", "--show-toplevel")
        merge_base = git(repository, "merge-base", base, head).strip()
        paths = git(repository, "diff", "--name-only", "-z", "--no-renames", merge_base, head)
    except (OSError, subprocess.CalledProcessError):
        return True
    try:
        changed_paths = [path.decode("utf-8") for path in paths.split(b"\0") if path]
    except UnicodeDecodeError:
        return True
    return not changed_paths or not all(is_safe_path(path) for path in changed_paths)


def write_output(output, run_expensive):
    try:
        Path(output).write_text(
            f"run_expensive={'true' if run_expensive else 'false'}\n", encoding="utf-8"
        )
    except OSError as error:
        print(f"ci-changed-paths: cannot write GitHub output: {error}", file=sys.stderr)
        return 1
    return 0


def github_output_argument(arguments):
    for index, argument in enumerate(arguments[:-1]):
        if argument == "--github-output":
            return arguments[index + 1]
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo")
    parser.add_argument("--event")
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--github-output")
    try:
        arguments = parser.parse_args()
    except SystemExit as error:
        output = github_output_argument(sys.argv[1:])
        if output:
            return write_output(output, True)
        return error.code
    if not arguments.github_output:
        parser.error("the following arguments are required: --github-output")
    if not all((arguments.repo, arguments.event, arguments.base, arguments.head)):
        return write_output(arguments.github_output, True)
    return write_output(
        arguments.github_output,
        classify(arguments.repo, arguments.event, arguments.base, arguments.head),
    )


if __name__ == "__main__":
    sys.exit(main())
