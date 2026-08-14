from __future__ import annotations

import argparse
import fcntl
import json
import os
import importlib.util
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Optional
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CBM_SCRIPT = ROOT / "skills" / "cbm-onboard" / "scripts" / "cbm-onboard.sh"
SPIN_SCRIPT = ROOT / "skills" / "spin-worktree" / "scripts" / "spin-worktree.py"
CODEX_WORKER = ROOT / "skills" / "orchestrate" / "scripts" / "codex-worker.py"
BEGIN_IGNORE = "# >>> cbm-onboard managed baseline — do not edit inside this block >>>"
BEGIN_HOOK = "# >>> cbm-onboard managed reindex >>>"

WORKER_SPEC = importlib.util.spec_from_file_location("orchestrate_worker", CODEX_WORKER)
assert WORKER_SPEC and WORKER_SPEC.loader
WORKER_MODULE = importlib.util.module_from_spec(WORKER_SPEC)
WORKER_SPEC.loader.exec_module(WORKER_MODULE)


def run(
    command: list[str], *, cwd: Path, env: Optional[dict[str, str]] = None
):
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class CbmOnboardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.scratch = Path(self.temporary.name)
        self.repo = self.scratch / "repo"
        self.repo.mkdir()
        result = run(["git", "init", "-b", "main"], cwd=self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.binary = self.scratch / "codebase-memory-mcp"
        self.binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.binary.chmod(0o755)
        self.environment = os.environ.copy()
        self.environment["CODEBASE_MEMORY_BIN"] = str(self.binary)
        self.environment["PRIVATE_SENTINEL"] = "must-not-appear"

    def tearDown(self):
        self.temporary.cleanup()

    def onboard(self):
        result = run(
            [str(CBM_SCRIPT), str(self.repo)],
            cwd=ROOT,
            env=self.environment,
        )
        self.assertNotIn("must-not-appear", result.stdout + result.stderr)
        return result

    def test_refuses_cbmignore_symlink_without_touching_target(self):
        target = self.scratch / "outside-ignore"
        target.write_text("sentinel\n", encoding="utf-8")
        (self.repo / ".cbmignore").symlink_to(target)

        result = self.onboard()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing symlink target", result.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), "sentinel\n")

    def test_refuses_hook_symlink_and_honors_core_hooks_path(self):
        run(
            ["git", "config", "core.hooksPath", ".custom-hooks"],
            cwd=self.repo,
        )
        hooks = self.repo / ".custom-hooks"
        hooks.mkdir()
        target = self.scratch / "outside-hook"
        target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (hooks / "post-commit").symlink_to(target)

        result = self.onboard()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing symlink target", result.stderr)
        self.assertEqual(
            target.read_text(encoding="utf-8"),
            "#!/bin/sh\nexit 0\n",
        )
        self.assertFalse((self.repo / ".git" / "hooks" / "post-commit").exists())

    def test_preserves_unmatched_markers_foreign_hook_and_is_idempotent(self):
        run(
            ["git", "config", "core.hooksPath", ".custom-hooks"],
            cwd=self.repo,
        )
        hooks = self.repo / ".custom-hooks"
        hooks.mkdir()
        ignore_original = f"custom-before/\n{BEGIN_IGNORE}\ncustom-after/\n"
        hook_original = (
            "#!/bin/sh\n"
            "printf '%s\\n' foreign-hook\n"
            f"{BEGIN_HOOK}\n"
            "printf '%s\\n' after-unmatched-marker\n"
        )
        (self.repo / ".cbmignore").write_text(ignore_original, encoding="utf-8")
        hook = hooks / "post-commit"
        hook.write_text(hook_original, encoding="utf-8")
        hook.chmod(0o755)

        first = self.onboard()
        self.assertEqual(first.returncode, 0, first.stderr)
        first_ignore = (self.repo / ".cbmignore").read_bytes()
        first_hook = hook.read_bytes()
        second = self.onboard()
        self.assertEqual(second.returncode, 0, second.stderr)

        self.assertEqual((self.repo / ".cbmignore").read_bytes(), first_ignore)
        self.assertEqual(hook.read_bytes(), first_hook)
        self.assertIn(ignore_original, first_ignore.decode())
        self.assertIn(hook_original, first_hook.decode())
        for exclusion in (".env.*", "*.pem", "*.key", "credentials/", "secrets/"):
            self.assertIn(exclusion, first_ignore.decode())
        self.assertFalse((self.repo / ".git" / "hooks" / "post-commit").exists())

    def test_skips_non_shell_foreign_hook_without_modifying_it(self):
        run(
            ["git", "config", "core.hooksPath", ".custom-hooks"],
            cwd=self.repo,
        )
        hooks = self.repo / ".custom-hooks"
        hooks.mkdir()
        hook = hooks / "post-commit"
        original = "#!/usr/bin/env python3\nprint('foreign')\n"
        hook.write_text(original, encoding="utf-8")
        hook.chmod(0o755)

        result = self.onboard()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SKIP hook installation", result.stderr)
        self.assertEqual(hook.read_text(encoding="utf-8"), original)


class SpinWorktreeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.scratch = Path(self.temporary.name)
        self.repo = self.scratch / "repo"
        self.repo.mkdir()
        self.assertEqual(
            run(["git", "init", "-b", "main"], cwd=self.repo).returncode,
            0,
        )
        run(["git", "config", "user.name", "Test User"], cwd=self.repo)
        run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo)
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        run(["git", "add", "README.md"], cwd=self.repo)
        self.assertEqual(
            run(["git", "commit", "-m", "fixture"], cwd=self.repo).returncode,
            0,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def spin(self, *arguments: str):
        return run(
            [
                "python3",
                str(SPIN_SCRIPT),
                "--repo",
                str(self.repo),
                "--worktree-root",
                str(self.scratch / "worktrees"),
                *arguments,
            ],
            cwd=ROOT,
        )

    def test_rejects_names_that_can_escape_the_task_directory(self):
        for unsafe in ("", ".", "..", "../escape", "nested/name", "nested\\name", "/tmp/x"):
            with self.subTest(unsafe=unsafe):
                result = self.spin(
                    "--issue",
                    "1",
                    "--name",
                    unsafe,
                    "--dry-run",
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("one safe relative directory name", result.stderr)
        self.assertFalse((self.scratch / "escape").exists())

    def test_uses_an_existing_local_branch_without_an_origin_remote(self):
        run(["git", "branch", "local-topic"], cwd=self.repo)

        result = self.spin(
            "--branch",
            "local-topic",
            "--name",
            "local-topic",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            (self.scratch / "worktrees" / "repo" / "local-topic" / ".git").exists()
        )


class CodexWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.scratch = Path(self.temporary.name)
        self.control = self.scratch / "control"
        self.worktree = self.scratch / "worktree"
        self.control.mkdir()
        self.worktree.mkdir()
        self.state = self.scratch / "worker-state.json"
        self.codex_home = self.scratch / "codex-home"
        self.binary = self.scratch / "fake-codex"
        self.arguments = self.scratch / "arguments.json"
        self.child_cwd = self.scratch / "child-cwd"
        self.binary.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, pathlib, signal, subprocess, sys, time\n"
            "pathlib.Path(os.environ['FAKE_CODEX_ARGUMENTS']).write_text(json.dumps(sys.argv[1:]))\n"
            "if os.environ.get('FAKE_CODEX_CWD'):\n"
            "    pathlib.Path(os.environ['FAKE_CODEX_CWD']).write_text(os.getcwd())\n"
            "if os.environ.get('FAKE_CODEX_HOLD'):\n"
            "    child = subprocess.Popen([sys.executable, '-c', \"import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)\"])\n"
            "    pathlib.Path(os.environ['FAKE_CODEX_CHILD']).write_text(str(child.pid))\n"
            "    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))\n"
            "    while True: time.sleep(1)\n"
            "sys.stdout.write(os.environ.get('FAKE_CODEX_OUTPUT', ''))\n"
            "sys.exit(int(os.environ.get('FAKE_CODEX_EXIT', '0')))\n",
            encoding="utf-8",
        )
        self.binary.chmod(0o755)
        self.environment = os.environ.copy()
        self.environment["CODEX_HOME"] = str(self.codex_home)
        self.environment["FAKE_CODEX_ARGUMENTS"] = str(self.arguments)

    def tearDown(self):
        self.temporary.cleanup()

    def worker(self, *arguments: str):
        return run(
            ["python3", str(CODEX_WORKER), *arguments],
            cwd=ROOT,
            env=self.environment,
        )

    def start(
        self,
        output: str,
        *,
        sandbox: str = "read-only",
        final_message: Optional[str] = "worker answer",
    ):
        if final_message is not None:
            output += json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": final_message},
                }
            ) + "\n"
        self.environment["FAKE_CODEX_OUTPUT"] = output
        arguments = [
            "start",
            "--codex",
            str(self.binary),
            "--state",
            str(self.state),
            "--model",
            "Terra",
            "--sandbox",
            sandbox,
            "--cwd",
            str(self.worktree),
        ]
        if sandbox == "workspace-write":
            arguments.extend(["--control-checkout", str(self.control)])
        return self.worker(*arguments, "do the work")

    def launch_holding_worker(self, state: Path, cwd: Path, child: Path):
        environment = self.environment.copy()
        environment["FAKE_CODEX_HOLD"] = "1"
        environment["FAKE_CODEX_CHILD"] = str(child)
        command = [
            "python3", str(CODEX_WORKER), "start", "--codex", str(self.binary),
            "--state", str(state), "--model", "Terra", "--sandbox", "read-only",
            "--cwd", str(cwd), "hold",
        ]
        launcher = subprocess.Popen(command, cwd=ROOT, env=environment)
        deadline = time.monotonic() + 3
        while (not child.exists() or not state.exists()) and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(child.exists(), "fixture child did not start")
        self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["lifecycle"], "running")
        return launcher

    def launch_holding_resume(self, child: Path):
        environment = self.environment.copy()
        environment["FAKE_CODEX_HOLD"] = "1"
        environment["FAKE_CODEX_CHILD"] = str(child)
        launcher = subprocess.Popen(
            ["python3", str(CODEX_WORKER), "resume", "--codex", str(self.binary), "--state", str(self.state), "hold"],
            cwd=ROOT,
            env=environment,
        )
        deadline = time.monotonic() + 3
        while (not child.exists() or not self.state.exists()) and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(child.exists(), "resumed fixture child did not start")
        self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["lifecycle"], "running")
        return launcher

    def stop_fixture(self, state: Path, cwd: Path):
        result = self.worker("stop", "--state", str(state), "--cwd", str(cwd))
        self.assertEqual(result.returncode, 0, result.stderr)
        verified = self.worker("verify", "--state", str(state), "--cwd", str(cwd))
        self.assertEqual(verified.returncode, 0, verified.stderr)

    def assert_alive(self, path: Path):
        os.kill(int(path.read_text(encoding="utf-8")), 0)

    def rollout(self, name: str, session_id: str, *events: dict):
        path = self.codex_home / "sessions" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        entries = [
            {"type": "session_meta", "payload": {"session_id": session_id}},
            *events,
        ]
        path.write_text(
            "".join(json.dumps(entry) + "\n" for entry in entries), encoding="utf-8"
        )

    def test_start_persists_worker_state_and_uses_canonical_cwd(self):
        result = self.start('{"type":"thread.started","thread_id":"worker-1"}\n')

        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertEqual(state["version"], 2)
        self.assertEqual(state["lifecycle"], "exited")
        self.assertEqual(state["session_id"], "worker-1")
        self.assertEqual(state["cwd"], str(self.worktree.resolve()))
        self.assertEqual(state["pid"], state["pgid"])
        self.assertEqual(state["pid"], state["sid"])
        self.assertIn("seconds", state["birth"])
        self.assertIn("microseconds", state["birth"])
        arguments = json.loads(self.arguments.read_text(encoding="utf-8"))
        self.assertIn("--sandbox", arguments)
        self.assertIn(str(self.worktree.resolve()), arguments)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["final_message"], "worker answer")
        self.assertEqual(payload["headroom_status"], "unknown")

    def test_resume_reapplies_persisted_model_and_sandbox(self):
        started = self.start(
            '{"type":"thread.started","thread_id":"worker-1"}\n',
            sandbox="workspace-write",
        )
        self.assertEqual(started.returncode, 0, started.stderr)
        self.environment["FAKE_CODEX_OUTPUT"] = (
            '{"type":"thread.started","thread_id":"worker-1"}\n'
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"resume answer"}}\n'
        )

        result = self.worker(
            "resume",
            "--codex",
            str(self.binary),
            "--state",
            str(self.state),
            "continue with the failing test",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(self.arguments.read_text(encoding="utf-8")),
            [
                "exec",
                "resume",
                "worker-1",
                "-m",
                "Terra",
                "-c",
                'sandbox_mode="workspace-write"',
                "--json",
                "continue with the failing test",
            ],
        )
        self.assertEqual(json.loads(result.stdout)["final_message"], "resume answer")

    def test_resume_runs_the_codex_process_in_the_persisted_worktree(self):
        started = self.start('{"type":"thread.started","thread_id":"worker-1"}\n')
        self.assertEqual(started.returncode, 0, started.stderr)
        self.environment["FAKE_CODEX_CWD"] = str(self.child_cwd)
        self.environment["FAKE_CODEX_OUTPUT"] = (
            '{"type":"thread.started","thread_id":"worker-1"}\n'
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"resume answer"}}\n'
        )

        result = self.worker(
            "resume",
            "--codex",
            str(self.binary),
            "--state",
            str(self.state),
            "continue with the failing test",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.child_cwd.read_text(encoding="utf-8"), str(self.worktree.resolve())
        )

    def test_error_item_fails_even_when_codex_exits_zero(self):
        result = self.start(
            '{"type":"thread.started","thread_id":"worker-1"}\n'
            '{"type":"item.completed","item":{"type":"error"}}\n'
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reported an error item", result.stderr)
        self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["lifecycle"], "exited")

    def test_start_fails_without_a_completed_agent_message(self):
        result = self.start(
            '{"type":"thread.started","thread_id":"worker-1"}\n'
            '{"type":"item.completed","item":{"type":"reasoning"}}\n',
            final_message=None,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing completed agent message", result.stderr)
        self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["lifecycle"], "exited")

    def test_preserves_a_nonzero_codex_exit_status(self):
        self.environment["FAKE_CODEX_EXIT"] = "7"

        result = self.start("worker failed\n", final_message=None)

        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout, "worker failed\n")
        self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["lifecycle"], "exited")

    def test_headroom_uses_the_matching_session_rollout(self):
        token_count = {
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "rate_limits": {"primary": {"used_percent": 40}},
            },
        }
        self.rollout("matching.jsonl", "worker-1", token_count)
        self.rollout(
            "unrelated.jsonl",
            "other-worker",
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "rate_limits": {"primary": {"used_percent": 99}},
                },
            },
        )

        result = self.start('{"type":"thread.started","thread_id":"worker-1"}\n')

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["headroom"], 60)
        self.assertEqual(payload["headroom_status"], "known")

    def test_missing_rate_limits_reports_unknown(self):
        self.rollout(
            "matching.jsonl",
            "worker-1",
            {"type": "event_msg", "payload": {"type": "token_count"}},
        )

        result = self.start('{"type":"thread.started","thread_id":"worker-1"}\n')

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIsNone(payload["headroom"])
        self.assertEqual(payload["headroom_status"], "unknown")

    def test_malformed_missing_and_ambiguous_thread_ids_fail_closed(self):
        cases = {
            "malformed": "not json\n",
            "missing": '{"type":"item.completed","item":{"type":"agent_message"}}\n',
            "ambiguous": (
                '{"type":"thread.started","thread_id":"one"}\n'
                '{"type":"thread.started","thread_id":"two"}\n'
            ),
        }
        for name, output in cases.items():
            with self.subTest(name=name):
                if self.state.exists():
                    self.state.unlink()
                result = self.start(output)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["lifecycle"], "exited")

    def test_workspace_write_rejects_the_control_checkout(self):
        self.environment["FAKE_CODEX_OUTPUT"] = (
            '{"type":"thread.started","thread_id":"worker-1"}\n'
        )
        result = self.worker(
            "start",
            "--codex",
            str(self.binary),
            "--state",
            str(self.state),
            "--model",
            "Terra",
            "--sandbox",
            "workspace-write",
            "--cwd",
            str(self.control),
            "--control-checkout",
            str(self.control),
            "do the work",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refuses the control checkout", result.stderr)
        self.assertFalse(self.arguments.exists())

    def test_stop_kills_only_the_recorded_group_after_its_leader_exits(self):
        child = self.scratch / "child-pid"
        self.environment["FAKE_CODEX_HOLD"] = "1"
        self.environment["FAKE_CODEX_CHILD"] = str(child)
        command = [
            "python3", str(CODEX_WORKER), "start", "--codex", str(self.binary),
            "--state", str(self.state), "--model", "Terra", "--sandbox", "read-only",
            "--cwd", str(self.worktree), "hold",
        ]
        launcher = subprocess.Popen(command, cwd=ROOT, env=self.environment)
        try:
            deadline = time.monotonic() + 3
            while not child.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(child.exists())
            result = self.worker("stop", "--state", str(self.state), "--cwd", str(self.worktree))
            self.assertEqual(result.returncode, 0, result.stderr)
            verified = self.worker("verify", "--state", str(self.state), "--cwd", str(self.worktree))
            self.assertEqual(verified.returncode, 0, verified.stderr)
        finally:
            if launcher.poll() is None and self.state.exists():
                self.worker("stop", "--state", str(self.state), "--cwd", str(self.worktree))
            launcher.wait(timeout=5)

    def test_stopping_one_distinct_worktree_group_leaves_the_other_group_alive(self):
        other_worktree = self.scratch / "other-worktree"
        other_worktree.mkdir()
        first_state = self.scratch / "first-state.json"
        second_state = self.scratch / "second-state.json"
        first_child = self.scratch / "first-child"
        second_child = self.scratch / "second-child"
        first = self.launch_holding_worker(first_state, self.worktree, first_child)
        second = self.launch_holding_worker(second_state, other_worktree, second_child)
        try:
            self.stop_fixture(first_state, self.worktree)
            self.assert_alive(second_child)
            self.assertEqual(
                json.loads(second_state.read_text(encoding="utf-8"))["cwd"],
                str(other_worktree.resolve()),
            )
            still_running = self.worker("verify", "--state", str(second_state), "--cwd", str(other_worktree))
            self.assertNotEqual(still_running.returncode, 0)
        finally:
            if first.poll() is None and first_state.exists():
                self.stop_fixture(first_state, self.worktree)
            if second.poll() is None and second_state.exists():
                self.stop_fixture(second_state, other_worktree)
            first.wait(timeout=5)
            second.wait(timeout=5)

    def test_identity_and_cwd_mismatches_refuse_without_signaling_the_fixture(self):
        child = self.scratch / "child-pid"
        launcher = self.launch_holding_worker(self.state, self.worktree, child)
        original = json.loads(self.state.read_text(encoding="utf-8"))
        other_worktree = self.scratch / "other-worktree"
        other_worktree.mkdir()
        try:
            mismatch = self.worker("stop", "--state", str(self.state), "--cwd", str(other_worktree))
            self.assertNotEqual(mismatch.returncode, 0)
            self.assertIn("cwd mismatch", mismatch.stderr)
            self.assert_alive(child)
            for field, changed in (
                ("birth", {"seconds": original["birth"]["seconds"] + 1, "microseconds": original["birth"]["microseconds"]}),
                ("pgid", original["pgid"] + 1),
                ("sid", original["sid"] + 1),
            ):
                state = dict(original)
                state[field] = changed
                self.state.write_text(json.dumps(state), encoding="utf-8")
                mismatch = self.worker("stop", "--state", str(self.state), "--cwd", str(self.worktree))
                self.assertNotEqual(mismatch.returncode, 0)
                self.assertIn("identity mismatch", mismatch.stderr)
                self.assert_alive(child)
            self.state.write_text(json.dumps(original), encoding="utf-8")
        finally:
            self.stop_fixture(self.state, self.worktree)
            launcher.wait(timeout=5)

    def test_concurrent_resume_cannot_win_against_a_durable_launch_claim(self):
        started = self.start('{"type":"thread.started","thread_id":"worker-1"}\n')
        self.assertEqual(started.returncode, 0, started.stderr)
        child = self.scratch / "resumed-child"
        launcher = self.launch_holding_resume(child)
        try:
            concurrent = self.worker("resume", "--codex", str(self.binary), "--state", str(self.state), "compete")
            self.assertNotEqual(concurrent.returncode, 0)
            self.assertIn("terminal worker state", concurrent.stderr)
            self.assert_alive(child)
            self.stop_fixture(self.state, self.worktree)
        finally:
            if launcher.poll() is None and self.state.exists():
                self.stop_fixture(self.state, self.worktree)
            launcher.wait(timeout=5)
        self.environment["FAKE_CODEX_OUTPUT"] = (
            '{"type":"thread.started","thread_id":"worker-1"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"resumed"}}\n'
        )
        repeated = self.worker("resume", "--codex", str(self.binary), "--state", str(self.state), "again")
        self.assertEqual(repeated.returncode, 0, repeated.stderr)

    def test_lock_contended_stop_and_resume_cannot_both_win(self):
        child = self.scratch / "contended-child"
        launcher = self.launch_holding_worker(self.state, self.worktree, child)
        lock_path = self.state.with_name(self.state.name + ".lock")
        with lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            stop = subprocess.Popen(
                ["python3", str(CODEX_WORKER), "stop", "--state", str(self.state), "--cwd", str(self.worktree)],
                cwd=ROOT, env=self.environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            resume = subprocess.Popen(
                ["python3", str(CODEX_WORKER), "resume", "--codex", str(self.binary), "--state", str(self.state), "compete"],
                cwd=ROOT, env=self.environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            time.sleep(0.05)
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        try:
            _, stop_error = stop.communicate(timeout=5)
            _, resume_error = resume.communicate(timeout=5)
            self.assertEqual(stop.returncode, 0, stop_error)
            self.assertNotEqual(resume.returncode, 0)
            self.assertIn("terminal worker state", resume_error)
        finally:
            if launcher.poll() is None and self.state.exists():
                self.stop_fixture(self.state, self.worktree)
            launcher.wait(timeout=5)

    def test_workspace_write_rejects_a_path_inside_the_control_checkout(self):
        nested = self.control / "nested"
        nested.mkdir()
        self.environment["FAKE_CODEX_OUTPUT"] = (
            '{"type":"thread.started","thread_id":"worker-1"}\n'
        )

        result = self.worker(
            "start",
            "--codex",
            str(self.binary),
            "--state",
            str(self.state),
            "--model",
            "Terra",
            "--sandbox",
            "workspace-write",
            "--cwd",
            str(nested),
            "--control-checkout",
            str(self.control),
            "do the work",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refuses the control checkout", result.stderr)
        self.assertFalse(self.arguments.exists())

    def test_resume_rejects_a_persisted_path_inside_the_control_checkout(self):
        nested = self.control / "nested"
        nested.mkdir()
        self.state.write_text(
            json.dumps(
                {
                    "session_id": "worker-1",
                    "model": "Terra",
                    "sandbox": "workspace-write",
                    "cwd": str(nested),
                    "control_checkout": str(self.control),
                }
            ),
            encoding="utf-8",
        )

        result = self.worker(
            "resume",
            "--codex",
            str(self.binary),
            "--state",
            str(self.state),
            "continue with the failing test",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refuses the control checkout", result.stderr)
        self.assertFalse(self.arguments.exists())


class OrchestrateCodexPolicyTests(unittest.TestCase):
    def test_codex_headroom_and_single_rung_policy_are_explicit(self):
        skill = (ROOT / "skills" / "orchestrate" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        dispatch = (
            ROOT / "skills" / "orchestrate" / "references" / "dispatch-codex.md"
        ).read_text(encoding="utf-8")

        self.assertIn("If headroom is ≤ 5%, **unknown**", skill)
        self.assertIn("Codex UI parent:** it has a Codex-only constraint", skill)
        self.assertIn("Do not switch to Claude workers.", skill)
        self.assertIn("stop with **NO_VALIDATED_ROUTE**", skill)
        self.assertIn("Never escalate Terra, Luna, or Sol to Sonnet or Opus.", skill)
        for model in ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"):
            self.assertIn(model, dispatch)
        self.assertIn("cannot switch to Claude workers", dispatch)
        self.assertIn("headroom at or below 5%", dispatch)
        self.assertIn("Each admitted v0 route is one", dispatch)


class WorkerLifecycleContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cwd = self.root / "worktree"
        self.cwd.mkdir()
        self.cwd = self.cwd.resolve()
        self.state = self.root / "state.json"
        self.identity = {
            "pid": 41,
            "pgid": 41,
            "sid": 41,
            "cwd": str(self.cwd.resolve()),
            "birth": {"seconds": 1, "microseconds": 2},
        }

    def tearDown(self):
        self.temporary.cleanup()

    def family_state(self, lifecycle="running", session_id="worker-1"):
        return {
            "version": WORKER_MODULE.STATE_VERSION,
            "lifecycle": lifecycle,
            "session_id": session_id,
            "model": "Terra",
            "sandbox": "read-only",
            **self.identity,
        }

    def arguments(self):
        return argparse.Namespace(state=self.state, cwd=self.cwd, grace_seconds=0.01)

    def test_transition_table_and_atomic_replace_fsync_the_state_and_parent(self):
        self.assertEqual(WORKER_MODULE.TRANSITIONS["launching"], {"running", "stopping", "exited"})
        self.assertEqual(WORKER_MODULE.TRANSITIONS["running"], {"stopping", "exited"})
        self.assertEqual(WORKER_MODULE.TRANSITIONS["stopping"], {"stopped", "exited"})
        with mock.patch.object(WORKER_MODULE.os, "fsync", wraps=os.fsync) as fsync, mock.patch.object(WORKER_MODULE.os, "replace", wraps=os.replace) as replace:
            WORKER_MODULE.atomic_write(self.state, self.family_state("launching"))
        self.assertEqual(replace.call_count, 1)
        self.assertGreaterEqual(fsync.call_count, 2)
        state = WORKER_MODULE.read_state(self.state, family_required=True)
        self.assertEqual(WORKER_MODULE.transition(self.state, state, "running")["lifecycle"], "running")
        with self.assertRaises(ValueError):
            WORKER_MODULE.transition(self.state, state, "stopped")

    def test_every_legal_transition_is_persisted_and_every_other_edge_is_rejected(self):
        for source, destinations in WORKER_MODULE.TRANSITIONS.items():
            for destination in destinations:
                with self.subTest(source=source, destination=destination):
                    WORKER_MODULE.atomic_write(self.state, self.family_state(source))
                    state = WORKER_MODULE.read_state(self.state, family_required=True)
                    self.assertEqual(WORKER_MODULE.transition(self.state, state, destination)["lifecycle"], destination)
            illegal = next(candidate for candidate in WORKER_MODULE.TRANSITIONS if candidate not in destinations)
            with self.subTest(source=source, illegal=illegal):
                WORKER_MODULE.atomic_write(self.state, self.family_state(source))
                with self.assertRaises(ValueError):
                    WORKER_MODULE.transition(self.state, WORKER_MODULE.read_state(self.state), illegal)

    def test_missing_corrupt_stale_and_legacy_state_are_rejected_by_stop_and_verify(self):
        for name, contents in (
            ("missing", None),
            ("corrupt", "not json"),
            ("stale", json.dumps({"version": 1})),
            ("legacy", json.dumps({"session_id": "old", "model": "Terra", "sandbox": "read-only", "cwd": str(self.cwd)})),
        ):
            with self.subTest(name=name), mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()), mock.patch.object(WORKER_MODULE.os, "killpg") as killpg:
                if contents is None:
                    self.state.unlink(missing_ok=True)
                else:
                    self.state.write_text(contents, encoding="utf-8")
                self.assertNotEqual(WORKER_MODULE.stop(self.arguments()), 0)
                self.assertNotEqual(WORKER_MODULE.verify(self.arguments()), 0)
                killpg.assert_not_called()

    def test_unsupported_platform_returns_the_exact_code_without_signaling(self):
        with mock.patch.object(WORKER_MODULE, "_libproc", return_value=None), mock.patch.object(WORKER_MODULE.os, "killpg") as killpg:
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 1)
            self.assertEqual(WORKER_MODULE.verify(self.arguments()), 1)
            killpg.assert_not_called()

    def test_already_exited_leader_with_empty_group_stops_without_a_signal(self):
        WORKER_MODULE.atomic_write(self.state, self.family_state())
        with mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()), mock.patch.object(WORKER_MODULE, "live_identity", return_value=None), mock.patch.object(WORKER_MODULE, "group_members", return_value=[]), mock.patch.object(WORKER_MODULE.os, "killpg") as killpg:
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 0)
            self.assertEqual(WORKER_MODULE.read_state(self.state)["lifecycle"], "stopped")
            killpg.assert_not_called()

    def test_launch_gate_eof_exits_before_exec_with_a_dedicated_session_identity(self):
        marker = self.root / "executed"
        process, release = WORKER_MODULE.gated_process(
            [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"],
            self.cwd,
        )
        try:
            deadline = time.monotonic() + 1
            identity = None
            while time.monotonic() < deadline:
                identity = WORKER_MODULE.live_identity(process.pid)
                if identity and identity["pid"] == identity["pgid"] == identity["sid"]:
                    break
                time.sleep(0.01)
            self.assertIsNotNone(identity)
            self.assertEqual(identity["cwd"], str(self.cwd))
            self.assertFalse(marker.exists())
        finally:
            os.close(release)
        process.communicate(timeout=3)
        self.assertEqual(process.returncode, 125)
        self.assertFalse(marker.exists())

    def test_nonterminal_resume_is_rejected_and_legacy_completed_resume_is_accepted_to_launch(self):
        WORKER_MODULE.atomic_write(self.state, self.family_state("running"))
        with mock.patch.object(WORKER_MODULE, "run_lifecycle") as launch:
            self.assertNotEqual(WORKER_MODULE.resume(argparse.Namespace(state=self.state, codex="codex", prompt="continue")), 0)
            launch.assert_not_called()
        legacy = {"session_id": "old", "model": "Terra", "sandbox": "read-only", "cwd": str(self.cwd)}
        self.state.write_text(json.dumps(legacy), encoding="utf-8")
        with mock.patch.object(WORKER_MODULE, "run_lifecycle", return_value=0) as launch:
            self.assertEqual(WORKER_MODULE.resume(argparse.Namespace(state=self.state, codex="codex", prompt="continue")), 0)
            self.assertEqual(launch.call_args.args[2]["lifecycle"], "launching")

    def test_darwin_probe_contract_and_no_global_cleanup_authority(self):
        self.assertEqual(WORKER_MODULE.BSD_SIZE, 136)
        self.assertEqual(WORKER_MODULE.VNODE_SIZE, 2352)
        self.assertEqual(WORKER_MODULE.PROC_PIDTBSDINFO, 3)
        self.assertEqual(WORKER_MODULE.PROC_PIDVNODEPATHINFO, 9)
        identity = WORKER_MODULE.live_identity(os.getpid())
        self.assertIsNotNone(identity)
        self.assertEqual(identity["cwd"], str(ROOT.resolve()))
        self.assertIn(os.getpid(), WORKER_MODULE.group_members(os.getpgrp()))
        source = CODEX_WORKER.read_text(encoding="utf-8")
        instructions = (ROOT / "skills" / "orchestrate" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("pkill", source)
        self.assertNotIn("proc_listchildpids", source)
        self.assertNotIn("proc_name", source)
        self.assertIn("Successors never discover or clean", instructions)


if __name__ == "__main__":
    unittest.main()
