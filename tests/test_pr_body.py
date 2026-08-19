from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "tools" / "pr-body" / "scripts" / "pr_body_lint.py"
SKILL_MD = ROOT / "skills" / "tools" / "pr-body" / "SKILL.md"
RUBRIC_MD = ROOT / "skills" / "tools" / "pr-body" / "references" / "rubric.md"

DISCLOSURE = "> Written by an AI agent operating for <operator>. Verify before relying on it."
LEGACY_DISCLOSURE = "This PR was written in part with the assistance of generative AI."


def lint(body: str, *, repo: Optional[Path] = None) -> dict:
    command = [sys.executable, str(SCRIPT), "--json"]
    if repo is not None:
        command.extend(["--repo", str(repo)])
    result = subprocess.run(
        command,
        input=body,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=5,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise AssertionError(
            f"non-JSON output (exit {result.returncode}): "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        ) from error


def rules_fired(result: dict) -> set[str]:
    return {finding["rule"] for finding in result["findings"]}


def finding_for(result: dict, rule: str) -> dict:
    for finding in result["findings"]:
        if finding["rule"] == rule:
            return finding
    raise AssertionError(f"rule {rule!r} did not fire: {result}")


class EmptyBodyTests(unittest.TestCase):
    def test_trips_on_empty_and_whitespace_only_bodies(self):
        for body in ("", "   ", "\n\n  \n"):
            with self.subTest(body=repr(body)):
                result = lint(body)
                self.assertEqual(result["verdict"], "fail")
                self.assertIn("empty-body", rules_fired(result))

    def test_does_not_trip_on_a_real_body(self):
        body = f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertNotIn("empty-body", rules_fired(result))

    def test_fix_text_is_an_instruction(self):
        result = lint("")
        finding = finding_for(result, "empty-body")
        self.assertIn("state", finding["fix"].lower())


class AiDisclosureMissingTests(unittest.TestCase):
    def test_trips_when_no_disclosure_is_present(self):
        body = "Grows the appliance data volume from 2TB to 4TB.\n"
        result = lint(body)
        self.assertEqual(result["verdict"], "fail")
        self.assertIn("ai-disclosure-missing", rules_fired(result))

    def test_does_not_trip_on_the_suggested_wording(self):
        body = f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertNotIn("ai-disclosure-missing", rules_fired(result))

    def test_does_not_trip_on_the_legacy_sentence_form(self):
        # The old plain-sentence disclosure still satisfies the rule: it
        # matches the same loose pattern, and retro-failing bodies written
        # before the blockquote convention would be pure audit noise.
        body = f"Grows the appliance data volume from 2TB to 4TB.\n\n{LEGACY_DISCLOSURE}\n"
        result = lint(body)
        self.assertNotIn("ai-disclosure-missing", rules_fired(result))

    def test_does_not_trip_on_a_differently_worded_disclosure(self):
        body = (
            "Grows the appliance data volume from 2TB to 4TB.\n\n"
            "Written with AI assistance.\n"
        )
        result = lint(body)
        self.assertNotIn("ai-disclosure-missing", rules_fired(result))

    def test_fix_text_supplies_the_blockquote_form(self):
        result = lint("Grows the appliance data volume from 2TB to 4TB.\n")
        finding = finding_for(result, "ai-disclosure-missing")
        self.assertIn("written by an ai agent operating for", finding["fix"].lower())

    def test_disclosure_blockquote_is_exempt_from_prose_density_rules(self):
        # The scaffolding mask keys on an AI term plus an assist verb
        # anywhere in the line, not on the leading "> ", so a blockquote
        # disclosure carrying density-rule bait (an em dash, a rated
        # verdict) must still be masked out rather than flagged.
        body = (
            "Grows the appliance data volume from 2TB to 4TB.\n\n"
            "> Written by an AI agent operating for <operator> — this is a "
            "low-risk change. Verify before relying on it.\n"
        )
        result = lint(body)
        self.assertNotIn("em-dash", rules_fired(result))
        self.assertNotIn("verdict-clause", rules_fired(result))
        self.assertNotIn("ai-disclosure-missing", rules_fired(result))


class EmptyTemplateSectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        (self.repo / ".github").mkdir()
        (self.repo / ".github" / "pull_request_template.md").write_text(
            "## What does this PR do?\n\n## Testing\n\n## Jira ticket number?\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_trips_when_a_template_section_is_left_unfilled(self):
        # The empty section sits before another heading, not at the very
        # end, so it is not the exempt trailing-metadata case.
        body = (
            "## What does this PR do?\n\n"
            f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n\n"
            "## Testing\n\n"
            "## Jira ticket number?\n\nDEVOPS-1234\n"
        )
        result = lint(body, repo=self.repo)
        self.assertEqual(result["verdict"], "fail")
        self.assertIn("empty-template-section", rules_fired(result))

    def test_does_not_trip_when_every_section_is_filled(self):
        body = (
            "## What does this PR do?\n\n"
            f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n\n"
            "## Testing\n\nResources: 1 to update.\n\n"
            "## Jira ticket number?\n\nDEVOPS-1234\n"
        )
        result = lint(body, repo=self.repo)
        self.assertNotIn("empty-template-section", rules_fired(result))

    def test_does_not_trip_when_only_the_trailing_section_is_empty(self):
        # An empty final section is almost always optional metadata (a
        # ticket link with no ticket); it is not the abandoned-template
        # failure this rule targets.
        body = (
            "## What does this PR do?\n\n"
            f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n\n"
            "## Jira ticket number?\n"
        )
        result = lint(body, repo=self.repo)
        self.assertNotIn("empty-template-section", rules_fired(result))

    def test_fix_text_names_the_empty_heading(self):
        body = (
            "## What does this PR do?\n\n"
            f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n\n"
            "## Testing\n\n"
            "## Jira ticket number?\n\nDEVOPS-1234\n"
        )
        result = lint(body, repo=self.repo)
        finding = finding_for(result, "empty-template-section")
        self.assertIn("Testing", finding["fix"])


class VacuousOpenerTests(unittest.TestCase):
    def test_trips_on_googles_named_bad_openers(self):
        for opener in ("Fix bug", "Fix build", "Add patch", "Phase 1"):
            with self.subTest(opener=opener):
                body = f"{opener}.\n\n{DISCLOSURE}\n"
                result = lint(body)
                self.assertIn("vacuous-opener", rules_fired(result), body)

    def test_does_not_trip_on_a_real_opener(self):
        body = f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertNotIn("vacuous-opener", rules_fired(result))

    def test_fix_text_asks_for_the_actual_behavior(self):
        result = lint(f"Fix bug.\n\n{DISCLOSURE}\n")
        finding = finding_for(result, "vacuous-opener")
        self.assertIn("behavior", finding["fix"].lower())


class EmDashTests(unittest.TestCase):
    def test_trips_on_an_em_dash(self):
        body = f"Grows the volume — it was near capacity.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertIn("em-dash", rules_fired(result))

    def test_does_not_trip_without_one(self):
        body = f"Grows the volume; it was near capacity.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertNotIn("em-dash", rules_fired(result))

    def test_fix_text_asks_for_a_rewrite(self):
        result = lint(f"Grows the volume — it was near capacity.\n\n{DISCLOSURE}\n")
        finding = finding_for(result, "em-dash")
        self.assertIn("em dash", finding["fix"].lower())


class EmojiTests(unittest.TestCase):
    def test_trips_on_an_emoji(self):
        body = f"Grows the volume \U0001F680 to 4TB.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertIn("emoji", rules_fired(result))

    def test_does_not_trip_without_one(self):
        body = f"Grows the volume from 2TB to 4TB.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertNotIn("emoji", rules_fired(result))

    def test_fix_text_asks_for_removal(self):
        result = lint(f"Grows the volume \U0001F680 to 4TB.\n\n{DISCLOSURE}\n")
        finding = finding_for(result, "emoji")
        self.assertIn("remove", finding["fix"].lower())


class PathInProseTests(unittest.TestCase):
    def test_trips_on_a_path_in_prose(self):
        body = (
            "Fixes the rule loaded from roles/checkmk_manage_config/tasks/rules.yml.\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        self.assertIn("path-in-prose", rules_fired(result))

    def test_does_not_trip_on_the_same_path_in_a_code_fence(self):
        body = (
            "Fixes the rule loading order.\n\n"
            "```\nroles/checkmk_manage_config/tasks/rules.yml\n```\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        self.assertNotIn("path-in-prose", rules_fired(result))

    def test_does_not_trip_on_the_same_path_in_backticks(self):
        body = (
            "Fixes the rule loading order in `roles/checkmk_manage_config/tasks/rules.yml`.\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        self.assertNotIn("path-in-prose", rules_fired(result))

    def test_does_not_trip_on_a_markdown_link_target(self):
        body = (
            "See [the rule file](roles/checkmk_manage_config/tasks/rules.yml) for detail.\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        self.assertNotIn("path-in-prose", rules_fired(result))

    def test_fix_text_asks_for_behavior_not_files(self):
        body = (
            "Fixes the rule loaded from roles/checkmk_manage_config/tasks/rules.yml.\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        finding = finding_for(result, "path-in-prose")
        self.assertIn("diff already lists files", finding["fix"])


class MethodNarrationTests(unittest.TestCase):
    def test_trips_on_narrating_the_verification_method(self):
        body = f"Verified with pulumi preview against dev.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertIn("method-narration", rules_fired(result))

    def test_does_not_trip_on_stating_the_result(self):
        body = f"Resources: 1 to update.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertNotIn("method-narration", rules_fired(result))

    def test_fix_text_asks_for_the_result(self):
        result = lint(f"I ran the test suite locally.\n\n{DISCLOSURE}\n")
        finding = finding_for(result, "method-narration")
        self.assertIn("result", finding["fix"].lower())


class VerdictClauseTests(unittest.TestCase):
    def test_trips_on_a_rating_of_the_change(self):
        body = f"This is a low-risk change.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertIn("verdict-clause", rules_fired(result))

    def test_does_not_trip_on_the_mechanism_fact(self):
        body = f"EBS expands online, no downtime.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertNotIn("verdict-clause", rules_fired(result))

    def test_fix_text_asks_for_the_concrete_fact(self):
        result = lint(f"This is a low-risk change.\n\n{DISCLOSURE}\n")
        finding = finding_for(result, "verdict-clause")
        self.assertIn("fact", finding["fix"].lower())


class ReviewerInstructionTests(unittest.TestCase):
    def test_trips_on_an_instruction_to_the_reviewer(self):
        body = f"Please review the linked runbook before merging.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertIn("reviewer-instruction", rules_fired(result))

    def test_does_not_trip_when_nothing_is_asked(self):
        body = f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertNotIn("reviewer-instruction", rules_fired(result))

    def test_fix_text_asks_to_delete_the_instruction(self):
        result = lint(f"Please review the linked runbook before merging.\n\n{DISCLOSURE}\n")
        finding = finding_for(result, "reviewer-instruction")
        self.assertIn("delete", finding["fix"].lower())


class BulletPerFileTests(unittest.TestCase):
    def test_trips_when_most_bullets_lead_with_a_file(self):
        body = (
            "Refactors the config loader.\n\n"
            "- config/loader.py: rewrote parsing\n"
            "- config/schema.yml: added new fields\n"
            "- tests/test_loader.py: added coverage\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        self.assertIn("bullet-per-file", rules_fired(result))

    def test_does_not_trip_when_bullets_describe_behavior(self):
        body = (
            "Refactors the config loader to validate schema before parsing.\n\n"
            "- Validates required fields before parsing\n"
            "- Falls back to defaults for optional fields\n"
            "- Adds coverage for the new validation path\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        self.assertNotIn("bullet-per-file", rules_fired(result))

    def test_fix_text_asks_for_the_shared_behavior(self):
        body = (
            "Refactors the config loader.\n\n"
            "- config/loader.py: rewrote parsing\n"
            "- config/schema.yml: added new fields\n"
            "- tests/test_loader.py: added coverage\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        finding = finding_for(result, "bullet-per-file")
        self.assertIn("behavior", finding["fix"].lower())


class SymbolInProseTests(unittest.TestCase):
    def test_trips_on_an_identifier_outside_backticks(self):
        body = f"Sets schedule_expression to run nightly.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertIn("symbol-in-prose", rules_fired(result))

    def test_is_warn_severity_and_does_not_fail_the_verdict_alone(self):
        body = f"Sets schedule_expression to run nightly.\n\n{DISCLOSURE}\n"
        result = lint(body)
        finding = finding_for(result, "symbol-in-prose")
        self.assertEqual(finding["severity"], "warn")
        self.assertEqual(result["verdict"], "pass")

    def test_does_not_trip_when_the_identifier_is_backticked(self):
        body = f"Sets `schedule_expression` to run nightly.\n\n{DISCLOSURE}\n"
        result = lint(body)
        self.assertNotIn("symbol-in-prose", rules_fired(result))


class TemplateAwarenessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name)
        (self.repo / ".github").mkdir()
        (self.repo / ".github" / "pull_request_template.md").write_text(
            "## What does this PR do?\n\n"
            "## Testing\n\n"
            "## Jira ticket number?\n\n"
            "- [ ] Please review the linked runbook before merging\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_template_checkbox_line_is_not_flagged_as_a_reviewer_instruction(self):
        body = (
            "## What does this PR do?\n\n"
            f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n\n"
            "- [ ] Please review the linked runbook before merging\n\n"
            "## Testing\n\nResources: 1 to update.\n\n"
            "## Jira ticket number?\n\nDEVOPS-1234\n"
        )
        result = lint(body, repo=self.repo)
        self.assertNotIn("reviewer-instruction", rules_fired(result))

    def test_unfilled_template_section_still_trips_despite_scaffolding(self):
        # "Testing" is left blank and is not the trailing section, so the
        # scaffolding checkbox elsewhere in the body must not mask it.
        body = (
            "## What does this PR do?\n\n"
            f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n\n"
            "- [ ] Please review the linked runbook before merging\n\n"
            "## Testing\n\n"
            "## Jira ticket number?\n\nDEVOPS-1234\n"
        )
        result = lint(body, repo=self.repo)
        self.assertIn("empty-template-section", rules_fired(result))

    def test_without_repo_the_same_checkbox_line_is_scored_normally(self):
        body = (
            "## What does this PR do?\n\n"
            f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n\n"
            "- [ ] Please review the linked runbook before merging\n\n"
            "## Jira ticket number?\n"
        )
        result = lint(body, repo=None)
        self.assertIn("reviewer-instruction", rules_fired(result))


class NonSignalRegressionTests(unittest.TestCase):
    """Guards against re-adding rules the corpus and research refuted."""

    def test_markdown_headers_alone_do_not_fail(self):
        body = (
            "## Summary\n\n"
            "Grows the appliance data volume from 2TB to 4TB.\n\n"
            "## Testing\n\n"
            "Resources: 1 to update.\n\n"
            "## Notes\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        self.assertEqual(result["verdict"], "pass")

    def test_checkboxes_alone_do_not_fail(self):
        body = (
            "Grows the appliance data volume from 2TB to 4TB.\n\n"
            "- [ ] Migration applied in staging\n"
            "- [ ] On-call notified\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        self.assertEqual(result["verdict"], "pass")

    def test_generic_ai_vocabulary_words_alone_do_not_fail(self):
        body = (
            "This is a comprehensive, robust rewrite that seamlessly leverages "
            "the existing cache layer.\n\n"
            f"{DISCLOSURE}\n"
        )
        result = lint(body)
        self.assertEqual(result["verdict"], "pass")


class BacktrackingGuardTests(unittest.TestCase):
    def test_pathological_input_completes_quickly(self):
        cases = [
            "/" * 50_000,
            "-" * 50_000,
            ("to " * 5_000) + "x",
            ("/" + "a" * 10 + ".py ") * 3_000,
            "!" * 50_000,
        ]
        for case in cases:
            with self.subTest(case=case[:20]):
                start = time.monotonic()
                result = lint(case)
                elapsed = time.monotonic() - start
                self.assertLess(elapsed, 2.0)
                self.assertIn(result["verdict"], ("pass", "fail"))

    def test_oversized_input_is_a_block_not_a_hang(self):
        start = time.monotonic()
        result = lint("x" * 30_000)
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 2.0)
        self.assertEqual(result["verdict"], "fail")
        self.assertIn("oversized-input", rules_fired(result))

    def test_oversized_input_fix_asks_for_a_file_not_a_shorter_body(self):
        result = lint("x" * 30_000)
        finding = finding_for(result, "oversized-input")
        self.assertIn("--body-file", finding["fix"])


class RobustnessTests(unittest.TestCase):
    def test_exit_code_matches_verdict(self):
        passing = subprocess.run(
            [sys.executable, str(SCRIPT), "--json"],
            input=f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(passing.returncode, 0)

        failing = subprocess.run(
            [sys.executable, str(SCRIPT), "--json"],
            input="",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(failing.returncode, 1)

    def test_body_file_argument_is_read_instead_of_stdin(self):
        with tempfile.TemporaryDirectory() as scratch:
            body_file = Path(scratch) / "body.txt"
            body_file.write_text(
                f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--json", "--body-file", str(body_file)],
                input="",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["verdict"], "pass")


class RuleNameDriftTests(unittest.TestCase):
    """Keeps the rule names in the scorer, SKILL.md, and rubric.md from diverging.

    Extraction convention (keep this comment accurate if the docs' shape changes):
      - pr_body_lint.py: the keys of its own SEVERITY dict, the scorer's rule
        registry.
      - SKILL.md: the first column of the "Rules the scorer implements" table,
        a backticked lowercase-hyphen token at the start of a table row
        (`^\\| \\`([a-z][a-z0-9-]*)\\` \\|`).
      - rubric.md: the rule heading for each entry, a level-3 heading whose text
        is a backticked lowercase-hyphen token followed by "(block)" or "(warn)"
        (`^### \\`([a-z][a-z0-9-]*)\\` \\((?:block|warn)\\)`). This intentionally
        excludes the "Known disagreements" headings further down that also
        backtick a rule name (e.g. "`reviewer-instruction` runs against..."),
        because those aren't followed by a severity in parens.
    """

    SKILL_TABLE_ROW_RE = re.compile(r"^\|\s*`([a-z][a-z0-9-]*)`\s*\|", re.MULTILINE)
    RUBRIC_HEADING_RE = re.compile(
        r"^### `([a-z][a-z0-9-]*)` \((?:block|warn)\)", re.MULTILINE
    )

    @staticmethod
    def _rules_in_lint_registry() -> set[str]:
        spec = importlib.util.spec_from_file_location("pr_body_lint_drift_check", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return set(module.SEVERITY.keys())

    @classmethod
    def _rules_in_skill_md(cls) -> set[str]:
        return set(cls.SKILL_TABLE_ROW_RE.findall(SKILL_MD.read_text(encoding="utf-8")))

    @classmethod
    def _rules_in_rubric_md(cls) -> set[str]:
        return set(cls.RUBRIC_HEADING_RE.findall(RUBRIC_MD.read_text(encoding="utf-8")))

    def test_rule_names_agree_across_scorer_skill_and_rubric(self):
        sources = {
            "pr_body_lint.py (SEVERITY registry)": self._rules_in_lint_registry(),
            "SKILL.md (rules table)": self._rules_in_skill_md(),
            "references/rubric.md (rule headings)": self._rules_in_rubric_md(),
        }
        for name, rules in sources.items():
            self.assertTrue(rules, f"extracted zero rule names from {name}; "
                                    f"the extraction pattern likely no longer matches its shape")

        all_rules = set().union(*sources.values())
        problems = []
        for rule in sorted(all_rules):
            missing_from = [name for name, rules in sources.items() if rule not in rules]
            if missing_from:
                problems.append(f"  {rule!r} missing from: {', '.join(missing_from)}")

        if problems:
            self.fail(
                "Rule name drift between the scorer, SKILL.md, and rubric.md "
                "(a rule present in one and absent from another is decorative "
                "documentation or an unscored claim):\n" + "\n".join(problems)
            )


if __name__ == "__main__":
    unittest.main()
