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
CBM_TEARDOWN = ROOT / "skills" / "tools" / "cbm-onboard" / "scripts" / "cbm-teardown.sh"
SPIN_SCRIPT = ROOT / "skills" / "tools" / "spin-worktree" / "scripts" / "spin-worktree.py"
CODEX_WORKER = ROOT / "skills" / "drivers" / "orchestrate" / "scripts" / "codex-worker.py"
UI_CRAFT_AUDIT = ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "audit.md"
UI_CRAFT_CRITIQUE = ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "critique.md"
UI_CRAFT_SWEEP = ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "behavior-sweep.md"
UI_CRAFT_ROUTE = ROOT / "skills" / "drivers" / "ui-craft" / "scripts" / "route.mjs"
README = ROOT / "README.md"
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

    def portable_state(self, generation=1):
        return {
            "version": WORKER_MODULE.STATE_VERSION,
            "lifecycle": "exited",
            "session_id": "worker-1",
            "model": "Terra",
            "sandbox": "read-only",
            "cwd": str(self.cwd),
            "family_semantics": WORKER_MODULE.FAMILY_SEMANTICS_UNSUPPORTED,
            "generation": generation,
        }

    def arguments(self):
        return argparse.Namespace(state=self.state, cwd=self.cwd, grace_seconds=0.01)

    def resume_arguments(self):
        return argparse.Namespace(state=self.state, codex="codex", prompt="continue")

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
                    WORKER_MODULE.atomic_write(self.state, state)
                    error = io.StringIO()
                    with (
                        mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()) as libproc,
                        mock.patch.object(WORKER_MODULE, "gated_process") as gated,
                        mock.patch.object(WORKER_MODULE, "live_identity") as identity,
                        mock.patch.object(WORKER_MODULE, "group_members") as members,
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
                    WORKER_MODULE.atomic_write(self.state, state)
                    error = io.StringIO()
                    with (
                        mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()) as libproc,
                        mock.patch.object(WORKER_MODULE, "gated_process") as gated,
                        mock.patch.object(WORKER_MODULE, "live_identity") as identity,
                        mock.patch.object(WORKER_MODULE, "group_members") as members,
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
        WORKER_MODULE.atomic_write(self.state, self.family_state())
        for operation in (WORKER_MODULE.stop, WORKER_MODULE.verify):
            with self.subTest(operation=operation.__name__):
                error = io.StringIO()
                with (
                    mock.patch.object(WORKER_MODULE, "_libproc", return_value=None),
                    mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
                    redirect_stderr(error),
                ):
                    self.assertEqual(operation(self.arguments()), 1)
                self.assertEqual(
                    error.getvalue(),
                    f"codex-worker: {WORKER_MODULE.UNSUPPORTED}\n",
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
            mock.patch.object(WORKER_MODULE, "_libproc", return_value=None),
            mock.patch.object(WORKER_MODULE.subprocess, "run", return_value=completed) as run_worker,
            mock.patch.object(WORKER_MODULE, "gated_process") as gated,
            mock.patch.object(WORKER_MODULE, "latest_rate_limits", return_value=None),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(WORKER_MODULE.start(arguments), 0)

        state = WORKER_MODULE.read_state(self.state)
        self.assertEqual(state["version"], WORKER_MODULE.STATE_VERSION)
        self.assertEqual(state["lifecycle"], "exited")
        self.assertEqual(state["session_id"], "worker-1")
        self.assertEqual(state["family_semantics"], "unsupported")
        self.assertEqual(state["generation"], 1)
        self.assertFalse({"pid", "pgid", "sid", "birth"} & set(state))
        run_worker.assert_called_once()
        gated.assert_not_called()

        refusal = io.StringIO()
        with (
            mock.patch.object(WORKER_MODULE, "_libproc", return_value=None),
            mock.patch.object(WORKER_MODULE.subprocess, "run", return_value=completed) as resume_worker,
            mock.patch.object(WORKER_MODULE, "gated_process") as resume_gate,
            mock.patch.object(WORKER_MODULE, "latest_rate_limits", return_value=None),
            mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
            redirect_stdout(io.StringIO()),
            redirect_stderr(refusal),
        ):
            self.assertEqual(WORKER_MODULE.resume(self.resume_arguments()), 0)
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 1)
            self.assertEqual(WORKER_MODULE.verify(self.arguments()), 1)

        resumed = WORKER_MODULE.read_state(self.state)
        self.assertTrue(WORKER_MODULE.valid_portable_schema(resumed))
        self.assertEqual(resumed["generation"], 2)
        self.assertIn("resume", resume_worker.call_args.args[0])
        resume_gate.assert_not_called()
        self.assertEqual(
            refusal.getvalue(),
            f"codex-worker: {WORKER_MODULE.UNSUPPORTED}\n" * 2,
        )
        killpg.assert_not_called()

        with (
            mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()),
            mock.patch.object(WORKER_MODULE, "live_identity") as identity,
            mock.patch.object(WORKER_MODULE, "group_members") as members,
            mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
            redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 1)
            self.assertEqual(WORKER_MODULE.verify(self.arguments()), 1)
        identity.assert_not_called()
        members.assert_not_called()
        killpg.assert_not_called()

    def test_already_exited_leader_with_empty_group_stops_without_a_signal(self):
        WORKER_MODULE.atomic_write(self.state, self.family_state())
        with mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()), mock.patch.object(WORKER_MODULE, "live_identity", return_value=None), mock.patch.object(WORKER_MODULE, "group_members", return_value=[]), mock.patch.object(WORKER_MODULE.os, "killpg") as killpg:
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 0)
            self.assertEqual(WORKER_MODULE.read_state(self.state)["lifecycle"], "stopped")
            killpg.assert_not_called()

    @unittest.skipUnless(sys.platform == "darwin", "requires Darwin process-family probes")
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

    def test_resume_cutpoints_before_family_persistence_preserve_the_terminal_state(self):
        terminal = self.family_state("exited")
        for name, cutpoint in (
            ("before gate", "before gate"),
            ("before family persistence", "before family persistence"),
        ):
            with self.subTest(name=name):
                WORKER_MODULE.atomic_write(self.state, terminal)
                if cutpoint == "before gate":
                    patches = (
                        mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()),
                        mock.patch.object(WORKER_MODULE, "gated_process", side_effect=RuntimeError("cutpoint")),
                    )
                    read_fd = None
                else:
                    read_fd, write_fd = os.pipe()
                    process = mock.Mock(pid=41)
                    patches = (
                        mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()),
                        mock.patch.object(WORKER_MODULE, "gated_process", return_value=(process, write_fd)),
                        mock.patch.object(WORKER_MODULE, "live_identity", side_effect=RuntimeError("cutpoint")),
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
                self.assertEqual(WORKER_MODULE.read_state(self.state), terminal)

    def test_resume_cutpoint_after_family_persistence_is_settled_without_signaling(self):
        WORKER_MODULE.atomic_write(self.state, self.family_state("exited"))
        read_fd, write_fd = os.pipe()
        process = mock.Mock(pid=41)
        try:
            with (
                mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()),
                mock.patch.object(WORKER_MODULE, "gated_process", return_value=(process, write_fd)),
                mock.patch.object(WORKER_MODULE, "live_identity", return_value=self.identity),
                mock.patch.object(WORKER_MODULE.os, "write", side_effect=RuntimeError("cutpoint")),
            ):
                with self.assertRaisesRegex(RuntimeError, "cutpoint"):
                    WORKER_MODULE.resume(self.resume_arguments())
        finally:
            os.close(read_fd)

        persisted = WORKER_MODULE.read_state(self.state)
        self.assertEqual(persisted["lifecycle"], "launching")
        self.assertEqual(
            {key: persisted[key] for key in self.identity},
            self.identity,
        )
        with (
            mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()),
            mock.patch.object(WORKER_MODULE, "live_identity", return_value=None),
            mock.patch.object(WORKER_MODULE, "group_members", return_value=[]),
            mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
        ):
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 0)
            self.assertEqual(WORKER_MODULE.verify(self.arguments()), 0)
            killpg.assert_not_called()

    def test_resume_cutpoint_after_release_before_running_is_settled_without_signaling(self):
        WORKER_MODULE.atomic_write(self.state, self.family_state("exited"))
        read_fd, write_fd = os.pipe()
        process = mock.Mock(pid=41)
        try:
            with (
                mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()),
                mock.patch.object(WORKER_MODULE, "gated_process", return_value=(process, write_fd)),
                mock.patch.object(WORKER_MODULE, "live_identity", return_value=self.identity),
                mock.patch.object(WORKER_MODULE, "transition", side_effect=RuntimeError("cutpoint")),
            ):
                with self.assertRaisesRegex(RuntimeError, "cutpoint"):
                    WORKER_MODULE.resume(self.resume_arguments())
            self.assertEqual(os.read(read_fd, 1), b"R")
        finally:
            os.close(read_fd)

        persisted = WORKER_MODULE.read_state(self.state)
        self.assertEqual(persisted["lifecycle"], "launching")
        with (
            mock.patch.object(WORKER_MODULE, "_libproc", return_value=object()),
            mock.patch.object(WORKER_MODULE, "live_identity", return_value=None),
            mock.patch.object(WORKER_MODULE, "group_members", return_value=[]),
            mock.patch.object(WORKER_MODULE.os, "killpg") as killpg,
        ):
            self.assertEqual(WORKER_MODULE.stop(self.arguments()), 0)
            self.assertEqual(WORKER_MODULE.verify(self.arguments()), 0)
            killpg.assert_not_called()

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

    def test_process_family_constants_and_no_global_cleanup_authority(self):
        self.assertEqual(WORKER_MODULE.BSD_SIZE, 136)
        self.assertEqual(WORKER_MODULE.VNODE_SIZE, 2352)
        self.assertEqual(WORKER_MODULE.PROC_PIDTBSDINFO, 3)
        self.assertEqual(WORKER_MODULE.PROC_PIDVNODEPATHINFO, 9)
        source = CODEX_WORKER.read_text(encoding="utf-8")
        instructions = (ROOT / "skills" / "drivers" / "orchestrate" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("pkill", source)
        self.assertNotIn("proc_listchildpids", source)
        self.assertNotIn("proc_name", source)
        self.assertIn("Successors never discover or clean", instructions)

    @unittest.skipUnless(sys.platform == "darwin", "requires Darwin process-family probes")
    def test_darwin_probe_contract(self):
        identity = WORKER_MODULE.live_identity(os.getpid())
        self.assertIsNotNone(identity)
        self.assertEqual(identity["cwd"], str(ROOT.resolve()))
        self.assertIn(os.getpid(), WORKER_MODULE.group_members(os.getpgrp()))


class EvidenceEnvelopeTests(unittest.TestCase):
    def test_examples_use_upstream_wire_tags_and_integer_time(self):
        positive = ROOT / "docs" / "evidence" / "examples" / "positive.json"
        observations = json.loads(positive.read_text(encoding="utf-8"))["observations"]

        self.assertEqual(
            {item["envelope_kind"] for item in observations},
            {"failure_observation", "producer_fact"},
        )
        self.assertTrue(
            all(
                isinstance(item["observed_at"], int)
                and not isinstance(item["observed_at"], bool)
                for item in observations
            )
        )

    def mutated_validation(self, mutate):
        # The fixture commit can leave a hook or an auto-gc still writing under
        # .git when the block exits, so cleanup races the fixture's own repo.
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
            positive = copy / "docs" / "evidence" / "examples" / "positive.json"
            payload = json.loads(positive.read_text(encoding="utf-8"))
            mutate(payload)
            positive.write_text(json.dumps(payload), encoding="utf-8")

            return run(["python3", "scripts/validate.py"], cwd=copy)

    def test_v2_contract_and_provenance_are_vendored(self):
        evidence = ROOT / "docs" / "evidence"

        self.assertTrue((evidence / "contract-v2.json").is_file())
        self.assertTrue((evidence / "contract-v2.provenance.json").is_file())

    def test_validator_rejects_a_mutated_vendored_contract(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            copy = Path(temporary) / "skills"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            self.assertEqual(run(["git", "init"], cwd=copy).returncode, 0)
            self.assertEqual(run(["git", "add", "."], cwd=copy).returncode, 0)
            self.assertEqual(
                run(
                    ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture"],
                    cwd=copy,
                ).returncode,
                0,
            )
            contract = copy / "docs" / "evidence" / "contract-v2.json"
            contract.write_text("{}\n", encoding="utf-8")

            result = run(["python3", "scripts/validate.py"], cwd=copy)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contract-v2.json", result.stderr)

    def test_validator_rejects_mutated_contract_provenance(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            copy = Path(temporary) / "skills"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            self.assertEqual(run(["git", "init"], cwd=copy).returncode, 0)
            self.assertEqual(run(["git", "add", "."], cwd=copy).returncode, 0)
            self.assertEqual(run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture"], cwd=copy).returncode, 0)
            provenance = copy / "docs" / "evidence" / "contract-v2.provenance.json"
            payload = json.loads(provenance.read_text(encoding="utf-8"))
            payload["source_git_blob"] = "0" * 40
            provenance.write_text(json.dumps(payload), encoding="utf-8")

            result = run(["python3", "scripts/validate.py"], cwd=copy)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("provenance", result.stderr)

    def test_validator_rejects_a_candidate_presented_as_an_observation(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            copy = Path(temporary) / "skills"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            self.assertEqual(run(["git", "init"], cwd=copy).returncode, 0)
            self.assertEqual(run(["git", "add", "."], cwd=copy).returncode, 0)
            self.assertEqual(
                run(
                    ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture"],
                    cwd=copy,
                ).returncode,
                0,
            )
            positive = copy / "docs" / "evidence" / "examples" / "positive.json"
            payload = json.loads(positive.read_text(encoding="utf-8"))
            producer = next(
                item for item in payload["observations"] if "producer" in item
            )
            producer["producer"]["producer_kind"] = "candidate"
            positive.write_text(json.dumps(payload), encoding="utf-8")

            result = run(["python3", "scripts/validate.py"], cwd=copy)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("producer_kind", result.stderr)

    def test_validator_reports_a_non_object_negative_fixture(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            copy = Path(temporary) / "skills"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            self.assertEqual(run(["git", "init"], cwd=copy).returncode, 0)
            self.assertEqual(run(["git", "add", "."], cwd=copy).returncode, 0)
            self.assertEqual(run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture"], cwd=copy).returncode, 0)
            negative = copy / "docs" / "evidence" / "examples" / "negative.json"
            payload = json.loads(negative.read_text(encoding="utf-8"))
            payload["invalid_observations"][0] = []
            negative.write_text(json.dumps(payload), encoding="utf-8")

            result = run(["python3", "scripts/validate.py"], cwd=copy)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture does not reject a prohibited kind", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_validator_rejects_extra_failure_fields(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            copy = Path(temporary) / "skills"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            self.assertEqual(run(["git", "init"], cwd=copy).returncode, 0)
            self.assertEqual(run(["git", "add", "."], cwd=copy).returncode, 0)
            self.assertEqual(run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture"], cwd=copy).returncode, 0)
            positive = copy / "docs" / "evidence" / "examples" / "positive.json"
            payload = json.loads(positive.read_text(encoding="utf-8"))
            failure = next(
                item
                for item in payload["observations"]
                if item["envelope_kind"] == "failure_observation"
            )
            failure["unexpected"] = "field"
            positive.write_text(json.dumps(payload), encoding="utf-8")

            result = run(["python3", "scripts/validate.py"], cwd=copy)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failure_observation envelope", result.stderr)

    def test_validator_rejects_a_missing_producer_kind(self):
        def remove_kind(payload):
            payload["observations"] = [
                item
                for item in payload["observations"]
                if item.get("producer", {}).get("producer_kind") != "criterion"
            ]

        result = self.mutated_validation(remove_kind)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("producer kind matrix", result.stderr)

    def test_validator_rejects_a_missing_failure_class(self):
        def remove_class(payload):
            payload["observations"] = [
                item
                for item in payload["observations"]
                if item.get("failure", {}).get("failure_class") != "plan_gap"
            ]

        result = self.mutated_validation(remove_class)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failure class matrix", result.stderr)

    def test_validator_rejects_a_missing_required_relation(self):
        def remove_relation(payload):
            fix = next(
                item
                for item in payload["observations"]
                if item.get("producer", {}).get("producer_kind") == "fix"
            )
            fix["links"] = [
                link for link in fix["links"] if link["relation"] != "addresses"
            ]

        result = self.mutated_validation(remove_relation)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required lineage", result.stderr)

    def test_validator_rejects_illegal_lineage_direction(self):
        def reverse_governing_direction(payload):
            criterion = next(
                item
                for item in payload["observations"]
                if item.get("producer", {}).get("producer_kind") == "criterion"
            )
            criterion["links"][0]["relation"] = "governs"

        result = self.mutated_validation(reverse_governing_direction)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("illegal lineage direction", result.stderr)

    def test_validator_rejects_a_duplicate_observation_id(self):
        def duplicate_id(payload):
            payload["observations"][1]["observation_id"] = payload["observations"][0][
                "observation_id"
            ]

        result = self.mutated_validation(duplicate_id)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate observation_id", result.stderr)

    def test_validator_reports_an_unhashable_observation_id(self):
        def replace_id(payload):
            payload["observations"][0]["observation_id"] = {}

        result = self.mutated_validation(replace_id)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("observation_id must follow the upstream ID grammar", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_validator_rejects_a_sparse_link_ordinal(self):
        def sparse_ordinal(payload):
            linked = next(item for item in payload["observations"] if item.get("links"))
            linked["links"][0]["ordinal"] = len(linked["links"]) + 1

        result = self.mutated_validation(sparse_ordinal)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dense ordinals", result.stderr)

    def test_validator_reports_unhashable_lineage_fields(self):
        for field in ("relation", "target_event_id"):
            with self.subTest(field=field):
                def replace_field(payload, field=field):
                    linked = next(
                        item for item in payload["observations"] if item.get("links")
                    )
                    linked["links"][0][field] = {}

                result = self.mutated_validation(replace_field)

                self.assertNotEqual(result.returncode, 0)
                expected = (
                    "link fields or relation are invalid"
                    if field == "relation"
                    else "target_event_id must follow the upstream ID grammar"
                )
                self.assertIn(expected, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_validator_rejects_snapshot_confusion_at_one_head(self):
        def confuse_snapshots(payload):
            snapshots = [
                item["subject"]
                for item in payload["observations"]
                if item.get("subject", {}).get("subject", "").startswith("base:")
            ]
            snapshots[1]["revision"] = snapshots[0]["revision"]

        result = self.mutated_validation(confuse_snapshots)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("distinct dirty snapshots", result.stderr)

    def test_validator_rejects_snapshot_head_source_confusion(self):
        def confuse_head(payload):
            for item in payload["observations"]:
                subject = item.get("subject", {})
                if subject.get("subject", "").startswith("base:"):
                    subject["subject"] = subject["subject"].replace(
                        "head:" + "b" * 40, "head:" + "c" * 40
                    )

        result = self.mutated_validation(confuse_head)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("snapshot head must match source revision", result.stderr)

    def test_validator_rejects_short_envelope_tags(self):
        for original, short in (
            ("failure_observation", "failure"),
            ("producer_fact", "producer"),
        ):
            with self.subTest(short=short):
                def shorten(payload, original=original, short=short):
                    item = next(
                        observation
                        for observation in payload["observations"]
                        if observation["envelope_kind"] == original
                    )
                    item["envelope_kind"] = short

                result = self.mutated_validation(shorten)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid envelope_kind", result.stderr)

    def test_validator_rejects_string_and_bool_observed_at(self):
        for invalid in ("1786662000", True):
            with self.subTest(invalid=invalid):
                def replace_time(payload, invalid=invalid):
                    payload["observations"][0]["observed_at"] = invalid

                result = self.mutated_validation(replace_time)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("observed_at must be a nonnegative integer", result.stderr)

    def test_validator_rejects_sha256_prefixed_digest_fields(self):
        def producer_digest(payload):
            item = next(observation for observation in payload["observations"] if "producer" in observation)
            item["producer"]["fact_digest"] = "sha256:" + item["producer"]["fact_digest"]

        def failure_digest(payload):
            item = next(observation for observation in payload["observations"] if "failure" in observation)
            item["failure"]["signature_digest"] = "sha256:" + item["failure"]["signature_digest"]

        def source_digest(payload):
            item = payload["observations"][0]
            item["source"]["content_hash"] = "sha256:" + item["source"]["content_hash"]

        def subject_digest(payload):
            item = next(observation for observation in payload["observations"] if "content_digest" in observation["subject"])
            item["subject"]["content_digest"] = "sha256:" + item["subject"]["content_digest"]

        for mutate in (producer_digest, failure_digest, source_digest, subject_digest):
            with self.subTest(field=mutate.__name__):
                result = self.mutated_validation(mutate)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("raw lowercase hex", result.stderr)

    def test_validator_rejects_wrong_subject_and_source_kinds(self):
        def wrong_subject(payload):
            payload["observations"][0]["subject"]["subject_kind"] = "git_commit"

        def wrong_source(payload):
            payload["observations"][0]["source"]["authority_kind"] = "git"

        for mutate, message in (
            (wrong_subject, "invalid subject_kind"),
            (wrong_source, "invalid source authority_kind"),
        ):
            with self.subTest(field=mutate.__name__):
                result = self.mutated_validation(mutate)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)

    def test_validator_rejects_nullable_or_extra_review_action(self):
        def nullable(payload):
            item = next(
                observation
                for observation in payload["observations"]
                if observation.get("producer", {}).get("producer_kind") == "review_action"
            )
            item["producer"]["review_action"] = None

        def extra(payload):
            item = next(
                observation
                for observation in payload["observations"]
                if observation.get("producer", {}).get("producer_kind") == "claim"
            )
            item["producer"]["review_action"] = None

        for mutate in (nullable, extra):
            with self.subTest(field=mutate.__name__):
                result = self.mutated_validation(mutate)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("review_action", result.stderr)

    def test_validator_rejects_extra_parent_and_fixer_fields(self):
        def add_fixer_lineage(payload):
            item = next(
                observation
                for observation in payload["observations"]
                if observation.get("failure", {}).get("failure_class") == "original_defect"
            )
            item["failure"]["reviewed_parent_revision"] = "b" * 40
            item["failure"]["fixer_revision"] = "c" * 40

        result = self.mutated_validation(add_fixer_lineage)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failure fields are not closed", result.stderr)

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


class WayfinderResearchDispatchHandshakeTests(unittest.TestCase):
    RESEARCH = (ROOT / "skills" / "tools" / "research" / "SKILL.md").read_text(encoding="utf-8")
    WAYFINDER = (ROOT / "skills" / "drivers" / "wayfinder" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    TRACKER = (
        ROOT / "skills" / "drivers" / "wayfinder" / "references" / "github-tracker.md"
    ).read_text(encoding="utf-8")

    def require(self, text, pattern):
        self.assertRegex(text, re.compile(pattern, re.IGNORECASE))

    def test_research_recognizes_it_is_already_running_in_a_worker(self):
        self.require(self.RESEARCH, r"already (a )?(spawned|background|subagent)")

    def test_research_forbids_recursive_delegation(self):
        self.require(
            self.RESEARCH,
            r"(never|do not) spawn (a |another )?(nested|background )?(agent|worker)",
        )

    def test_wayfinder_supervises_launched_workers_to_a_terminal_outcome(self):
        self.require(
            self.WAYFINDER, r"(supervise|wait for).*(terminal|completion|complete)"
        )

    def test_wayfinder_releases_a_failed_workers_claim(self):
        self.require(
            self.WAYFINDER,
            r"if a worker fails or is interrupted,\s+release its `wayfinder:resolving` claim",
        )

    def test_tracker_excludes_awaiting_disposition_from_the_frontier(self):
        self.require(
            self.TRACKER,
            r"wayfinder:awaiting-disposition.*excluded from the frontier",
        )

    def test_wayfinder_reconciles_every_awaiting_disposition_child(self):
        self.require(
            self.WAYFINDER,
            r"reconcile every one carrying `wayfinder:awaiting-disposition`",
        )

    def test_tracker_map_index_is_not_the_authoritative_pending_queue(self):
        self.require(
            self.TRACKER,
            r"durable queue; `Awaiting disposition` is its map index",
        )

    def test_wayfinder_defines_structured_candidate_envelope(self):
        self.require(self.WAYFINDER, r"wayfinder_findings:")

    def test_wayfinder_candidate_identity_is_stable_replay_identity(self):
        self.require(
            self.WAYFINDER, r"not titles or list position, are the replay identity"
        )

    def test_wayfinder_map_only_link_does_not_count_as_durable_handoff(self):
        self.require(
            self.WAYFINDER,
            r"map (link|Handoffs entry) alone.*(never|does not).*count",
        )

    def test_wayfinder_must_not_close_with_undisposed_candidates(self):
        self.require(
            self.WAYFINDER,
            r"close.*only after every.*candidate.*(disposed|disposition)",
        )

    def test_wayfinder_build_issue_carries_candidate_identity_marker(self):
        self.require(self.WAYFINDER, r"Wayfinder candidate:")

    def test_tracker_candidate_identity_is_copied_into_handoff_or_disposition(self):
        self.require(
            self.TRACKER,
            r"exact candidate identity copied into each Build Issue or disposition",
        )

    def test_tracker_validates_a_disposition_before_treating_it_complete(self):
        self.require(
            self.TRACKER,
            r"disposition comment as complete only when.*candidate",
        )

    def test_tracker_complete_disposition_retains_its_trigger(self):
        self.require(self.TRACKER, r"required observable trigger")

    def test_tracker_complete_disposition_retains_its_verification_condition(self):
        self.require(self.TRACKER, r"verification condition")

    def test_tracker_documents_in_place_repair_edit(self):
        self.require(self.TRACKER, r"issues/comments/COMMENT_ID")

    def test_wayfinder_workers_must_not_unconditionally_close_tickets(self):
        self.assertNotRegex(
            self.WAYFINDER,
            re.compile(r"claims, researches, comments, closes", re.IGNORECASE),
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


if __name__ == "__main__":
    unittest.main()
