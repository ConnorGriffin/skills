"""Behavior tests for scripts/check_dco.py.

Drives the script as a subprocess against a throwaway fixture git repository,
following tests/test_pr_body_gate.py's pattern of testing a script rather than
importing it as a module.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_dco.py"

SIGNED_TRAILER = "Signed-off-by: Test Author <author@example.com>\n"


def git(*arguments: str, cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *arguments],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=True,
    )


def run_check(base: str, head: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), base, head],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class CheckDcoTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        git("init", "--quiet", cwd=self.repo)
        git("config", "user.name", "Test Author", cwd=self.repo)
        git("config", "user.email", "author@example.com", cwd=self.repo)
        # Suppress any interactive editor a merge commit might otherwise open
        # on a machine without one configured.
        self.env = dict(os.environ)
        self.env["GIT_MERGE_AUTOEDIT"] = "no"
        self.env["GIT_EDITOR"] = "true"

    def tearDown(self):
        self.temporary.cleanup()

    def commit(self, name: str, message: str) -> str:
        path = self.repo / name
        path.write_text(name, encoding="utf-8")
        git("add", name, cwd=self.repo)
        git("commit", "--quiet", "-m", message, cwd=self.repo, env=self.env)
        return git("rev-parse", "HEAD", cwd=self.repo, env=self.env).stdout.strip()

    def merge_branches(self, other_branch: str, message: str) -> str:
        """Create an unsigned two-parent merge commit onto the current branch."""
        git(
            "merge",
            "--no-ff",
            "--no-edit",
            "-m",
            message,
            other_branch,
            cwd=self.repo,
            env=self.env,
        )
        return git("rev-parse", "HEAD", cwd=self.repo, env=self.env).stdout.strip()


class MergeCommitIsSkippedTests(CheckDcoTestCase):
    def test_signed_authored_commit_plus_unsigned_merge_commit_passes(self):
        """A range whose head is an unsigned merge commit still passes, because
        --no-merges skips it. This one fixture shape stands in for both
        observed triggers (the button-pushed merge commit from #105 and the
        stale-base synthetic merge commit from #111): check_dco.py cannot
        distinguish them, both are unsigned merge commits GitHub authored,
        and --no-merges skips both identically.
        """
        base = self.commit("base.txt", "base commit\n\n" + SIGNED_TRAILER)
        git("checkout", "--quiet", "-b", "feature", cwd=self.repo, env=self.env)
        self.commit("feature.txt", "authored change\n\n" + SIGNED_TRAILER)
        git("checkout", "--quiet", "-b", "main-advance", base, cwd=self.repo, env=self.env)
        self.commit("main.txt", "unrelated main advance\n\n" + SIGNED_TRAILER)
        git("checkout", "--quiet", "feature", cwd=self.repo, env=self.env)
        head = self.merge_branches(
            "main-advance", "Merge branch 'main' into feature"
        )

        result = run_check(base, head, self.repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DCO_OK", result.stdout)

    def test_unsigned_authored_commit_still_fails_even_with_a_merge_commit_present(self):
        base = self.commit("base.txt", "base commit\n\n" + SIGNED_TRAILER)
        git("checkout", "--quiet", "-b", "feature", cwd=self.repo, env=self.env)
        unsigned = self.commit("feature.txt", "authored change with no trailer\n")
        git("checkout", "--quiet", "-b", "main-advance", base, cwd=self.repo, env=self.env)
        self.commit("main.txt", "unrelated main advance\n\n" + SIGNED_TRAILER)
        git("checkout", "--quiet", "feature", cwd=self.repo, env=self.env)
        head = self.merge_branches(
            "main-advance", "Merge branch 'main' into feature"
        )

        result = run_check(base, head, self.repo)

        self.assertEqual(result.returncode, 1)
        self.assertIn(unsigned, result.stderr)


class NoMergeCommitsInRangeTests(CheckDcoTestCase):
    def test_range_with_no_merge_commits_and_all_signed_still_passes(self):
        base = self.commit("base.txt", "base commit\n\n" + SIGNED_TRAILER)
        self.commit("one.txt", "first authored change\n\n" + SIGNED_TRAILER)
        head = self.commit("two.txt", "second authored change\n\n" + SIGNED_TRAILER)

        result = run_check(base, head, self.repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DCO_OK commits=2", result.stdout)


if __name__ == "__main__":
    unittest.main()
