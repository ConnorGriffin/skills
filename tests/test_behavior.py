from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
CBM_SCRIPT = ROOT / "skills" / "cbm-onboard" / "scripts" / "cbm-onboard.sh"
SPIN_SCRIPT = ROOT / "skills" / "spin-worktree" / "scripts" / "spin-worktree.py"
BEGIN_IGNORE = "# >>> cbm-onboard managed baseline — do not edit inside this block >>>"
BEGIN_HOOK = "# >>> cbm-onboard managed reindex >>>"


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


if __name__ == "__main__":
    unittest.main()
