from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
BENCH_SCRIPT = ROOT / "bench" / "pr_body_bench.py"


def _load_bench():
    spec = importlib.util.spec_from_file_location("pr_body_bench", BENCH_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BENCH = _load_bench()

DISCLOSURE = "> Written by an AI agent operating for <operator>. Verify before relying on it."
BODY_PASS = f"Grows the appliance data volume from 2TB to 4TB.\n\n{DISCLOSURE}\n"
BODY_FAIL_VACUOUS = "Fix bug.\n"


class SkillSliceExtractionTests(unittest.TestCase):
    """Experiment A: does extraction find the four slices, and fail loudly if not."""

    def test_extracts_all_four_slices_non_empty_or_deliberately_empty(self):
        slices = BENCH.build_skill_slices()
        self.assertEqual(slices["none"], "")
        for arm in ("example", "rules", "full"):
            self.assertTrue(slices[arm].strip(), f"{arm} slice was empty")

    def test_example_slice_contains_the_fenced_block_and_following_paragraph(self):
        slices = BENCH.build_skill_slices()
        self.assertIn("```markdown", slices["example"])
        self.assertIn(DISCLOSURE, slices["example"])
        self.assertIn("Copy its shape", slices["example"])

    def test_rules_slice_contains_the_principles_and_never_list_only(self):
        slices = BENCH.build_skill_slices()
        self.assertIn("Point at the spec", slices["rules"])
        self.assertIn("Method narration", slices["rules"])
        # Content unique to other sections must not leak in.
        self.assertNotIn("gh pr create --body-file", slices["rules"])
        self.assertNotIn("PreToolUse hook", slices["rules"])

    def test_full_slice_is_the_entire_skill_md(self):
        slices = BENCH.build_skill_slices()
        self.assertEqual(slices["full"], BENCH.SKILL_MD.read_text(encoding="utf-8"))

    def test_slices_are_disjoint_in_size_and_full_is_largest(self):
        slices = BENCH.build_skill_slices()
        sizes = {arm: len(slices[arm]) for arm in BENCH.ARMS}
        self.assertLess(sizes["none"], sizes["example"])
        self.assertLess(sizes["example"], sizes["full"])
        self.assertLess(sizes["rules"], sizes["full"])

    def test_moved_principles_heading_raises_instead_of_shipping_empty_slice(self):
        text = BENCH.SKILL_MD.read_text(encoding="utf-8").replace(
            "## What that body does", "## What the body doess"
        )
        with self.assertRaises(BENCH.SkillExtractionError):
            BENCH.build_skill_slices(text)

    def test_moved_never_heading_raises(self):
        text = BENCH.SKILL_MD.read_text(encoding="utf-8").replace(
            "## Never", "## Stuff to trim"
        )
        with self.assertRaises(BENCH.SkillExtractionError):
            BENCH.build_skill_slices(text)

    def test_missing_fenced_example_block_raises(self):
        text = BENCH.SKILL_MD.read_text(encoding="utf-8").replace(
            "```markdown", "~~~markdown"
        )
        with self.assertRaises(BENCH.SkillExtractionError):
            BENCH.build_skill_slices(text)

    def test_heading_present_but_body_empty_raises(self):
        text = (
            "# PR body\n\n## The gold standard\n\n```markdown\nbody\n```\n\n"
            "## What that body does\n\n## Never\n\nsomething\n"
        )
        with self.assertRaises(BENCH.SkillExtractionError):
            BENCH.build_skill_slices(text)


class BuildPromptTests(unittest.TestCase):
    def test_none_arm_is_the_diff_only(self):
        slices = {"none": "", "example": "EX", "rules": "R", "full": "F"}
        prompt = BENCH.build_prompt("diff body", "none", slices)
        self.assertNotIn("EX", prompt)
        self.assertIn("diff body", prompt)

    def test_other_arms_prepend_their_slice(self):
        slices = {"none": "", "example": "EX-TEXT", "rules": "R", "full": "F"}
        prompt = BENCH.build_prompt("diff body", "example", slices)
        self.assertIn("EX-TEXT", prompt)
        self.assertLess(prompt.index("EX-TEXT"), prompt.index("diff body"))


class RetryPromptTests(unittest.TestCase):
    """Experiment C: fix-text carries the fix instruction, rule-names does not."""

    def setUp(self):
        self.findings = [
            {"rule": "em-dash", "severity": "block", "line": 3, "excerpt": "x",
             "fix": "Rewrite without an em dash; use a period or parentheses instead."},
            {"rule": "symbol-in-prose", "severity": "warn", "line": 5, "excerpt": "y",
             "fix": "Wrap the identifier in backticks."},
        ]

    def test_fix_text_mode_includes_the_fix_instruction(self):
        prompt = BENCH.build_retry_prompt("previous body", self.findings, "fix-text")
        self.assertIn("Rewrite without an em dash", prompt)
        self.assertIn("Wrap the identifier in backticks", prompt)
        self.assertIn("em-dash", prompt)

    def test_rule_names_mode_excludes_the_fix_instruction(self):
        prompt = BENCH.build_retry_prompt("previous body", self.findings, "rule-names")
        self.assertIn("em-dash", prompt)
        self.assertNotIn("Rewrite without an em dash", prompt)
        self.assertNotIn("Wrap the identifier in backticks", prompt)

    def test_both_modes_echo_the_previous_body(self):
        for mode in ("fix-text", "rule-names"):
            prompt = BENCH.build_retry_prompt("previous body", self.findings, mode)
            self.assertIn("previous body", prompt)


class ScoreBodyTests(unittest.TestCase):
    def test_passing_body_scores_pass_with_no_blocking_rules(self):
        result = BENCH.score_body(BODY_PASS)
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["blocking_rules_fired"], [])

    def test_failing_body_carries_findings_for_the_retry_prompt(self):
        result = BENCH.score_body(BODY_FAIL_VACUOUS)
        self.assertEqual(result["verdict"], "fail")
        self.assertIn("vacuous-opener", result["rules_fired"])
        findings_rules = {f["rule"] for f in result["findings"]}
        self.assertIn("vacuous-opener", findings_rules)


class OneRunLoopTests(unittest.TestCase):
    """Experiment B: the deny-and-fix loop, exercised with a stubbed call_claude
    so no model call happens. Each test replaces BENCH.call_claude with a canned
    sequence of responses and checks the round bookkeeping one_run produces."""

    def setUp(self):
        self._original_call_claude = BENCH.call_claude
        self.slices = {"none": "", "example": "EX", "rules": "R", "full": "F"}
        self._tmpdir = tempfile.TemporaryDirectory()
        self.diff_path = Path(self._tmpdir.name) / "fixture.diff"
        self.diff_path.write_text("diff --git a/x b/x\n+line\n", encoding="utf-8")

    def tearDown(self):
        BENCH.call_claude = self._original_call_claude
        self._tmpdir.cleanup()

    def _run(self, responses, arm="none", retry_mode="fix-text"):
        fake = MagicMock(side_effect=responses)
        BENCH.call_claude = fake
        row = BENCH.one_run(
            project=Path("/unused"), model="m", arm=arm,
            diff_path=self.diff_path,
            retry_mode=retry_mode, skill_slices=self.slices,
        )
        return row, fake

    def test_pass_on_first_draft_needs_no_retry(self):
        row, fake = self._run([{"body": BODY_PASS, "output_tokens": 10}])
        self.assertEqual(fake.call_count, 1)
        self.assertEqual(len(row["rounds"]), 1)
        self.assertEqual(row["rounds"][0]["verdict"], "pass")
        self.assertEqual(row["rounds_to_pass"], 0)
        self.assertEqual(row["output_tokens_total"], 10)
        self.assertNotIn("error", row)

    def test_fails_then_recovers_on_first_retry(self):
        row, fake = self._run([
            {"body": BODY_FAIL_VACUOUS, "output_tokens": 5},
            {"body": BODY_PASS, "output_tokens": 8},
        ])
        self.assertEqual(fake.call_count, 2)
        self.assertEqual(len(row["rounds"]), 2)
        self.assertEqual(row["rounds"][0]["verdict"], "fail")
        self.assertEqual(row["rounds"][1]["verdict"], "pass")
        self.assertEqual(row["rounds_to_pass"], 1)
        self.assertEqual(row["output_tokens_total"], 13)

    def test_retry_prompt_carries_the_prior_findings(self):
        _row, fake = self._run([
            {"body": BODY_FAIL_VACUOUS, "output_tokens": 5},
            {"body": BODY_PASS, "output_tokens": 8},
        ], retry_mode="fix-text")
        second_call_prompt = fake.call_args_list[1].args[2]
        self.assertIn("vacuous-opener", second_call_prompt)
        self.assertIn(BODY_FAIL_VACUOUS.strip(), second_call_prompt)

    def test_never_passes_stops_after_max_rounds(self):
        row, fake = self._run([{"body": BODY_FAIL_VACUOUS, "output_tokens": 1}] * 4)
        self.assertEqual(fake.call_count, 4, "1 draft + 3 retries, no 5th call")
        self.assertEqual(len(row["rounds"]), 4)
        self.assertIsNone(row["rounds_to_pass"])
        self.assertNotIn("error", row)

    def test_error_mid_loop_stops_and_is_recorded_without_a_synthetic_round(self):
        row, fake = self._run([
            {"body": BODY_FAIL_VACUOUS, "output_tokens": 1},
            {"error": "socket timeout"},
        ])
        self.assertEqual(fake.call_count, 2)
        self.assertEqual(len(row["rounds"]), 1, "the errored attempt never got scored")
        self.assertEqual(row.get("error"), "socket timeout")
        self.assertIsNone(row["rounds_to_pass"])

    def test_draft_error_leaves_rounds_empty(self):
        row, fake = self._run([{"error": "no draft"}])
        self.assertEqual(fake.call_count, 1)
        self.assertEqual(row["rounds"], [])
        self.assertEqual(row["error"], "no draft")


class CompletedKeysTests(unittest.TestCase):
    def test_dedupes_by_arm_diff_model_repeat_and_retry_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            rows = [
                {"arm": "full", "diff": "a.diff", "model": "m", "repeat": 0, "retry_mode": "fix-text"},
                {"arm": "full", "diff": "a.diff", "model": "m", "repeat": 0, "retry_mode": "rule-names"},
                {"arm": "full", "diff": "a.diff", "model": "m"},  # legacy row, no repeat/retry_mode
            ]
            path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
            keys = BENCH._completed_keys(path)
        self.assertIn(("full", "a.diff", "m", 0, "fix-text"), keys)
        self.assertIn(("full", "a.diff", "m", 0, "rule-names"), keys)
        self.assertEqual(len(keys), 2, "legacy row with no retry_mode collapses onto fix-text/repeat0")

    def test_missing_file_yields_empty_set(self):
        self.assertEqual(BENCH._completed_keys(Path("/no/such/file.jsonl")), set())


def _row(arm, rounds, retry_mode="fix-text", error=None, diff="d.diff", repeat=0):
    row = {
        "arm": arm, "retry_mode": retry_mode, "diff": diff, "model": "m",
        "repeat": repeat, "rounds": rounds,
    }
    if rounds:
        row["rounds_to_pass"] = next(
            (r["round"] for r in rounds if r["verdict"] == "pass"), None
        )
    else:
        row["rounds_to_pass"] = None
    if error:
        row["error"] = error
    return row


def _round(index, verdict, rules_fired, chars=100):
    blocking = list(rules_fired) if verdict == "fail" else []
    return {
        "round": index, "body": f"body {index}", "chars": chars, "verdict": verdict,
        "rules_fired": list(rules_fired), "blocking_rules_fired": blocking,
    }


class AggregationTests(unittest.TestCase):
    """Exercises cmd_score's aggregation and reporting against fabricated rows,
    standing in for a real 'run' (no model call is made anywhere in this class)."""

    def _canned_rows(self):
        rows = []
        # Two never-in-3 survivors sharing "path-in-prose" so the final-round
        # per-rule table should flag it as surviving the loop.
        rows.append(_row("none", [
            _round(0, "fail", ["ai-disclosure-missing"]),
            _round(1, "pass", []),
        ]))
        rows.append(_row("none", [
            _round(0, "fail", ["ai-disclosure-missing", "path-in-prose"]),
            _round(1, "fail", ["path-in-prose"]),
            _round(2, "fail", ["path-in-prose"]),
            _round(3, "fail", ["path-in-prose"]),
        ]))
        rows.append(_row("example", [_round(0, "pass", [])]))
        rows.append(_row("example", [
            _round(0, "fail", ["em-dash"]),
            _round(1, "pass", []),
        ]))
        rows.append(_row("rules", [
            _round(0, "fail", ["path-in-prose"]),
            _round(1, "fail", ["path-in-prose"]),
            _round(2, "fail", ["path-in-prose"]),
            _round(3, "fail", ["path-in-prose"]),
        ]))
        rows.append(_row("full", [_round(0, "pass", [])]))
        # Fully errored: no draft at all.
        rows.append(_row("full", [], error="timeout"))
        # Partial: a draft exists but a retry call errored before round 3.
        rows.append(_row("rules", [_round(0, "fail", ["emoji"])], error="non-JSON output"))
        # rule-names arm for Experiment C.
        rows.append(_row("full", [
            _round(0, "fail", ["em-dash"]),
            _round(1, "pass", []),
        ], retry_mode="rule-names"))
        rows.append(_row("full", [
            _round(0, "fail", ["em-dash"]),
            _round(1, "fail", ["em-dash"]),
            _round(2, "fail", ["em-dash"]),
            _round(3, "fail", ["em-dash"]),
        ], retry_mode="rule-names"))
        return rows

    def _score_output(self, tag="canned"):
        with tempfile.TemporaryDirectory() as tmp:
            results_dir = Path(tmp)
            original_results = BENCH.RESULTS
            BENCH.RESULTS = results_dir
            try:
                out_path = results_dir / f"{tag}.jsonl"
                out_path.write_text(
                    "\n".join(json.dumps(r) for r in self._canned_rows()) + "\n"
                )
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    exit_code = BENCH.cmd_score(argparse.Namespace(tag=tag))
            finally:
                BENCH.RESULTS = original_results
        return exit_code, buffer.getvalue()

    def test_reports_the_caveat_verbatim_and_not_buried(self):
        _code, output = self._score_output()
        self.assertIn(BENCH.CAVEAT, output)

    def test_counts_fully_errored_and_partial_rows_separately(self):
        _code, output = self._score_output()
        self.assertIn("1 errored before any draft", output)
        self.assertIn("1 errored mid-loop after a draft", output)

    def test_reports_first_draft_pass_rate_per_arm_with_n(self):
        _code, output = self._score_output()
        for arm in BENCH.ARMS:
            self.assertIn(f"{arm}:", output)
        self.assertIn("n=", output)

    def test_untaught_ai_disclosure_is_adjusted_for_the_none_arm(self):
        # Row 1 for "none" fails raw lint on ai-disclosure-missing alone at
        # round 0; the adjusted first-draft pass rate must still count it as
        # a pass, since "none" was never told the requirement exists.
        rows = [r for r in self._canned_rows() if r["arm"] == "none"]
        bucket = BENCH._bucket_first_draft(rows, "none")
        self.assertEqual(bucket["n"], 2)
        self.assertEqual(bucket["raw_pass"], 0, "both round-0s fail raw lint")
        self.assertEqual(bucket["adj_pass"], 1, "only the disclosure-only failure is forgiven")

    def test_flags_a_rule_that_survives_the_loop(self):
        _code, output = self._score_output()
        self.assertIn("SURVIVES THE LOOP", output)
        self.assertIn("path-in-prose", output)

    def test_prints_not_measurable_language_when_a_delta_is_inside_the_band(self):
        _code, output = self._score_output()
        self.assertIn("the effect is not measurable at this sample size", output)

    def test_experiment_c_section_compares_fix_text_and_rule_names(self):
        _code, output = self._score_output()
        self.assertIn("Experiment C", output)
        self.assertIn("fix-text vs rule-names", output)
        self.assertIn("rule-names:", output)

    def test_experiment_c_section_handles_no_rule_names_data_gracefully(self):
        rows = [r for r in self._canned_rows() if r.get("retry_mode") != "rule-names"]
        with tempfile.TemporaryDirectory() as tmp:
            results_dir = Path(tmp)
            original_results = BENCH.RESULTS
            BENCH.RESULTS = results_dir
            try:
                out_path = results_dir / "no-rn.jsonl"
                out_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    exit_code = BENCH.cmd_score(argparse.Namespace(tag="no-rn"))
            finally:
                BENCH.RESULTS = original_results
        self.assertEqual(exit_code, 0)
        self.assertIn("no rule-names runs recorded", buffer.getvalue())

    def test_missing_results_file_reports_error_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            original_results = BENCH.RESULTS
            BENCH.RESULTS = Path(tmp)
            try:
                exit_code = BENCH.cmd_score(argparse.Namespace(tag="does-not-exist"))
            finally:
                BENCH.RESULTS = original_results
        self.assertEqual(exit_code, 1)


class TwoSampleReportTests(unittest.TestCase):
    def _capture(self, *args):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            BENCH._report_two_sample("label", *args)
        return buffer.getvalue()

    def test_small_delta_relative_to_band_is_not_measurable(self):
        output = self._capture(0.55, 20, 0.50, 20)
        self.assertIn("the effect is not measurable at this sample size", output)

    def test_large_delta_relative_to_band_clears_the_band(self):
        output = self._capture(0.95, 40, 0.10, 40)
        self.assertIn("clears the noise band", output)

    def test_both_unanimous_and_equal_reports_zero_effect_not_measurable(self):
        output = self._capture(1.0, 10, 1.0, 10)
        self.assertIn("the effect is not measurable at this sample size", output)

    def test_both_unanimous_but_different_reports_full_separation(self):
        output = self._capture(1.0, 10, 0.0, 10)
        self.assertIn("full separation", output)


if __name__ == "__main__":
    unittest.main()
