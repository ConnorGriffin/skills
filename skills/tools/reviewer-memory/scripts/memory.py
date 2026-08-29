#!/usr/bin/env python3
"""Maintain the local, append-only reviewer-memory store."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StoreError(RuntimeError):
    """A store that exists but cannot safely be used."""


def normalize_remote(value: str) -> str:
    """Match ticket.py's remote identity so SSH and HTTPS share a store."""
    value = value.strip()
    if value.endswith(".git"):
        value = value[: -len(".git")]
    scp_match = re.match(r"^[^/@]+@([^:]+):(.+)$", value)
    if scp_match:
        return f"{scp_match.group(1)}/{scp_match.group(2)}"
    url_match = re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://(?:[^/@]+@)?([^/]+)/(.+)$", value)
    if url_match:
        return f"{url_match.group(1)}/{url_match.group(2)}"
    return value


def repository_identity(value: str) -> str:
    """Resolve a checkout to origin when possible, otherwise treat it as a remote."""
    candidate = Path(value).expanduser()
    if candidate.exists():
        try:
            remote = subprocess.run(
                ["git", "-C", str(candidate), "remote", "get-url", "origin"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except OSError:
            remote = None
        if remote is not None and remote.returncode == 0 and remote.stdout.strip():
            return normalize_remote(remote.stdout)
        try:
            toplevel = subprocess.run(
                ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except OSError:
            toplevel = None
        if toplevel is not None and toplevel.returncode == 0 and toplevel.stdout.strip():
            return toplevel.stdout.strip()
    return normalize_remote(value)


def repository_key(value: str) -> str:
    identity = repository_identity(value)
    key = re.sub(r"[^A-Za-z0-9._-]+", "_", identity).strip("._-")
    if not key:
        raise StoreError("repo must resolve to a non-empty remote or checkout path")
    return key


def store_paths(repo: str) -> tuple[str, Path, Path, Path]:
    key = repository_key(repo)
    root = (Path.home() / ".config" / "reviewer-memory" / key).absolute()
    return key, root, root / "raw.jsonl", root / "okf" / "index.md"


def permission_message(action: str, path: Path) -> str:
    return (
        f"cannot {action} {path}: permission denied; rerun this verb outside the "
        "sandbox or with escalated permissions"
    )


def reject_symlink(path: Path) -> None:
    if path.is_symlink():
        raise StoreError(f"symlinked store path is not allowed: {path}; replace it with a regular path, then retry")


def create_skeleton(root: Path, raw: Path, index: Path) -> None:
    try:
        index.parent.mkdir(parents=True, exist_ok=True)
        raw.touch(exist_ok=True)
        index.write_text(
            "---\n"
            "title: Reviewer memory\n"
            f"updated: {datetime.now(timezone.utc).date().isoformat()}\n"
            "tags: []\n"
            "---\n",
            encoding="utf-8",
        )
    except PermissionError as error:
        raise StoreError(permission_message("create", error.filename and Path(error.filename) or root)) from error
    except OSError as error:
        raise StoreError(f"cannot create {error.filename or root}: {error.strerror}") from error


def validate_raw(raw: Path) -> list[dict[str, Any]]:
    try:
        lines = raw.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise StoreError(f"invalid UTF-8 in {raw}: {error}") from error
    except PermissionError as error:
        raise StoreError(permission_message("read", raw)) from error
    except OSError as error:
        raise StoreError(f"cannot read {raw}: {error.strerror}") from error
    records = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise StoreError(f"malformed JSON line in {raw}:{line_number}: {error.msg}") from error
        if not isinstance(record, dict):
            raise StoreError(f"malformed JSON line in {raw}:{line_number}: expected an object")
        records.append(record)
    return records


def validate_index(index: Path) -> bool:
    try:
        text = index.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise StoreError(f"invalid UTF-8 in {index}: {error}") from error
    except PermissionError as error:
        raise StoreError(permission_message("read", index)) from error
    except OSError as error:
        raise StoreError(f"cannot read {index}: {error.strerror}") from error
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise StoreError(f"unparseable OKF index frontmatter in {index}: begin and close it with --- lines")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise StoreError(f"unparseable OKF index frontmatter in {index}: begin and close it with --- lines") from error
    return bool("\n".join(lines[closing + 1:]).strip())


def open_store(repo: str) -> tuple[str, Path, Path, Path, bool]:
    key, root, raw, index = store_paths(repo)
    for path in (root.parent.parent, root.parent, root, raw, index.parent, index):
        reject_symlink(path)
    if not root.exists():
        create_skeleton(root, raw, index)
    elif not root.is_dir():
        raise StoreError(f"store root is not a directory: {root}; remove or repair it, then retry")
    if not raw.is_file():
        raise StoreError(f"missing raw record file: {raw}; repair the store, then retry")
    if not index.is_file():
        raise StoreError(f"missing OKF index: {index}; repair the store, then retry")
    validate_raw(raw)
    has_content = validate_index(index)
    return key, root, raw, index, has_content


def read_input_object() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except UnicodeDecodeError as error:
        raise StoreError(f"stdin must contain UTF-8 JSON: {error}") from error
    except json.JSONDecodeError as error:
        raise StoreError(f"stdin must contain one JSON object: {error.msg}") from error
    if not isinstance(value, dict):
        raise StoreError("stdin must contain one JSON object")
    return value


def append(repo: str, kind: str) -> None:
    _, _, raw, _, _ = open_store(repo)
    record = read_input_object()
    record["kind"] = kind
    record["recorded_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        with raw.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
    except PermissionError as error:
        raise StoreError(permission_message("write", raw)) from error
    except OSError as error:
        raise StoreError(f"cannot write {raw}: {error.strerror}") from error


def command_ensure(repo: str) -> None:
    key, root, raw, index, has_content = open_store(repo)
    print(json.dumps({"key": key, "root": str(root), "raw_path": str(raw), "index_path": str(index), "has_content": has_content}))


def command_pointer(repo: str) -> None:
    _, _, _, index, _ = open_store(repo)
    print(index)


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain the local reviewer-memory store.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("ensure", "append-review", "append-slicing", "pointer"):
        command = subcommands.add_parser(name)
        command.add_argument("repo", help="remote URL or checkout path")
    arguments = parser.parse_args()
    try:
        if arguments.command == "ensure":
            command_ensure(arguments.repo)
        elif arguments.command == "append-review":
            append(arguments.repo, "review")
        elif arguments.command == "append-slicing":
            append(arguments.repo, "slicing")
        else:
            command_pointer(arguments.repo)
    except StoreError as error:
        print(f"reviewer-memory: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
