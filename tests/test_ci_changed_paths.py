import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ci_changed_paths.py"
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"


def run(command, *, cwd=None, check=True):
    return subprocess.run(
        command,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
    )


class ChangedPathsCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        run(["git", "init", "-q"], cwd=self.repo)
        run(["git", "config", "user.email", "fixture@example.com"], cwd=self.repo)
        run(["git", "config", "user.name", "Fixture"], cwd=self.repo)
        (self.repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        run(["git", "add", "."], cwd=self.repo)
        run(["git", "commit", "-qm", "seed"], cwd=self.repo)
        self.base = run(["git", "rev-parse", "HEAD"], cwd=self.repo).stdout.strip()

    def tearDown(self):
        self.temporary.cleanup()

    def commit(self, changes):
        for relative_path, content in changes.items():
            path = self.repo / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        run(["git", "add", "-A"], cwd=self.repo)
        run(["git", "commit", "-qm", "fixture change"], cwd=self.repo)
        return run(["git", "rev-parse", "HEAD"], cwd=self.repo).stdout.strip()

    def classify(
        self, *, event="pull_request", base=None, head=None, output=None, repo=None
    ):
        output = output or (Path(self.temporary.name) / "github-output")
        result = run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo",
                str(repo or self.repo),
                "--event",
                event,
                "--base",
                base or self.base,
                "--head",
                head or "HEAD",
                "--github-output",
                str(output),
            ],
            check=False,
        )
        value = output.read_text(encoding="utf-8").strip() if output.is_file() else None
        return result, value

    def test_documentation_only_pull_requests_skip_expensive_work(self):
        safe_paths = (
            "README.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "LICENSE",
            "NOTICE",
            "docs/adr/adr-143-example.md",
            "docs/scope/example.md",
            "docs/overlay.md",
            "openspec/changes/epic-rework/ledger.md",
        )
        head = self.commit({path: "documentation\n" for path in safe_paths})

        result, output = self.classify(head=head)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "run_expensive=false")

    def test_unsafe_and_mixed_pull_requests_run_expensive_work(self):
        for relative_path in (
            "docs/render_comparison.py",
            "skills/drivers/ticket/SKILL.md",
            "scripts/validate.py",
            "tests/test_ticket.py",
            ".github/workflows/validate.yml",
        ):
            with self.subTest(relative_path=relative_path):
                head = self.commit({relative_path: "changed\n"})
                result, output = self.classify(base=f"{head}^", head=head)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output, "run_expensive=true")

        head = self.commit({"docs/adr/safe.md": "safe\n", "tools/unsafe.txt": "unsafe\n"})
        result, output = self.classify(base=f"{head}^", head=head)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "run_expensive=true")

    def test_rename_and_deletion_classify_both_sides_of_the_change(self):
        unsafe = self.repo / "scripts" / "tool.py"
        unsafe.parent.mkdir(parents=True)
        unsafe.write_text("print('unsafe')\n", encoding="utf-8")
        run(["git", "add", "-A"], cwd=self.repo)
        run(["git", "commit", "-qm", "add unsafe"], cwd=self.repo)
        before_rename = run(["git", "rev-parse", "HEAD"], cwd=self.repo).stdout.strip()
        safe = self.repo / "docs" / "tool.md"
        safe.parent.mkdir(parents=True)
        os.rename(unsafe, safe)
        run(["git", "add", "-A"], cwd=self.repo)
        run(["git", "commit", "-qm", "rename across boundary"], cwd=self.repo)

        result, output = self.classify(base=before_rename)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "run_expensive=true")

        before_delete = run(["git", "rev-parse", "HEAD"], cwd=self.repo).stdout.strip()
        (self.repo / "seed.txt").unlink()
        run(["git", "add", "-A"], cwd=self.repo)
        run(["git", "commit", "-qm", "delete unsafe"], cwd=self.repo)
        result, output = self.classify(base=before_delete)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "run_expensive=true")

    def test_non_pr_empty_and_invalid_diffs_fail_closed_to_full_work(self):
        for event, base, head in (
            ("push", self.base, "HEAD"),
            ("pull_request", "HEAD", "HEAD"),
            ("pull_request", "missing-ref", "HEAD"),
        ):
            with self.subTest(event=event, base=base, head=head):
                result, output = self.classify(event=event, base=base, head=head)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output, "run_expensive=true")

    def test_pull_request_diff_uses_the_merge_base_not_the_moving_base_tip(self):
        advanced_base = self.commit({"scripts/base-only.py": "print('base')\n"})
        run(["git", "checkout", "-q", self.base], cwd=self.repo)
        head = self.commit({"docs/pr-only.md": "documentation\n"})

        result, output = self.classify(base=advanced_base, head=head)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "run_expensive=false")

    def test_repository_discovery_failure_fails_closed_when_output_is_writable(self):
        missing_repo = Path(self.temporary.name) / "not-a-repository"

        result, output = self.classify(repo=missing_repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "run_expensive=true")

    def test_missing_classifier_input_fails_closed_when_output_is_writable(self):
        output = Path(self.temporary.name) / "github-output"
        result = run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo",
                str(self.repo),
                "--event",
                "pull_request",
                "--head",
                "HEAD",
                "--github-output",
                str(output),
            ],
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_text(encoding="utf-8").strip(), "run_expensive=true")

    def test_malformed_input_recovers_equals_form_github_output(self):
        output = Path(self.temporary.name) / "github-output"
        result = run(
            [
                sys.executable,
                str(SCRIPT),
                "--bogus",
                f"--github-output={output}",
            ],
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_text(encoding="utf-8").strip(), "run_expensive=true")

    def test_output_transport_failure_is_visible(self):
        output = Path(self.temporary.name) / "missing" / "github-output"

        result, written = self.classify(event="push", output=output)

        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(written)
        self.assertIn("ci-changed-paths: cannot write GitHub output", result.stderr)
        self.assertNotIn("can't open file", result.stderr)


class ValidateWorkflowContractTests(unittest.TestCase):
    EXPENSIVE_STEPS = (
        "Fresh-install through the standard skills CLI",
        "Verify installed skills",
        "Install pinned browser driver dependencies",
        "Run browser driver self-check",
    )
    CLASSIFIER_CONDITION = "steps.changed-paths.outputs.run_expensive != 'false'"

    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding="utf-8")

    def step(self, name):
        marker = f"      - name: {name}\n"
        start = self.workflow.index(marker)
        end = self.workflow.find("      - name:", start + len(marker))
        return self.workflow[start : None if end == -1 else end]

    def test_required_skills_job_and_classifier_are_unconditional(self):
        self.assertIn("  pull_request:\n", self.workflow)
        self.assertNotIn("paths:", self.workflow)
        self.assertNotIn("paths-ignore:", self.workflow)
        self.assertIn("  skills:\n    runs-on:", self.workflow)
        self.assertNotIn("\n        if:", self.step("Classify changed paths"))

    def test_classifier_is_the_single_output_producer_after_unconditional_checks(self):
        classifier = self.step("Classify changed paths")
        self.assertEqual(self.workflow.count("id: changed-paths"), 1)
        self.assertIn('python3 scripts/ci_changed_paths.py', classifier)
        self.assertIn('--event "${{ github.event_name }}"', classifier)
        self.assertIn('--base "${{ github.event.pull_request.base.sha }}"', classifier)
        self.assertIn('--head "${{ github.event.pull_request.head.sha }}"', classifier)
        self.assertIn('--github-output "$GITHUB_OUTPUT"', classifier)
        self.assertLess(
            self.workflow.index("Check Python, JavaScript, and shell syntax"),
            self.workflow.index("Classify changed paths"),
        )

    def test_every_expensive_step_uses_the_same_classifier_condition(self):
        conditions = []
        for name in self.EXPENSIVE_STEPS:
            step = self.step(name)
            self.assertIn(f"if: {self.CLASSIFIER_CONDITION}", step)
            conditions.append(
                next(line.strip() for line in step.splitlines() if line.strip().startswith("if:"))
            )
        self.assertEqual(conditions, [f"if: {self.CLASSIFIER_CONDITION}"] * 4)


if __name__ == "__main__":
    unittest.main()
