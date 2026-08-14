#!/usr/bin/env python3
"""Manage receipts proving a PR body was scored and passed.

A receipt is keyed by the sha256 of the body file's exact bytes, so editing
the file after scoring invalidates it; that is the property pr-body-gate
relies on. `write` is called by the skill only after both the linter and the
judge pass. `check` is the same lookup as a standalone exit code. `prune`
clears receipts older than a week so the state directory does not grow
without bound.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

STATE_ROOT = Path.home() / ".local" / "state" / "pr-body"
RECEIPTS_DIR = STATE_ROOT / "receipts"
BY_PATH_DIR = RECEIPTS_DIR / "by-path"
PRUNE_AGE = timedelta(days=7)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _receipt_path(digest: str) -> Path:
    return RECEIPTS_DIR / f"{digest}.json"


def _path_pointer_path(abs_path: str) -> Path:
    # Keyed by a hash of the path, not the path itself, so the receipt tree
    # never has to worry about characters a filesystem rejects in a name.
    return BY_PATH_DIR / f"{_sha256_bytes(abs_path.encode('utf-8'))}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)


def _read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _read_body_bytes(body_file: str) -> Optional[bytes]:
    try:
        return Path(body_file).read_bytes()
    except OSError as error:
        print(f"pr_body_receipt: cannot read {body_file}: {error}", file=sys.stderr)
        return None


def cmd_write(body_file: str) -> int:
    data = _read_body_bytes(body_file)
    if data is None:
        return 1
    digest = _sha256_bytes(data)
    _ensure_dir(RECEIPTS_DIR)
    _ensure_dir(BY_PATH_DIR)
    timestamp = _now_iso()
    receipt = {"sha256": digest, "timestamp": timestamp, "verdict": "pass"}
    _receipt_path(digest).write_text(json.dumps(receipt), encoding="utf-8")

    # The by-path pointer lets a later `check` on the same path tell "never
    # scored" apart from "scored, then edited" instead of just failing both
    # the same way.
    abs_path = str(Path(body_file).resolve())
    pointer = {"path": abs_path, "sha256": digest, "timestamp": timestamp}
    _path_pointer_path(abs_path).write_text(json.dumps(pointer), encoding="utf-8")
    return 0


def cmd_check(body_file: str) -> int:
    data = _read_body_bytes(body_file)
    if data is None:
        return 1
    digest = _sha256_bytes(data)
    receipt = _read_json(_receipt_path(digest))
    if receipt and receipt.get("sha256") == digest and receipt.get("verdict") == "pass":
        print("valid")
        return 0

    abs_path = str(Path(body_file).resolve())
    pointer = _read_json(_path_pointer_path(abs_path))
    if pointer and pointer.get("sha256") and pointer.get("sha256") != digest:
        print("stale: body edited after it was scored", file=sys.stderr)
    else:
        print("no receipt for this body", file=sys.stderr)
    return 1


def cmd_prune() -> int:
    cutoff = datetime.now(timezone.utc) - PRUNE_AGE
    removed = 0
    for directory in (RECEIPTS_DIR, BY_PATH_DIR):
        if not directory.is_dir():
            continue
        for entry in directory.glob("*.json"):
            record = _read_json(entry)
            timestamp = record.get("timestamp") if record else None
            when = None
            if timestamp:
                try:
                    when = datetime.fromisoformat(timestamp)
                except ValueError:
                    when = None
            if when is None or when < cutoff:
                entry.unlink(missing_ok=True)
                removed += 1
    print(f"pruned {removed} receipt(s)")
    return 0


def parse_arguments(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)

    write_parser = subparsers.add_parser("write", help="record a passing receipt")
    write_parser.add_argument("body_file")

    check_parser = subparsers.add_parser("check", help="exit 0 if a valid receipt exists")
    check_parser.add_argument("body_file")

    subparsers.add_parser("prune", help="delete receipts older than 7 days")

    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    try:
        arguments = parse_arguments(argv)
        if arguments.action == "write":
            return cmd_write(arguments.body_file)
        if arguments.action == "check":
            return cmd_check(arguments.body_file)
        if arguments.action == "prune":
            return cmd_prune()
    except Exception as error:  # noqa: BLE001 - must never crash the caller
        print(f"pr_body_receipt: internal error: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
