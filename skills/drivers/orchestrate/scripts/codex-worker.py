#!/usr/bin/env python3
"""Launch, resume, stop, and verify one durable Codex worker process family."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worker_lifecycle as lifecycle


# The 2026-08-27 live API probe recorded in docs/scope/149-probes/effort-enums.md
# accepted none, low, medium, high, xhigh, and max for Codex 5.6. The Codex CLI
# validates nothing locally, so this adapter owns the local guard. Not shared
# with claude-worker.py's enum.
EFFORT_LEVELS = {"none", "low", "medium", "high", "xhigh", "max"}
DEFAULT_EFFORT = "medium"


def fail(message: str, code: int = 1) -> int:
    print(f"codex-worker: {message}", file=sys.stderr)
    return code


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
    if any(item.get("type") == "item.completed" and isinstance(item.get("item"), dict) and item["item"].get("type") == "error" for item in items):
        return None, "Codex reported an error item"
    ids = {item["thread_id"] for item in items if item.get("type") == "thread.started" and isinstance(item.get("thread_id"), str) and item["thread_id"]}
    return (ids.pop(), None) if len(ids) == 1 else (None, "missing or ambiguous thread ID in Codex JSONL")


def final_agent_message(items: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    messages = [item["item"]["text"] for item in items if item.get("type") == "item.completed" and isinstance(item.get("item"), dict) and item["item"].get("type") == "agent_message" and isinstance(item["item"].get("text"), str)]
    return (messages[-1], None) if messages else (None, "missing completed agent message in Codex JSONL")


def latest_rate_limits(session_id: str) -> dict[str, Any] | None:
    root = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    matches = []
    for rollout in root.rglob("*.jsonl") if root.exists() else ():
        try:
            entries, error = parse_jsonl(rollout.read_text(encoding="utf-8"))
        except OSError:
            continue
        if error is None and any(entry.get("type") == "session_meta" and isinstance(entry.get("payload"), dict) and entry["payload"].get("session_id") == session_id for entry in entries):
            matches.append(rollout)
    if not matches:
        return None
    entries, error = parse_jsonl(max(matches, key=lambda item: item.stat().st_mtime_ns).read_text(encoding="utf-8"))
    if error:
        return None
    limits = None
    for entry in entries:
        payload = entry.get("payload")
        if entry.get("type") == "event_msg" and isinstance(payload, dict) and payload.get("type") == "token_count":
            limits = payload.get("rate_limits") if isinstance(payload.get("rate_limits"), dict) else None
    return limits


def effort_of(state: dict[str, Any]) -> str:
    return state.get("effort", DEFAULT_EFFORT)


def existing_file(value: str) -> Path:
    path = Path(value).resolve(strict=True)
    if not path.is_file():
        raise argparse.ArgumentTypeError("must be an existing file")
    return path


def image_arguments(paths: list[Path]) -> list[str]:
    return [value for path in paths for value in ("--image", str(path))]


def network_arguments(enabled: bool) -> list[str]:
    return ["-c", "web_search=live", "-c", "tools.web_search=true"] if enabled else []


def parse(output: str) -> tuple[str | None, str | None, Any, str | None]:
    items, error = parse_jsonl(output)
    if error:
        return None, None, None, error
    session_id, error = captured_thread_id(items)
    if error:
        return None, None, None, error
    message, error = final_agent_message(items)
    return session_id, message, None, error


def emit(state: dict[str, Any], final_message: str, _metadata: Any = None) -> None:
    limits = latest_rate_limits(state["session_id"])
    primary = limits.get("primary") if isinstance(limits, dict) else None
    remaining = 100 - primary["used_percent"] if isinstance(primary, dict) and isinstance(primary.get("used_percent"), (int, float)) else None
    print(json.dumps({"session_id": state["session_id"], "model": state["model"], "sandbox": state["sandbox"], "cwd": state["cwd"], "effort": effort_of(state), "network": state.get("network", False), "final_message": final_message, "headroom": remaining, "headroom_status": "known" if remaining is not None else "unknown"}))


def start(args: argparse.Namespace) -> int:
    state, error = lifecycle.prepare_start(
        args, effort_levels=EFFORT_LEVELS, default_effort=DEFAULT_EFFORT
    )
    if error:
        return fail(error)
    assert state is not None
    effort = effort_of(state)
    command = [args.codex, "exec", "-m", args.model, "-c", f"model_reasoning_effort={effort}", *network_arguments(state.get("network", False)), "--sandbox", args.sandbox, "--skip-git-repo-check", "-C", str(args.cwd), "--json", args.prompt, *image_arguments(getattr(args, "image", []))]
    return lifecycle.run_lifecycle(
        args, command, state, parse=parse, emit=emit, fail=fail,
        stdin_text=None, effort_levels=EFFORT_LEVELS,
    )


def resume(args: argparse.Namespace) -> int:
    fresh, expected, error = lifecycle.prepare_resume(
        args, effort_levels=EFFORT_LEVELS, default_effort=DEFAULT_EFFORT
    )
    if error:
        return fail(error)
    assert fresh is not None and expected is not None
    effort = effort_of(fresh)
    command = [args.codex, "exec", "resume", fresh["session_id"], "-m", fresh["model"], "-c", f'sandbox_mode="{fresh["sandbox"]}"', "-c", f"model_reasoning_effort={effort}", *network_arguments(fresh.get("network", False)), "--skip-git-repo-check", "--json", args.prompt, *image_arguments(getattr(args, "image", []))]
    return lifecycle.run_lifecycle(
        args, command, fresh, expected=expected, parse=parse, emit=emit, fail=fail,
        stdin_text=None, effort_levels=EFFORT_LEVELS,
    )


def verify(args: argparse.Namespace) -> int:
    code, error = lifecycle.verify_worker(args, effort_levels=EFFORT_LEVELS)
    return fail(error) if error else (code or 0)


def stop(args: argparse.Namespace) -> int:
    code, error = lifecycle.stop_worker(args, effort_levels=EFFORT_LEVELS)
    return fail(error) if error else (code or 0)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--codex", default="codex")
    common.add_argument("--state", type=Path, required=True)
    common.add_argument("--image", action="append", default=[], type=existing_file)
    common.add_argument("prompt", nargs="?")
    start_parser = commands.add_parser("start", parents=[common]); start_parser.add_argument("--model", required=True); start_parser.add_argument("--sandbox", choices=("read-only", "workspace-write"), required=True); start_parser.add_argument("--effort", default=DEFAULT_EFFORT); start_parser.add_argument("--network", action="store_true"); start_parser.add_argument("--cwd", type=lifecycle.resolved_directory, required=True); start_parser.add_argument("--control-checkout", type=lifecycle.resolved_directory); start_parser.set_defaults(handler=start)
    resume_parser = commands.add_parser("resume", parents=[common]); resume_parser.set_defaults(handler=resume)
    for name, handler in (("stop", stop), ("verify", verify)):
        command = commands.add_parser(name, parents=[common]); command.add_argument("--cwd", type=lifecycle.resolved_directory, required=True); command.add_argument("--grace-seconds", type=float, default=1.0); command.set_defaults(handler=handler)
    return result


if __name__ == "__main__":
    arguments = parser().parse_args()
    if arguments.command in {"start", "resume"} and not arguments.prompt:
        raise SystemExit(fail("prompt is required"))
    raise SystemExit(arguments.handler(arguments))
