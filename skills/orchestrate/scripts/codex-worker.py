#!/usr/bin/env python3
"""Start and resume isolated Codex CLI workers for /orchestrate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def fail(message: str) -> int:
    print(f"codex-worker: {message}", file=sys.stderr)
    return 1


def resolved_directory(value: str) -> Path:
    path = Path(value).resolve(strict=True)
    if not path.is_dir():
        raise argparse.ArgumentTypeError("must be an existing directory")
    return path


def is_within(path: Path, directory: Path) -> bool:
    """Return whether a resolved path is the directory or one of its descendants."""
    return path == directory or directory in path.parents


def parse_jsonl(output: str) -> tuple[list[dict[str, Any]], str | None]:
    items: list[dict[str, Any]] = []
    for number, line in enumerate(output.splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            return [], f"invalid JSONL on line {number}"
        if not isinstance(item, dict):
            return [], f"JSONL item on line {number} is not an object"
        items.append(item)
    return items, None


def captured_thread_id(items: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    if any(
        item.get("type") == "item.completed"
        and isinstance(item.get("item"), dict)
        and item["item"].get("type") == "error"
        for item in items
    ):
        return None, "Codex reported an error item"
    ids = {
        item["thread_id"]
        for item in items
        if item.get("type") == "thread.started"
        and isinstance(item.get("thread_id"), str)
        and item["thread_id"]
    }
    if len(ids) != 1:
        return None, "missing or ambiguous thread ID in Codex JSONL"
    return ids.pop(), None


def final_agent_message(items: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    message = None
    for entry in items:
        item = entry.get("item")
        if (
            entry.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
        ):
            message = item["text"]
    if message is None:
        return None, "missing completed agent message in Codex JSONL"
    return message, None


def latest_rate_limits(session_id: str) -> dict[str, Any] | None:
    root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    matches: list[Path] = []
    for rollout in root.rglob("*.jsonl") if root.exists() else ():
        try:
            entries, error = parse_jsonl(rollout.read_text(encoding="utf-8"))
        except OSError:
            continue
        if error is None and any(
            entry.get("type") == "session_meta"
            and isinstance(entry.get("payload"), dict)
            and entry["payload"].get("session_id") == session_id
            for entry in entries
        ):
            matches.append(rollout)
    if not matches:
        return None
    rollout = max(matches, key=lambda path: path.stat().st_mtime_ns)
    entries, error = parse_jsonl(rollout.read_text(encoding="utf-8"))
    if error:
        return None
    rate_limits = None
    for entry in entries:
        payload = entry.get("payload")
        if (
            entry.get("type") == "event_msg"
            and isinstance(payload, dict)
            and payload.get("type") == "token_count"
        ):
            candidate = payload.get("rate_limits")
            rate_limits = candidate if isinstance(candidate, dict) else None
    return rate_limits


def headroom(rate_limits: dict[str, Any] | None) -> int | float | None:
    if not rate_limits:
        return None
    primary = rate_limits.get("primary")
    if not isinstance(primary, dict):
        return None
    used_percent = primary.get("used_percent")
    if not isinstance(used_percent, (int, float)):
        return None
    return 100 - used_percent


def write_state(
    path: Path,
    session_id: str,
    model: str,
    sandbox: str,
    cwd: Path,
    control_checkout: Path | None,
) -> None:
    state: dict[str, str] = {
        "session_id": session_id,
        "model": model,
        "sandbox": sandbox,
        "cwd": str(cwd),
    }
    if control_checkout is not None:
        state["control_checkout"] = str(control_checkout)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
    )


def run_worker(
    command: list[str],
    cwd: Path,
) -> tuple[subprocess.CompletedProcess[str], list[dict[str, Any]] | None, str | None]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result, None, None
    items, error = parse_jsonl(result.stdout)
    return result, items, error


def emit(
    session_id: str,
    model: str,
    sandbox: str,
    cwd: Path,
    final_message: str,
) -> None:
    limits = latest_rate_limits(session_id)
    remaining = headroom(limits)
    print(
        json.dumps(
            {
                "session_id": session_id,
                "model": model,
                "sandbox": sandbox,
                "cwd": str(cwd),
                "final_message": final_message,
                "headroom": remaining,
                "headroom_status": "known" if remaining is not None else "unknown",
            }
        )
    )


def start(args: argparse.Namespace) -> int:
    cwd = args.cwd
    if args.sandbox == "workspace-write":
        if args.control_checkout is None:
            return fail("workspace-write requires --control-checkout")
        if is_within(cwd, args.control_checkout):
            return fail("workspace-write refuses the control checkout")
    command = [
        args.codex,
        "exec",
        "-m",
        args.model,
        "-c",
        "model_reasoning_effort=medium",
        "--sandbox",
        args.sandbox,
        "--skip-git-repo-check",
        "-C",
        str(cwd),
        "--json",
        args.prompt,
    ]
    result, items, error = run_worker(command, cwd)
    if result.returncode:
        return result.returncode
    if error:
        return fail(error)
    session_id, error = captured_thread_id(items or [])
    if error:
        return fail(error)
    message, error = final_agent_message(items or [])
    if error:
        return fail(error)
    write_state(
        args.state,
        session_id or "",
        args.model,
        args.sandbox,
        cwd,
        args.control_checkout,
    )
    emit(session_id or "", args.model, args.sandbox, cwd, message or "")
    return 0


def resume(args: argparse.Namespace) -> int:
    try:
        state = json.loads(args.state.read_text(encoding="utf-8"))
        session_id, model, sandbox, cwd = (
            state[key] for key in ("session_id", "model", "sandbox", "cwd")
        )
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return fail("state file is malformed or incomplete")
    if not all(isinstance(value, str) and value for value in (session_id, model, sandbox, cwd)):
        return fail("state file is malformed or incomplete")
    if sandbox not in {"read-only", "workspace-write"}:
        return fail("state file has an invalid sandbox")
    try:
        canonical_cwd = resolved_directory(cwd)
    except (OSError, argparse.ArgumentTypeError):
        return fail("state file has an invalid cwd")
    control_checkout = None
    if sandbox == "workspace-write":
        control = state.get("control_checkout")
        if not isinstance(control, str) or not control:
            return fail("state file is missing the control checkout")
        try:
            control_checkout = resolved_directory(control)
        except (OSError, argparse.ArgumentTypeError):
            return fail("state file has an invalid control checkout")
        if is_within(canonical_cwd, control_checkout):
            return fail("workspace-write refuses the control checkout")
    command = [
        args.codex,
        "exec",
        "resume",
        session_id,
        "-m",
        model,
        "-c",
        f'sandbox_mode="{sandbox}"',
        "--json",
        args.prompt,
    ]
    result, items, error = run_worker(command, canonical_cwd)
    if result.returncode:
        return result.returncode
    if error:
        return fail(error)
    returned_id, error = captured_thread_id(items or [])
    if error:
        return fail(error)
    if returned_id != session_id:
        return fail("resume returned a different thread ID")
    message, error = final_agent_message(items or [])
    if error:
        return fail(error)
    write_state(
        args.state,
        session_id,
        model,
        sandbox,
        canonical_cwd,
        control_checkout,
    )
    emit(session_id, model, sandbox, canonical_cwd, message or "")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--codex", default="codex")
    common.add_argument("--state", type=Path, required=True)
    common.add_argument("prompt")
    start_parser = commands.add_parser("start", parents=[common])
    start_parser.add_argument("--model", required=True)
    start_parser.add_argument(
        "--sandbox", choices=("read-only", "workspace-write"), required=True
    )
    start_parser.add_argument("--cwd", type=resolved_directory, required=True)
    start_parser.add_argument("--control-checkout", type=resolved_directory)
    start_parser.set_defaults(handler=start)
    resume_parser = commands.add_parser("resume", parents=[common])
    resume_parser.set_defaults(handler=resume)
    return result


if __name__ == "__main__":
    arguments = parser().parse_args()
    raise SystemExit(arguments.handler(arguments))
