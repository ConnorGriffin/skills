from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_SCRIPT = ROOT / "skills" / "pr-body" / "scripts" / "pr_body_receipt.py"
# The gate is a hook, so it lives with the machine's other hooks rather than in
# this pack. Point PR_BODY_GATE_HOOK at a working copy to test it before install;
# otherwise these tests run against the installed hook, or skip.
HOOK = Path(
    os.environ.get("PR_BODY_GATE_HOOK", Path.home() / ".claude" / "hooks" / "pr-body-gate")
)

BODY = "Grows the appliance data volume from 2TB to 4TB.\n"


def run_hook(command: str, cwd: Path, home: Path) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_input": {"command": command}, "cwd": str(cwd)})
    env = dict(os.environ)
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
        timeout=5,
    )


def run_hook_raw(stdin_text: str, cwd: Path, home: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
        timeout=5,
        cwd=str(cwd),
    )


def deny_reason(result: subprocess.CompletedProcess) -> Optional[str]:
    stdout = result.stdout.strip()
    if not stdout:
        return None
    payload = json.loads(stdout)
    return payload["hookSpecificOutput"]["permissionDecisionReason"]


def write_receipt(body_file: Path, home: Path) -> None:
    env = dict(os.environ)
    env["HOME"] = str(home)
    result = subprocess.run(
        [sys.executable, str(RECEIPT_SCRIPT), "write", str(body_file)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@unittest.skipUnless(
    HOOK.exists(),
    f"gate hook not found at {HOOK}; set PR_BODY_GATE_HOOK to a working copy",
)
class GateTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.cwd = Path(self.temporary.name)
        self.home = self.cwd / "home"
        self.home.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def write_body(self, name: str, text: str = BODY) -> Path:
        path = self.cwd / name
        path.write_text(text, encoding="utf-8")
        return path


class ValidReceiptTests(GateTestCase):
    def test_body_file_with_a_valid_receipt_is_allowed(self):
        body = self.write_body("body.md")
        write_receipt(body, self.home)
        result = run_hook(f"gh pr create --body-file {body.name}", self.cwd, self.home)
        self.assertIsNone(deny_reason(result))

    def test_pr_edit_with_a_valid_receipt_is_allowed(self):
        body = self.write_body("body.md")
        write_receipt(body, self.home)
        result = run_hook(
            f"gh pr edit 5 --body-file {body.name}", self.cwd, self.home
        )
        self.assertIsNone(deny_reason(result))

    def test_short_flag_and_equals_form_are_both_recognized(self):
        body = self.write_body("body.md")
        write_receipt(body, self.home)
        for command in (f"gh pr create -F{body.name}", f"gh pr create --body-file={body.name}"):
            with self.subTest(command=command):
                result = run_hook(command, self.cwd, self.home)
                self.assertIsNone(deny_reason(result))


class NoReceiptTests(GateTestCase):
    def test_body_file_with_no_receipt_denies(self):
        body = self.write_body("body.md")
        result = run_hook(f"gh pr create --body-file {body.name}", self.cwd, self.home)
        reason = deny_reason(result)
        self.assertIsNotNone(reason)
        self.assertIn("no scoring receipt", reason)
        self.assertIn("pr-body skill", reason)


class StaleReceiptTests(GateTestCase):
    def test_editing_the_body_after_scoring_denies_and_names_the_edit(self):
        body = self.write_body("body.md")
        write_receipt(body, self.home)
        body.write_text(BODY + "One more sentence.\n", encoding="utf-8")
        result = run_hook(f"gh pr create --body-file {body.name}", self.cwd, self.home)
        reason = deny_reason(result)
        self.assertIsNotNone(reason)
        self.assertIn("changed since it was scored", reason)


class UnreadableBodyFormTests(GateTestCase):
    def test_a_missing_body_file_denies_as_unreadable(self):
        result = run_hook("gh pr create --body-file does-not-exist.md", self.cwd, self.home)
        reason = deny_reason(result)
        self.assertIsNotNone(reason)
        self.assertIn("cannot read", reason)


class BypassShapeTests(GateTestCase):
    """One assertion per way the body flag can dodge the receipt check."""

    def test_inline_body_text_denies(self):
        result = run_hook('gh pr create --body "some inline text"', self.cwd, self.home)
        self.assertIsNotNone(deny_reason(result))

    def test_body_from_a_shell_variable_denies(self):
        result = run_hook('gh pr create --body "$BODY"', self.cwd, self.home)
        self.assertIsNotNone(deny_reason(result))

    def test_body_from_a_command_substitution_denies(self):
        result = run_hook('gh pr create --body "$(cat f.md)"', self.cwd, self.home)
        self.assertIsNotNone(deny_reason(result))

    def test_body_from_a_heredoc_denies(self):
        command = (
            'gh pr create --body "$(cat <<'"'"'EOF'"'"'\n'
            "some heredoc body\n"
            'EOF\n'
            ')"'
        )
        result = run_hook(command, self.cwd, self.home)
        self.assertIsNotNone(deny_reason(result))

    def test_fill_denies(self):
        result = run_hook("gh pr create --fill", self.cwd, self.home)
        self.assertIsNotNone(deny_reason(result))

    def test_bypass_deny_reason_names_body_file(self):
        result = run_hook('gh pr create --body "inline"', self.cwd, self.home)
        reason = deny_reason(result)
        self.assertIn("--body-file", reason)


class ApiPullRequestTests(GateTestCase):
    def test_api_post_to_a_pulls_collection_denies(self):
        result = run_hook(
            "gh api repos/o/r/pulls -X POST -f title=x -f body=y", self.cwd, self.home
        )
        reason = deny_reason(result)
        self.assertIsNotNone(reason)
        self.assertIn("gh api", reason)

    def test_api_patch_to_a_specific_pull_denies(self):
        result = run_hook(
            "gh api repos/o/r/pulls/12 -X PATCH -f body=y", self.cwd, self.home
        )
        self.assertIsNotNone(deny_reason(result))

    def test_api_post_without_explicit_dash_x_still_denies(self):
        # gh switches its default method from GET to POST once a data flag
        # is present, with no explicit -X required.
        result = run_hook("gh api repos/o/r/pulls -f title=x -f body=y", self.cwd, self.home)
        self.assertIsNotNone(deny_reason(result))

    def test_api_get_against_pulls_is_allowed(self):
        result = run_hook("gh api repos/o/r/pulls", self.cwd, self.home)
        self.assertIsNone(deny_reason(result))


class ScopeTests(GateTestCase):
    def test_a_non_gh_command_is_allowed(self):
        result = run_hook('git commit -m "unrelated change"', self.cwd, self.home)
        self.assertIsNone(deny_reason(result))

    def test_pr_edit_that_does_not_touch_the_body_is_allowed(self):
        result = run_hook("gh pr edit 5 --add-label needs-review", self.cwd, self.home)
        self.assertIsNone(deny_reason(result))

    def test_pr_list_is_out_of_scope_and_allowed(self):
        result = run_hook("gh pr list --state open", self.cwd, self.home)
        self.assertIsNone(deny_reason(result))


class MalformedPayloadTests(GateTestCase):
    def test_malformed_json_payload_denies(self):
        result = run_hook_raw("not valid json", self.cwd, self.home)
        reason = deny_reason(result)
        self.assertIsNotNone(reason)
        self.assertIn("hook payload", reason)


class RobustnessTests(GateTestCase):
    def test_hook_never_exits_nonzero(self):
        result = run_hook_raw("not valid json", self.cwd, self.home)
        self.assertEqual(result.returncode, 0)

    def test_hook_never_prints_to_stderr_on_normal_input(self):
        result = run_hook('git status', self.cwd, self.home)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
