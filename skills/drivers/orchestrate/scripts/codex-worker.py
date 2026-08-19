#!/usr/bin/env python3
"""Launch, resume, stop, and verify one durable Codex worker process family."""

from __future__ import annotations

import argparse
import ctypes
import fcntl
import json
import os
import signal
import struct
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

STATE_VERSION = 2
UNSUPPORTED = "UNSUPPORTED_PROCESS_FAMILY_SEMANTICS"
FAMILY_SEMANTICS_UNSUPPORTED = "unsupported"
TERMINAL = {"stopped", "exited"}
TRANSITIONS = {
    "launching": {"running", "stopping", "exited"},
    "running": {"stopping", "exited"},
    "stopping": {"stopped", "exited"},
    "stopped": set(),
    "exited": set(),
}
PROC_PIDTBSDINFO = 3
PROC_PIDVNODEPATHINFO = 9
BSD_SIZE = 136
VNODE_SIZE = 2352
VNODE_CWD_OFFSET = 152
PID_MAX = 2**31 - 1
UINT64_MAX = 2**64 - 1


def fail(message: str, code: int = 1) -> int:
    print(f"codex-worker: {message}", file=sys.stderr)
    return code


def resolved_directory(value: str) -> Path:
    path = Path(value).resolve(strict=True)
    if not path.is_dir():
        raise argparse.ArgumentTypeError("must be an existing directory")
    return path


def is_within(path: Path, directory: Path) -> bool:
    return path == directory or directory in path.parents


@contextmanager
def state_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    with lock.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield


def atomic_write(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(state, file, indent=2, sort_keys=True)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
        parent = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_state(path: Path, *, family_required: bool = False) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    if family_required and value.get("version") != STATE_VERSION:
        return None
    return value


def transition(path: Path, state: dict[str, Any], lifecycle: str) -> dict[str, Any]:
    previous = state.get("lifecycle")
    if previous not in TRANSITIONS or lifecycle not in TRANSITIONS[previous]:
        raise ValueError(f"illegal lifecycle transition {previous!r} to {lifecycle!r}")
    updated = dict(state)
    updated["lifecycle"] = lifecycle
    atomic_write(path, updated)
    return updated


def _bounded_integer(value: Any, minimum: int, maximum: int) -> bool:
    return type(value) is int and minimum <= value <= maximum


def _canonical_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or not Path(value).is_absolute():
        return False
    try:
        return str(Path(value).resolve()) == value
    except (OSError, RuntimeError, ValueError):
        return False


BASE_STATE_FIELDS = {"version", "lifecycle", "session_id", "model", "sandbox", "cwd"}


def _valid_common_schema(state: dict[str, Any], allowed: set[str]) -> bool:
    if not BASE_STATE_FIELDS.issubset(state):
        return False
    if not set(state).issubset(allowed):
        return False
    if type(state["version"]) is not int or state["version"] != STATE_VERSION:
        return False
    if not isinstance(state["lifecycle"], str) or state["lifecycle"] not in TRANSITIONS:
        return False
    if not isinstance(state["session_id"], str):
        return False
    if not isinstance(state["model"], str) or not state["model"]:
        return False
    if not isinstance(state["sandbox"], str) or state["sandbox"] not in {"read-only", "workspace-write"}:
        return False
    if not _canonical_path(state["cwd"]):
        return False
    control = state.get("control_checkout")
    if control is not None and not _canonical_path(control):
        return False
    if state["sandbox"] == "workspace-write":
        if control is None or is_within(Path(state["cwd"]), Path(control)):
            return False
    return True


def valid_family_schema(state: dict[str, Any]) -> bool:
    identity = {"pid", "pgid", "sid", "birth"}
    if not identity.issubset(state):
        return False
    if not _valid_common_schema(state, BASE_STATE_FIELDS | identity | {"control_checkout"}):
        return False
    for field in ("pid", "pgid", "sid"):
        if not _bounded_integer(state[field], 1, PID_MAX):
            return False
    birth = state["birth"]
    if not isinstance(birth, dict) or set(birth) != {"seconds", "microseconds"}:
        return False
    if not _bounded_integer(birth["seconds"], 1, UINT64_MAX):
        return False
    if not _bounded_integer(birth["microseconds"], 0, 999_999):
        return False
    return True


def valid_portable_schema(state: dict[str, Any]) -> bool:
    allowed = BASE_STATE_FIELDS | {"control_checkout", "family_semantics", "generation"}
    if not _valid_common_schema(state, allowed):
        return False
    if state["lifecycle"] != "exited":
        return False
    if state.get("family_semantics") != FAMILY_SEMANTICS_UNSUPPORTED:
        return False
    if not _bounded_integer(state.get("generation"), 1, UINT64_MAX):
        return False
    return True


def _libproc() -> ctypes.CDLL | None:
    if sys.platform != "darwin":
        return None
    try:
        library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        library.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
        library.proc_pidinfo.restype = ctypes.c_int
        library.proc_listpgrppids.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
        library.proc_listpgrppids.restype = ctypes.c_int
        return library
    except OSError:
        return None


def live_identity(pid: int) -> dict[str, Any] | None:
    library = _libproc()
    if library is None:
        return None
    bsd = ctypes.create_string_buffer(BSD_SIZE)
    ctypes.set_errno(0)
    if library.proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, bsd, BSD_SIZE) != BSD_SIZE:
        return None
    cwd = ctypes.create_string_buffer(VNODE_SIZE)
    ctypes.set_errno(0)
    if library.proc_pidinfo(pid, PROC_PIDVNODEPATHINFO, 0, cwd, VNODE_SIZE) != VNODE_SIZE:
        return None
    try:
        returned_pid = struct.unpack_from("<I", bsd.raw, 12)[0]
        pgid = struct.unpack_from("<I", bsd.raw, 100)[0]
        seconds, microseconds = struct.unpack_from("<QQ", bsd.raw, 120)
        sid = os.getsid(pid)
        directory = cwd.raw[VNODE_CWD_OFFSET:].split(b"\0", 1)[0].decode("utf-8")
        canonical_cwd = str(Path(directory).resolve(strict=True))
    except (OSError, UnicodeDecodeError, struct.error):
        return None
    if returned_pid != pid or not directory:
        return None
    return {"pid": pid, "pgid": pgid, "sid": sid, "cwd": canonical_cwd,
            "birth": {"seconds": seconds, "microseconds": microseconds}}


def group_members(pgid: int) -> list[int] | None:
    library = _libproc()
    if library is None:
        return None
    capacity = 64
    while capacity <= 65536:
        values = (ctypes.c_int * capacity)()
        ctypes.set_errno(0)
        count = library.proc_listpgrppids(pgid, values, ctypes.sizeof(values))
        if count < 0 or (count == 0 and ctypes.get_errno()):
            return None
        members = list(values[:count])
        if count < capacity:
            return members
        capacity *= 2
    return None


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
        try: entries, error = parse_jsonl(rollout.read_text(encoding="utf-8"))
        except OSError: continue
        if error is None and any(entry.get("type") == "session_meta" and isinstance(entry.get("payload"), dict) and entry["payload"].get("session_id") == session_id for entry in entries): matches.append(rollout)
    if not matches: return None
    entries, error = parse_jsonl(max(matches, key=lambda item: item.stat().st_mtime_ns).read_text(encoding="utf-8"))
    if error: return None
    limits = None
    for entry in entries:
        payload = entry.get("payload")
        if entry.get("type") == "event_msg" and isinstance(payload, dict) and payload.get("type") == "token_count": limits = payload.get("rate_limits") if isinstance(payload.get("rate_limits"), dict) else None
    return limits


def emit(state: dict[str, Any], final_message: str) -> None:
    limits = latest_rate_limits(state["session_id"])
    primary = limits.get("primary") if isinstance(limits, dict) else None
    remaining = 100 - primary["used_percent"] if isinstance(primary, dict) and isinstance(primary.get("used_percent"), (int, float)) else None
    print(json.dumps({"session_id": state["session_id"], "model": state["model"], "sandbox": state["sandbox"], "cwd": state["cwd"], "final_message": final_message, "headroom": remaining, "headroom_status": "known" if remaining is not None else "unknown"}))


def gate_wait(fd: int) -> None:
    if os.read(fd, 1) != b"R":
        os._exit(125)


def gated_process(command: list[str], cwd: Path) -> tuple[subprocess.Popen[str], int]:
    """Exec a session-leading gate wrapper; Popen can return before the real exec."""
    gate_read, gate_write = os.pipe()
    wrapper = (
        "import json,os,sys; "
        "os.setsid(); os.chdir(sys.argv[2]); "
        "os.read(int(sys.argv[1]), 1) == b'R' or os._exit(125); "
        "os.execvp(json.loads(sys.argv[3])[0], json.loads(sys.argv[3]))"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", wrapper, str(gate_read), str(cwd), json.dumps(command)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=(gate_read,),
    )
    os.close(gate_read)
    return process, gate_write


def establish_family(
    args: argparse.Namespace,
    command: list[str],
    state: dict[str, Any],
) -> tuple[subprocess.Popen[str] | None, int | None]:
    """Persist and release one gated family while the caller holds the state lock."""
    process, write_fd = gated_process(command, Path(state["cwd"]))
    pid = process.pid
    try:
        identity = None
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            identity = live_identity(pid)
            if identity and identity["pgid"] == pid and identity["sid"] == pid and identity["cwd"] == state["cwd"]:
                break
            time.sleep(0.01)
        if identity is None or identity["pgid"] != pid or identity["sid"] != pid or identity["cwd"] != state["cwd"]:
            os.kill(pid, signal.SIGKILL); process.communicate()
            return None, fail(f"could not establish dedicated worker process family: observed={identity!r} expected_cwd={state['cwd']!r}")
        state = {**state, **identity}
        atomic_write(args.state, state)
        os.write(write_fd, b"R")
        state = transition(args.state, state, "running")
    finally:
        os.close(write_fd)
    return process, None


def finish_lifecycle(args: argparse.Namespace, process: subprocess.Popen[str]) -> int:
    stdout, stderr = process.communicate()
    returncode = process.returncode
    with state_lock(args.state):
        current = read_state(args.state, family_required=True)
        if current and current.get("lifecycle") in {"launching", "running"}:
            state = transition(args.state, current, "running") if current["lifecycle"] == "launching" else current
            state = transition(args.state, state, "exited")
    if returncode:
        sys.stdout.write(stdout); sys.stderr.write(stderr); return returncode
    items, error = parse_jsonl(stdout)
    if error: return fail(error)
    session_id, error = captured_thread_id(items)
    if error: return fail(error)
    message, error = final_agent_message(items)
    if error: return fail(error)
    with state_lock(args.state):
        current = read_state(args.state, family_required=True)
        if current is None: return fail("state file was lost during worker execution")
        current["session_id"] = session_id
        atomic_write(args.state, current)
    emit(current, message)
    return 0


def run_portable(
    args: argparse.Namespace,
    command: list[str],
    state: dict[str, Any],
    generation: int,
) -> int:
    """Run under the state lock and persist no recoverable process-family claim."""
    result = subprocess.run(
        command,
        cwd=Path(state["cwd"]),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    terminal = {
        **state,
        "lifecycle": "exited",
        "family_semantics": FAMILY_SEMANTICS_UNSUPPORTED,
        "generation": generation,
    }
    if result.returncode:
        atomic_write(args.state, terminal)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode
    items, error = parse_jsonl(result.stdout)
    session_id = None
    message = None
    if error is None:
        session_id, error = captured_thread_id(items)
    if error is None:
        message, error = final_agent_message(items)
    if session_id is not None:
        terminal["session_id"] = session_id
    atomic_write(args.state, terminal)
    if error is not None:
        return fail(error)
    emit(terminal, message or "")
    return 0


def run_lifecycle(
    args: argparse.Namespace,
    command: list[str],
    state: dict[str, Any],
    *,
    expected: dict[str, Any] | None = None,
) -> int:
    with state_lock(args.state):
        if expected is not None and read_state(args.state) != expected:
            return fail("resume requires an unchanged terminal worker state")
        if _libproc() is None:
            previous_generation = expected["generation"] if expected is not None and valid_portable_schema(expected) else 0
            if previous_generation == UINT64_MAX:
                return fail("portable state generation exhausted")
            return run_portable(args, command, state, previous_generation + 1)
        process, error = establish_family(args, command, state)
        if error is not None:
            return error
    assert process is not None
    return finish_lifecycle(args, process)


def start(args: argparse.Namespace) -> int:
    if args.sandbox == "workspace-write":
        if args.control_checkout is None: return fail("workspace-write requires --control-checkout")
        if is_within(args.cwd, args.control_checkout): return fail("workspace-write refuses the control checkout")
    state: dict[str, Any] = {"version": STATE_VERSION, "lifecycle": "launching", "model": args.model, "sandbox": args.sandbox, "cwd": str(args.cwd), "session_id": ""}
    if args.control_checkout: state["control_checkout"] = str(args.control_checkout)
    command = [args.codex, "exec", "-m", args.model, "-c", "model_reasoning_effort=medium", "--sandbox", args.sandbox, "--skip-git-repo-check", "-C", str(args.cwd), "--json", args.prompt]
    return run_lifecycle(args, command, state)


def resume(args: argparse.Namespace) -> int:
    snapshot = read_state(args.state)
    with state_lock(args.state):
        state = read_state(args.state)
        if state != snapshot:
            return fail("resume requires an unchanged terminal worker state")
        if state is None: return fail("state file is malformed or incomplete")
        if "version" not in state:
            # Legacy completed states are compatible only for ordinary resume.
            legacy = {"session_id", "model", "sandbox", "cwd"}
            if not legacy.issubset(state) or not set(state).issubset(legacy | {"control_checkout"}): return fail("state file is malformed or incomplete")
            if not all(isinstance(state[key], str) and state[key] for key in legacy): return fail("state file is malformed or incomplete")
        elif not (valid_family_schema(state) or valid_portable_schema(state)):
            return fail("state file is malformed or incomplete")
        elif state["lifecycle"] not in TERMINAL or not state["session_id"]:
            return fail("resume requires a terminal worker state with a session ID")
        try: cwd = resolved_directory(state["cwd"])
        except (OSError, argparse.ArgumentTypeError): return fail("state file has an invalid cwd")
        sandbox = state.get("sandbox")
        if sandbox not in {"read-only", "workspace-write"}: return fail("state file has an invalid sandbox")
        if sandbox == "workspace-write":
            try: control = resolved_directory(state["control_checkout"])
            except (KeyError, OSError, argparse.ArgumentTypeError): return fail("state file is missing the control checkout")
            if is_within(cwd, control): return fail("workspace-write refuses the control checkout")
        fresh = {"version": STATE_VERSION, "lifecycle": "launching", "session_id": state["session_id"], "model": state["model"], "sandbox": sandbox, "cwd": str(cwd)}
        if sandbox == "workspace-write": fresh["control_checkout"] = str(control)
    command = [args.codex, "exec", "resume", fresh["session_id"], "-m", fresh["model"], "-c", f'sandbox_mode="{fresh["sandbox"]}"', "--json", args.prompt]
    return run_lifecycle(args, command, fresh, expected=state)


def family_state(path: Path, expected: Path) -> tuple[dict[str, Any] | None, str | None]:
    state = read_state(path)
    if state is None: return None, "state is missing, corrupt, or legacy"
    version = state.get("version")
    if "version" not in state or (type(version) is int and version != STATE_VERSION):
        return None, "state is missing, corrupt, or legacy"
    if not (valid_family_schema(state) or valid_portable_schema(state)):
        return None, "state is malformed"
    if state["cwd"] != str(expected): return None, f"cwd mismatch: recorded={state['cwd']!r} expected={str(expected)!r}"
    return state, None


def matching_leader(state: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    observed = live_identity(state["pid"])
    if observed is None: return None, "leader identity probe failed"
    recorded = {key: state[key] for key in ("pid", "pgid", "sid", "cwd", "birth")}
    if observed != recorded: return None, f"identity mismatch: recorded={recorded!r} observed={observed!r}"
    return observed, None


def verify(args: argparse.Namespace) -> int:
    with state_lock(args.state):
        state, error = family_state(args.state, args.cwd)
        if error: return fail(error)
        if _libproc() is None: return fail(UNSUPPORTED)
        if valid_portable_schema(state):
            return fail("state has no recoverable process family")
        members = group_members(state["pgid"])
        if members is None: return fail("process-group probe failed")
        if members: return fail(f"worker process group still has members: {members}")
        if state["lifecycle"] not in TERMINAL:
            if state["lifecycle"] != "stopping":
                state = transition(args.state, state, "stopping")
            state = transition(args.state, state, "stopped")
    return 0


def stop(args: argparse.Namespace) -> int:
    with state_lock(args.state):
        state, error = family_state(args.state, args.cwd)
        if error: return fail(error)
        if _libproc() is None: return fail(UNSUPPORTED)
        if valid_portable_schema(state):
            return fail("state has no recoverable process family")
        leader, error = matching_leader(state)
        if error and state["lifecycle"] not in TERMINAL:
            if "identity mismatch:" in error:
                return fail(error)
            # A gone leader is safe only after the recorded PGID is observed empty
            # or is itself the exact group proved eligible for KILL below.
            members = group_members(state["pgid"])
            if members is None: return fail("process-group probe failed")
            if not members:
                if state["lifecycle"] != "stopping": state = transition(args.state, state, "stopping")
                transition(args.state, state, "stopped")
                return 0
            state = transition(args.state, state, "stopping") if state["lifecycle"] != "stopping" else state
            try: os.killpg(state["pgid"], signal.SIGKILL)
            except OSError as exc: return fail(f"KILL refused: {exc}")
            return 0
        members = group_members(state["pgid"])
        if members is None: return fail("process-group probe failed")
        if not members:
            if state["lifecycle"] not in TERMINAL:
                if state["lifecycle"] != "stopping": state = transition(args.state, state, "stopping")
                transition(args.state, state, "stopped")
            return 0
        if state["lifecycle"] in TERMINAL:
            try: os.killpg(state["pgid"], signal.SIGKILL)
            except OSError as exc: return fail(f"KILL refused: {exc}")
            deadline = time.monotonic() + args.grace_seconds
            while time.monotonic() < deadline:
                members = group_members(state["pgid"])
                if members is None: return fail("process-group probe failed")
                if not members: return verify(args)
                time.sleep(0.05)
            return fail(f"worker process group still has members: {members}")
        if state["lifecycle"] != "stopping": state = transition(args.state, state, "stopping")
        try: os.killpg(state["pgid"], signal.SIGTERM)
        except OSError as exc: return fail(f"TERM refused: {exc}")
    deadline = time.monotonic() + args.grace_seconds
    while time.monotonic() < deadline:
        members = group_members(state["pgid"])
        if members is None: return fail("process-group probe failed")
        if not members:
            with state_lock(args.state):
                current = read_state(args.state, family_required=True)
                if current and current["lifecycle"] == "stopping": transition(args.state, current, "stopped")
            return 0
        time.sleep(0.05)
    members = group_members(state["pgid"])
    if members is None: return fail("process-group probe failed")
    if not members: return 0
    # The leader may have exited; KILL is authorized solely by a successful exact-group enumeration.
    try: os.killpg(state["pgid"], signal.SIGKILL)
    except OSError as exc: return fail(f"KILL refused: {exc}")
    deadline = time.monotonic() + args.grace_seconds
    while time.monotonic() < deadline:
        members = group_members(state["pgid"])
        if members is None: return fail("process-group probe failed")
        if not members: break
        time.sleep(0.05)
    return verify(args)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--codex", default="codex")
    common.add_argument("--state", type=Path, required=True)
    common.add_argument("prompt", nargs="?")
    start_parser = commands.add_parser("start", parents=[common]); start_parser.add_argument("--model", required=True); start_parser.add_argument("--sandbox", choices=("read-only", "workspace-write"), required=True); start_parser.add_argument("--cwd", type=resolved_directory, required=True); start_parser.add_argument("--control-checkout", type=resolved_directory); start_parser.set_defaults(handler=start)
    resume_parser = commands.add_parser("resume", parents=[common]); resume_parser.set_defaults(handler=resume)
    for name, handler in (("stop", stop), ("verify", verify)):
        command = commands.add_parser(name, parents=[common]); command.add_argument("--cwd", type=resolved_directory, required=True); command.add_argument("--grace-seconds", type=float, default=1.0); command.set_defaults(handler=handler)
    return result


if __name__ == "__main__":
    arguments = parser().parse_args()
    if arguments.command in {"start", "resume"} and not arguments.prompt:
        raise SystemExit(fail("prompt is required"))
    raise SystemExit(arguments.handler(arguments))
