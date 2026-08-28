from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Optional
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CBM_SCRIPT = ROOT / "skills" / "tools" / "cbm-onboard" / "scripts" / "cbm-onboard.sh"
CBM_REINDEX = ROOT / "skills" / "tools" / "cbm-onboard" / "scripts" / "cbm-reindex.sh"
CBM_TEARDOWN = ROOT / "skills" / "tools" / "cbm-onboard" / "scripts" / "cbm-teardown.sh"
CBM_LIFECYCLE = ROOT / "skills" / "tools" / "cbm-onboard" / "scripts" / "cbm-lifecycle.py"
SPIN_SCRIPT = ROOT / "skills" / "tools" / "spin-worktree" / "scripts" / "spin-worktree.py"
CODEX_WORKER = ROOT / "skills" / "drivers" / "orchestrate" / "scripts" / "codex-worker.py"
CLAUDE_WORKER = ROOT / "skills" / "drivers" / "orchestrate" / "scripts" / "claude-worker.py"
WORKER_LIFECYCLE = ROOT / "skills" / "drivers" / "orchestrate" / "scripts" / "worker_lifecycle.py"
UI_CRAFT_AUDIT = ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "audit.md"
UI_CRAFT_CRITIQUE = ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "critique.md"
UI_CRAFT_SWEEP = ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "behavior-sweep.md"
UI_CRAFT_ROUTE = ROOT / "skills" / "drivers" / "ui-craft" / "scripts" / "route.mjs"
README = ROOT / "README.md"
BEGIN_IGNORE = "# >>> cbm-onboard managed baseline — do not edit inside this block >>>"
BEGIN_HOOK = "# >>> cbm-onboard managed reindex >>>"
LIFECYCLE_SPEC = importlib.util.spec_from_file_location("worker_lifecycle", WORKER_LIFECYCLE)
assert LIFECYCLE_SPEC and LIFECYCLE_SPEC.loader
LIFECYCLE_MODULE = importlib.util.module_from_spec(LIFECYCLE_SPEC)
sys.modules["worker_lifecycle"] = LIFECYCLE_MODULE
LIFECYCLE_SPEC.loader.exec_module(LIFECYCLE_MODULE)

WORKER_SPEC = importlib.util.spec_from_file_location("orchestrate_worker", CODEX_WORKER)
assert WORKER_SPEC and WORKER_SPEC.loader
WORKER_MODULE = importlib.util.module_from_spec(WORKER_SPEC)
WORKER_SPEC.loader.exec_module(WORKER_MODULE)

CLAUDE_WORKER_SPEC = importlib.util.spec_from_file_location("orchestrate_claude_worker", CLAUDE_WORKER)
assert CLAUDE_WORKER_SPEC and CLAUDE_WORKER_SPEC.loader
CLAUDE_WORKER_MODULE = importlib.util.module_from_spec(CLAUDE_WORKER_SPEC)
CLAUDE_WORKER_SPEC.loader.exec_module(CLAUDE_WORKER_MODULE)


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


class CbmEnsureTests(unittest.TestCase):
    """The machine interface a workflow uses to bind one checkout to one project."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.scratch = Path(self.temporary.name)
        self.repo = self.scratch / "repo"
        self.repo.mkdir()
        self.assertEqual(run(["git", "init", "-b", "main"], cwd=self.repo).returncode, 0)
        (self.repo / "module.py").write_text("def hello():\n    return 1\n", encoding="utf-8")
        self.requests = self.scratch / "requests.jsonl"
        self.indexed = self.scratch / "indexed"
        self.binary = self.scratch / "codebase-memory-mcp"
        self.binary.write_text(
            """#!/usr/bin/env python3
import json
import os
import sys

if sys.argv[1:] == ["--version"]:
    print(os.environ.get("CBM_FAKE_VERSION", "codebase-memory-mcp 0.10.8"))
    raise SystemExit(0)

with open(os.environ["CBM_FAKE_REQUESTS"], "a", encoding="utf-8") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\\n")

indexed = os.environ["CBM_FAKE_INDEXED"]
if os.environ.get("CBM_FAKE_EMPTY_FAIL") == "1":
    raise SystemExit(1)
if os.environ.get("CBM_FAKE_MALFORMED") == "1":
    print("not json")
    raise SystemExit(0)

if "index_repository" in sys.argv:
    if os.environ.get("CBM_FAKE_RECHECK_MISSING") != "1":
        open(indexed, "w", encoding="utf-8").close()
    print(json.dumps({
        "structuredContent": {
            "project": sys.argv[sys.argv.index("--name") + 1],
            "status": "indexed",
        },
        "isError": False,
    }))
    raise SystemExit(0)

if "index_status" in sys.argv:
    project = sys.argv[sys.argv.index("--project") + 1]
    if not os.path.exists(indexed):
        print(json.dumps({
            "structuredContent": {"error": "project not found or not indexed"},
            "isError": True,
        }))
        raise SystemExit(1)
    print(json.dumps({
        "structuredContent": {
            "project": os.environ.get("CBM_FAKE_PROJECT", project),
            "status": os.environ.get("CBM_FAKE_STATUS", "ready"),
            "root_path": os.environ.get("CBM_FAKE_ROOT", os.environ["CBM_FAKE_REAL_ROOT"]),
        },
        "isError": False,
    }))
    raise SystemExit(0)

raise SystemExit(9)
""",
            encoding="utf-8",
        )
        self.binary.chmod(0o755)
        self.environment = os.environ.copy()
        self.environment["CODEBASE_MEMORY_BIN"] = str(self.binary)
        self.environment["CBM_FAKE_REQUESTS"] = str(self.requests)
        self.environment["CBM_FAKE_INDEXED"] = str(self.indexed)
        self.environment["CBM_FAKE_REAL_ROOT"] = str(self.repo.resolve())
        self.environment["GIT_CONFIG_GLOBAL"] = os.devnull
        self.environment["GIT_CONFIG_SYSTEM"] = os.devnull

    def tearDown(self):
        self.temporary.cleanup()

    def ensure(self, target=None):
        return run(
            ["python3", str(CBM_LIFECYCLE), "ensure", str(target or self.repo)],
            cwd=ROOT,
            env=self.environment,
        )

    def project_for(self, checkout: Path) -> str:
        return "cbm-onboard-v1-" + hashlib.sha256(os.fsencode(checkout.resolve())).hexdigest()

    def issued(self) -> list[list[str]]:
        if not self.requests.exists():
            return []
        return [json.loads(line) for line in self.requests.read_text(encoding="utf-8").splitlines()]

    def test_a_missing_project_is_indexed_under_its_own_name_and_rechecked(self):
        result = self.ensure()

        self.assertEqual(result.returncode, 0, result.stderr)
        project = self.project_for(self.repo)
        self.assertEqual(
            json.loads(result.stdout),
            {"root_path": str(self.repo.resolve()), "project": project, "status": "indexed"},
        )
        self.assertEqual(
            self.issued(),
            [
                ["cli", "--json", "index_status", "--project", project],
                [
                    "cli",
                    "--json",
                    "index_repository",
                    "--repo-path",
                    str(self.repo.resolve()),
                    "--mode",
                    "full",
                    "--name",
                    project,
                ],
                ["cli", "--json", "index_status", "--project", project],
            ],
        )

    def test_an_existing_project_is_reported_ready_without_reindexing(self):
        self.indexed.touch()

        result = self.ensure()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "ready")
        self.assertEqual(
            self.issued(),
            [["cli", "--json", "index_status", "--project", self.project_for(self.repo)]],
        )

    def test_the_checkout_its_git_configuration_and_hooks_are_left_alone(self):
        hook = self.repo / ".git" / "hooks" / "post-commit"
        hook.write_bytes(b"#!/bin/sh\nprintf 'sentinel\\n'\n")
        before = {
            "tracked": run(["git", "status", "--porcelain"], cwd=self.repo).stdout,
            "config": (self.repo / ".git" / "config").read_bytes(),
            "hook": hook.read_bytes(),
        }

        self.assertEqual(self.ensure().returncode, 0)

        self.assertFalse((self.repo / ".cbmignore").exists())
        self.assertEqual(run(["git", "status", "--porcelain"], cwd=self.repo).stdout, before["tracked"])
        self.assertEqual((self.repo / ".git" / "config").read_bytes(), before["config"])
        self.assertEqual(hook.read_bytes(), before["hook"])

    def test_identity_is_physical_and_per_checkout_never_chosen_from_an_inventory(self):
        run(["git", "config", "user.name", "Test User"], cwd=self.repo)
        run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo)
        run(["git", "add", "module.py"], cwd=self.repo)
        self.assertEqual(run(["git", "commit", "-m", "fixture"], cwd=self.repo).returncode, 0)
        worktree = self.scratch / "linked"
        self.assertEqual(
            run(["git", "worktree", "add", "-b", "fixture", str(worktree)], cwd=self.repo).returncode,
            0,
        )
        spelling = self.scratch / "spelled"
        spelling.symlink_to(self.repo)
        self.indexed.touch()

        projects = []
        for target, root in ((self.repo, self.repo), (spelling, self.repo), (worktree, worktree)):
            self.environment["CBM_FAKE_REAL_ROOT"] = str(root.resolve())
            result = self.ensure(target)
            self.assertEqual(result.returncode, 0, result.stderr)
            projects.append(json.loads(result.stdout)["project"])

        self.assertEqual(projects[0], projects[1])
        self.assertNotEqual(projects[0], projects[2])
        self.assertEqual(projects[2], self.project_for(worktree))
        self.assertNotIn("list_projects", json.dumps(self.issued()))

    def test_a_missing_or_too_old_binary_is_one_visible_unavailable_outcome(self):
        for label, override in (
            ("missing", {"CODEBASE_MEMORY_BIN": str(self.scratch / "absent")}),
            ("too old", {"CBM_FAKE_VERSION": "codebase-memory-mcp 0.10.7"}),
            ("unparseable", {"CBM_FAKE_VERSION": "some other tool 1.0"}),
        ):
            with self.subTest(label):
                self.environment.update(override)
                result = self.ensure()
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(json.loads(result.stdout), {"status": "unavailable"})
                self.environment["CODEBASE_MEMORY_BIN"] = str(self.binary)
                self.environment.pop("CBM_FAKE_VERSION", None)

    def test_a_nonzero_exit_with_empty_stdout_is_the_unavailable_outcome(self):
        """A binary that can't operate here (e.g. a sandbox blocking its daemon
        endpoint) fails with a nonzero exit and no stdout at all. That is the
        same degraded mode as a missing or too-old binary, not a protocol
        violation: ensure must report unavailable, not fail hard."""

        self.environment["CBM_FAKE_EMPTY_FAIL"] = "1"

        result = self.ensure()

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"status": "unavailable"})
        self.assertEqual(
            self.issued(),
            [["cli", "--json", "index_status", "--project", self.project_for(self.repo)]],
        )

    def test_a_response_for_another_project_root_or_state_stops_the_binding(self):
        self.indexed.touch()
        for label, override in (
            ("another project", {"CBM_FAKE_PROJECT": "cbm-onboard-v1-somebody-else"}),
            ("another root", {"CBM_FAKE_ROOT": str(self.scratch / "elsewhere")}),
            ("not ready", {"CBM_FAKE_STATUS": "indexing"}),
            ("malformed", {"CBM_FAKE_MALFORMED": "1"}),
        ):
            with self.subTest(label):
                self.environment.update(override)
                result = self.ensure()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("index_repository", json.dumps(self.issued()))
                self.assertNotIn("delete_project", json.dumps(self.issued()))
                for key in override:
                    self.environment.pop(key)

    def test_an_index_that_cannot_be_confirmed_at_the_requested_root_fails(self):
        self.environment["CBM_FAKE_RECHECK_MISSING"] = "1"

        result = self.ensure()

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(result.stdout, "")
        self.assertIn("after indexing", result.stderr)
        self.assertEqual([request[2] for request in self.issued()], ["index_status", "index_repository", "index_status"])

    def test_a_path_that_is_not_a_checkout_is_refused_before_any_tool_call(self):
        result = self.ensure(self.scratch / "not-a-repo")

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.issued(), [])


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
        # A developer's own global core.hooksPath would otherwise decide where the
        # script installs, and the run would write outside the fixture.
        self.environment["GIT_CONFIG_GLOBAL"] = os.devnull
        self.environment["GIT_CONFIG_SYSTEM"] = os.devnull

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

    def configure_lifecycle_binary(self):
        self.requests = self.scratch / "requests.jsonl"
        self.binary.write_text(
            """#!/usr/bin/env python3
import json
import os
import sys

if sys.argv[1:] == ["--version"]:
    print(os.environ.get("CBM_FAKE_VERSION", "codebase-memory-mcp 0.10.8"))
    raise SystemExit(0)

with open(os.environ["CBM_FAKE_REQUESTS"], "a", encoding="utf-8") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\\n")

if "index_repository" in sys.argv:
    project = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else "derived-by-cbm"
    status = "indexed"
    is_error = False
    exit_code = 0
elif "delete_project" in sys.argv:
    project = sys.argv[sys.argv.index("--project") + 1]
    state = os.environ["CBM_FAKE_DELETE_STATE"]
    if os.path.exists(state):
        status = "not_found"
        is_error = True
        exit_code = 1
    else:
        open(state, "w", encoding="utf-8").close()
        status = "deleted"
        is_error = False
        exit_code = 0
else:
    raise SystemExit(9)
project = os.environ.get("CBM_FAKE_PROJECT", project)
status = os.environ.get("CBM_FAKE_STATUS", status)
if "CBM_FAKE_IS_ERROR" in os.environ:
    is_error = os.environ["CBM_FAKE_IS_ERROR"] == "true"
exit_code = int(os.environ.get("CBM_FAKE_EXIT", exit_code))
if os.environ.get("CBM_FAKE_MALFORMED") == "1":
    print("not json")
    raise SystemExit(exit_code)
print(json.dumps({
    "structuredContent": {"project": project, "status": status},
    "isError": is_error,
}))
raise SystemExit(exit_code)
""",
            encoding="utf-8",
        )
        self.binary.chmod(0o755)
        self.environment["CBM_FAKE_REQUESTS"] = str(self.requests)
        self.environment["CBM_FAKE_DELETE_STATE"] = str(self.scratch / "deleted")

    def issued(self) -> list[list[str]]:
        if not self.requests.exists():
            return []
        return [
            json.loads(line)
            for line in self.requests.read_text(encoding="utf-8").splitlines()
        ]

    def wait_for_requests(self, count: int) -> list[list[str]]:
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            requests = self.issued()
            if len(requests) >= count:
                return requests
            time.sleep(0.01)
        return self.issued()

    def seed_repository(self):
        run(["git", "config", "user.name", "Test User"], cwd=self.repo)
        run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo)
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        run(["git", "add", "README.md"], cwd=self.repo)
        result = run(["git", "commit", "-m", "fixture"], cwd=self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)

    def add_linked_worktree(self) -> Path:
        worktree = self.scratch / "linked worktree"
        result = run(
            ["git", "worktree", "add", "-b", "fixture-worktree", str(worktree)],
            cwd=self.repo,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return worktree

    def install_reindex_hooks(self, environment=None):
        result = run(
            [str(CBM_SCRIPT), str(self.repo)],
            cwd=ROOT,
            env=(environment or self.environment) | {"CBM_SKIP_INDEX": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def commit_change(self, checkout: Path, message: str, environment=None):
        (checkout / "README.md").write_text("changed\n", encoding="utf-8")
        run(
            ["git", "add", "README.md"],
            cwd=checkout,
            env=environment or self.environment,
        )
        return run(
            ["git", "commit", "-m", message],
            cwd=checkout,
            env=environment or self.environment,
        )

    def test_worktree_commit_reindexes_once_under_its_deterministic_identity(self):
        self.seed_repository()
        worktree = self.add_linked_worktree()
        self.configure_lifecycle_binary()
        self.install_reindex_hooks()

        committed = self.commit_change(worktree, "exercise reindex hook")

        self.assertEqual(committed.returncode, 0, committed.stderr)
        canonical = str(worktree.resolve())
        expected_name = "cbm-onboard-v1-" + hashlib.sha256(os.fsencode(canonical)).hexdigest()
        self.assertEqual(
            self.wait_for_requests(1),
            [[
                "cli",
                "--json",
                "index_repository",
                "--repo-path",
                canonical,
                "--mode",
                "fast",
                "--name",
                expected_name,
            ]],
        )

    def test_maintained_checkout_commit_keeps_derived_name_reindexing(self):
        self.seed_repository()
        self.configure_lifecycle_binary()
        self.install_reindex_hooks()

        committed = self.commit_change(self.repo, "exercise reindex hook")

        self.assertEqual(committed.returncode, 0, committed.stderr)
        requests = self.wait_for_requests(1)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0][:2], ["cli", "index_repository"])
        self.assertEqual(
            json.loads(requests[0][2]),
            {"repo_path": str(self.repo.resolve()), "mode": "fast"},
        )
        self.assertNotIn("--name", requests[0])

    def test_logical_checkout_path_is_still_classified_as_maintained(self):
        self.seed_repository()
        self.configure_lifecycle_binary()
        logical_root = self.scratch / "logical checkout"
        logical_root.symlink_to(self.repo, target_is_directory=True)
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        shim_directory = self.scratch / "bin"
        shim_directory.mkdir()
        git_shim = shim_directory / "git"
        git_shim.write_text(
            f"""#!{sys.executable}
import os
import sys

if "--show-toplevel" in sys.argv:
    print({str(logical_root)!r})
    raise SystemExit(0)
if "--absolute-git-dir" in sys.argv:
    print({str(self.repo.resolve() / '.git')!r})
    raise SystemExit(0)
if "--git-common-dir" in sys.argv:
    print(".git")
    raise SystemExit(0)
os.execv({real_git!r}, [{real_git!r}, *sys.argv[1:]])
""",
            encoding="utf-8",
        )
        git_shim.chmod(0o755)
        environment = self.environment | {
            "PATH": f"{shim_directory}{os.pathsep}{self.environment['PATH']}",
            "PWD": str(logical_root),
        }

        result = run([str(CBM_REINDEX)], cwd=logical_root, env=environment)

        self.assertEqual(result.returncode, 0, result.stderr)
        requests = self.wait_for_requests(1)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0][:2], ["cli", "index_repository"])
        self.assertEqual(
            json.loads(requests[0][2]),
            {"repo_path": str(logical_root), "mode": "fast"},
        )
        self.assertNotIn("--name", requests[0])

    def test_commit_lands_when_reindex_binary_is_missing_and_names_the_reason(self):
        self.seed_repository()
        self.configure_lifecycle_binary()
        self.install_reindex_hooks()
        self.binary.unlink()

        committed = self.commit_change(self.repo, "exercise missing binary")

        self.assertEqual(committed.returncode, 0, committed.stderr)
        self.assertEqual(
            committed.stderr.splitlines(),
            ["Codebase Memory refresh skipped: binary is not executable"],
        )
        self.assertEqual(self.issued(), [])

    def test_reindex_names_a_missing_detached_launcher(self):
        self.seed_repository()
        self.configure_lifecycle_binary()
        shim_directory = self.scratch / "bin"
        shim_directory.mkdir()
        for command in ("dirname", "git", "python3"):
            executable = shutil.which(command)
            self.assertIsNotNone(executable)
            (shim_directory / command).symlink_to(executable)
        environment = self.environment | {"PATH": str(shim_directory)}

        result = run([str(CBM_REINDEX)], cwd=self.repo, env=environment)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stderr.splitlines(),
            ["Codebase Memory refresh skipped: detached launcher is unavailable"],
        )
        self.assertEqual(self.issued(), [])

    def test_reindex_skips_when_checkout_classification_fails(self):
        self.seed_repository()
        self.configure_lifecycle_binary()
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        shim_directory = self.scratch / "bin"
        shim_directory.mkdir()
        git_shim = shim_directory / "git"
        git_shim.write_text(
            f"""#!{sys.executable}
import os
import sys

if "--absolute-git-dir" in sys.argv:
    raise SystemExit(1)
os.execv({real_git!r}, [{real_git!r}, *sys.argv[1:]])
""",
            encoding="utf-8",
        )
        git_shim.chmod(0o755)
        environment = self.environment | {
            "PATH": f"{shim_directory}{os.pathsep}{self.environment['PATH']}"
        }

        result = run(
            [str(CBM_REINDEX)], cwd=self.repo, env=environment
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stderr.splitlines(),
            ["Codebase Memory refresh skipped: checkout classification failed"],
        )
        self.assertEqual(self.issued(), [])

    def test_worktree_commit_skips_an_unsupported_binary_without_falling_back(self):
        self.seed_repository()
        worktree = self.add_linked_worktree()
        self.configure_lifecycle_binary()
        environment = self.environment | {"CBM_FAKE_VERSION": "codebase-memory-mcp 0.10.7"}
        self.install_reindex_hooks(environment)

        committed = self.commit_change(
            worktree, "exercise unsupported binary", environment
        )

        self.assertEqual(committed.returncode, 0, committed.stderr)
        self.assertEqual(
            committed.stderr.splitlines(),
            ["Codebase Memory refresh skipped: binary version is unsupported"],
        )
        self.assertEqual(self.issued(), [])

    def test_worktree_commit_skips_when_identity_cannot_be_derived(self):
        self.seed_repository()
        worktree = self.add_linked_worktree()
        self.configure_lifecycle_binary()
        self.install_reindex_hooks()
        shim_directory = self.scratch / "bin"
        shim_directory.mkdir()
        python_shim = shim_directory / "python3"
        python_shim.write_text(
            f"""#!{sys.executable}
import os
import sys

if len(sys.argv) > 2 and sys.argv[1].endswith("cbm-lifecycle.py") and sys.argv[2] == "identity":
    raise SystemExit(1)
os.execv({sys.executable!r}, [{sys.executable!r}, *sys.argv[1:]])
""",
            encoding="utf-8",
        )
        python_shim.chmod(0o755)
        environment = self.environment | {
            "PATH": f"{shim_directory}{os.pathsep}{self.environment['PATH']}"
        }

        committed = self.commit_change(
            worktree, "exercise missing identity helper", environment
        )

        self.assertEqual(committed.returncode, 0, committed.stderr)
        self.assertEqual(
            committed.stderr.splitlines(),
            ["Codebase Memory refresh skipped: worktree identity could not be derived"],
        )
        self.assertEqual(self.issued(), [])

    def test_hookless_onboarding_indexes_exact_worktree_without_touching_hooks(self):
        run(["git", "config", "user.name", "Test User"], cwd=self.repo)
        run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo)
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        run(["git", "add", "README.md"], cwd=self.repo)
        self.assertEqual(run(["git", "commit", "-m", "fixture"], cwd=self.repo).returncode, 0)
        worktree = self.scratch / "linked worktree"
        self.assertEqual(
            run(["git", "worktree", "add", "-b", "fixture-worktree", str(worktree)], cwd=self.repo).returncode,
            0,
        )
        run(["git", "config", "core.hooksPath", ".custom-hooks"], cwd=self.repo)
        configured_hooks = self.repo / ".custom-hooks"
        configured_hooks.mkdir()
        hooks = (
            self.repo / ".git" / "hooks" / "post-commit",
            configured_hooks / "post-commit",
        )
        for hook in hooks:
            hook.write_bytes(b"#!/bin/sh\nprintf 'sentinel\\n'\n")
        before = {hook: hook.read_bytes() for hook in hooks}
        self.configure_lifecycle_binary()

        result = run(
            [str(CBM_SCRIPT), "--no-hooks", "--this-checkout", str(worktree)],
            cwd=ROOT,
            env=self.environment,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((worktree / ".cbmignore").exists())
        self.assertFalse((self.repo / ".cbmignore").exists())
        self.assertEqual({hook: hook.read_bytes() for hook in hooks}, before)
        request = json.loads(self.requests.read_text(encoding="utf-8"))
        canonical = str(worktree.resolve())
        expected_name = "cbm-onboard-v1-" + hashlib.sha256(canonical.encode()).hexdigest()
        self.assertEqual(
            request,
            ["cli", "--json", "index_repository", "--repo-path", canonical, "--mode", "full", "--name", expected_name],
        )

    def test_teardown_is_exact_idempotent_and_does_not_mutate_repository(self):
        self.configure_lifecycle_binary()
        hook = self.repo / ".git" / "hooks" / "post-commit"
        hook.write_bytes(b"#!/bin/sh\nprintf 'sentinel\\n'\n")
        onboard = run(
            [str(CBM_SCRIPT), "--no-hooks", "--this-checkout", str(self.repo)],
            cwd=ROOT,
            env=self.environment,
        )
        self.assertEqual(onboard.returncode, 0, onboard.stderr)
        before = {
            "ignore": (self.repo / ".cbmignore").read_bytes(),
            "hook": hook.read_bytes(),
        }
        before_files = {
            path.relative_to(self.repo): (path.stat().st_mode, path.read_bytes())
            for path in self.repo.rglob("*")
            if path.is_file() and not path.is_symlink()
        }

        first = run([str(CBM_TEARDOWN), str(self.repo)], cwd=ROOT, env=self.environment)
        second = run([str(CBM_TEARDOWN), str(self.repo)], cwd=ROOT, env=self.environment)

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("deleted", first.stdout)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("not found", second.stdout)
        self.assertEqual((self.repo / ".cbmignore").read_bytes(), before["ignore"])
        self.assertEqual(hook.read_bytes(), before["hook"])
        after_files = {
            path.relative_to(self.repo): (path.stat().st_mode, path.read_bytes())
            for path in self.repo.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        self.assertEqual(after_files, before_files)
        canonical = str(self.repo.resolve())
        project = "cbm-onboard-v1-" + hashlib.sha256(canonical.encode()).hexdigest()
        requests = [json.loads(line) for line in self.requests.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(
            requests[1:],
            [
                ["cli", "--json", "delete_project", "--project", project],
                ["cli", "--json", "delete_project", "--project", project],
            ],
        )
        self.assertTrue(all("list_projects" not in request for request in requests))

    def test_default_onboarding_keeps_skip_hooks_and_derived_name_request(self):
        self.configure_lifecycle_binary()
        skipped_environment = self.environment | {"CBM_SKIP_INDEX": "1"}

        skipped = run([str(CBM_SCRIPT), str(self.repo)], cwd=ROOT, env=skipped_environment)

        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        self.assertIn(BEGIN_HOOK, (self.repo / ".git" / "hooks" / "post-commit").read_text())
        self.assertFalse(self.requests.exists())

        indexed = run([str(CBM_SCRIPT), str(self.repo)], cwd=ROOT, env=self.environment)

        self.assertEqual(indexed.returncode, 0, indexed.stderr)
        request = json.loads(self.requests.read_text(encoding="utf-8"))
        self.assertEqual(request[:2], ["cli", "index_repository"])
        self.assertEqual(json.loads(request[2]), {"repo_path": str(self.repo.resolve()), "mode": "full"})
        self.assertNotIn("--name", request)

    def test_tilde_hooks_path_installs_under_home_not_inside_the_checkout(self):
        self.configure_lifecycle_binary()
        home = self.scratch / "home"
        (home / "hooks").mkdir(parents=True)
        run(["git", "config", "core.hooksPath", "~/hooks"], cwd=self.repo)

        result = run(
            [str(CBM_SCRIPT), str(self.repo)],
            cwd=ROOT,
            env=self.environment | {"HOME": str(home), "CBM_SKIP_INDEX": "1"},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(BEGIN_HOOK, (home / "hooks" / "post-commit").read_text())
        self.assertFalse((self.repo / "~").exists())

    def test_hookless_onboarding_enforces_stable_numeric_version_grammar(self):
        self.configure_lifecycle_binary()
        cases = (
            ("codebase-memory-mcp 0.10.7", False),
            ("codebase-memory-mcp 0.10.8", True),
            ("codebase-memory-mcp 0.10.10", True),
            ("codebase-memory-mcp 0.11.0", True),
            ("codebase-memory-mcp 1.0.0", True),
            ("codebase-memory-mcp 0.010.8", False),
            ("codebase-memory-mcp 0.10", False),
            ("codebase-memory-mcp 0.10.8-beta.1", False),
            ("prefix codebase-memory-mcp 0.10.8", False),
            ("codebase-memory-mcp 0.10.8 suffix", False),
        )

        for banner, supported in cases:
            with self.subTest(banner=banner):
                ignore = self.repo / ".cbmignore"
                if ignore.exists():
                    ignore.unlink()
                if self.requests.exists():
                    self.requests.unlink()
                environment = self.environment | {"CBM_FAKE_VERSION": banner}

                result = run(
                    [str(CBM_SCRIPT), "--no-hooks", "--this-checkout", str(self.repo)],
                    cwd=ROOT,
                    env=environment,
                )

                self.assertEqual(result.returncode == 0, supported, result.stderr)
                self.assertEqual(ignore.exists(), supported)
                self.assertEqual(self.requests.exists(), supported)

    def test_lifecycle_responses_fail_closed(self):
        self.configure_lifecycle_binary()
        index_cases = (
            {"CBM_FAKE_PROJECT": "wrong-project"},
            {"CBM_FAKE_STATUS": "deleted"},
            {"CBM_FAKE_IS_ERROR": "true"},
            {"CBM_FAKE_EXIT": "1"},
            {"CBM_FAKE_MALFORMED": "1"},
        )
        for update in index_cases:
            with self.subTest(operation="index", update=update):
                if self.requests.exists():
                    self.requests.unlink()
                result = run(
                    [str(CBM_SCRIPT), "--no-hooks", "--this-checkout", str(self.repo)],
                    cwd=ROOT,
                    env=self.environment | update,
                )
                self.assertNotEqual(result.returncode, 0)
                request = json.loads(self.requests.read_text(encoding="utf-8"))
                self.assertIn("index_repository", request)

        delete_cases = (
            {"CBM_FAKE_PROJECT": "wrong-project", "CBM_FAKE_STATUS": "deleted", "CBM_FAKE_IS_ERROR": "false", "CBM_FAKE_EXIT": "0"},
            {"CBM_FAKE_STATUS": "indexed", "CBM_FAKE_IS_ERROR": "false", "CBM_FAKE_EXIT": "0"},
            {"CBM_FAKE_STATUS": "deleted", "CBM_FAKE_IS_ERROR": "true", "CBM_FAKE_EXIT": "0"},
            {"CBM_FAKE_STATUS": "deleted", "CBM_FAKE_IS_ERROR": "false", "CBM_FAKE_EXIT": "1"},
            {"CBM_FAKE_STATUS": "not_found", "CBM_FAKE_IS_ERROR": "true", "CBM_FAKE_EXIT": "0"},
            {"CBM_FAKE_STATUS": "deleted", "CBM_FAKE_IS_ERROR": "false", "CBM_FAKE_EXIT": "2"},
            {"CBM_FAKE_MALFORMED": "1", "CBM_FAKE_EXIT": "0"},
        )
        for update in delete_cases:
            with self.subTest(operation="delete", update=update):
                if self.requests.exists():
                    self.requests.unlink()
                result = run(
                    [str(CBM_TEARDOWN), str(self.repo)],
                    cwd=ROOT,
                    env=self.environment | update,
                )
                self.assertNotEqual(result.returncode, 0)
                request = json.loads(self.requests.read_text(encoding="utf-8"))
                self.assertEqual(request[2], "delete_project")
                self.assertNotIn("list_projects", request)

    def test_identity_is_physical_across_relative_and_symlink_spellings(self):
        self.configure_lifecycle_binary()
        alias = self.scratch / "repo alias"
        alias.symlink_to(self.repo, target_is_directory=True)
        relative = os.path.relpath(self.repo, ROOT)

        onboard = run(
            [str(CBM_SCRIPT), "--no-hooks", "--this-checkout", str(alias)],
            cwd=ROOT,
            env=self.environment,
        )
        teardown = run([str(CBM_TEARDOWN), relative], cwd=ROOT, env=self.environment)

        self.assertEqual(onboard.returncode, 0, onboard.stderr)
        self.assertEqual(teardown.returncode, 0, teardown.stderr)
        requests = [json.loads(line) for line in self.requests.read_text().splitlines()]
        indexed_name = requests[0][requests[0].index("--name") + 1]
        deleted_name = requests[1][requests[1].index("--project") + 1]
        self.assertEqual(indexed_name, deleted_name)
        self.assertEqual(
            indexed_name,
            "cbm-onboard-v1-" + hashlib.sha256(os.fsencode(self.repo.resolve())).hexdigest(),
        )

    def test_newline_checkout_paths_fail_before_mutation_or_graph_request(self):
        self.configure_lifecycle_binary()
        for name in ("embedded\nname", "trailing\n"):
            with self.subTest(name=name):
                checkout = self.scratch / name
                checkout.mkdir()
                self.assertEqual(run(["git", "init", "-b", "main"], cwd=checkout).returncode, 0)
                if self.requests.exists():
                    self.requests.unlink()

                onboard = run(
                    [str(CBM_SCRIPT), "--no-hooks", "--this-checkout", str(checkout)],
                    cwd=ROOT,
                    env=self.environment,
                )
                teardown = run([str(CBM_TEARDOWN), str(checkout)], cwd=ROOT, env=self.environment)

                self.assertNotEqual(onboard.returncode, 0)
                self.assertNotEqual(teardown.returncode, 0)
                self.assertFalse((checkout / ".cbmignore").exists())
                self.assertFalse(self.requests.exists())

    def test_hookless_without_this_checkout_retains_main_checkout_resolution(self):
        run(["git", "config", "user.name", "Test User"], cwd=self.repo)
        run(["git", "config", "user.email", "test@example.invalid"], cwd=self.repo)
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        run(["git", "add", "README.md"], cwd=self.repo)
        self.assertEqual(run(["git", "commit", "-m", "fixture"], cwd=self.repo).returncode, 0)
        worktree = self.scratch / "linked"
        self.assertEqual(
            run(["git", "worktree", "add", "-b", "linked", str(worktree)], cwd=self.repo).returncode,
            0,
        )
        self.configure_lifecycle_binary()

        result = run(
            [str(CBM_SCRIPT), "--no-hooks", str(worktree)],
            cwd=ROOT,
            env=self.environment,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.repo / ".cbmignore").exists())
        self.assertFalse((worktree / ".cbmignore").exists())
        request = json.loads(self.requests.read_text())
        self.assertEqual(request[request.index("--repo-path") + 1], str(self.repo.resolve()))

    def test_rejects_invalid_arguments_and_hookless_skip_before_mutation(self):
        cases = (
            (["--unknown"], {}),
            ([str(self.repo), str(self.scratch)], {}),
            (["--no-hooks", str(self.repo)], {"CBM_SKIP_INDEX": "1"}),
        )

        for arguments, environment_update in cases:
            with self.subTest(arguments=arguments):
                ignore = self.repo / ".cbmignore"
                if ignore.exists():
                    ignore.unlink()
                environment = self.environment | environment_update
                result = run(
                    [str(CBM_SCRIPT), *arguments],
                    cwd=ROOT,
                    env=environment,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(ignore.exists())
                self.assertFalse(
                    (self.repo / ".git" / "hooks" / "post-commit").exists()
                )

        for arguments in (["--unknown"], [str(self.repo), str(self.scratch)]):
            with self.subTest(command="teardown", arguments=arguments):
                result = run(
                    [str(CBM_TEARDOWN), *arguments],
                    cwd=ROOT,
                    env=self.environment,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.repo / ".cbmignore").exists())

    def test_refuses_cbmignore_symlink_without_touching_target(self):
        target = self.scratch / "outside-ignore"
        target.write_text("sentinel\n", encoding="utf-8")
        (self.repo / ".cbmignore").symlink_to(target)

        result = self.onboard()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing symlink target", result.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), "sentinel\n")

    def test_follows_hook_symlink_to_its_target_and_honors_core_hooks_path(self):
        run(
            ["git", "config", "core.hooksPath", ".custom-hooks"],
            cwd=self.repo,
        )
        hooks = self.repo / ".custom-hooks"
        hooks.mkdir()
        target = self.scratch / "outside-hook"
        target.write_text("#!/bin/sh\nprintf 'dispatcher\\n'\n", encoding="utf-8")
        link = hooks / "post-commit"
        link.symlink_to(target)

        result = self.onboard()

        self.assertEqual(result.returncode, 0, result.stderr)
        physical_link = Path(os.path.realpath(link.parent)) / link.name
        self.assertIn(
            f"following symlink {physical_link} to {Path(os.path.realpath(target))}",
            result.stdout,
        )
        contents = target.read_text(encoding="utf-8")
        self.assertIn("printf 'dispatcher\\n'", contents)
        self.assertIn(BEGIN_HOOK, contents)
        self.assertTrue(link.is_symlink())
        self.assertFalse((self.repo / ".git" / "hooks" / "post-commit").exists())

        again = self.onboard()

        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), contents)

    def test_refuses_hook_symlink_with_no_regular_file_target(self):
        run(
            ["git", "config", "core.hooksPath", ".custom-hooks"],
            cwd=self.repo,
        )
        hooks = self.repo / ".custom-hooks"
        hooks.mkdir()
        (hooks / "post-commit").symlink_to(self.scratch / "does-not-exist")

        result = self.onboard()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing symlink without a regular-file target", result.stderr)
        self.assertFalse((self.scratch / "does-not-exist").exists())

    def test_reonboarding_replaces_only_the_legacy_hook_block(self):
        legacy_marker = (
            "# codebase-memory-mcp: reindex on commit "
            "(managed by cbm-onboard — cbm-reindex)"
        )
        legacy_script = self.scratch / "legacy install" / "cbm-reindex.sh"
        unrelated_script = self.scratch / "other" / "cbm-reindex.sh"
        cases = (
            (f'"{legacy_script}"', (f'exec "{unrelated_script}"',)),
            (
                f'"{legacy_script}" --extra',
                (f'"{legacy_script}" --extra', f'exec "{unrelated_script}"'),
            ),
        )

        for invocation, preserved in cases:
            with self.subTest(invocation=invocation):
                hook = self.repo / ".git" / "hooks" / "post-commit"
                hook.write_text(
                    "#!/bin/sh\n"
                    "printf 'before\\n'\n"
                    f"{legacy_marker}\n"
                    f"{invocation}\n"
                    "printf 'after\\n'\n"
                    f'exec "{unrelated_script}"\n',
                    encoding="utf-8",
                )
                hook.chmod(0o755)

                result = run(
                    [str(CBM_SCRIPT), str(self.repo)],
                    cwd=ROOT,
                    env=self.environment | {"CBM_SKIP_INDEX": "1"},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                contents = hook.read_text(encoding="utf-8")
                self.assertNotIn(legacy_marker, contents)
                self.assertEqual(contents.count(BEGIN_HOOK), 1)
                self.assertEqual(contents.count(f'"{CBM_REINDEX}"'), 1)
                self.assertIn("printf 'before\\n'", contents)
                self.assertIn("printf 'after\\n'", contents)
                for line in preserved:
                    self.assertIn(line, contents)

    def test_repaired_legacy_hook_reindexes_the_next_commit(self):
        self.seed_repository()
        legacy_script = self.scratch / "legacy install" / "cbm-reindex.sh"
        hook = self.repo / ".git" / "hooks" / "post-commit"
        hook.write_text(
            "#!/bin/sh\n"
            "# codebase-memory-mcp: reindex on commit "
            "(managed by cbm-onboard — cbm-reindex)\n"
            f'"{legacy_script}"\n',
            encoding="utf-8",
        )
        hook.chmod(0o755)
        self.configure_lifecycle_binary()
        self.install_reindex_hooks()

        committed = self.commit_change(self.repo, "exercise repaired hook")

        self.assertEqual(committed.returncode, 0, committed.stderr)
        request = self.wait_for_requests(1)
        self.assertEqual(len(request), 1)
        self.assertEqual(
            json.loads(request[0][2]),
            {"repo_path": str(self.repo.resolve()), "mode": "fast"},
        )

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


class UiCraftContractTests(unittest.TestCase):
    def test_shipped_surface_routing_contract_is_closed(self):
        audit = UI_CRAFT_AUDIT.read_text(encoding="utf-8")
        critique = UI_CRAFT_CRITIQUE.read_text(encoding="utf-8")
        sweep = UI_CRAFT_SWEEP.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")

        cases = (
            (("greenfield", "unavailable", "absent", "unknown"), 0, "lock"),
            (("shipped", "runnable", "complete", "synthetic"), 0, "revise"),
            (("shipped", "runnable", "complete", "manufactured"), 0, "revise"),
            (("shipped", "runnable", "absent", "unknown"), 0, "lock-fallback"),
            (("shipped", "runnable", "incomplete", "unknown"), 2, "refuse"),
            (("shipped", "runnable", "ambiguous", "unknown"), 2, "refuse"),
            (("shipped", "runnable", "complete", "real"), 2, "refuse"),
            (("shipped", "unavailable", "complete", "synthetic"), 2, "refuse"),
        )
        for arguments, exit_code, mode in cases:
            with self.subTest(arguments=arguments):
                result = run(
                    [
                        "node",
                        str(UI_CRAFT_ROUTE),
                        "--embodiment",
                        arguments[0],
                        "--runnability",
                        arguments[1],
                        "--declaration",
                        arguments[2],
                        "--data-source",
                        arguments[3],
                    ],
                    cwd=ROOT,
                )
                self.assertEqual(result.returncode, exit_code, result.stderr)
                self.assertEqual(json.loads(result.stdout)["mode"], mode)

        self.assertIn("`revise` for shipped-surface changes", audit)
        self.assertIn("Route every shipped-surface change through `revise`", critique)
        self.assertRegex(sweep, r"Under `revise`, the\s+ledger amendment")
        self.assertIn("--skill spin-worktree", readme)

    def test_web_implementation_is_disclosed_without_becoming_a_standalone_skill(self):
        skill = (ROOT / "skills" / "drivers" / "ui-craft" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        build = (ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "build.md").read_text(
            encoding="utf-8"
        )
        revise = (
            ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "revise.md"
        ).read_text(encoding="utf-8")
        web = (
            ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "web-implementation.md"
        ).read_text(encoding="utf-8")
        web_contract = " ".join(web.split())

        pointer = "[reference/web-implementation.md](reference/web-implementation.md)"
        self.assertIn(pointer, skill)
        self.assertIn("web-implementation.md", build)
        self.assertIn("web-implementation.md", revise)
        self.assertLess(
            web.index("## Establish the baseline"),
            web.index("## Preserve behavior and choose CSS deliberately"),
        )
        for question in (
            "ECMAScript standardization",
            "Runtime or host support",
            "Transform or polyfill support",
        ):
            self.assertIn(question, web)
        for requirement in (
            "browser and support policy",
            "TypeScript target and libraries",
            "async sequencing, concurrency, and cancellation",
            "mutation and change-by-copy",
            "nullish and other property states",
            "Grid for two-dimensional layout",
            "Flexbox for one-dimensional layout",
            "container queries",
            "logical properties",
            "reduced motion",
            "@supports",
            "fallback or acceptable degradation",
            "lock manifest",
            "behavior ledger",
            "rendered evidence",
        ):
            self.assertIn(requirement, web_contract)
        for forbidden in ("browser or Node matrices", "edition snapshots", "proposal tables"):
            self.assertIn(forbidden, web)
        self.assertNotRegex(web, r"(?m)^\s*\|")
        self.assertNotRegex(web, r"\b(?:Chrome|Firefox|Safari|Edge|Node)\s+(?:v)?\d+\b")
        self.assertIn(
            "https://github.com/ccheney/robust-skills/tree/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/modern-javascript",
            web,
        )
        self.assertIn(
            "https://github.com/ccheney/robust-skills/tree/0ace9a7f5c20d19cad678b894a717945da2ea8ed/skills/modern-css",
            web,
        )
        for name in ("modern-css", "modern-javascript"):
            self.assertFalse((ROOT / "skills" / "tools" / name).exists())


class CodebaseDesignHexagonalContractTests(unittest.TestCase):
    def test_hexagonal_direction_preserves_seam_discipline(self):
        skill = (ROOT / "skills" / "tools" / "codebase-design" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        deepening = (
            ROOT / "skills" / "tools" / "codebase-design" / "references" / "DEEPENING.md"
        ).read_text(encoding="utf-8")
        core = skill.split("**Core**", 1)[1].split("**Leverage**", 1)[0]
        principles = skill.split("## Principles", 1)[1].split(
            "## Designing for testability", 1
        )[0]
        skill_direction = principles.split("**Hexagonal direction.**", 1)[1]
        seam_discipline = deepening.split("## Seam discipline", 1)[1].split(
            "## Testing strategy", 1
        )[0]
        deepening_direction = seam_discipline.split("**Hexagonal direction.**", 1)[1]

        core_terms = core.lower()
        for requirement in ("offers", "interface", "requires", "core side"):
            self.assertIn(requirement, core_terms)

        self.assertLess(
            principles.index("**One adapter means a hypothetical seam."),
            principles.index("**Hexagonal direction.**"),
        )
        self.assertLess(
            seam_discipline.index("**One adapter means a hypothetical seam."),
            seam_discipline.index("**Internal seams vs external seams.**"),
        )
        self.assertLess(
            seam_discipline.index("**Internal seams vs external seams.**"),
            seam_discipline.index("**Hexagonal direction.**"),
        )

        for direction in (skill_direction, deepening_direction):
            normalized = " ".join(direction.lower().split())
            for requirement in (
                "adapters depend toward the core",
                "core code must not import",
                "translate",
                "business rules",
                "composition selects adapters",
                "one-adapter case local",
                "handler directly",
            ):
                self.assertIn(requirement, normalized)
            self.assertLess(
                normalized.index("adapters depend toward the core"),
                normalized.index("composition selects adapters"),
            )

        self.assertIn("The deletion test.", principles)
        self.assertIn("Locality", skill)
        self.assertIn("core side of the seam", deepening_direction)

        design_contract = "\n".join((skill, deepening)).lower()
        for forbidden in ("cqrs", "event sourcing", "aggregate limit", "outbox"):
            self.assertNotIn(forbidden, design_contract)


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

    def spin(self, *arguments: str, env: Optional[dict[str, str]] = None):
        return self.spin_from(self.repo, *arguments, env=env)

    def spin_from(
        self, repo: Path, *arguments: str, env: Optional[dict[str, str]] = None
    ):
        return run(
            [
                sys.executable,
                str(SPIN_SCRIPT),
                "--repo",
                str(repo),
                "--worktree-root",
                str(self.scratch / "worktrees"),
                *arguments,
            ],
            cwd=ROOT,
            env=env,
        )

    def config_environment(
        self, contents: Optional[str | bytes] = None
    ) -> dict[str, str]:
        home = self.scratch / "home"
        if contents is not None:
            config = home / ".config" / "spin-worktree" / "config.json"
            config.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(contents, bytes):
                config.write_bytes(contents)
            else:
                config.write_text(contents, encoding="utf-8")
        return {**os.environ, "HOME": str(home)}

    def configure_origin(self):
        remote = self.scratch / "origin.git"
        result = run(
            ["git", "init", "--bare", "-b", "main", str(remote)],
            cwd=self.scratch,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo)
        result = run(["git", "push", "-u", "origin", "main"], cwd=self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)

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

    def test_dirty_control_checkout_does_not_block_fresh_issue_work(self):
        self.configure_origin()
        untracked = self.repo / "unfinished-notes.md"
        untracked.write_text("keep me\n", encoding="utf-8")

        result = self.spin(
            "--issue",
            "13",
            "--slug",
            "isf-safety-predicate",
            "--name",
            "13",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        worktree = self.scratch / "worktrees" / "repo" / "13"
        self.assertTrue((worktree / ".git").exists())
        branch = run(["git", "branch", "--show-current"], cwd=worktree)
        self.assertEqual(branch.stdout.strip(), "13-isf-safety-predicate")
        self.assertEqual(untracked.read_text(encoding="utf-8"), "keep me\n")
        status = run(["git", "status", "--short"], cwd=self.repo)
        self.assertEqual(status.stdout, "?? unfinished-notes.md\n")

    def test_linked_worktree_input_uses_primary_repository_identity(self):
        run(["git", "branch", "task-52"], cwd=self.repo)
        run(["git", "branch", "local-topic"], cwd=self.repo)
        linked = self.scratch / "linked" / "52"
        linked.parent.mkdir()
        result = run(
            ["git", "worktree", "add", str(linked), "task-52"],
            cwd=self.repo,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        result = self.spin_from(
            linked,
            "--branch",
            "local-topic",
            "--name",
            "13",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.scratch / "worktrees" / "repo" / "13" / ".git").exists())
        self.assertFalse((self.scratch / "worktrees" / "52").exists())

    def test_branch_prefix_flag_wins_over_config(self):
        self.configure_origin()

        result = self.spin(
            "--issue",
            "13",
            "--slug",
            "flag-wins",
            "--branch-prefix",
            "flag",
            env=self.config_environment('{"branchPrefix": "config"}'),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        branch = run(
            ["git", "branch", "--show-current"],
            cwd=self.scratch / "worktrees" / "repo" / "13",
        )
        self.assertEqual(branch.stdout.strip(), "flag/13-flag-wins")

    def test_branch_prefix_uses_config_when_flag_is_absent(self):
        self.configure_origin()

        result = self.spin(
            "--issue",
            "13",
            "--slug",
            "from-config",
            env=self.config_environment('{"branchPrefix": "config"}'),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        branch = run(
            ["git", "branch", "--show-current"],
            cwd=self.scratch / "worktrees" / "repo" / "13",
        )
        self.assertEqual(branch.stdout.strip(), "config/13-from-config")

    def test_branch_prefix_defaults_to_bare_issue_branch(self):
        self.configure_origin()

        result = self.spin("--issue", "13", env=self.config_environment())

        self.assertEqual(result.returncode, 0, result.stderr)
        branch = run(
            ["git", "branch", "--show-current"],
            cwd=self.scratch / "worktrees" / "repo" / "13",
        )
        self.assertEqual(branch.stdout.strip(), "issue-13")

    def test_empty_branch_prefix_flag_requests_bare_slug_branch(self):
        self.configure_origin()

        result = self.spin(
            "--issue",
            "13",
            "--slug",
            "bare-branch",
            "--branch-prefix",
            "",
            env=self.config_environment('{"branchPrefix": "config"}'),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        branch = run(
            ["git", "branch", "--show-current"],
            cwd=self.scratch / "worktrees" / "repo" / "13",
        )
        self.assertEqual(branch.stdout.strip(), "13-bare-branch")

    def test_unusable_branch_prefix_config_resolves_to_no_prefix(self):
        self.configure_origin()
        for contents in (None, "not json", b"\xff", "{}", '{"branchPrefix": 13}'):
            with self.subTest(contents=contents):
                result = self.spin(
                    "--issue",
                    "13",
                    "--slug",
                    "no-prefix",
                    "--dry-run",
                    env=self.config_environment(contents),
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout[result.stdout.index("{") :])
                self.assertEqual(output["branch"], "13-no-prefix")


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
            "if os.environ.get('FAKE_CODEX_WAIT_FOR'):\n"
            "    pathlib.Path(os.environ['FAKE_CODEX_STARTED']).touch()\n"
            "    while not pathlib.Path(os.environ['FAKE_CODEX_WAIT_FOR']).exists(): time.sleep(0.01)\n"
            "if os.environ.get('FAKE_CODEX_HOLD'):\n"
            "    child = subprocess.Popen([sys.executable, '-c', \"import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)\"])\n"
            "    pathlib.Path(os.environ['FAKE_CODEX_CHILD']).write_text(str(child.pid))\n"
            "    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))\n"
            "    while True: time.sleep(1)\n"
            "if os.environ.get('FAKE_CODEX_READ_STDIN') == '1':\n"
            "    sys.stdin.read()\n"
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
        if sys.platform == "darwin":
            self.assertEqual(state["pid"], state["pgid"])
            self.assertEqual(state["pid"], state["sid"])
            self.assertIn("seconds", state["birth"])
            self.assertIn("microseconds", state["birth"])
            self.assertNotIn("family_semantics", state)
        else:
            self.assertEqual(state["family_semantics"], "unsupported")
            self.assertEqual(state["generation"], 1)
            self.assertFalse({"pid", "pgid", "sid", "birth"} & set(state))
        arguments = json.loads(self.arguments.read_text(encoding="utf-8"))
        self.assertIn("--sandbox", arguments)
        self.assertIn(str(self.worktree.resolve()), arguments)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["final_message"], "worker answer")
        self.assertEqual(payload["headroom_status"], "unknown")

    def test_resume_in_a_non_checkout_reapplies_persisted_model_and_sandbox(self):
        self.assertFalse((self.worktree / ".git").exists())
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
                "-c",
                "model_reasoning_effort=medium",
                "--skip-git-repo-check",
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

    @unittest.skipUnless(sys.platform == "darwin", "requires Darwin process-family probes")
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

    @unittest.skipUnless(sys.platform == "darwin", "requires Darwin process-family probes")
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

    @unittest.skipUnless(sys.platform == "darwin", "requires Darwin process-family probes")
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

    @unittest.skipUnless(sys.platform == "darwin", "requires Darwin process-family probes")
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

    @unittest.skipIf(sys.platform == "darwin", "requires unsupported process-family semantics")
    def test_portable_concurrent_resume_refuses_the_stale_contender(self):
        started = self.start('{"type":"thread.started","thread_id":"worker-1"}\n')
        self.assertEqual(started.returncode, 0, started.stderr)
        first_started = self.scratch / "first-resume-started"
        release = self.scratch / "release-first-resume"
        environment = self.environment.copy()
        environment.update(
            {
                "FAKE_CODEX_WAIT_FOR": str(release),
                "FAKE_CODEX_STARTED": str(first_started),
                "FAKE_CODEX_OUTPUT": (
                    '{"type":"thread.started","thread_id":"worker-1"}\n'
                    '{"type":"item.completed","item":{"type":"agent_message","text":"resumed"}}\n'
                ),
            }
        )
        command = [
            "python3", str(CODEX_WORKER), "resume", "--codex", str(self.binary),
            "--state", str(self.state), "continue",
        ]
        first = subprocess.Popen(
            command, cwd=ROOT, env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        deadline = time.monotonic() + 3
        while not first_started.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(first_started.exists(), "portable resume did not start")
        second = subprocess.Popen(
            command, cwd=ROOT, env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        time.sleep(0.1)
        release.touch()
        first_output, first_error = first.communicate(timeout=5)
        second_output, second_error = second.communicate(timeout=5)

        self.assertEqual(first.returncode, 0, first_error)
        self.assertEqual(json.loads(first_output)["final_message"], "resumed")
        self.assertNotEqual(second.returncode, 0, second_output)
        self.assertIn("unchanged terminal worker state", second_error)
        self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["generation"], 2)

    @unittest.skipUnless(sys.platform == "darwin", "requires Darwin process-family probes")
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


    def test_a_worker_launched_with_an_open_stdin_does_not_hang_before_session_start(self):
        self.environment["FAKE_CODEX_READ_STDIN"] = "1"
        self.environment["FAKE_CODEX_OUTPUT"] = (
            '{"type":"thread.started","thread_id":"worker-1"}\n'
            + json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "worker answer"},
                }
            )
            + "\n"
        )
        held, other = socket.socketpair()
        process = None
        try:
            process = subprocess.Popen(
                [
                    "python3", str(CODEX_WORKER), "start",
                    "--codex", str(self.binary),
                    "--state", str(self.state),
                    "--model", "Terra",
                    "--sandbox", "read-only",
                    "--cwd", str(self.worktree),
                    "do the work",
                ],
                cwd=ROOT,
                env=self.environment,
                stdin=held.fileno(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                stdout, stderr = process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                self.fail("the worker hung waiting on an inherited open stdin")
            self.assertEqual(process.returncode, 0, stderr)
            self.assertIn("worker answer", stdout)
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.communicate()
            held.close()
            other.close()


class OrchestrateCodexPolicyTests(unittest.TestCase):
    def test_codex_dispatch_policy_rules_are_explicit(self):
        skill = (ROOT / "skills" / "drivers" / "orchestrate" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        dispatch = (
            ROOT / "skills" / "drivers" / "orchestrate" / "references" / "dispatch-codex.md"
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
        self.assertIn("The helper closes a worker's stdin itself.", dispatch)
        self.assertIn("must redirect stdin from /dev/null", dispatch)
        self.assertIn("an inherited open stdin is a permanent pre-session hang", dispatch)
        self.assertIn("## Worker liveness", dispatch)
        self.assertIn("A PID appearing in `ps` proves nothing.", dispatch)
        self.assertIn("`ps -o time` is growing", dispatch)
        self.assertIn("rollout-*.jsonl", dispatch)

    def test_claude_parent_codex_dispatch_reference_is_pinned(self):
        skill = (ROOT / "skills" / "drivers" / "orchestrate" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        dispatch = (
            ROOT / "skills" / "drivers" / "orchestrate" / "references" / "dispatch-codex.md"
        ).read_text(encoding="utf-8")
        from_claude = (
            ROOT
            / "skills"
            / "drivers"
            / "orchestrate"
            / "references"
            / "dispatch-codex-from-claude.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Before\n  dispatching a Codex worker, read\n  `references/dispatch-codex-from-claude.md`.",
            skill,
        )
        self.assertIn(
            "Use this adapter only when the interactive coordinator is a Codex UI parent.",
            dispatch,
        )

        self.assertIn(
            "only when the interactive coordinator is a Claude Code\nparent dispatching a **Codex** worker",
            from_claude,
        )
        self.assertIn("read-only", from_claude)


class ReviewerRoutingCanonicalContractTests(unittest.TestCase):
    def test_orchestrate_pack_wide_reach_boundaries_are_preserved(self):
        skill = (ROOT / "skills" / "drivers" / "orchestrate" / "SKILL.md").read_bytes()

        self.assertIn(b"## Pack-wide reach", skill)
        self.assertEqual(skill.count(b"\n## Maintenance\n"), 1)
        self.assertIn(
            b"A future skill that dispatches a model converts behind its\n"
            b"own issue before the ban binds it.",
            skill,
        )

    def test_routing_table_review_consumer_block_is_load_bearing(self):
        text = " ".join(
            (ROOT / "skills/drivers/orchestrate/references/routing-table.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn(
            "Before applying their own named area row, `code-review` and `plan-review` obtain "
            "routine/load-bearing routing stakes and their initial route directly from "
            "[`review-routing.md`](review-routing.md).",
            text,
        )

    def test_routing_table_routes_keep_the_review_row_and_escalation_rule(self):
        text = " ".join(
            (ROOT / "skills/drivers/orchestrate/references/routing-table.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn(
            "Escalate one step at a time along the row's ladder; at the last rung, stop and "
            "surface both failed attempts to the operator.",
            text,
        )
        self.assertIn(
            "Opus was the only model to catch all 3 planted defects", text
        )

    def test_code_review_dependency_selection_keeps_the_headroom_gate(self):
        text = " ".join(
            (ROOT / "skills/tools/code-review/SKILL.md").read_text(encoding="utf-8").split()
        )
        self.assertIn(
            "Use the four-row reviewer matrix, classify this skill's area as "
            "`Code review`, and apply the matrix's Claude-parent Codex presence/headroom gate "
            "to select the initial reviewer adapter and model.",
            text,
        )

    def test_orchestrate_review_precedence_overrides_generic_area_routing(self):
        text = " ".join(
            (ROOT / "skills/drivers/orchestrate/SKILL.md").read_text(encoding="utf-8").split()
        )
        self.assertIn(
            "Review dispatch is classified before the generic area routing above.", text
        )
        self.assertIn(
            "Do not infer a reviewer from builder tier or borrow a fallback from another "
            "routing-table row.",
            text,
        )

    def test_orchestrate_collect_child_results_binds_every_dispatch(self):
        text = " ".join(
            (ROOT / "skills/drivers/orchestrate/SKILL.md").read_text(encoding="utf-8").split()
        )
        self.assertIn("This contract binds every model dispatch owned by this pack.", text)
        self.assertIn(
            "A coordinator never ends a turn solely because a child is unfinished, and it "
            "does not treat a completion notification as the result.",
            text,
        )

    def test_coordinator_reviewer_selection_requires_independent_verification(self):
        text = " ".join(
            (ROOT / "skills/drivers/ticket/references/coordinator-mode.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn(
            "Two things happen, in order, and neither substitutes for the other:", text
        )
        self.assertIn(
            "Verify the result yourself, as `/orchestrate` requires of every delegated "
            "result: read the diff, run the verification command, check the chunk's Done when "
            "clause.",
            text,
        )

    def test_readme_lists_code_review_and_plan_review_with_orchestrate_integration(self):
        readme = README.read_text(encoding="utf-8")
        code_review_rows = [
            line for line in readme.splitlines() if line.startswith("| [`code-review`")
        ]
        plan_review_rows = [
            line for line in readme.splitlines() if line.startswith("| [`plan-review`")
        ]
        self.assertEqual(len(code_review_rows), 1)
        self.assertEqual(len(plan_review_rows), 1)
        self.assertIn(
            "`orchestrate` is an optional integration used for reviewer routing when installed",
            code_review_rows[0],
        )
        self.assertIn(
            "`orchestrate` is an optional integration used for reviewer routing when installed",
            plan_review_rows[0],
        )


class WorkerEffortDialTests(unittest.TestCase):
    """Sub-order 1/2 149: the effort dial on both adapters and the STATE_VERSION
    choice (effort is optional-with-default, not added to BASE_STATE_FIELDS,
    so STATE_VERSION stays 2 and pre-existing state files remain valid)."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.scratch = Path(self.temporary.name)
        self.control = self.scratch / "control"
        self.worktree = self.scratch / "worktree"
        self.control.mkdir()
        self.worktree.mkdir()
        self.state = self.scratch / "worker-state.json"
        self.arguments = self.scratch / "arguments.json"
        self.stdin_capture = self.scratch / "stdin.txt"
        self.codex_home = self.scratch / "codex-home"
        self.codex_home_marker = self.scratch / "codex-home-marker"

        self.codex_binary = self.scratch / "fake-codex"
        self.codex_binary.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, pathlib, sys\n"
            "pathlib.Path(os.environ['FAKE_ARGUMENTS']).write_text(json.dumps(sys.argv[1:]))\n"
            "if os.environ.get('FAKE_EXPECTED_CODEX_HOME'):\n"
            "    pathlib.Path(os.environ['FAKE_CODEX_HOME_MARKER']).write_text('fixture' if os.environ.get('CODEX_HOME') == os.environ['FAKE_EXPECTED_CODEX_HOME'] else 'wrong')\n"
            "sys.stdout.write(os.environ.get('FAKE_OUTPUT', ''))\n"
            "sys.exit(int(os.environ.get('FAKE_EXIT', '0')))\n",
            encoding="utf-8",
        )
        self.codex_binary.chmod(0o755)

        self.claude_binary = self.scratch / "fake-claude"
        self.claude_binary.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, pathlib, sys\n"
            "pathlib.Path(os.environ['FAKE_ARGUMENTS']).write_text(json.dumps(sys.argv[1:]))\n"
            "pathlib.Path(os.environ['FAKE_STDIN']).write_text(sys.stdin.read())\n"
            "sys.stdout.write(os.environ.get('FAKE_OUTPUT', ''))\n"
            "sys.exit(int(os.environ.get('FAKE_EXIT', '0')))\n",
            encoding="utf-8",
        )
        self.claude_binary.chmod(0o755)

        self.environment = os.environ.copy()
        self.environment["CODEX_HOME"] = str(self.codex_home)
        self.environment["FAKE_ARGUMENTS"] = str(self.arguments)
        self.environment["FAKE_STDIN"] = str(self.stdin_capture)
        self.environment["FAKE_EXPECTED_CODEX_HOME"] = str(self.codex_home)
        self.environment["FAKE_CODEX_HOME_MARKER"] = str(self.codex_home_marker)

    def tearDown(self):
        self.temporary.cleanup()

    def run_codex(self, *arguments: str):
        return run(["python3", str(CODEX_WORKER), *arguments], cwd=ROOT, env=self.environment)

    def run_claude(self, *arguments: str):
        return run(["python3", str(CLAUDE_WORKER), *arguments], cwd=ROOT, env=self.environment)

    # --- codex-worker.py -------------------------------------------------

    def test_codex_worker_subprocess_uses_the_fixture_session_home(self):
        self.environment["FAKE_OUTPUT"] = '{"type":"thread.started","thread_id":"worker-1"}\n{"type":"item.completed","item":{"type":"agent_message","text":"ok"}}\n'
        result = self.run_codex(
            "start", "--codex", str(self.codex_binary), "--state", str(self.state),
            "--model", "Terra", "--sandbox", "read-only", "--cwd", str(self.worktree), "do the work",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.codex_home_marker.read_text(encoding="utf-8"), "fixture")

    def test_codex_start_defaults_to_medium_effort_in_argv(self):
        self.environment["FAKE_OUTPUT"] = '{"type":"thread.started","thread_id":"worker-1"}\n{"type":"item.completed","item":{"type":"agent_message","text":"ok"}}\n'
        result = self.run_codex(
            "start", "--codex", str(self.codex_binary), "--state", str(self.state),
            "--model", "Terra", "--sandbox", "read-only", "--cwd", str(self.worktree), "do the work",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(self.arguments.read_text(encoding="utf-8"))
        self.assertIn("model_reasoning_effort=medium", argv)
        self.assertNotIn("effort", json.loads(self.state.read_text(encoding="utf-8")))

    def test_codex_start_carries_a_custom_effort_and_persists_it(self):
        self.environment["FAKE_OUTPUT"] = '{"type":"thread.started","thread_id":"worker-1"}\n{"type":"item.completed","item":{"type":"agent_message","text":"ok"}}\n'
        result = self.run_codex(
            "start", "--codex", str(self.codex_binary), "--state", str(self.state),
            "--model", "Terra", "--sandbox", "read-only", "--effort", "high",
            "--cwd", str(self.worktree), "do the work",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(self.arguments.read_text(encoding="utf-8"))
        self.assertIn("model_reasoning_effort=high", argv)
        self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["effort"], "high")

    def test_codex_effort_enum_matches_the_live_api_probe(self):
        self.assertEqual(
            WORKER_MODULE.EFFORT_LEVELS,
            {"none", "low", "medium", "high", "xhigh", "max"},
        )

    def test_codex_replays_persisted_effort_on_resume(self):
        legacy = {
            "version": LIFECYCLE_MODULE.STATE_VERSION, "lifecycle": "exited",
            "session_id": "worker-1", "model": "Terra", "sandbox": "read-only",
            "cwd": str(self.worktree.resolve()), "effort": "high",
            "family_semantics": "unsupported", "generation": 1,
        }
        self.state.write_text(json.dumps(legacy), encoding="utf-8")
        self.environment["FAKE_OUTPUT"] = '{"type":"thread.started","thread_id":"worker-1"}\n{"type":"item.completed","item":{"type":"agent_message","text":"ok"}}\n'
        result = self.run_codex("resume", "--codex", str(self.codex_binary), "--state", str(self.state), "continue")
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(self.arguments.read_text(encoding="utf-8"))
        self.assertIn("model_reasoning_effort=high", argv)
        self.assertEqual(json.loads(result.stdout)["effort"], "high")

    # --- claude-worker.py -------------------------------------------------

    def test_claude_start_puts_prompt_on_stdin_not_argv(self):
        self.environment["FAKE_OUTPUT"] = json.dumps({"session_id": "s1", "result": "ok", "is_error": False})
        result = self.run_claude(
            "start", "--claude", str(self.claude_binary), "--state", str(self.state),
            "--model", "sonnet", "--sandbox", "read-only", "--cwd", str(self.worktree), "the actual prompt text",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(self.arguments.read_text(encoding="utf-8"))
        self.assertNotIn("the actual prompt text", argv)
        self.assertEqual(self.stdin_capture.read_text(encoding="utf-8"), "the actual prompt text")

    def test_claude_start_defaults_to_medium_effort_in_argv(self):
        self.environment["FAKE_OUTPUT"] = json.dumps({"session_id": "s1", "result": "ok", "is_error": False})
        result = self.run_claude(
            "start", "--claude", str(self.claude_binary), "--state", str(self.state),
            "--model", "sonnet", "--sandbox", "read-only", "--cwd", str(self.worktree), "do the work",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(self.arguments.read_text(encoding="utf-8"))
        self.assertIn("--effort", argv)
        self.assertEqual(argv[argv.index("--effort") + 1], "medium")
        self.assertNotIn("effort", json.loads(self.state.read_text(encoding="utf-8")))
        self.assertEqual(json.loads(result.stdout)["effort"], "medium")

    def test_claude_start_carries_a_custom_effort_and_persists_it(self):
        self.environment["FAKE_OUTPUT"] = json.dumps({"session_id": "s1", "result": "ok", "is_error": False})
        result = self.run_claude(
            "start", "--claude", str(self.claude_binary), "--state", str(self.state),
            "--model", "sonnet", "--sandbox", "read-only", "--effort", "xhigh",
            "--cwd", str(self.worktree), "do the work",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(self.arguments.read_text(encoding="utf-8"))
        self.assertEqual(argv[argv.index("--effort") + 1], "xhigh")
        self.assertEqual(json.loads(self.state.read_text(encoding="utf-8"))["effort"], "xhigh")
        self.assertEqual(json.loads(result.stdout)["effort"], "xhigh")

    def test_claude_rejects_an_effort_outside_its_own_enum(self):
        # "minimal" is invalid for both adapters, although their enums differ.
        result = self.run_claude(
            "start", "--claude", str(self.claude_binary), "--state", str(self.state),
            "--model", "sonnet", "--sandbox", "read-only", "--effort", "minimal",
            "--cwd", str(self.worktree), "do the work",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--effort", result.stderr)
        self.assertFalse(self.state.exists())

    def test_claude_replays_persisted_effort_on_resume(self):
        legacy = {
            "version": LIFECYCLE_MODULE.STATE_VERSION, "lifecycle": "exited",
            "session_id": "worker-1", "model": "sonnet", "sandbox": "read-only",
            "cwd": str(self.worktree.resolve()), "effort": "high",
            "family_semantics": "unsupported", "generation": 1,
        }
        self.state.write_text(json.dumps(legacy), encoding="utf-8")
        self.environment["FAKE_OUTPUT"] = json.dumps({"session_id": "worker-1", "result": "ok", "is_error": False})
        result = self.run_claude("resume", "--claude", str(self.claude_binary), "--state", str(self.state), "continue")
        self.assertEqual(result.returncode, 0, result.stderr)
        argv = json.loads(self.arguments.read_text(encoding="utf-8"))
        self.assertEqual(argv[argv.index("--effort") + 1], "high")
        self.assertEqual(json.loads(result.stdout)["effort"], "high")

    def test_claude_start_argv_carries_no_cwd_flag_and_settings_matches_sandbox_mode(self):
        # The installed claude CLI has no --cwd flag; the adapter establishes
        # the working directory via os.chdir in the gate wrapper (and cwd= in
        # run_portable), never as an argv token. A fake binary that accepts
        # any argv would let a stray --cwd slip through unnoticed, so assert
        # the flag set explicitly for both sandbox modes.
        for sandbox, expect_deny in (("read-only", True), ("workspace-write", False)):
            with self.subTest(sandbox=sandbox):
                self.arguments.unlink(missing_ok=True)
                self.environment["FAKE_OUTPUT"] = json.dumps({"session_id": "s1", "result": "ok", "is_error": False})
                arguments = [
                    "start", "--claude", str(self.claude_binary), "--state", str(self.state),
                    "--model", "sonnet", "--sandbox", sandbox, "--cwd", str(self.worktree),
                ]
                if sandbox == "workspace-write":
                    arguments += ["--control-checkout", str(self.control)]
                result = self.run_claude(*arguments, "do the work")
                self.assertEqual(result.returncode, 0, result.stderr)
                argv = json.loads(self.arguments.read_text(encoding="utf-8"))
                self.assertNotIn("--cwd", argv)
                self.assertEqual(
                    argv,
                    [
                        "-p", "--model", "sonnet", "--effort", "medium",
                        "--permission-mode", "dontAsk", "--settings", argv[argv.index("--settings") + 1],
                        "--session-id", argv[argv.index("--session-id") + 1],
                        "--output-format", "json",
                    ],
                )
                settings_path = Path(argv[argv.index("--settings") + 1])
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
                if expect_deny:
                    self.assertIn("Write", settings["permissions"]["deny"])
                    self.assertIn("filesystem", settings["sandbox"])
                else:
                    self.assertIn("Write", settings["permissions"]["allow"])
                    self.assertIn(str(self.worktree.resolve()), settings["sandbox"]["filesystem"]["allowWrite"])
                    self.assertNotIn("denyWrite", settings["sandbox"]["filesystem"])
                self.state.unlink(missing_ok=True)

    def test_claude_resume_argv_carries_no_cwd_flag(self):
        for sandbox in ("read-only", "workspace-write"):
            with self.subTest(sandbox=sandbox):
                self.arguments.unlink(missing_ok=True)
                legacy = {
                    "version": LIFECYCLE_MODULE.STATE_VERSION, "lifecycle": "exited",
                    "session_id": "worker-1", "model": "sonnet", "sandbox": sandbox,
                    "cwd": str(self.worktree.resolve()),
                    "family_semantics": "unsupported", "generation": 1,
                }
                if sandbox == "workspace-write":
                    legacy["control_checkout"] = str(self.control.resolve())
                self.state.write_text(json.dumps(legacy), encoding="utf-8")
                self.environment["FAKE_OUTPUT"] = json.dumps({"session_id": "worker-1", "result": "ok", "is_error": False})
                result = self.run_claude("resume", "--claude", str(self.claude_binary), "--state", str(self.state), "continue")
                self.assertEqual(result.returncode, 0, result.stderr)
                argv = json.loads(self.arguments.read_text(encoding="utf-8"))
                self.assertNotIn("--cwd", argv)
                self.assertEqual(argv[0], "-p")
                self.assertEqual(argv[1:4], ["--resume", "worker-1", "--model"])
                self.state.unlink(missing_ok=True)

    def test_claude_workspace_write_rejects_the_control_checkout(self):
        result = self.run_claude(
            "start", "--claude", str(self.claude_binary), "--state", str(self.state),
            "--model", "sonnet", "--sandbox", "workspace-write",
            "--cwd", str(self.control), "--control-checkout", str(self.control),
            "do the work",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("control checkout", result.stderr)
        self.assertFalse(self.state.exists())

    def test_claude_generated_readonly_settings_deny_writes_and_disable_unsandboxed_retry(self):
        settings = CLAUDE_WORKER_MODULE.sandbox_settings("read-only", self.worktree.resolve())
        self.assertEqual(settings["sandbox"]["allowUnsandboxedCommands"], False)
        self.assertIn("/", settings["sandbox"]["filesystem"]["denyWrite"])
        self.assertIn("Write", settings["permissions"]["deny"])
        self.assertIn("Edit", settings["permissions"]["deny"])

    def test_claude_generated_write_settings_confine_writes_to_cwd_and_keep_unsandboxed_retry_disabled(self):
        # A real run of #149 with no `filesystem` block present wrote straight
        # through to $HOME/.cache — see docs/scope/149-probes/run-log.md's
        # `write` case. allowWrite must name the worker's own cwd, alone: a
        # real run also confirmed denyWrite always wins over allowWrite for
        # the same path, so pairing them re-blocks the cwd allowWrite exists
        # to carve out.
        cwd = self.worktree.resolve()
        settings = CLAUDE_WORKER_MODULE.sandbox_settings("workspace-write", cwd)
        self.assertEqual(settings["sandbox"]["allowUnsandboxedCommands"], False)
        self.assertIn(str(cwd), settings["sandbox"]["filesystem"]["allowWrite"])
        self.assertNotIn("denyWrite", settings["sandbox"]["filesystem"])
        self.assertIn("Write", settings["permissions"]["allow"])
        self.assertIn("Edit", settings["permissions"]["allow"])

    def test_missing_effort_defaults_to_medium_without_a_version_bump(self):
        # STATE_VERSION decision: effort lives only in each command's `allowed`
        # schema superset, never in BASE_STATE_FIELDS, so a pre-existing state
        # file with no "effort" key stays valid at STATE_VERSION 2 and reads
        # back as the medium default on both adapters.
        self.assertEqual(LIFECYCLE_MODULE.STATE_VERSION, 2)
        self.assertEqual(LIFECYCLE_MODULE.STATE_VERSION, 2)
        state = {
            "version": 2, "lifecycle": "running", "session_id": "s",
            "model": "Terra", "sandbox": "read-only", "cwd": str(self.worktree.resolve()),
            "pid": 1, "pgid": 1, "sid": 1, "birth": {"seconds": 1, "microseconds": 0},
        }
        self.assertTrue(
            LIFECYCLE_MODULE.valid_family_schema(
                state, effort_levels=WORKER_MODULE.EFFORT_LEVELS
            )
        )
        self.assertEqual(WORKER_MODULE.effort_of(state), "medium")
        state["model"] = "sonnet"
        self.assertTrue(
            LIFECYCLE_MODULE.valid_family_schema(
                state, effort_levels=CLAUDE_WORKER_MODULE.EFFORT_LEVELS
            )
        )
        self.assertEqual(CLAUDE_WORKER_MODULE.effort_of(state), "medium")

    def test_claude_max_effort_runs_start_resume_stop_and_verify_through_shared_lifecycle(self):
        self.environment["FAKE_OUTPUT"] = json.dumps(
            {"session_id": "worker-1", "result": "started", "is_error": False}
        )
        started = self.run_claude(
            "start", "--claude", str(self.claude_binary), "--state", str(self.state),
            "--model", "sonnet", "--sandbox", "read-only", "--effort", "max",
            "--cwd", str(self.worktree), "do the work",
        )
        self.assertEqual(started.returncode, 0, started.stderr)
        self.assertEqual(json.loads(started.stdout)["final_message"], "started")

        self.environment["FAKE_OUTPUT"] = json.dumps(
            {"session_id": "worker-1", "result": "resumed", "is_error": False}
        )
        resumed = self.run_claude(
            "resume", "--claude", str(self.claude_binary), "--state", str(self.state),
            "continue",
        )
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(json.loads(resumed.stdout)["final_message"], "resumed")
        self.assertEqual(
            json.loads(self.state.read_text(encoding="utf-8"))["effort"], "max"
        )

        for command in ("stop", "verify"):
            with self.subTest(command=command):
                result = self.run_claude(
                    command, "--state", str(self.state), "--cwd", str(self.worktree)
                )
                if sys.platform == "darwin":
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(
                        result.stderr,
                        f"claude-worker: {LIFECYCLE_MODULE.UNSUPPORTED}\n",
                    )
                self.assertNotIn("malformed", result.stderr)


class OrchestrateAdapterDispatchTests(unittest.TestCase):
    def test_skill_bans_agent_tool_workflow_tool_and_background_agents_for_dispatch(self):
        skill = (ROOT / "skills" / "drivers" / "orchestrate" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("never through the Agent tool, the Workflow tool, or a\n  background agent", skill)
        self.assertIn("claude-worker.py", skill)
        self.assertIn("claude-worker.py resume", skill)
        self.assertNotIn("via the Agent tool with a `model` override", skill)
        self.assertIn("defaulting to medium", skill)

    def test_dispatch_claude_reference_exists_and_names_both_sandbox_modes(self):
        dispatch = (
            ROOT / "skills" / "drivers" / "orchestrate" / "references" / "dispatch-claude.md"
        ).read_text(encoding="utf-8")
        self.assertIn("read-only", dispatch)
        self.assertIn("workspace-write", dispatch)
        self.assertIn("prompt to the worker's stdin", dispatch)
        self.assertIn("liveness", dispatch.lower())
        self.assertIn("permission_denials", dispatch)
        self.assertIn("command -v claude", dispatch)
        # The workspace-write shape is the one a real run of #149 corrected: with
        # no filesystem block, a worker wrote through to $HOME/.cache. Pin the
        # corrected shape so this reference cannot drift back to describing the
        # pre-fix sandbox while the adapter generates the fixed one — nothing
        # else asserts what this document claims the shape is.
        self.assertIn("filesystem.allowWrite", dispatch)
        self.assertNotIn("no filesystem deny-list", dispatch)

    def test_routing_table_effort_notes_name_both_enums(self):
        table = (
            ROOT / "skills" / "drivers" / "orchestrate" / "references" / "routing-table.md"
        ).read_text(encoding="utf-8")
        self.assertIn("low|medium|high|xhigh|max", table)
        self.assertIn("none|low|medium|high|xhigh|max", table)
        self.assertIn("defaulting to medium", table)


class CodeReviewAdapterProtocolTests(unittest.TestCase):
    """Execute the coordinator contract through the public adapter CLIs."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.worktree = self.root / "worktree"
        self.worktree.mkdir()
        self.events = self.root / "events.log"
        self.release = self.root / "release"
        self.binary = self.root / "fake-reviewer"
        self.binary.write_text(
            """#!/usr/bin/env python3
import json, os, pathlib, sys, time

arguments = sys.argv[1:]
is_claude = arguments[:1] == ["-p"]
prompt = sys.stdin.read() if is_claude else arguments[-1]
if "axis=" not in prompt:
    raise SystemExit("missing axis prompt")
axis = prompt.split("axis=", 1)[1].split()[0].rstrip(";")
if is_claude:
    required = {"--model", "--effort", "--permission-mode", "--settings", "--session-id", "--output-format"}
    if not required.issubset(arguments) or arguments[arguments.index("--output-format") + 1] != "json":
        raise SystemExit("unexpected Claude adapter argv")
    if prompt in arguments:
        raise SystemExit("Claude prompt leaked into argv")
else:
    required = {"exec", "-m", "-c", "--sandbox", "--skip-git-repo-check", "-C", "--json"}
    if not required.issubset(arguments) or arguments[-1] != prompt:
        raise SystemExit("unexpected Codex adapter argv")

events = pathlib.Path(os.environ["REVIEW_EVENTS"])
with events.open("a", encoding="utf-8") as handle:
    handle.write(f"start {axis}\\n")
if axis == os.environ.get("REVIEW_HOLD_AXIS"):
    pathlib.Path(os.environ["REVIEW_HELD"]).touch()
    while not pathlib.Path(os.environ["REVIEW_RELEASE"]).exists():
        time.sleep(0.01)
if axis == os.environ.get("REVIEW_FAIL_AXIS"):
    raise SystemExit(17)
with events.open("a", encoding="utf-8") as handle:
    handle.write(f"end {axis}\\n")
if is_claude:
    print(json.dumps({"session_id": axis, "result": f"answer-{axis}", "is_error": False}))
else:
    print(json.dumps({"type": "thread.started", "thread_id": axis}))
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": f"answer-{axis}"}}))
""",
            encoding="utf-8",
        )
        self.binary.chmod(0o755)
        self.portable_launcher = self.root / "force-portable.py"
        self.portable_launcher.write_text(
            """#!/usr/bin/env python3
import importlib.util, pathlib, sys

worker = pathlib.Path(sys.argv.pop(1))
spec = importlib.util.spec_from_file_location("forced_portable_worker", worker)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.lifecycle._libproc = lambda: None
arguments = module.parser().parse_args()
if arguments.command in {"start", "resume"} and not arguments.prompt:
    raise SystemExit(module.fail("prompt is required"))
raise SystemExit(arguments.handler(arguments))
""",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def coordinate(self, adapter, admitted, *, hold_axis=None, fail_axis=None, launch_fail_axis=None, force_portable=False, broken=None):
        state_dir = self.root / f"state-{adapter}-{broken or 'correct'}-{len(list(self.root.glob('state-*')))}"
        state_dir.mkdir()
        self.events.unlink(missing_ok=True)
        self.release.unlink(missing_ok=True)
        (self.root / "held").unlink(missing_ok=True)
        environment = os.environ.copy()
        environment.update(
            {
                "CODEX_HOME": str(self.root / "codex-home"),
                "REVIEW_EVENTS": str(self.events),
                "REVIEW_HELD": str(self.root / "held"),
                "REVIEW_RELEASE": str(self.release),
                "REVIEW_HOLD_AXIS": hold_axis or "",
                "REVIEW_FAIL_AXIS": fail_axis or "",
            }
        )
        force_portable = force_portable or os.environ.get("CODE_REVIEW_TEST_FORCE_PORTABLE") == "1"
        worker = CODEX_WORKER if adapter == "codex" else CLAUDE_WORKER
        worker_module = WORKER_MODULE if adapter == "codex" else CLAUDE_WORKER_MODULE
        native_family = not force_portable and LIFECYCLE_MODULE._libproc() is not None
        option = "--codex" if adapter == "codex" else "--claude"
        model = "Terra" if adapter == "codex" else "sonnet"
        axes = (*admitted, "spec") if broken == "launch-unadmitted-spec" else admitted
        launches = {}
        launch_errors = {}
        artifacts = {}
        actions = []

        def wait_for_recovery(claim):
            deadline = time.monotonic() + 3
            portable_terminal = False
            while time.monotonic() < deadline:
                if claim["state"].exists():
                    candidate = json.loads(claim["state"].read_text(encoding="utf-8"))
                    if LIFECYCLE_MODULE.valid_family_schema(
                        candidate, effort_levels=worker_module.EFFORT_LEVELS
                    ):
                        return candidate, "family-state", False
                    portable_terminal = LIFECYCLE_MODULE.valid_portable_schema(
                        candidate, effort_levels=worker_module.EFFORT_LEVELS
                    )
                if claim["process"].poll() is not None:
                    return None, "helper-exit", portable_terminal
                time.sleep(0.01)
            return None, None, portable_terminal

        for axis in axes:
            if broken == "serial" and launches:
                self.release.touch()
                launches[next(reversed(launches))]["process"].wait(timeout=3)
            state = state_dir / f"{axis}.json"
            stdout = state_dir / f"{axis}.stdout"
            stderr = state_dir / f"{axis}.stderr"
            axis_worker = self.root / "unlaunchable-adapter" if axis == launch_fail_axis else worker
            launcher = [sys.executable, str(self.portable_launcher), str(axis_worker)] if force_portable else [sys.executable, str(axis_worker)]
            command = [
                *( [str(axis_worker)] if axis == launch_fail_axis else launcher ),
                "start", option, str(self.binary), "--state", str(state),
                "--model", model, "--sandbox", "read-only", "--effort", "high", "--cwd", str(self.worktree),
                f"axis={axis}; do not modify, patch, or stash",
            ]
            out = stdout.open("w", encoding="utf-8")
            err = stderr.open("w", encoding="utf-8")
            artifacts[axis] = (stdout, stderr)
            try:
                launches[axis] = {"process": subprocess.Popen(command, cwd=ROOT, env=environment, stdin=subprocess.DEVNULL, stdout=out, stderr=err), "state": state, "out": out, "err": err}
            except OSError as error:
                out.close()
                err.close()
                launch_errors[axis] = str(error)
                break
        deadline = time.monotonic() + 3
        expected_starts = {f"start {axis}" for axis in launches}
        while time.monotonic() < deadline:
            started_before_release = self.events.read_text(encoding="utf-8").splitlines() if self.events.exists() else []
            if expected_starts.issubset(started_before_release):
                break
            time.sleep(0.01)
        if hold_axis and not launch_errors:
            self.release.touch()

        result = {"artifacts": artifacts, "actions": actions, "answers": {}, "launch_errors": launch_errors, "launched": {axis: claim["process"].pid for axis, claim in launches.items()}, "returncodes": {}, "started_before_release": started_before_release, "joined": [], "unlaunched_actions": []}
        if launch_errors:
            failed_axis = next(iter(launch_errors))
            survivor, claim = next(iter(launches.items()))
            if not native_family:
                self.release.touch()
            recovery_state, recovery_ready, portable_terminal = wait_for_recovery(claim)
            result["recoverable"] = recovery_state is not None
            result["recovery_ready"] = recovery_ready
            result["portable_terminal"] = portable_terminal
            if broken == "touch-unlaunched":
                for operation in ("stop", "verify"):
                    cleanup = run([sys.executable, str(worker), operation, option, str(self.binary), "--state", str(state_dir / f"{failed_axis}.json"), "--cwd", str(self.worktree)], cwd=ROOT, env=environment)
                    result["unlaunched_actions"].append((operation, failed_axis, cleanup.returncode))
            if result["recoverable"]:
                for operation in ("stop", "verify"):
                    cleanup = run([sys.executable, str(worker), operation, option, str(self.binary), "--state", str(claim["state"]), "--cwd", str(self.worktree)], cwd=ROOT, env=environment)
                    self.assertEqual(cleanup.returncode, 0, cleanup.stderr)
                    actions.append((operation, survivor))
            else:
                self.release.touch()
            result["error"] = f"{failed_axis} failed to launch"
        if fail_axis and fail_axis in launches:
            failure = launches[fail_axis]["process"]
            result["returncodes"][fail_axis] = failure.wait(timeout=3)
            result["joined"].append(fail_axis)
            if result["returncodes"][fail_axis] and broken != "ignore-nonzero":
                survivor = next(axis for axis in admitted if axis != fail_axis)
                claim = launches[survivor]
                recovery_state, _, _ = wait_for_recovery(claim)
                result["recoverable"] = recovery_state is not None
                if result["recoverable"]:
                    for operation in ("stop", "verify"):
                        cleanup = run([sys.executable, str(worker), operation, option, str(self.binary), "--state", str(claim["state"]), "--cwd", str(self.worktree)], cwd=ROOT, env=environment)
                        self.assertEqual(cleanup.returncode, 0, cleanup.stderr)
                        actions.append((operation, survivor))
                result["error"] = f"{fail_axis} exited {result['returncodes'][fail_axis]}"
        for axis, claim in launches.items():
            if axis in result["returncodes"]:
                continue
            result["returncodes"][axis] = claim["process"].wait(timeout=3)
            result["joined"].append(axis)
            if result["returncodes"][axis] and broken != "ignore-nonzero" and "error" not in result:
                result["error"] = f"{axis} exited {result['returncodes'][axis]}"
            elif not result["returncodes"][axis] and broken != "state-answer":
                result["answers"][axis] = json.loads(artifacts[axis][0].read_text(encoding="utf-8"))["final_message"]
        for claim in launches.values():
            claim["out"].close()
            claim["err"].close()
        result["events"] = self.events.read_text(encoding="utf-8").splitlines()
        return result

    def assert_broken_then_correct(self, broken, assertion, **arguments):
        with self.assertRaises(AssertionError):
            assertion(self.coordinate(broken=broken, **arguments))
        assertion(self.coordinate(**arguments))

    def test_portable_path_starts_second_axis_before_the_held_first_axis_finishes(self):
        for adapter in ("codex", "claude"):
            with self.subTest(adapter=adapter):
                def concurrent(result):
                    self.assertIn("start standards", result["started_before_release"])
                    self.assertIn("start spec", result["started_before_release"])
                    self.assertLess(result["events"].index("start spec"), result["events"].index("end standards"))
                    self.assertEqual(result["joined"], ["standards", "spec"])

                self.assert_broken_then_correct(
                    "serial", concurrent, adapter=adapter, admitted=("standards", "spec"), hold_axis="standards"
                )

    def test_spec_unavailable_launches_only_standards(self):
        for adapter in ("codex", "claude"):
            with self.subTest(adapter=adapter):
                def standards_only(result):
                    self.assertEqual(result["joined"], ["standards"])
                    self.assertEqual(set(result["artifacts"]), {"standards"})
                    self.assertEqual(result["answers"], {"standards": "answer-standards"})

                self.assert_broken_then_correct(
                    "launch-unadmitted-spec", standards_only, adapter=adapter, admitted=("standards",)
                )

    def test_stdout_artifacts_supply_answers_and_nonzero_exits_are_rejected(self):
        for adapter in ("codex", "claude"):
            with self.subTest(adapter=adapter):
                def successful(result):
                    self.assertEqual(result["answers"], {"standards": "answer-standards", "spec": "answer-spec"})
                    self.assertTrue(all(path.exists() for pair in result["artifacts"].values() for path in pair))
                    self.assertNotIn("error", result)

                self.assert_broken_then_correct(
                    "state-answer", successful, adapter=adapter, admitted=("standards", "spec")
                )
                rejected = self.coordinate(adapter, ("standards", "spec"), fail_axis="spec")
                self.assertEqual(rejected["error"], "spec exited 17")
                with self.assertRaises(AssertionError):
                    self.assertIn("error", self.coordinate(adapter, ("standards", "spec"), fail_axis="spec", broken="ignore-nonzero"))

    def test_partial_launch_failure_waits_then_scoped_stop_and_verify_only_for_survivor(self):
        for adapter in ("codex", "claude"):
            force_portable_only = os.environ.get("CODE_REVIEW_TEST_FORCE_PORTABLE") == "1"
            family_modes = (("native", False), ("portable", True)) if sys.platform == "darwin" and not force_portable_only else (("portable", True),)
            for family_mode, force_portable in family_modes:
                with self.subTest(adapter=adapter, family_mode=family_mode):
                    def recovered(result):
                        self.assertEqual(result["launched"].keys(), {"standards"})
                        self.assertNotIn("spec", result["joined"])
                        if family_mode == "native":
                            self.assertTrue(result["recoverable"])
                            self.assertEqual(result["recovery_ready"], "family-state")
                            self.assertFalse(result["portable_terminal"])
                            self.assertEqual(result["actions"], [("stop", "standards"), ("verify", "standards")])
                        else:
                            self.assertFalse(result["recoverable"])
                            self.assertEqual(result["recovery_ready"], "helper-exit")
                            self.assertTrue(result["portable_terminal"])
                            self.assertEqual(result["actions"], [])
                        self.assertEqual(result["unlaunched_actions"], [])
                        self.assertEqual(result["joined"], ["standards"])
                        self.assertEqual(result["error"], "spec failed to launch")

                    self.assert_broken_then_correct(
                        "touch-unlaunched", recovered, adapter=adapter, admitted=("standards", "spec"),
                        hold_axis="standards", launch_fail_axis="spec", force_portable=force_portable,
                    )


class CodeReviewAdapterDispatchTests(unittest.TestCase):
    SKILL = ROOT / "skills" / "tools" / "code-review" / "SKILL.md"

    def setUp(self):
        self.text = self.SKILL.read_text(encoding="utf-8")
        self.dispatch = " ".join(
            self.text.split("### 4. Run both axes in parallel", 1)[1]
            .split("### 5. Aggregate and report", 1)[0]
            .split()
        )

    def test_dispatch_uses_only_pack_adapters_with_explicit_inputs(self):
        self.assertIn("reviewer model", self.dispatch)
        self.assertIn("reviewer effort", self.dispatch)
        self.assertIn("Pass model and effort through unchanged", self.dispatch)
        self.assertIn("codex-worker.py", self.dispatch)
        self.assertIn("claude-worker.py", self.dispatch)
        self.assertNotIn("general-purpose", self.dispatch)
        self.assertNotIn("Agent tool", self.dispatch)
        self.assertNotIn("Workflow tool", self.dispatch)
        self.assertNotIn("background agent", self.dispatch)

    def test_admitted_axes_have_deterministic_files_concurrent_launch_and_individual_joins(self):
        for path in ("<review-state-dir>/standards.json", "<review-state-dir>/spec.json"):
            self.assertIn(path, self.dispatch)
        for artifact in ("standards.stdout", "standards.stderr", "spec.stdout", "spec.stderr"):
            self.assertIn(artifact, self.dispatch)
        self.assertIn("start all admitted helper invocations as background processes before waiting", self.dispatch)
        self.assertIn("Retain each axis-specific launcher PID", self.dispatch)
        self.assertIn("waiting on its retained PID individually", self.dispatch)
        self.assertLess(
            self.dispatch.index("start all admitted helper invocations"),
            self.dispatch.index("waiting on its retained PID individually"),
        )
        self.assertIn("second admitted axis starts while the first remains active", self.dispatch)

    def test_answers_come_from_successful_stdout_and_retries_reuse_state(self):
        self.assertIn("Reject every nonzero exit", self.dispatch)
        self.assertIn("parse `final_message` from its stdout artifact", self.dispatch)
        self.assertIn("State files carry lifecycle metadata only and never the reviewer answer", self.dispatch)
        self.assertIn("resume` command against the same axis state file", self.dispatch)

    def test_readonly_prompt_transport_contract_is_explicit(self):
        self.assertIn("`--sandbox read-only`", self.dispatch)
        self.assertIn("explicit coordinator-supplied `--model` and `--effort`", self.dispatch)
        self.assertIn("must not modify, patch, or stash", self.dispatch)
        self.assertIn("Codex receives the positional prompt with inherited stdin closed", self.dispatch)
        self.assertIn("Claude adapter receives the positional prompt and delivers it to the child on stdin", self.dispatch)

    def test_spec_unavailable_runs_standards_alone_and_reports_it(self):
        self.assertIn("When Spec is unavailable, launch Standards only", self.dispatch)
        self.assertIn("do not launch Spec", self.dispatch)
        self.assertIn("report Spec unavailable", self.dispatch)

    def test_partial_launch_recovery_is_scoped_to_the_surviving_launched_worker(self):
        self.assertIn("If a later launch fails after another worker launched", self.dispatch)
        self.assertIn("wait for the surviving helper to reach valid readable state or exit", self.dispatch)
        self.assertIn("Only when recoverable state exists", self.dispatch)
        self.assertIn("scoped `stop --state ... --cwd ...`", self.dispatch)
        self.assertIn("scoped `verify --state ... --cwd ...`", self.dispatch)
        self.assertIn("Then join that worker's retained PID", self.dispatch)
        self.assertIn("Do not discover, stop, verify, or join an unlaunched worker", self.dispatch)
        self.assertLess(self.dispatch.index("scoped `stop"), self.dispatch.index("scoped `verify"))


class PlanReviewAdapterDispatchTests(unittest.TestCase):
    SKILL = ROOT / "skills" / "tools" / "plan-review" / "SKILL.md"

    def setUp(self):
        self.source = self.SKILL.read_bytes()

    def test_caller_owned_round_ledger_covers_both_plan_locations(self):
        dispatch = self.source.split(b"## Cold-reader dispatch\n", 1)[1].split(
            b"## Mechanical fix in place\n", 1
        )[0]
        self.assertIn(b"For a durable plan", dispatch)
        self.assertIn(b"durable plan\nlocator and immutable revision", dispatch)
        self.assertIn(b"For a chat-delivered plan", dispatch)
        self.assertIn(b"record that plan file path", dispatch)
        self.assertIn(b"plan-review-mechanical-fixes.md", dispatch)

    def test_mechanical_fix_in_place_stays_narrow_and_deterministic(self):
        text = " ".join(self.source.decode("utf-8").split())
        self.assertIn(
            "A coordinator may correct a cold-review finding in the order without opening a "
            "rewrite-plus-review round only when both the finding and its correction are "
            "deterministic and mechanical: for example, a wrong heading anchor, a missing exact "
            "string, or nondeterministic command ordering.",
            text,
        )
        self.assertIn(
            "A correction that requires judgment, changes a decision, changes scope, or reopens "
            "a settled ruling stays in the panel-or-operator path and does consume the ordinary "
            "revision cycle.",
            text,
        )


class AssuranceLevelMatchingContractTests(unittest.TestCase):
    PROFILE = ROOT / "profile" / "base.md"
    PLAN_REVIEW = ROOT / "skills" / "tools" / "plan-review" / "SKILL.md"
    ORCHESTRATE = ROOT / "skills" / "drivers" / "orchestrate" / "SKILL.md"

    def setUp(self):
        self.profile = " ".join(self.PROFILE.read_text(encoding="utf-8").split())
        self.plan_review = " ".join(
            self.PLAN_REVIEW.read_text(encoding="utf-8").split()
        )
        self.orchestrate = " ".join(
            self.ORCHESTRATE.read_text(encoding="utf-8").split()
        )

    def test_working_preference_matches_mechanism_to_requested_assurance(self):
        self.assertIn(
            "**Match the mechanism to the assurance level that was asked for.** Do not introduce "
            "parsers, formal grammars, provenance records, state machines, content filtering, "
            "or runtime enforcement for a prose contract unless explicitly asked. Treat a "
            "review finding that demands stronger assurance than the requested behavior, or "
            "than the admitted risk contract where one exists, as scope expansion rather than "
            "a blocker, except when it names a documented rule of the repo (including "
            "`profile/CHARTER.md`) or a must-prevent outcome in the admitted risk contract. "
            "Prefer ordinary semantic interpretation and the smallest change that works.",
            self.profile,
        )

    def test_axis_four_keeps_the_reviewer_within_the_assurance_boundary(self):
        self.assertIn(
            "A reviewer may test whether the proposed mechanism satisfies the stated risk "
            "contract, but may not raise that contract or demand a parser, formal grammar, "
            "provenance record, state machine, content filtering, or runtime enforcement beyond "
            "the requested behavior, or beyond the admitted risk contract where one exists. An "
            "objection that only holds if the assurance bar rises is scope expansion and is "
            "discarded, unless evidence, not judgment, changes the assumed likelihood, "
            "consequence, or recoverability; then the evidence-reopen rule earlier in this axis "
            "governs and the objection stands. A finding that names a documented rule of the "
            "repo (including `profile/CHARTER.md`) or a must-prevent outcome in the admitted risk "
            "contract is never discarded on this ground. The cycle's step 0 generated-facts "
            "demand and the evidence-block spot check's **BLOCKED** verdict are this skill's own "
            "triage and evidence obligations, not assurance escalation, and are unaffected.",
            self.plan_review,
        )

    def test_partial_checks_are_supplemental_not_full_verification(self):
        self.assertIn(
            "Focused, targeted, or subset checks are supplemental evidence and never stand "
            "in for the named verification command.",
            self.orchestrate,
        )

    def test_cycle_rereads_settled_decisions_after_compaction(self):
        self.assertIn(
            "If the coordinator session running the review has its context compacted mid-review, "
            "it re-reads the settled decisions in the plan's scope ledger wherever `/scope` "
            "placed it (`docs/scope/<slug>.md` or the session scratchpad) and the risk contract "
            "copied into the plan before evaluating the reviewer's deltas. It treats decisions "
            "recorded there as settled rather than re-deriving them from what survived "
            "compaction. Cold reviewers stay cold: this rule adds nothing to the cold-reader "
            "prompt, and `plan-review-mechanical-fixes.md` remains the round ledger rather than "
            "the settled-decision record.",
            self.plan_review,
        )


class VerbatimEvidenceBlockContractTests(unittest.TestCase):
    """Subject is the command-output-pasting contract, not the retired evidence-v2
    envelope machinery: preflight's and plan-review's own review evidence blocks."""

    def test_preflight_forbids_edited_command_output(self):
        text = " ".join(
            (ROOT / "skills" / "tools" / "preflight" / "SKILL.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn(
            "Every `command → output` evidence block is pasted verbatim from an actual command "
            "run.",
            text,
        )
        self.assertIn(
            "Manual edits are prohibited and require a **BLOCKED** verdict on their own.", text
        )

    def test_plan_review_spot_checks_at_least_one_evidence_block(self):
        text = " ".join(
            (ROOT / "skills" / "tools" / "plan-review" / "SKILL.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn(
            "During the cold read, spot-check at least one `command → output` evidence block: "
            "run its recorded command and compare the complete result to the cited output.",
            text,
        )
        self.assertIn(
            "Treat a manual edit found in any evidence block as independently requiring a "
            "**BLOCKED** verdict.",
            text,
        )


class PersonaReviewAdapterDispatchTests(unittest.TestCase):
    SKILL = ROOT / "skills" / "tools" / "persona-review" / "SKILL.md"

    def setUp(self):
        self.text = self.SKILL.read_text(encoding="utf-8")

    def test_panelist_dispatch_stays_on_the_worker_adapters_only(self):
        normalized = " ".join(self.text.split())
        self.assertIn(
            "The coordinator supplies the selected adapter, explicit reviewer model, and "
            "explicit reviewer effort. For each panelist, dispatch only through "
            "`skills/drivers/orchestrate/scripts/codex-worker.py` or "
            "`skills/drivers/orchestrate/scripts/claude-worker.py`, using the selected "
            "adapter's read-only review surface. Never use the built-in Agent tool, Workflow "
            "tool, or background-agent machinery.",
            normalized,
        )

    def test_panelist_prompt_excludes_persona_and_panel_content(self):
        normalized = " ".join(self.text.split())
        self.assertIn(
            "The prompt contains no persona name, simulation label, mine date, panel "
            "narrative, or profile, review-log, or override content.",
            normalized,
        )

    def test_serial_no_lookback_fallback_is_preserved(self):
        remainder = self.text.split("## Cold review, per persona\n\n", 1)[1]
        self.assertIn("\n\n## Synthesis\n", remainder)
        cold_review = remainder.split("\n\n## Synthesis", 1)[0]
        self.assertIn(
            "Where adapter dispatch isn't available, review personas serially in the main session,",
            cold_review,
        )
        self.assertIn(
            "deliberately not looking back at an earlier persona's output while forming the next one's position.",
            cold_review,
        )

class ResearchAdapterDispatchTests(unittest.TestCase):
    SKILL = ROOT / "skills" / "tools" / "research" / "SKILL.md"
    AGENT_METADATA = ROOT / "skills" / "tools" / "research" / "agents" / "openai.yaml"

    def setUp(self):
        self.text = self.SKILL.read_text(encoding="utf-8")
        self.agent_metadata = self.AGENT_METADATA.read_text(encoding="utf-8")

    def test_agent_metadata_describes_pack_adapter_dispatch(self):
        self.assertIn(
            'short_description: "Research primary sources through a selected pack adapter"',
            self.agent_metadata,
        )
        self.assertNotIn("background agent", self.agent_metadata)

    def research_job(self):
        anchor = "## The research worker's job\n\n"
        self.assertIn(anchor, self.text)
        return " ".join(self.text.split(anchor, 1)[1].split())

    def test_research_job_requires_primary_sources(self):
        self.assertIn("Investigate the question against **primary sources**", self.research_job())

    def test_research_job_requires_source_citations_for_each_claim(self):
        self.assertIn("citing each claim's source", self.research_job())

    def test_coordinator_writes_one_markdown_file_using_repository_convention(self):
        job = self.research_job()
        self.assertIn("The coordinator writes the returned findings to a single Markdown file", job)
        self.assertIn("Save it where the repo already keeps such notes; match the existing convention", job)


class DesignItTwiceAdapterDispatchTests(unittest.TestCase):
    REFERENCE = ROOT / "skills" / "tools" / "codebase-design" / "references" / "DESIGN-IT-TWICE.md"

    def setUp(self):
        self.text = " ".join(self.REFERENCE.read_text(encoding="utf-8").split())

    def test_dispatch_stays_on_the_worker_adapters_only(self):
        self.assertIn(
            "Dispatch only through `skills/drivers/orchestrate/scripts/codex-worker.py` or "
            "`skills/drivers/orchestrate/scripts/claude-worker.py`, using the selected "
            "adapter's read-only surface.",
            self.text,
        )
        self.assertIn(
            "Never use the built-in Agent tool, Workflow tool, or background-agent machinery.",
            self.text,
        )

    def test_procedure_does_not_select_adapter_model_or_effort(self):
        self.assertIn(
            "This procedure does not select an adapter, model, or effort, apply a "
            "routing table or headroom policy, or add defaults.",
            self.text,
        )


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
            "version": LIFECYCLE_MODULE.STATE_VERSION,
            "lifecycle": lifecycle,
            "session_id": session_id,
            "model": "Terra",
            "sandbox": "read-only",
            **self.identity,
        }

    def portable_state(self, generation=1):
        return {
            "version": LIFECYCLE_MODULE.STATE_VERSION,
            "lifecycle": "exited",
            "session_id": "worker-1",
            "model": "Terra",
            "sandbox": "read-only",
            "cwd": str(self.cwd),
            "family_semantics": LIFECYCLE_MODULE.FAMILY_SEMANTICS_UNSUPPORTED,
            "generation": generation,
        }

    def arguments(self):
        return argparse.Namespace(state=self.state, cwd=self.cwd, grace_seconds=0.01)

    def resume_arguments(self):
        return argparse.Namespace(state=self.state, codex="codex", prompt="continue")

    def test_moved_lifecycle_names_have_one_patchable_owner(self):
        """A moved-name re-export can make a patch resolve without intercepting."""
        moved = (
            "STATE_VERSION", "UNSUPPORTED", "FAMILY_SEMANTICS_UNSUPPORTED",
            "TERMINAL", "TRANSITIONS", "PROC_PIDTBSDINFO",
            "PROC_PIDVNODEPATHINFO", "BSD_SIZE", "VNODE_SIZE",
            "VNODE_CWD_OFFSET", "PID_MAX", "UINT64_MAX", "resolved_directory",
            "is_within", "state_lock", "atomic_write", "read_state", "transition",
            "_bounded_integer", "_canonical_path", "BASE_STATE_FIELDS",
            "_valid_common_schema", "valid_family_schema", "valid_portable_schema",
            "_libproc", "live_identity", "group_members", "gated_process",
            "establish_family", "finish_lifecycle", "run_portable",
            "run_lifecycle", "family_state", "matching_leader",
        )
        self.assertTrue(WORKER_LIFECYCLE.exists())
        for name in moved:
            self.assertIn(name, LIFECYCLE_MODULE.__dict__)
            self.assertNotIn(name, WORKER_MODULE.__dict__)
            self.assertNotIn(name, CLAUDE_WORKER_MODULE.__dict__)
        for adapter in (CODEX_WORKER, CLAUDE_WORKER):
            source = adapter.read_text(encoding="utf-8")
            for name in moved:
                self.assertIsNone(
                    re.search(rf"(?<![.\w]){re.escape(name)}\(", source),
                    f"{adapter.name} calls moved name {name} without lifecycle qualification",
                )

    def test_both_adapters_route_all_four_commands_through_shared_lifecycle(self):
        expected = self.portable_state()
        fresh = {
            "version": LIFECYCLE_MODULE.STATE_VERSION,
            "lifecycle": "launching",
            "session_id": "worker-1",
            "model": "model",
            "sandbox": "read-only",
            "cwd": str(self.cwd),
        }
        for adapter, binary_name, stdin_text in (
            (WORKER_MODULE, "codex", None),
            (CLAUDE_WORKER_MODULE, "claude", "continue"),
        ):
            with self.subTest(adapter=adapter.__name__):
                arguments = argparse.Namespace(
                    state=self.state,
                    cwd=self.cwd,
                    sandbox="read-only",
                    control_checkout=None,
                    model="model",
                    effort="medium",
                    prompt="continue",
                    codex="codex",
                    claude="claude",
                    grace_seconds=0.01,
                )
                with (
                    mock.patch.object(
                        LIFECYCLE_MODULE, "prepare_start", return_value=(fresh, None)
                    ) as prepare_start,
                    mock.patch.object(
                        LIFECYCLE_MODULE, "run_lifecycle", return_value=0
                    ) as launch,
                ):
                    self.assertEqual(adapter.start(arguments), 0)
                    prepare_start.assert_called_once()
                    self.assertEqual(launch.call_args.args[2], fresh)
                    self.assertIs(launch.call_args.kwargs["parse"], adapter.parse)
                    self.assertIs(launch.call_args.kwargs["emit"], adapter.emit)
                    self.assertIs(launch.call_args.kwargs["fail"], adapter.fail)
                    self.assertEqual(launch.call_args.kwargs["stdin_text"], stdin_text)
                    self.assertEqual(launch.call_args.args[1][0], getattr(arguments, binary_name))
                with (
                    mock.patch.object(
                        LIFECYCLE_MODULE,
                        "prepare_resume",
                        return_value=(fresh, expected, None),
                    ) as prepare_resume,
                    mock.patch.object(
                        LIFECYCLE_MODULE, "run_lifecycle", return_value=0
                    ) as launch,
                ):
                    self.assertEqual(adapter.resume(arguments), 0)
                    prepare_resume.assert_called_once()
                    self.assertEqual(launch.call_args.kwargs["expected"], expected)
                    self.assertEqual(launch.call_args.kwargs["stdin_text"], stdin_text)
                with mock.patch.object(
                    LIFECYCLE_MODULE, "stop_worker", return_value=(0, None)
                ) as stop_worker:
                    self.assertEqual(adapter.stop(arguments), 0)
                    stop_worker.assert_called_once()
                with mock.patch.object(
                    LIFECYCLE_MODULE, "verify_worker", return_value=(0, None)
                ) as verify_worker:
                    self.assertEqual(adapter.verify(arguments), 0)
                    verify_worker.assert_called_once()

    def test_none_stdin_keeps_the_portable_launch_closed(self):
        completed = subprocess.CompletedProcess(["worker"], 0, "output", "")
        state = {
            "version": LIFECYCLE_MODULE.STATE_VERSION,
            "lifecycle": "launching",
            "session_id": "",
            "model": "model",
            "sandbox": "read-only",
            "cwd": str(self.cwd),
        }
        with (
            mock.patch.object(
                LIFECYCLE_MODULE.subprocess, "run", return_value=completed
            ) as launch,
            mock.patch.object(LIFECYCLE_MODULE, "atomic_write"),
        ):
            self.assertEqual(
                LIFECYCLE_MODULE.run_portable(
                    argparse.Namespace(state=self.state),
                    ["worker"],
                    state,
                    1,
                    parse=lambda _output: ("session", "done", None, None),
                    emit=lambda *_args: None,
                    fail=lambda _message: 1,
                    stdin_text=None,
                ),
                0,
            )
        self.assertIs(launch.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertNotIn("input", launch.call_args.kwargs)

    def test_transition_table_and_atomic_replace_fsync_the_state_and_parent(self):
        self.assertEqual(LIFECYCLE_MODULE.TRANSITIONS["launching"], {"running", "stopping", "exited"})
        self.assertEqual(LIFECYCLE_MODULE.TRANSITIONS["running"], {"stopping", "exited"})
        self.assertEqual(LIFECYCLE_MODULE.TRANSITIONS["stopping"], {"stopped", "exited"})
        with mock.patch.object(WORKER_MODULE.os, "fsync", wraps=os.fsync) as fsync, mock.patch.object(WORKER_MODULE.os, "replace", wraps=os.replace) as replace:
            LIFECYCLE_MODULE.atomic_write(self.state, self.family_state("launching"))
        self.assertEqual(replace.call_count, 1)
        self.assertGreaterEqual(fsync.call_count, 2)
        state = LIFECYCLE_MODULE.read_state(self.state, family_required=True)
        self.assertEqual(LIFECYCLE_MODULE.transition(self.state, state, "running")["lifecycle"], "running")
        with self.assertRaises(ValueError):
            LIFECYCLE_MODULE.transition(self.state, state, "stopped")

    def test_every_legal_transition_is_persisted_and_every_other_edge_is_rejected(self):
        for source, destinations in LIFECYCLE_MODULE.TRANSITIONS.items():
            for destination in destinations:
                with self.subTest(source=source, destination=destination):
                    LIFECYCLE_MODULE.atomic_write(self.state, self.family_state(source))
                    state = LIFECYCLE_MODULE.read_state(self.state, family_required=True)
                    self.assertEqual(LIFECYCLE_MODULE.transition(self.state, state, destination)["lifecycle"], destination)
            illegal = next(candidate for candidate in LIFECYCLE_MODULE.TRANSITIONS if candidate not in destinations)
            with self.subTest(source=source, illegal=illegal):
                LIFECYCLE_MODULE.atomic_write(self.state, self.family_state(source))
                with self.assertRaises(ValueError):
                    LIFECYCLE_MODULE.transition(self.state, LIFECYCLE_MODULE.read_state(self.state), illegal)

    def test_missing_corrupt_stale_and_legacy_state_are_rejected_by_stop_and_verify(self):
        for name, contents in (
            ("missing", None),
            ("corrupt", "not json"),
            ("stale", json.dumps({"version": 1})),
            ("legacy", json.dumps({"session_id": "old", "model": "Terra", "sandbox": "read-only", "cwd": str(self.cwd)})),
        ):
            with self.subTest(name=name), mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()), mock.patch.object(WORKER_MODULE.os, "killpg") as killpg:
                if contents is None:
                    self.state.unlink(missing_ok=True)
                else:
                    self.state.write_text(contents, encoding="utf-8")
                self.assertNotEqual(WORKER_MODULE.stop(self.arguments()), 0)
                self.assertNotEqual(WORKER_MODULE.verify(self.arguments()), 0)
                killpg.assert_not_called()

    def test_malformed_v2_mutations_are_rejected_before_any_process_probe_or_signal(self):
        base = self.family_state()
        mutations = (
            *((f"missing {field}", {key: value for key, value in base.items() if key != field}) for field in base),
            ("version type", {**base, "version": "2"}),
            ("version null", {**base, "version": None}),
            ("version bool", {**base, "version": True}),
            ("version value", {**base, "version": 3}),
            ("lifecycle type", {**base, "lifecycle": []}),
            ("lifecycle value", {**base, "lifecycle": "unknown"}),
            ("pid type", {**base, "pid": "41"}),
            ("pid bool", {**base, "pid": True}),
            ("pid negative", {**base, "pid": -1}),
            ("pid zero", {**base, "pid": 0}),
            ("pid overflow", {**base, "pid": 2**31}),
            ("pgid type", {**base, "pgid": "41"}),
            ("pgid bool", {**base, "pgid": True}),
            ("pgid negative", {**base, "pgid": -1}),
            ("pgid zero", {**base, "pgid": 0}),
            ("pgid overflow", {**base, "pgid": 2**31}),
            ("sid type", {**base, "sid": "41"}),
            ("sid bool", {**base, "sid": True}),
            ("sid negative", {**base, "sid": -1}),
            ("sid zero", {**base, "sid": 0}),
            ("sid overflow", {**base, "sid": 2**31}),
            ("cwd type", {**base, "cwd": [str(self.cwd)]}),
            ("cwd empty", {**base, "cwd": ""}),
            ("cwd relative", {**base, "cwd": "worktree"}),
            ("cwd noncanonical", {**base, "cwd": str(self.cwd) + "/."}),
            ("birth type", {**base, "birth": [1, 2]}),
            ("birth missing seconds", {**base, "birth": {"microseconds": 2}}),
            ("birth missing microseconds", {**base, "birth": {"seconds": 1}}),
            ("birth seconds type", {**base, "birth": {"seconds": "1", "microseconds": 2}}),
            ("birth seconds bool", {**base, "birth": {"seconds": True, "microseconds": 2}}),
            ("birth seconds negative", {**base, "birth": {"seconds": -1, "microseconds": 2}}),
            ("birth seconds zero", {**base, "birth": {"seconds": 0, "microseconds": 2}}),
            ("birth seconds overflow", {**base, "birth": {"seconds": 2**64, "microseconds": 2}}),
            ("birth microseconds type", {**base, "birth": {"seconds": 1, "microseconds": "2"}}),
            ("birth microseconds bool", {**base, "birth": {"seconds": 1, "microseconds": True}}),
            ("birth microseconds negative", {**base, "birth": {"seconds": 1, "microseconds": -1}}),
            ("birth microseconds overflow", {**base, "birth": {"seconds": 1, "microseconds": 1_000_000}}),
            ("birth extra field", {**base, "birth": {"seconds": 1, "microseconds": 2, "ticks": 3}}),
            ("model type", {**base, "model": []}),
            ("model empty", {**base, "model": ""}),
            ("sandbox type", {**base, "sandbox": []}),
            ("sandbox value", {**base, "sandbox": "danger-full-access"}),
            ("session type", {**base, "session_id": 1}),
            ("workspace control missing", {**base, "sandbox": "workspace-write"}),
            ("control checkout type", {**base, "control_checkout": 1}),
            ("control checkout empty", {**base, "control_checkout": ""}),
            ("control checkout relative", {**base, "control_checkout": "control"}),
            ("unknown field", {**base, "leader_name": "codex"}),
        )
        for name, state in mutations:
            operations = (
                ("stop", WORKER_MODULE.stop, self.arguments()),
                ("verify", WORKER_MODULE.verify, self.arguments()),
                ("resume", WORKER_MODULE.resume, self.resume_arguments()),
            )
            for operation_name, operation, arguments in operations:
                with self.subTest(name=name, operation=operation_name):
                    LIFECYCLE_MODULE.atomic_write(self.state, state)
                    error = io.StringIO()
                    with (
                        mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()) as libproc,
                        mock.patch.object(LIFECYCLE_MODULE, "gated_process") as gated,
                        mock.patch.object(LIFECYCLE_MODULE, "live_identity") as identity,
                        mock.patch.object(LIFECYCLE_MODULE, "group_members") as members,
                        mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
                        redirect_stderr(error),
                    ):
                        self.assertEqual(operation(arguments), 1)
                    self.assertTrue(error.getvalue().startswith("codex-worker: state"))
                    libproc.assert_not_called()
                    gated.assert_not_called()
                    identity.assert_not_called()
                    members.assert_not_called()
                    killpg.assert_not_called()

    def test_malformed_portable_mutations_are_rejected_before_any_process_probe_or_signal(self):
        base = self.portable_state()
        mutations = (
            ("missing family semantics", {key: value for key, value in base.items() if key != "family_semantics"}),
            ("family semantics type", {**base, "family_semantics": []}),
            ("family semantics value", {**base, "family_semantics": "recoverable"}),
            ("missing generation", {key: value for key, value in base.items() if key != "generation"}),
            ("generation type", {**base, "generation": "1"}),
            ("generation bool", {**base, "generation": True}),
            ("generation zero", {**base, "generation": 0}),
            ("generation overflow", {**base, "generation": 2**64}),
            ("nonterminal lifecycle", {**base, "lifecycle": "running"}),
            ("fabricated identity", {**base, "pid": 41}),
        )
        for name, state in mutations:
            operations = (
                ("stop", WORKER_MODULE.stop, self.arguments()),
                ("verify", WORKER_MODULE.verify, self.arguments()),
                ("resume", WORKER_MODULE.resume, self.resume_arguments()),
            )
            for operation_name, operation, arguments in operations:
                with self.subTest(name=name, operation=operation_name):
                    LIFECYCLE_MODULE.atomic_write(self.state, state)
                    error = io.StringIO()
                    with (
                        mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()) as libproc,
                        mock.patch.object(LIFECYCLE_MODULE, "gated_process") as gated,
                        mock.patch.object(LIFECYCLE_MODULE, "live_identity") as identity,
                        mock.patch.object(LIFECYCLE_MODULE, "group_members") as members,
                        mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
                        redirect_stderr(error),
                    ):
                        self.assertEqual(operation(arguments), 1)
                    self.assertTrue(error.getvalue().startswith("codex-worker: state"))
                    libproc.assert_not_called()
                    gated.assert_not_called()
                    identity.assert_not_called()
                    members.assert_not_called()
                    killpg.assert_not_called()

    def test_unsupported_platform_returns_the_exact_code_without_signaling(self):
        LIFECYCLE_MODULE.atomic_write(self.state, self.family_state())
        for operation in (WORKER_MODULE.stop, WORKER_MODULE.verify):
            with self.subTest(operation=operation.__name__):
                error = io.StringIO()
                with (
                    mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=None),
                    mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
                    redirect_stderr(error),
                ):
                    self.assertEqual(operation(self.arguments()), 1)
                self.assertEqual(
                    error.getvalue(),
                    f"codex-worker: {LIFECYCLE_MODULE.UNSUPPORTED}\n",
                )
                killpg.assert_not_called()

    def test_forced_unsupported_start_resume_and_cleanup_contract(self):
        output = (
            '{"type":"thread.started","thread_id":"worker-1"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"answer"}}\n'
        )
        arguments = argparse.Namespace(
            state=self.state,
            codex="codex",
            prompt="do the work",
            model="Terra",
            sandbox="read-only",
            cwd=self.cwd,
            control_checkout=None,
        )
        completed = subprocess.CompletedProcess([], 0, stdout=output, stderr="")
        with (
            mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=None),
            mock.patch.object(WORKER_MODULE.subprocess, "run", return_value=completed) as run_worker,
            mock.patch.object(LIFECYCLE_MODULE, "gated_process") as gated,
            mock.patch.object(WORKER_MODULE, "latest_rate_limits", return_value=None),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(WORKER_MODULE.start(arguments), 0)

        state = LIFECYCLE_MODULE.read_state(self.state)
        self.assertEqual(state["version"], LIFECYCLE_MODULE.STATE_VERSION)
        self.assertEqual(state["lifecycle"], "exited")
        self.assertEqual(state["session_id"], "worker-1")
        self.assertEqual(state["family_semantics"], "unsupported")
        self.assertEqual(state["generation"], 1)
        self.assertFalse({"pid", "pgid", "sid", "birth"} & set(state))
        run_worker.assert_called_once()
        gated.assert_not_called()

        refusal = io.StringIO()
        with (
            mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=None),
            mock.patch.object(WORKER_MODULE.subprocess, "run", return_value=completed) as resume_worker,
            mock.patch.object(LIFECYCLE_MODULE, "gated_process") as resume_gate,
            mock.patch.object(WORKER_MODULE, "latest_rate_limits", return_value=None),
            mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
            redirect_stdout(io.StringIO()),
            redirect_stderr(refusal),
        ):
            self.assertEqual(WORKER_MODULE.resume(self.resume_arguments()), 0)
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 1)
            self.assertEqual(WORKER_MODULE.verify(self.arguments()), 1)

        resumed = LIFECYCLE_MODULE.read_state(self.state)
        self.assertTrue(
            LIFECYCLE_MODULE.valid_portable_schema(
                resumed, effort_levels=WORKER_MODULE.EFFORT_LEVELS
            )
        )
        self.assertEqual(resumed["generation"], 2)
        self.assertIn("resume", resume_worker.call_args.args[0])
        resume_gate.assert_not_called()
        self.assertEqual(
            refusal.getvalue(),
            f"codex-worker: {LIFECYCLE_MODULE.UNSUPPORTED}\n" * 2,
        )
        killpg.assert_not_called()

        with (
            mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()),
            mock.patch.object(LIFECYCLE_MODULE, "live_identity") as identity,
            mock.patch.object(LIFECYCLE_MODULE, "group_members") as members,
            mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 1)
            self.assertEqual(WORKER_MODULE.verify(self.arguments()), 1)
        identity.assert_not_called()
        members.assert_not_called()
        killpg.assert_not_called()

    def test_already_exited_leader_with_empty_group_stops_without_a_signal(self):
        LIFECYCLE_MODULE.atomic_write(self.state, self.family_state())
        with mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()), mock.patch.object(LIFECYCLE_MODULE, "live_identity", return_value=None), mock.patch.object(LIFECYCLE_MODULE, "group_members", return_value=[]), mock.patch.object(WORKER_MODULE.os, "killpg") as killpg:
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 0)
            self.assertEqual(LIFECYCLE_MODULE.read_state(self.state)["lifecycle"], "stopped")
            killpg.assert_not_called()

    @unittest.skipUnless(sys.platform == "darwin", "requires Darwin process-family probes")
    def test_launch_gate_eof_exits_before_exec_with_a_dedicated_session_identity(self):
        marker = self.root / "executed"
        process, release = LIFECYCLE_MODULE.gated_process(
            [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"],
            self.cwd,
            stdin_text=None,
        )
        try:
            deadline = time.monotonic() + 1
            identity = None
            while time.monotonic() < deadline:
                identity = LIFECYCLE_MODULE.live_identity(process.pid)
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

    def test_resume_cutpoints_before_family_persistence_preserve_the_terminal_state(self):
        terminal = self.family_state("exited")
        for name, cutpoint in (
            ("before gate", "before gate"),
            ("before family persistence", "before family persistence"),
        ):
            with self.subTest(name=name):
                LIFECYCLE_MODULE.atomic_write(self.state, terminal)
                if cutpoint == "before gate":
                    patches = (
                        mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()),
                        mock.patch.object(LIFECYCLE_MODULE, "gated_process", side_effect=RuntimeError("cutpoint")),
                    )
                    read_fd = None
                else:
                    read_fd, write_fd = os.pipe()
                    process = mock.Mock(pid=41)
                    patches = (
                        mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()),
                        mock.patch.object(LIFECYCLE_MODULE, "gated_process", return_value=(process, write_fd)),
                        mock.patch.object(LIFECYCLE_MODULE, "live_identity", side_effect=RuntimeError("cutpoint")),
                    )
                try:
                    with patches[0], patches[1]:
                        if len(patches) == 3:
                            with patches[2]:
                                with self.assertRaisesRegex(RuntimeError, "cutpoint"):
                                    WORKER_MODULE.resume(self.resume_arguments())
                        else:
                            with self.assertRaisesRegex(RuntimeError, "cutpoint"):
                                WORKER_MODULE.resume(self.resume_arguments())
                finally:
                    if read_fd is not None:
                        os.close(read_fd)
                self.assertEqual(LIFECYCLE_MODULE.read_state(self.state), terminal)

    def test_resume_cutpoint_after_family_persistence_is_settled_without_signaling(self):
        LIFECYCLE_MODULE.atomic_write(self.state, self.family_state("exited"))
        read_fd, write_fd = os.pipe()
        process = mock.Mock(pid=41)
        try:
            with (
                mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()),
                mock.patch.object(LIFECYCLE_MODULE, "gated_process", return_value=(process, write_fd)),
                mock.patch.object(LIFECYCLE_MODULE, "live_identity", return_value=self.identity),
                mock.patch.object(WORKER_MODULE.os, "write", side_effect=RuntimeError("cutpoint")),
            ):
                with self.assertRaisesRegex(RuntimeError, "cutpoint"):
                    WORKER_MODULE.resume(self.resume_arguments())
        finally:
            os.close(read_fd)

        persisted = LIFECYCLE_MODULE.read_state(self.state)
        self.assertEqual(persisted["lifecycle"], "launching")
        self.assertEqual(
            {key: persisted[key] for key in self.identity},
            self.identity,
        )
        with (
            mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()),
            mock.patch.object(LIFECYCLE_MODULE, "live_identity", return_value=None),
            mock.patch.object(LIFECYCLE_MODULE, "group_members", return_value=[]),
            mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
        ):
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 0)
            self.assertEqual(WORKER_MODULE.verify(self.arguments()), 0)
            killpg.assert_not_called()

    def test_resume_cutpoint_after_release_before_running_is_settled_without_signaling(self):
        LIFECYCLE_MODULE.atomic_write(self.state, self.family_state("exited"))
        read_fd, write_fd = os.pipe()
        process = mock.Mock(pid=41)
        try:
            with (
                mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()),
                mock.patch.object(LIFECYCLE_MODULE, "gated_process", return_value=(process, write_fd)),
                mock.patch.object(LIFECYCLE_MODULE, "live_identity", return_value=self.identity),
                mock.patch.object(LIFECYCLE_MODULE, "transition", side_effect=RuntimeError("cutpoint")),
            ):
                with self.assertRaisesRegex(RuntimeError, "cutpoint"):
                    WORKER_MODULE.resume(self.resume_arguments())
            self.assertEqual(os.read(read_fd, 1), b"R")
        finally:
            os.close(read_fd)

        persisted = LIFECYCLE_MODULE.read_state(self.state)
        self.assertEqual(persisted["lifecycle"], "launching")
        with (
            mock.patch.object(LIFECYCLE_MODULE, "_libproc", return_value=object()),
            mock.patch.object(LIFECYCLE_MODULE, "live_identity", return_value=None),
            mock.patch.object(LIFECYCLE_MODULE, "group_members", return_value=[]),
            mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
        ):
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 0)
            self.assertEqual(WORKER_MODULE.verify(self.arguments()), 0)
            killpg.assert_not_called()

    def test_nonterminal_resume_is_rejected_and_legacy_completed_resume_is_accepted_to_launch(self):
        LIFECYCLE_MODULE.atomic_write(self.state, self.family_state("running"))
        with mock.patch.object(LIFECYCLE_MODULE, "run_lifecycle") as launch:
            self.assertNotEqual(WORKER_MODULE.resume(argparse.Namespace(state=self.state, codex="codex", prompt="continue")), 0)
            launch.assert_not_called()
        legacy = {"session_id": "old", "model": "Terra", "sandbox": "read-only", "cwd": str(self.cwd)}
        self.state.write_text(json.dumps(legacy), encoding="utf-8")
        with mock.patch.object(LIFECYCLE_MODULE, "run_lifecycle", return_value=0) as launch:
            self.assertEqual(WORKER_MODULE.resume(argparse.Namespace(state=self.state, codex="codex", prompt="continue")), 0)
            self.assertEqual(launch.call_args.args[2]["lifecycle"], "launching")

    def test_process_family_constants_and_no_global_cleanup_authority(self):
        self.assertEqual(LIFECYCLE_MODULE.BSD_SIZE, 136)
        self.assertEqual(LIFECYCLE_MODULE.VNODE_SIZE, 2352)
        self.assertEqual(LIFECYCLE_MODULE.PROC_PIDTBSDINFO, 3)
        self.assertEqual(LIFECYCLE_MODULE.PROC_PIDVNODEPATHINFO, 9)
        instructions = (ROOT / "skills" / "drivers" / "orchestrate" / "SKILL.md").read_text(encoding="utf-8")
        for path in (WORKER_LIFECYCLE, CODEX_WORKER, CLAUDE_WORKER):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("pkill", source)
            self.assertNotIn("proc_listchildpids", source)
            self.assertNotIn("proc_name", source)
        self.assertIn("Successors never discover or clean", instructions)

    def test_claude_worker_process_family_constants_and_no_global_cleanup_authority(self):
        self.assertIs(WORKER_MODULE.lifecycle, LIFECYCLE_MODULE)
        self.assertIs(CLAUDE_WORKER_MODULE.lifecycle, LIFECYCLE_MODULE)
        codex_error = io.StringIO()
        claude_error = io.StringIO()
        with redirect_stderr(codex_error):
            WORKER_MODULE.fail("probe")
        with redirect_stderr(claude_error):
            CLAUDE_WORKER_MODULE.fail("probe")
        self.assertEqual(codex_error.getvalue(), "codex-worker: probe\n")
        self.assertEqual(claude_error.getvalue(), "claude-worker: probe\n")

    @unittest.skipUnless(sys.platform == "darwin", "requires Darwin process-family probes")
    def test_darwin_probe_contract(self):
        identity = LIFECYCLE_MODULE.live_identity(os.getpid())
        self.assertIsNotNone(identity)
        self.assertEqual(identity["cwd"], str(ROOT.resolve()))
        self.assertIn(os.getpid(), LIFECYCLE_MODULE.group_members(os.getpgrp()))


class ValidatorRegressionTests(unittest.TestCase):
    def test_validator_rejects_seeded_private_term_patterns(self):
        # Built by concatenation, the same defensive way validate.py itself
        # splits these patterns, so this file never carries the literal either.
        cases = (
            ("docs/seed-jira-corp.txt", "j" + "ira.corp" + ".example.net token\n"),
            (
                "docs/seed-jira-ticket-config.txt",
                "~/.config/" + "j" + "ira-ticket/" + "token\n",
            ),
        )
        for relative_path, seeded in cases:
            with self.subTest(relative_path=relative_path):
                with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
                    copy = Path(temporary) / "skills"
                    shutil.copytree(
                        ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__")
                    )
                    self.assertEqual(run(["git", "init"], cwd=copy).returncode, 0)
                    self.assertEqual(run(["git", "add", "."], cwd=copy).returncode, 0)
                    self.assertEqual(
                        run(
                            [
                                "git",
                                "-c",
                                "user.name=Test",
                                "-c",
                                "user.email=test@example.invalid",
                                "commit",
                                "-m",
                                "fixture",
                            ],
                            cwd=copy,
                        ).returncode,
                        0,
                    )

                    clean = run(["python3", "scripts/validate.py"], cwd=copy)
                    self.assertEqual(clean.returncode, 0, clean.stderr)

                    seed = copy / relative_path
                    seed.write_text(seeded, encoding="utf-8")
                    self.assertEqual(
                        run(["git", "add", relative_path], cwd=copy).returncode, 0
                    )

                    result = run(["python3", "scripts/validate.py"], cwd=copy)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(relative_path, result.stderr)

    def test_validator_rejects_an_unquoted_frontmatter_colon(self):
        self.assertEqual(run(["python3", "scripts/validate.py"], cwd=ROOT).returncode, 0)

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            copy = Path(temporary) / "skills"
            shutil.copytree(
                ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__")
            )
            self.assertEqual(run(["git", "init"], cwd=copy).returncode, 0)
            self.assertEqual(run(["git", "add", "."], cwd=copy).returncode, 0)
            self.assertEqual(
                run(
                    [
                        "git",
                        "-c",
                        "user.name=Test",
                        "-c",
                        "user.email=test@example.invalid",
                        "commit",
                        "-m",
                        "fixture",
                    ],
                    cwd=copy,
                ).returncode,
                0,
            )

            skill_path = Path("skills") / "drivers" / "openspec-adopt" / "SKILL.md"
            skill = copy / skill_path
            original = skill.read_text(encoding="utf-8")

            # Reproduce the defect this test guards: a description value that
            # carries ": " but lost its wrapping quotes.
            unquoted = re.sub(
                r'^description:\s*"(.*)"$',
                lambda match: f"description: {match.group(1)}",
                original,
                count=1,
                flags=re.MULTILINE,
            )
            self.assertNotEqual(unquoted, original)
            skill.write_text(unquoted, encoding="utf-8")

            failing = run(["python3", "scripts/validate.py"], cwd=copy)
            self.assertNotEqual(failing.returncode, 0)
            self.assertIn(str(skill_path), failing.stderr)

            skill.write_text(original, encoding="utf-8")
            passing = run(["python3", "scripts/validate.py"], cwd=copy)
            self.assertEqual(passing.returncode, 0, passing.stderr)


class OpenSpecCiContractTests(unittest.TestCase):
    WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"

    def test_ci_installs_the_pinned_openspec_cli(self):
        workflow = self.WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020", workflow)
        self.assertIn('node-version: "20.19.0"', workflow)
        self.assertIn("npm install --global @fission-ai/openspec@1.11.0", workflow)

    def test_ci_strictly_validates_every_openspec_artifact(self):
        workflow = self.WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("openspec validate --all --strict", workflow)


class OpenSpecAdoptionContractTests(unittest.TestCase):
    ADOPTION = ROOT / "skills" / "drivers" / "openspec-adopt" / "SKILL.md"
    ADR_FORMAT = ROOT / "skills" / "tools" / "domain-modeling" / "references" / "ADR-FORMAT.md"
    CHARTER = ROOT / "profile" / "CHARTER.md"
    CONFIG = ROOT / "openspec" / "config.yaml"

    def test_adoption_requires_the_pinned_cli_and_v1_initialization(self):
        adoption = self.ADOPTION.read_text(encoding="utf-8")

        self.assertIn("@fission-ai/openspec@1.11.0", adoption)
        self.assertIn("openspec init --tools none", adoption)
        self.assertIn("stop visibly", adoption)
        self.assertNotIn("npx openspec", adoption)
        self.assertNotIn("by hand", adoption)
        self.assertIn("Do not add generated agent integrations", adoption)
        self.assertIn("`openspec/AGENTS.md`", adoption)
        self.assertIn("`openspec/project.md`", adoption)

    def test_adoption_keeps_baselines_and_makes_archive_guidance_local(self):
        adoption = self.ADOPTION.read_text(encoding="utf-8")
        config = self.CONFIG.read_text(encoding="utf-8")

        self.assertIn("specs/<domain>/spec.md", adoption)
        self.assertIn("operations.archive.guidance", adoption)
        self.assertNotIn("archived in the pull request", adoption)
        self.assertIn("operations:\n  archive:\n    guidance:\n      -", config)
        self.assertIn("After a verified merge, update a clean main checkout to origin/main", config)
        self.assertIn("openspec archive <change-name> --json --yes", config)
        self.assertIn("openspec validate --all --strict", config)
        self.assertIn("Signed-off-by archive commit", config)
        self.assertIn("Push main directly", config)

    def test_readme_and_site_require_the_global_pinned_cli(self):
        readme = README.read_text(encoding="utf-8")
        relationships = (ROOT / "site" / "relationships.py").read_text(encoding="utf-8")

        readme_entry = next(line for line in readme.splitlines() if "openspec-adopt" in line)
        relationships_entry = next(
            line for line in relationships.splitlines() if '"openspec-adopt"' in line
        )
        self.assertIn("@fission-ai/openspec@1.11.0", readme_entry)
        self.assertIn("@fission-ai/openspec@1.11.0", relationships_entry)
        self.assertNotIn("npx openspec", readme)
        self.assertNotIn("npx openspec", relationships)

    def test_active_openspec_changes_are_the_single_adr_home(self):
        charter = self.CHARTER.read_text(encoding="utf-8")
        adr_format = self.ADR_FORMAT.read_text(encoding="utf-8")

        for surface in (charter, adr_format):
            self.assertIn("active OpenSpec changes", surface)
            self.assertIn("design.md", surface)
            self.assertIn("frozen legacy history", surface)
            self.assertIn("Without active OpenSpec changes", surface)
            self.assertNotIn("established `docs/adr/` tree wins", surface)




class DriveLocalWebappSandboxRecoveryTests(unittest.TestCase):
    DRIVER = ROOT / "skills" / "tools" / "drive-local-webapp" / "scripts" / "driver.mjs"
    DARWIN_ERROR = "MachPortRendezvousServer failed: bootstrap_check_in: Permission denied (1100)"
    DARWIN_ERROR_ALT = "Permission denied (1100) while starting MachPortRendezvousServer"
    TIMEOUT_ERROR = "MachPortRendezvousServer timed out"

    FORCE_DARWIN = (
        "import process from 'node:process';\n"
        "Object.defineProperty(process, 'platform', { value: 'darwin' });\n"
    )

    PLAYWRIGHT_PACKAGE_JSON = json.dumps(
        {"name": "playwright", "type": "module", "exports": "./index.js"}
    )

    # PLAYWRIGHT_STUB is controlled by two env vars read at import time:
    #   DRIVER_TEST_LAUNCH_ERROR   the message the first launch() throws
    #   DRIVER_TEST_RETRY_OK       "1" if the --no-sandbox/--single-process
    #                              retry should succeed instead of failing
    PLAYWRIGHT_STUB = """
const launchError = process.env.DRIVER_TEST_LAUNCH_ERROR || "";
const retryOk = process.env.DRIVER_TEST_RETRY_OK === "1";

const page = {
  on() {},
  async goto() {},
  async close() {},
};

const browser = {
  async newPage() {
    return page;
  },
  async close() {},
};

export const chromium = {
  async launch(opts) {
    const args = (opts && opts.args) || [];
    const isSandboxSafeRetry =
      args.includes("--no-sandbox") && args.includes("--single-process");
    if (isSandboxSafeRetry) {
      if (retryOk) return browser;
      throw new Error(launchError);
    }
    throw new Error(launchError);
  },
};
"""

    @classmethod
    def setUpClass(cls):
        if shutil.which("node") is None:
            raise RuntimeError(
                "node is required for DriveLocalWebappSandboxRecoveryTests"
            )

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.scratch = Path(self.temporary.name)

        shutil.copy(self.DRIVER, self.scratch / "driver.mjs")

        playwright_dir = self.scratch / "node_modules" / "playwright"
        playwright_dir.mkdir(parents=True)
        (playwright_dir / "package.json").write_text(
            self.PLAYWRIGHT_PACKAGE_JSON, encoding="utf-8"
        )
        (playwright_dir / "index.js").write_text(
            self.PLAYWRIGHT_STUB, encoding="utf-8"
        )

        self.force_darwin = self.scratch / "force-darwin.mjs"
        self.force_darwin.write_text(self.FORCE_DARWIN, encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def run_driver(self, *, launch_error, retry_ok):
        environment = os.environ.copy()
        environment["DRIVER_TEST_LAUNCH_ERROR"] = launch_error
        environment["DRIVER_TEST_RETRY_OK"] = "1" if retry_ok else "0"
        return subprocess.run(
            ["node", "--import", "./force-darwin.mjs", "driver.mjs"],
            cwd=self.scratch,
            env=environment,
            text=True,
            input="",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )

    def test_mach_port_denial_with_failed_retry_is_blocked(self):
        result = self.run_driver(launch_error=self.DARWIN_ERROR, retry_ok=False)

        self.assertEqual(result.returncode, 77, result.stdout + result.stderr)
        self.assertIn("HEADLESS-SANDBOX-BLOCKED", result.stdout + result.stderr)

    def test_mach_port_denial_alt_phrasing_with_failed_retry_is_blocked(self):
        result = self.run_driver(launch_error=self.DARWIN_ERROR_ALT, retry_ok=False)

        self.assertEqual(result.returncode, 77, result.stdout + result.stderr)
        self.assertIn("HEADLESS-SANDBOX-BLOCKED", result.stdout + result.stderr)

    def test_mach_port_denial_with_successful_retry_proceeds(self):
        result = self.run_driver(launch_error=self.DARWIN_ERROR, retry_ok=True)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("HEADLESS-SANDBOX-BLOCKED", result.stdout + result.stderr)

    def test_unrelated_mach_port_error_is_not_treated_as_sandbox_block(self):
        result = self.run_driver(launch_error=self.TIMEOUT_ERROR, retry_ok=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertNotEqual(result.returncode, 77)
        self.assertNotIn("HEADLESS-SANDBOX-BLOCKED", result.stdout + result.stderr)


class EpicProtocolContractTests(unittest.TestCase):
    RESEARCH = (ROOT / "skills" / "tools" / "research" / "SKILL.md").read_text(encoding="utf-8")
    EPIC = (ROOT / "skills" / "drivers" / "epic" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    TRACKER = (
        ROOT / "skills" / "drivers" / "epic" / "bindings" / "github-issues.md"
    ).read_text(encoding="utf-8")

    def require(self, text, pattern):
        self.assertRegex(text, re.compile(pattern, re.IGNORECASE))

    def test_research_worker_performs_research_directly(self):
        self.require(self.RESEARCH, r"worker performs the research directly")

    def test_research_forbids_recursive_delegation(self):
        self.require(
            self.RESEARCH,
            r"(never|do not) spawn (a |another )?(nested|background )?(agent|worker)",
        )

    def test_epic_names_proposal_design_and_tasks_as_authority(self):
        self.require(self.EPIC, r"proposal\.md.*design\.md.*tasks\.md.*authority")

    def test_epic_change_folder_uses_openspec_authority_and_task_linked_children(self):
        self.require(self.EPIC, r"proposal\.md.*design\.md.*tasks\.md.*authority")
        self.require(self.EPIC, r"tasks\.md.*link.*child issue")
        self.require(self.EPIC, r"live tracker state.*truth.*child")
        self.assertNotIn("ledger.md", self.EPIC)

    def test_named_design_open_questions_replace_fog(self):
        self.require(self.EPIC, r"design\.md.*named open question")
        self.require(self.EPIC, r"open question.*decision.*spike")
        self.assertIn("Do not add pointer-only Notes", self.EPIC)
        self.assertNotIn("## Fog", self.EPIC)

    def test_build_admission_refuses_open_spikes_or_design_questions(self):
        self.require(self.EPIC, r"refuse.*build.*open spike.*open question")
        self.require(self.EPIC, r"invalidate.*outcome.*constraints.*acceptance criteria")

    def test_build_admission_requires_adrs_and_locked_surface_spec(self):
        self.require(self.EPIC, r"load-bearing.*ADR")
        self.require(self.EPIC, r"user-facing.*locked.*ui-craft")

    def test_research_handoff_uses_exact_findings_heading_and_temporary_worktree(self):
        self.assertIn("## Findings", self.EPIC)
        self.require(self.EPIC, r"temporary per-spike worktree")
        self.require(self.EPIC, r"verif.*Findings.*close")
        self.require(self.EPIC, r"removes.*temporary.*unshipped.*only then closes")

    def test_research_close_uses_verified_tracker_evidence(self):
        self.require(self.EPIC, r"close.*spike.*only after.*verification")
        self.require(self.EPIC, r"failed worker.*spike.*dispatched")

    def test_deferred_children_have_explicit_close_out_dispositions(self):
        self.require(self.EPIC, r"promote.*remove.*deferred")
        self.require(self.EPIC, r"reparent.*future epic.*retaining.*deferred")
        self.require(self.EPIC, r"NOT_PLANNED.*remove.*deferred")
        self.require(self.EPIC, r"refuse.*archive.*open.*deferred")

    def test_tracker_bootstraps_the_four_protocol_labels_without_touching_ticket_axis(self):
        self.require(self.TRACKER, r"epic.*spike.*build.*deferred")
        self.require(self.TRACKER, r"ticket:\*.*independent")

    def test_tracker_uses_native_children_and_blocked_by_edges(self):
        self.require(self.TRACKER, r"--add-sub-issue")
        self.require(self.TRACKER, r"--add-blocked-by")

    def test_tracker_has_one_command_follow_up_creation_interface(self):
        self.require(
            self.TRACKER,
            r"gh issue create --repo OWNER/REPO --title.*--body-file.*--label (build|spike).*--parent EPIC_NUMBER",
        )
        self.require(self.TRACKER, r"returned URL.*originating ticket")
        self.require(
            self.TRACKER,
            r"gh issue create --help.*--repo.*--title.*--body-file.*--label.*--parent",
        )

    def test_tracker_reads_child_completion_fields_and_merged_at(self):
        self.require(self.TRACKER, r"subIssues\.nodes")
        self.require(self.TRACKER, r"stateReason")
        self.require(self.TRACKER, r"closedByPullRequestsReferences")
        self.require(self.TRACKER, r"mergedAt")

    def test_completion_checks_are_direct_and_merged_or_not_planned(self):
        self.require(self.TRACKER, r"no open spike child")
        self.require(self.TRACKER, r"merged.*NOT_PLANNED")
        self.require(self.TRACKER, r"no open deferred child")

    def test_epic_close_uses_live_checks_and_repository_archive_guidance(self):
        self.require(self.EPIC, r"completion predicates.*directly from GitHub")
        self.require(self.EPIC, r"repository.*archive guidance")
        self.require(self.EPIC, r"child work.*human-merged")
        self.assertNotIn("planning pull request", self.EPIC.lower())


class EpicAdapterDispatchTests(unittest.TestCase):
    EPIC = ROOT / "skills" / "drivers" / "epic" / "SKILL.md"

    def setUp(self):
        self.text = self.EPIC.read_text(encoding="utf-8")

    def test_research_spike_worker_findings_handoff_is_explicit(self):
        self.assertIn(
            "For a research spike, run `$research` in a temporary per-spike worktree. The worker "
            "returns the required Markdown findings to the home session. The home session writes the "
            "Markdown file required by its public interface, posts that returned content under the exact heading "
            "`## Findings`, verifies the `## Findings` comment, removes the temporary worktree and "
            "its unshipped file, and only then closes the spike.",
            self.text,
        )

    def test_spike_close_order_and_failed_worker_disposition_are_explicit(self):
        self.assertIn("Close the spike issue only after that verification.", self.text)
        self.assertIn("Record the resulting decision in `design.md`", self.text)
        self.assertIn("A failed worker leaves the spike `dispatched`", self.text)

    def test_research_worker_dispatch_stays_on_the_worker_adapters_only(self):
        normalized = " ".join(self.text.split())
        self.assertIn(
            "The coordinator supplies the selected adapter, explicit worker model, and explicit "
            "worker effort. Dispatch only through "
            "`skills/drivers/orchestrate/scripts/codex-worker.py` or "
            "`skills/drivers/orchestrate/scripts/claude-worker.py`. Never use the built-in Agent "
            "tool, Workflow tool, or background-agent machinery.",
            normalized,
        )


class EpicDelegatedExecutionContractTests(unittest.TestCase):
    EPIC = ROOT / "skills" / "drivers" / "epic" / "SKILL.md"

    def test_epic_delegated_execution_keeps_dispatch_and_wave_rules(self):
        epic = " ".join(self.EPIC.read_text(encoding="utf-8").split())
        self.assertIn("It stays at planning altitude", epic)
        self.assertIn("Coordinators do not nest.", epic)
        self.assertIn(
            "The home session dispatches only through the pack adapters, with prompt text "
            "passed positionally from coordinator-owned session-scratch prompt files and one "
            "coordinator-owned state file per dispatch. Do not add adapter flags or alter "
            "adapter mechanics.",
            epic,
        )
        self.assertIn(
            "Collect child results under `orchestrate`'s `## Collect child results` section.",
            epic,
        )


class ReviewRouteResolverTests(unittest.TestCase):
    RESOLVER = ROOT / "skills" / "workflows" / "review" / "scripts" / "resolve_route.py"
    ROUTES_JSON = ROOT / "skills" / "workflows" / "review" / "routes.json"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.scratch = Path(self.temporary.name)
        self.environment = os.environ.copy()
        # A nonexistent operator config is the "no operator rows" case, not an
        # error, so tests that don't care about operator rows can leave this
        # pointed at nothing rather than the real developer home directory.
        self.environment["REVIEW_ROUTES_CONFIG"] = str(self.scratch / "unset-routes.json")
        self.environment["REVIEW_SKILL_ROOTS"] = str(self.scratch / "empty-root")

    def tearDown(self):
        self.temporary.cleanup()

    def resolve(self, *arguments: str, env: Optional[dict[str, str]] = None):
        return run(
            ["python3", str(self.RESOLVER), *arguments],
            cwd=ROOT,
            env=env if env is not None else self.environment,
        )

    def test_installed_route_resolves_to_the_skill_path(self):
        root = self.scratch / "skills-root"
        skill_file = root / "code-review" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("---\nname: code-review\n---\n", encoding="utf-8")
        environment = dict(self.environment, REVIEW_SKILL_ROOTS=str(root))

        result = self.resolve("code", env=environment)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("code-review", result.stdout)
        self.assertIn(str(skill_file), result.stdout)

    def test_registered_route_with_missing_skill_names_the_install_command_only(self):
        result = self.resolve("code")

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("code-review", result.stdout)
        self.assertIn(
            "npx skills add ConnorGriffin/skills --skill code-review", result.stdout
        )
        for other_route in ("plan", "personas", "security"):
            self.assertNotIn(other_route, result.stdout)
        for other_skill in ("plan-review", "persona-review", "security-review"):
            self.assertNotIn(other_skill, result.stdout)

    def test_registered_route_missing_and_not_pack_shipped_names_the_source_file(self):
        operator_config = self.scratch / "routes.json"
        operator_config.write_text(
            json.dumps(
                [
                    {
                        "route": "infra",
                        "skill": "infra-plan-review",
                        "kind": "skill",
                        "for": "a pulumi or terraform plan before it's applied",
                    }
                ]
            ),
            encoding="utf-8",
        )
        environment = dict(self.environment, REVIEW_ROUTES_CONFIG=str(operator_config))

        result = self.resolve("infra", env=environment)

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("infra-plan-review", result.stdout)
        self.assertIn(str(operator_config), result.stdout)
        self.assertNotIn("npx skills add", result.stdout)

    def test_unregistered_name_is_not_a_route_and_lists_registered_names(self):
        result = self.resolve("nonsense")

        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertIn("not a registered review type", result.stdout)
        for route in ("code", "plan", "personas", "security"):
            self.assertIn(route, result.stdout)

    def test_agent_builtin_route_reports_unverified_presence_without_a_path(self):
        result = self.resolve("security")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ships with the agent", result.stdout)
        self.assertIn("not verified", result.stdout)
        self.assertNotIn("SKILL.md", result.stdout)

    def test_operator_config_replaces_a_route_and_adds_a_new_one(self):
        operator_config = self.scratch / "routes.json"
        operator_config.write_text(
            json.dumps(
                [
                    {
                        "route": "code",
                        "skill": "internal-code-review",
                        "kind": "skill",
                        "for": "changed code, using our internal standards checker",
                    },
                    {
                        "route": "infra",
                        "skill": "infra-plan-review",
                        "kind": "skill",
                        "for": "a pulumi or terraform plan before it's applied",
                    },
                ]
            ),
            encoding="utf-8",
        )
        environment = dict(self.environment, REVIEW_ROUTES_CONFIG=str(operator_config))

        result = self.resolve("--list", env=environment)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("code\tinternal-code-review\tskill\t", result.stdout)
        self.assertNotIn("code\tcode-review\tskill\t", result.stdout)
        self.assertIn("infra\tinfra-plan-review\tskill\t", result.stdout)
        self.assertIn("plan\tplan-review\tskill\t", result.stdout)

    def test_malformed_operator_config_invalid_json_exits_2_naming_the_file(self):
        operator_config = self.scratch / "routes.json"
        operator_config.write_text("not json", encoding="utf-8")
        environment = dict(self.environment, REVIEW_ROUTES_CONFIG=str(operator_config))

        result = self.resolve("code", env=environment)

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn(str(operator_config), result.stderr)

    def test_malformed_operator_config_unknown_kind_exits_2(self):
        operator_config = self.scratch / "routes.json"
        operator_config.write_text(
            json.dumps(
                [
                    {
                        "route": "infra",
                        "skill": "infra-plan-review",
                        "kind": "not-a-real-kind",
                        "for": "a pulumi or terraform plan before it's applied",
                    }
                ]
            ),
            encoding="utf-8",
        )
        environment = dict(self.environment, REVIEW_ROUTES_CONFIG=str(operator_config))

        result = self.resolve("--list", env=environment)

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn(str(operator_config), result.stderr)

    def test_symlinked_skill_directory_resolves(self):
        real_root = self.scratch / "real-skills"
        real_skill_file = real_root / "code-review" / "SKILL.md"
        real_skill_file.parent.mkdir(parents=True)
        real_skill_file.write_text("---\nname: code-review\n---\n", encoding="utf-8")
        linked_root = self.scratch / "linked-skills"
        linked_root.mkdir()
        (linked_root / "code-review").symlink_to(
            real_root / "code-review", target_is_directory=True
        )
        environment = dict(self.environment, REVIEW_SKILL_ROOTS=str(linked_root))

        result = self.resolve("code", env=environment)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(linked_root / "code-review" / "SKILL.md"), result.stdout)

    def test_shipped_routes_are_exactly_four_and_each_names_a_for_sentence(self):
        rows = json.loads(self.ROUTES_JSON.read_text(encoding="utf-8"))
        routes = {row["route"] for row in rows}

        self.assertEqual(routes, {"code", "plan", "personas", "security"})
        for row in rows:
            self.assertEqual(set(row), {"route", "skill", "kind", "for"})
            self.assertIsInstance(row["for"], str)
            self.assertTrue(row["for"].strip())


class UiCraftCliMainGuardTests(unittest.TestCase):
    """Every ui-craft CLI runs the same way through a symlinked skill directory.

    Skill packs are installed by symlink, so a CLI whose main guard compares raw
    path strings exits 0 without running. `route.mjs` is pinned against its own
    documented output; the other four are pinned differentially, against
    themselves, so no baseline is invented for output this repo never recorded.
    """

    UI_CRAFT = ROOT / "skills" / "drivers" / "ui-craft"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workdir = Path(self.temporary.name)
        self.linked = self.workdir / "ui-craft-link"
        self.linked.symlink_to(self.UI_CRAFT, target_is_directory=True)

    def script(self, *parts: str) -> tuple[Path, Path]:
        """The same script by its real path and through the symlinked directory."""
        relative = Path("scripts").joinpath(*parts)
        return self.UI_CRAFT / relative, self.linked / relative

    def test_route_prints_its_decision_through_a_symlinked_skill_directory(self):
        cases = (
            (("greenfield", "runnable", "complete", "manufactured"), 0, "lock"),
            (("shipped", "unavailable", "complete", "synthetic"), 2, "refuse"),
        )
        _, linked_route = self.script("route.mjs")
        for arguments, exit_code, mode in cases:
            with self.subTest(arguments=arguments):
                result = run(
                    [
                        "node",
                        str(linked_route),
                        "--embodiment",
                        arguments[0],
                        "--runnability",
                        arguments[1],
                        "--declaration",
                        arguments[2],
                        "--data-source",
                        arguments[3],
                    ],
                    cwd=self.workdir,
                )
                self.assertEqual(result.returncode, exit_code, result.stderr)
                self.assertEqual(json.loads(result.stdout)["mode"], mode)

    def assert_symlink_parity(
        self, parts: tuple[str, ...], arguments: list[str], suffix: str = ""
    ):
        """One read-only invocation run twice: by real path, then through the link.

        Non-emptiness is load-bearing. Bare parity is satisfied by two silent
        runs, so a guard that never fires would pass this test green — the very
        defect being repaired.

        `suffix` is appended to the path as a string, after pathlib is done with
        it: pathlib strips a trailing separator, which would silently turn the
        trailing-separator case into a rerun of the plain one.
        """
        real, linked = self.script(*parts)
        real_run = run(["node", f"{real}{suffix}", *arguments], cwd=self.workdir)
        linked_run = run(["node", f"{linked}{suffix}", *arguments], cwd=self.workdir)
        self.assertTrue(real_run.stdout.strip(), real_run.stderr)
        self.assertEqual(linked_run.stdout, real_run.stdout, linked_run.stderr)
        self.assertEqual(linked_run.returncode, real_run.returncode, linked_run.stderr)

    def test_migrated_clis_behave_identically_through_a_symlinked_directory(self):
        cases = (
            (("context-signals.mjs",), []),
            (("context.mjs",), []),
            (("critique-storage.mjs",), ["trend", "no-such-target"]),
            (("detector", "detect-antipatterns.mjs"), ["--help"]),
        )
        for parts, arguments in cases:
            with self.subTest(script=parts[-1]):
                self.assert_symlink_parity(parts, arguments)

    def test_detector_entry_path_arrives_normalized_with_a_trailing_separator(self):
        """Pins the invariant that let the `endsWith('...mjs/')` clause be deleted.

        Node normalizes the entry path before the module sees it, so
        `process.argv[1]` never carries a trailing separator. If a future runtime
        stops normalizing, this fails loudly instead of exiting 0 in silence.
        """
        self.assert_symlink_parity(
            ("detector", "detect-antipatterns.mjs"), ["--help"], suffix="/"
        )


class WorkerEgressConsentContractTests(unittest.TestCase):
    TICKET_SKILL = ROOT / "skills" / "drivers" / "ticket" / "SKILL.md"
    ORCHESTRATE_SKILL = ROOT / "skills" / "drivers" / "orchestrate" / "SKILL.md"
    TICKET_PROMPT = ROOT / "skills" / "drivers" / "ticket" / "agents" / "openai.yaml"
    ORCHESTRATE_PROMPT = (
        ROOT / "skills" / "drivers" / "orchestrate" / "agents" / "openai.yaml"
    )
    DISPATCH_REFERENCES = {
        "codex-ui": (
            ROOT
            / "skills"
            / "drivers"
            / "orchestrate"
            / "references"
            / "dispatch-codex.md",
            "OpenAI's Codex model service",
        ),
        "claude-to-codex": (
            ROOT
            / "skills"
            / "drivers"
            / "orchestrate"
            / "references"
            / "dispatch-codex-from-claude.md",
            "OpenAI's Codex model service",
        ),
        "claude-to-claude": (
            ROOT
            / "skills"
            / "drivers"
            / "orchestrate"
            / "references"
            / "dispatch-claude.md",
            "Anthropic's Claude model service",
        ),
    }

    @staticmethod
    def text(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def compact(text: str) -> str:
        return " ".join(text.split()).lower()

    @staticmethod
    def frontmatter_description(source: str) -> str:
        frontmatter = source.split("---\n", 2)[1]
        return next(
            line.removeprefix("description:").strip().strip('"')
            for line in frontmatter.splitlines()
            if line.startswith("description:")
        )

    def section(self, source: str, heading: str) -> str:
        anchor = f"{heading}\n\n"
        self.assertIn(anchor, source)
        body = source.split(anchor, 1)[1]
        return body.split("\n\n## ", 1)[0]

    def assert_material_boundary(self, text: str, destination: str) -> None:
        compact = self.compact(text)
        for term in (
            "work order or task prompt",
            "repository code and documentation",
            destination,
            "credentials",
            "secrets",
            "patient data",
            "`.env`",
            "real database contents",
        ):
            with self.subTest(term=term):
                self.assertIn(term.lower(), compact)
        self.assertIn(
            "credentials, secrets, patient data, `.env`, and real database contents are excluded",
            compact,
        )

    def assert_cross_parent_boundary(self, text: str) -> None:
        self.assert_material_boundary(text, "OpenAI's Codex model service")
        compact = self.compact(text)
        self.assertIn("anthropic's claude model service", compact)
        self.assertIn("codex ui parent", compact)
        self.assertIn("claude code parent", compact)

    def test_ticket_catalog_and_invocation_declare_bounded_consent(self):
        source = self.text(self.TICKET_SKILL)
        description = self.frontmatter_description(source)
        invocation = self.section(source, "## Invocation")

        for surface in (description, invocation):
            self.assert_cross_parent_boundary(surface)
            surface = self.compact(surface)
            self.assertIn("mandatory worker dispatch", surface)
            self.assertIn("nested review", surface)
            self.assertIn("nested orchestrate", surface)
            self.assertIn("automatic activation", surface)
            self.assertIn("asks once", surface)
        self.assertIn("triage", invocation)
        self.assertIn("start", invocation)
        self.assertIn("revise", invocation)
        self.assertIn("finalize", invocation)
        self.assertIn("no worker-egress consent", invocation)
        self.assertIn("triage, start, revise, finalize", description)
        self.assertIn("ticket id", description)
        self.assertNotIn("disable-model-invocation: true", source)

    def test_orchestrate_catalog_and_invocation_declare_bounded_consent(self):
        source = self.text(self.ORCHESTRATE_SKILL)
        description = self.frontmatter_description(source)
        invocation = self.section(source, "## Invocation")

        for surface in (description, invocation):
            self.assert_cross_parent_boundary(surface)
            surface = self.compact(surface)
            self.assertIn("mandatory worker dispatch", surface)
            self.assertIn("nested review", surface)
            self.assertIn("nested orchestrate", surface)
            self.assertIn("automatic activation", surface)
            self.assertIn("asks once", surface)
        self.assertIn("guardian-facing declaration", invocation)
        self.assertIn("not a platform-policy override", invocation)
        self.assertIn("not a byte filter", invocation)
        self.assertIn("parent agent plans, scopes, reviews, and ships", description)
        self.assertIn("asks the parent to act as an orchestrator/coordinator", description)
        self.assertNotIn("disable-model-invocation: true", source)

    def test_openai_default_prompts_request_the_openai_specific_transfer(self):
        for path in (self.TICKET_PROMPT, self.ORCHESTRATE_PROMPT):
            with self.subTest(path=path):
                prompt = self.text(path)
                self.assert_material_boundary(prompt, "OpenAI's Codex model service")
                self.assertIn("mandatory worker dispatch", prompt)
                self.assertNotIn("Anthropic's Claude model service", prompt)
        ticket_prompt = self.compact(self.text(self.TICKET_PROMPT))
        self.assertIn("triage, start, or revise", ticket_prompt)
        self.assertIn("triage, start, revise, or finalize", ticket_prompt)
        self.assertIn("finalize does not request", ticket_prompt)

    def test_adapter_approval_rationales_repeat_boundary_without_making_authority(self):
        for name, (path, destination) in self.DISPATCH_REFERENCES.items():
            with self.subTest(reference=name):
                rationale = self.section(self.text(path), "## Approval rationale")
                self.assert_material_boundary(rationale, destination)
                rationale = self.compact(rationale)
                self.assertIn("invoked ticket or orchestrate workflow", rationale)
                self.assertIn("every mandatory worker dispatch", rationale)
                self.assertIn("escalation justification", rationale)
                self.assertIn("assistant-authored rationale", rationale)
                self.assertIn("does not itself create user authorization", rationale)
                self.assertIn("when no invoked workflow supplies the consent", rationale)
                self.assertIn("stop and ask once before dispatch", rationale)


class DelegationAuthorityContractTests(unittest.TestCase):
    CODE_REVIEW = (ROOT / "skills" / "tools" / "code-review" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    PLAN_REVIEW = (ROOT / "skills" / "tools" / "plan-review" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    TICKET = (ROOT / "skills" / "drivers" / "ticket" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    TRIAGE = (ROOT / "skills" / "drivers" / "ticket" / "verbs" / "triage.md").read_text(
        encoding="utf-8"
    )
    PERSONA_REVIEW = (
        ROOT / "skills" / "tools" / "persona-review" / "SKILL.md"
    ).read_text(encoding="utf-8")

    ENTRY_POINTS = (CODE_REVIEW, PLAN_REVIEW, TICKET)
    AUTHORIZATION = "authorizes every sub-agent dispatch that this procedure marks mandatory"
    DISCRETIONARY_ONLY = (
        'Do not ask again solely because a session-level preference says "do not spawn '
        'agents"; apply that preference to discretionary delegation only.'
    )
    REFUSAL_STOPS_WORKFLOW = (
        "An explicit task-level refusal of this required review or revocation of "
        "delegation overrides this authorization: stop and state that the requested "
        "workflow cannot run without its required independent review."
    )

    def test_all_required_review_entry_points_authorize_mandatory_dispatch(self):
        for skill in self.ENTRY_POINTS:
            self.assertIn(self.AUTHORIZATION, skill)

    def test_session_preference_leaves_required_dispatch_authorized(self):
        for skill in self.ENTRY_POINTS:
            self.assertIn(self.DISCRETIONARY_ONLY, skill)

    def test_explicit_refusal_or_revocation_stops_required_review_workflow(self):
        for skill in self.ENTRY_POINTS:
            self.assertIn(self.REFUSAL_STOPS_WORKFLOW, skill)

    def test_persona_review_keeps_conditional_serial_fallback_without_authority(self):
        self.assertNotIn(self.AUTHORIZATION, self.PERSONA_REVIEW)
        self.assertIn(
            "Where adapter dispatch isn't available, review personas serially in the main session",
            self.PERSONA_REVIEW,
        )

    def test_ticket_authority_covers_triage_plan_review(self):
        self.assertIn("triage's mandatory `/plan-review`", self.TICKET)

    def test_triage_points_to_ticket_authority_without_repeating_it(self):
        self.assertIn("ticket skill page's `## Delegation authority` section", self.TRIAGE)
        self.assertNotIn(self.AUTHORIZATION, self.TRIAGE)


class LiveProseContractTests(unittest.TestCase):
    def test_reviewer_routing_and_admission_rules_remain_explicit(self):
        routing = (ROOT / "skills/drivers/orchestrate/references/review-routing.md").read_text(encoding="utf-8")
        dispatch = (ROOT / "skills/drivers/orchestrate/references/dispatch-codex.md").read_text(encoding="utf-8")
        normalized_routing = " ".join(routing.split())
        self.assertIn("sole live authority for reviewer classification", normalized_routing)
        self.assertIn("A Codex parent follows its own session policy", normalized_routing)
        self.assertIn("cannot switch to Claude workers", dispatch)
        self.assertIn("headroom at or below 5%", dispatch)

    def test_review_depth_and_slicing_keep_their_load_bearing_rules(self):
        depth = (ROOT / "skills/drivers/ticket/references/review-depth.md").read_text(encoding="utf-8")
        slicing = (ROOT / "skills/drivers/ticket/references/slicing.md").read_text(encoding="utf-8")
        self.assertIn("Full-depth orders keep one review round", " ".join(depth.split()))
        self.assertIn(
            "The coordinator never launches an agent smarter than itself.",
            " ".join(slicing.split()),
        )


class FieldRoutingFindingsContractTests(unittest.TestCase):
    ROUTING_TABLE = ROOT / "skills/drivers/orchestrate/references/routing-table.md"
    ORCHESTRATE = ROOT / "skills/drivers/orchestrate/SKILL.md"

    def test_field_findings_keep_benchmark_routes_and_provenance_distinct(self):
        table = self.ROUTING_TABLE.read_text(encoding="utf-8")

        self.assertIn("## Provenance labels", table)
        self.assertIn("field-validated (provisional)", table)
        self.assertIn("may not displace a benchmarked route's ordering", table)

    def test_render_evidence_requires_a_vision_capable_reviewer(self):
        table = self.ROUTING_TABLE.read_text(encoding="utf-8")

        self.assertIn("Any review whose evidence is rendered output needs a vision-capable reviewer", table)
        self.assertIn("Codex-family reviewers cannot", table)

    def test_executable_evidence_repairs_route_on_execution_access(self):
        table = self.ROUTING_TABLE.read_text(encoding="utf-8")

        self.assertIn("Executable-evidence repair", table)
        self.assertIn("execution access", table)
        self.assertIn("not model tier", table)

    def test_browser_failure_briefs_include_probe_and_environment_preflight(self):
        instructions = self.ORCHESTRATE.read_text(encoding="utf-8")

        self.assertIn("Before any browser-failure dispatch", instructions)
        self.assertIn("served projection and rendered DOM", instructions)
        self.assertIn("environment preflight", instructions)

    def test_completed_sol_replay_keeps_the_benchmarked_review_routes(self):
        table = " ".join(self.ROUTING_TABLE.read_text(encoding="utf-8").split())

        self.assertIn("Benchmarked replay (2026-08-27", table)
        self.assertIn("Sol's mechanical score was 1 against Luna's 2", table)
        self.assertIn("neither Codex model caught the subtle boundary defect", table)
        self.assertIn("does not out-detect Luna on planted defects at five times the price", table)


if __name__ == "__main__":
    unittest.main()
