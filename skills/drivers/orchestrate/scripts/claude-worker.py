#!/usr/bin/env python3
"""Launch, resume, stop, and verify one durable Claude worker process family."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import worker_lifecycle as lifecycle


EFFORT_LEVELS = {"low", "medium", "high", "xhigh", "max"}
DEFAULT_EFFORT = "medium"


def fail(message: str, code: int = 1) -> int:
    print(f"claude-worker: {message}", file=sys.stderr)
    return code


def parse_result(output: str) -> tuple[dict[str, Any] | None, str | None]:
    """Parse claude's single `--output-format json` object (not Codex's JSONL)."""
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return None, "invalid JSON in Claude output"
    if not isinstance(payload, dict):
        return None, "Claude output is not a JSON object"
    return payload, None


def final_result_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    if payload.get("is_error"):
        return None, "Claude reported is_error"
    result = payload.get("result")
    if not isinstance(result, str):
        return None, "missing result field in Claude output"
    return result, None


def captured_session_id(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return None, "missing session ID in Claude output"
    return session_id, None


def effort_of(state: dict[str, Any]) -> str:
    return state.get("effort", DEFAULT_EFFORT)


def network_arguments(enabled: bool) -> list[str]:
    option = "--allowedTools" if enabled else "--disallowedTools"
    return [option, "WebSearch,WebFetch"]


def parse(output: str) -> tuple[str | None, str | None, Any, str | None]:
    payload, error = parse_result(output)
    if error:
        return None, None, None, error
    assert payload is not None
    session_id, error = captured_session_id(payload)
    if error:
        return None, None, None, error
    message, error = final_result_message(payload)
    return session_id, message, payload.get("permission_denials"), error


def emit(state: dict[str, Any], final_message: str, permission_denials: Any) -> None:
    print(json.dumps({
        "session_id": state["session_id"],
        "model": state["model"],
        "sandbox": state["sandbox"],
        "cwd": state["cwd"],
        "effort": effort_of(state),
        "network": state.get("network", False),
        "final_message": final_message,
        "permission_denials": permission_denials if permission_denials is not None else [],
    }))


def sandbox_settings(sandbox: str, cwd: Path) -> dict[str, Any]:
    """Build the installed Claude CLI's two sandbox settings shapes."""
    if sandbox == "read-only":
        return {
            "sandbox": {
                "enabled": True,
                "allowUnsandboxedCommands": False,
                "filesystem": {"denyWrite": ["/", "~/"]},
            },
            "permissions": {"deny": ["Write", "Edit", "NotebookEdit"]},
        }
    return {
        "sandbox": {
            "enabled": True,
            "allowUnsandboxedCommands": False,
            "filesystem": {"allowWrite": [str(cwd)]},
        },
        "permissions": {"allow": ["Write", "Edit", "NotebookEdit"]},
    }


def write_settings_file(sandbox: str, cwd: Path) -> Path:
    descriptor, path = tempfile.mkstemp(prefix="claude-worker-settings-", suffix=".json")
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        json.dump(sandbox_settings(sandbox, cwd), file)
    return Path(path)


def start(args: argparse.Namespace) -> int:
    state, error = lifecycle.prepare_start(
        args, effort_levels=EFFORT_LEVELS, default_effort=DEFAULT_EFFORT
    )
    if error:
        return fail(error)
    assert state is not None
    settings = write_settings_file(args.sandbox, args.cwd)
    session_id = str(uuid.uuid4())
    command = [
        args.claude, "-p", "--model", args.model, "--effort", args.effort,
        "--permission-mode", "dontAsk", "--settings", str(settings),
        *network_arguments(state.get("network", False)),
        "--session-id", session_id, "--output-format", "json",
    ]
    return lifecycle.run_lifecycle(
        args, command, state, parse=parse, emit=emit, fail=fail,
        stdin_text=args.prompt, effort_levels=EFFORT_LEVELS,
    )


def resume(args: argparse.Namespace) -> int:
    fresh, expected, error = lifecycle.prepare_resume(
        args, effort_levels=EFFORT_LEVELS, default_effort=DEFAULT_EFFORT
    )
    if error:
        return fail(error)
    assert fresh is not None and expected is not None
    cwd = Path(fresh["cwd"])
    effort = effort_of(fresh)
    settings = write_settings_file(fresh["sandbox"], cwd)
    command = [
        args.claude, "-p", "--resume", fresh["session_id"], "--model", fresh["model"],
        "--effort", effort, "--permission-mode", "dontAsk", "--settings", str(settings),
        *network_arguments(fresh.get("network", False)),
        "--output-format", "json",
    ]
    return lifecycle.run_lifecycle(
        args, command, fresh, expected=expected, parse=parse, emit=emit, fail=fail,
        stdin_text=args.prompt, effort_levels=EFFORT_LEVELS,
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
    common.add_argument("--claude", default="claude")
    common.add_argument("--state", type=Path, required=True)
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
