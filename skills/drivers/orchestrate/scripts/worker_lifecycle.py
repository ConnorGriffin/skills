"""Shared durable worker process-family lifecycle."""

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
from typing import Any, Callable


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

Fail = Callable[[str], int]
Parse = Callable[[str], tuple]
Emit = Callable[[dict[str, Any], str, Any], None]


def resolved_directory(value: str) -> Path:
    path = Path(value).resolve(strict=True)
    if not path.is_dir():
        raise argparse.ArgumentTypeError("must be an existing directory")
    return path


def is_within(path: Path, directory: Path) -> bool:
    return path == directory or directory in path.parents


def _control_checkout_refusal(cwd: Path, control_checkout: Path) -> str | None:
    if is_within(cwd, control_checkout):
        return "workspace-write refuses the control checkout"
    return None


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


def _valid_common_schema(
    state: dict[str, Any], allowed: set[str], *, effort_levels: set[str]
) -> bool:
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
    if "effort" in state and (not isinstance(state["effort"], str) or state["effort"] not in effort_levels):
        return False
    control = state.get("control_checkout")
    if control is not None and not _canonical_path(control):
        return False
    if state["sandbox"] == "workspace-write":
        if control is None or is_within(Path(state["cwd"]), Path(control)):
            return False
    return True


def valid_family_schema(state: dict[str, Any], *, effort_levels: set[str]) -> bool:
    identity = {"pid", "pgid", "sid", "birth"}
    if not identity.issubset(state):
        return False
    allowed = BASE_STATE_FIELDS | identity | {"control_checkout", "effort"}
    if not _valid_common_schema(state, allowed, effort_levels=effort_levels):
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


def valid_portable_schema(state: dict[str, Any], *, effort_levels: set[str]) -> bool:
    allowed = BASE_STATE_FIELDS | {"control_checkout", "family_semantics", "generation", "effort"}
    if not _valid_common_schema(state, allowed, effort_levels=effort_levels):
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
    return {
        "pid": pid, "pgid": pgid, "sid": sid, "cwd": canonical_cwd,
        "birth": {"seconds": seconds, "microseconds": microseconds},
    }


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


def gate_wait(fd: int) -> None:
    if os.read(fd, 1) != b"R":
        os._exit(125)


def gated_process(
    command: list[str], cwd: Path, *, stdin_text: str | None
) -> tuple[subprocess.Popen[str], int]:
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
        text=True,
        stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        pass_fds=(gate_read,),
    )
    os.close(gate_read)
    return process, gate_write


def establish_family(
    args: argparse.Namespace,
    command: list[str],
    state: dict[str, Any],
    *,
    fail: Fail,
    stdin_text: str | None,
) -> tuple[subprocess.Popen[str] | None, int | None]:
    """Persist and release one gated family while the caller holds the state lock."""
    process, write_fd = gated_process(command, Path(state["cwd"]), stdin_text=stdin_text)
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
            os.kill(pid, signal.SIGKILL)
            process.communicate()
            return None, fail(
                f"could not establish dedicated worker process family: observed={identity!r} expected_cwd={state['cwd']!r}"
            )
        state = {**state, **identity}
        atomic_write(args.state, state)
        os.write(write_fd, b"R")
        transition(args.state, state, "running")
    finally:
        os.close(write_fd)
    return process, None


def finish_lifecycle(
    args: argparse.Namespace,
    process: subprocess.Popen[str],
    *,
    parse: Parse,
    emit: Emit,
    fail: Fail,
    stdin_text: str | None,
) -> int:
    stdout, stderr = process.communicate(input=stdin_text) if stdin_text is not None else process.communicate()
    returncode = process.returncode
    with state_lock(args.state):
        current = read_state(args.state, family_required=True)
        if current and current.get("lifecycle") in {"launching", "running"}:
            state = transition(args.state, current, "running") if current["lifecycle"] == "launching" else current
            transition(args.state, state, "exited")
    if returncode:
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        return returncode
    session_id, message, metadata, error = parse(stdout)
    if error:
        return fail(error)
    with state_lock(args.state):
        current = read_state(args.state, family_required=True)
        if current is None:
            return fail("state file was lost during worker execution")
        current["session_id"] = session_id
        atomic_write(args.state, current)
    emit(current, message or "", metadata)
    return 0


def run_portable(
    args: argparse.Namespace,
    command: list[str],
    state: dict[str, Any],
    generation: int,
    *,
    parse: Parse,
    emit: Emit,
    fail: Fail,
    stdin_text: str | None,
) -> int:
    """Run under the state lock and persist no recoverable process-family claim."""
    run_arguments: dict[str, Any] = {
        "cwd": Path(state["cwd"]),
        "text": True,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "check": False,
    }
    if stdin_text is None:
        run_arguments["stdin"] = subprocess.DEVNULL
    else:
        run_arguments["input"] = stdin_text
    result = subprocess.run(command, **run_arguments)
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
    session_id, message, metadata, error = parse(result.stdout)
    if session_id is not None:
        terminal["session_id"] = session_id
    atomic_write(args.state, terminal)
    if error is not None:
        return fail(error)
    emit(terminal, message or "", metadata)
    return 0


def run_lifecycle(
    args: argparse.Namespace,
    command: list[str],
    state: dict[str, Any],
    *,
    expected: dict[str, Any] | None = None,
    parse: Parse,
    emit: Emit,
    fail: Fail,
    stdin_text: str | None,
    effort_levels: set[str],
) -> int:
    with state_lock(args.state):
        if expected is not None and read_state(args.state) != expected:
            return fail("resume requires an unchanged terminal worker state")
        if _libproc() is None:
            previous_generation = (
                expected["generation"]
                if expected is not None and valid_portable_schema(expected, effort_levels=effort_levels)
                else 0
            )
            if previous_generation == UINT64_MAX:
                return fail("portable state generation exhausted")
            return run_portable(
                args, command, state, previous_generation + 1,
                parse=parse, emit=emit, fail=fail, stdin_text=stdin_text,
            )
        process, error = establish_family(
            args, command, state, fail=fail, stdin_text=stdin_text
        )
        if error is not None:
            return error
    assert process is not None
    return finish_lifecycle(
        args, process, parse=parse, emit=emit, fail=fail, stdin_text=stdin_text
    )


def prepare_start(
    args: argparse.Namespace, *, effort_levels: set[str], default_effort: str
) -> tuple[dict[str, Any] | None, str | None]:
    if args.sandbox == "workspace-write":
        if args.control_checkout is None:
            return None, "workspace-write requires --control-checkout"
        error = _control_checkout_refusal(args.cwd, args.control_checkout)
        if error:
            return None, error
    effort = getattr(args, "effort", default_effort)
    if effort not in effort_levels:
        return None, f"--effort must be one of {sorted(effort_levels)}"
    state: dict[str, Any] = {
        "version": STATE_VERSION,
        "lifecycle": "launching",
        "model": args.model,
        "sandbox": args.sandbox,
        "cwd": str(args.cwd),
        "session_id": "",
    }
    if effort != default_effort:
        state["effort"] = effort
    if args.control_checkout:
        state["control_checkout"] = str(args.control_checkout)
    return state, None


def prepare_resume(
    args: argparse.Namespace, *, effort_levels: set[str], default_effort: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    snapshot = read_state(args.state)
    with state_lock(args.state):
        state = read_state(args.state)
        if state != snapshot:
            return None, None, "resume requires an unchanged terminal worker state"
        if state is None:
            return None, None, "state file is malformed or incomplete"
        if "version" not in state:
            legacy = {"session_id", "model", "sandbox", "cwd"}
            if not legacy.issubset(state) or not set(state).issubset(legacy | {"control_checkout", "effort"}):
                return None, None, "state file is malformed or incomplete"
            if not all(isinstance(state[key], str) and state[key] for key in legacy):
                return None, None, "state file is malformed or incomplete"
        elif not (
            valid_family_schema(state, effort_levels=effort_levels)
            or valid_portable_schema(state, effort_levels=effort_levels)
        ):
            return None, None, "state file is malformed or incomplete"
        elif state["lifecycle"] not in TERMINAL or not state["session_id"]:
            return None, None, "resume requires a terminal worker state with a session ID"
        try:
            cwd = resolved_directory(state["cwd"])
        except (OSError, argparse.ArgumentTypeError):
            return None, None, "state file has an invalid cwd"
        sandbox = state.get("sandbox")
        if sandbox not in {"read-only", "workspace-write"}:
            return None, None, "state file has an invalid sandbox"
        if sandbox == "workspace-write":
            try:
                control = resolved_directory(state["control_checkout"])
            except (KeyError, OSError, argparse.ArgumentTypeError):
                return None, None, "state file is missing the control checkout"
            error = _control_checkout_refusal(cwd, control)
            if error:
                return None, None, error
        effort = state.get("effort", default_effort)
        if effort not in effort_levels:
            return None, None, "state file has an invalid effort"
        fresh = {
            "version": STATE_VERSION,
            "lifecycle": "launching",
            "session_id": state["session_id"],
            "model": state["model"],
            "sandbox": sandbox,
            "cwd": str(cwd),
        }
        if effort != default_effort:
            fresh["effort"] = effort
        if sandbox == "workspace-write":
            fresh["control_checkout"] = str(control)
    return fresh, state, None


def family_state(
    path: Path, expected: Path, *, effort_levels: set[str]
) -> tuple[dict[str, Any] | None, str | None]:
    state = read_state(path)
    if state is None:
        return None, "state is missing, corrupt, or legacy"
    version = state.get("version")
    if "version" not in state or (type(version) is int and version != STATE_VERSION):
        return None, "state is missing, corrupt, or legacy"
    if not (
        valid_family_schema(state, effort_levels=effort_levels)
        or valid_portable_schema(state, effort_levels=effort_levels)
    ):
        return None, "state is malformed"
    if state["cwd"] != str(expected):
        return None, f"cwd mismatch: recorded={state['cwd']!r} expected={str(expected)!r}"
    return state, None


def matching_leader(state: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    observed = live_identity(state["pid"])
    if observed is None:
        return None, "leader identity probe failed"
    recorded = {key: state[key] for key in ("pid", "pgid", "sid", "cwd", "birth")}
    if observed != recorded:
        return None, f"identity mismatch: recorded={recorded!r} observed={observed!r}"
    return observed, None


def verify_worker(
    args: argparse.Namespace, *, effort_levels: set[str]
) -> tuple[int | None, str | None]:
    with state_lock(args.state):
        state, error = family_state(args.state, args.cwd, effort_levels=effort_levels)
        if error:
            return None, error
        if _libproc() is None:
            return None, UNSUPPORTED
        assert state is not None
        if valid_portable_schema(state, effort_levels=effort_levels):
            return None, "state has no recoverable process family"
        members = group_members(state["pgid"])
        if members is None:
            return None, "process-group probe failed"
        if members:
            return None, f"worker process group still has members: {members}"
        if state["lifecycle"] not in TERMINAL:
            if state["lifecycle"] != "stopping":
                state = transition(args.state, state, "stopping")
            transition(args.state, state, "stopped")
    return 0, None


def stop_worker(
    args: argparse.Namespace, *, effort_levels: set[str]
) -> tuple[int | None, str | None]:
    with state_lock(args.state):
        state, error = family_state(args.state, args.cwd, effort_levels=effort_levels)
        if error:
            return None, error
        if _libproc() is None:
            return None, UNSUPPORTED
        assert state is not None
        if valid_portable_schema(state, effort_levels=effort_levels):
            return None, "state has no recoverable process family"
        _, error = matching_leader(state)
        if error and state["lifecycle"] not in TERMINAL:
            if "identity mismatch:" in error:
                return None, error
            members = group_members(state["pgid"])
            if members is None:
                return None, "process-group probe failed"
            if not members:
                if state["lifecycle"] != "stopping":
                    state = transition(args.state, state, "stopping")
                transition(args.state, state, "stopped")
                return 0, None
            state = transition(args.state, state, "stopping") if state["lifecycle"] != "stopping" else state
            try:
                os.killpg(state["pgid"], signal.SIGKILL)
            except OSError as exc:
                return None, f"KILL refused: {exc}"
            return 0, None
        members = group_members(state["pgid"])
        if members is None:
            return None, "process-group probe failed"
        if not members:
            if state["lifecycle"] not in TERMINAL:
                if state["lifecycle"] != "stopping":
                    state = transition(args.state, state, "stopping")
                transition(args.state, state, "stopped")
            return 0, None
        if state["lifecycle"] in TERMINAL:
            try:
                os.killpg(state["pgid"], signal.SIGKILL)
            except OSError as exc:
                return None, f"KILL refused: {exc}"
            deadline = time.monotonic() + args.grace_seconds
            while time.monotonic() < deadline:
                members = group_members(state["pgid"])
                if members is None:
                    return None, "process-group probe failed"
                if not members:
                    return verify_worker(args, effort_levels=effort_levels)
                time.sleep(0.05)
            return None, f"worker process group still has members: {members}"
        if state["lifecycle"] != "stopping":
            state = transition(args.state, state, "stopping")
        try:
            os.killpg(state["pgid"], signal.SIGTERM)
        except OSError as exc:
            return None, f"TERM refused: {exc}"
    deadline = time.monotonic() + args.grace_seconds
    while time.monotonic() < deadline:
        members = group_members(state["pgid"])
        if members is None:
            return None, "process-group probe failed"
        if not members:
            with state_lock(args.state):
                current = read_state(args.state, family_required=True)
                if current and current["lifecycle"] == "stopping":
                    transition(args.state, current, "stopped")
            return 0, None
        time.sleep(0.05)
    members = group_members(state["pgid"])
    if members is None:
        return None, "process-group probe failed"
    if not members:
        return 0, None
    try:
        os.killpg(state["pgid"], signal.SIGKILL)
    except OSError as exc:
        return None, f"KILL refused: {exc}"
    deadline = time.monotonic() + args.grace_seconds
    while time.monotonic() < deadline:
        members = group_members(state["pgid"])
        if members is None:
            return None, "process-group probe failed"
        if not members:
            break
        time.sleep(0.05)
    return verify_worker(args, effort_levels=effort_levels)
