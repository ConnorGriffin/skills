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
SPIN_SCRIPT = ROOT / "skills" / "tools" / "spin-worktree" / "scripts" / "spin-worktree.py"
UI_CRAFT_AUDIT = ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "audit.md"
UI_CRAFT_CRITIQUE = ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "critique.md"
UI_CRAFT_SWEEP = ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "behavior-sweep.md"
UI_CRAFT_ROUTE = ROOT / "skills" / "drivers" / "ui-craft" / "scripts" / "route.mjs"
README = ROOT / "README.md"

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

    def test_revision_rounds_and_retired_premise_bind_through_ui_craft(self):
        revise = (
            ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "revise.md"
        ).read_text(encoding="utf-8")
        sweep = UI_CRAFT_SWEEP.read_text(encoding="utf-8")
        build = (ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "build.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("### Running the rounds", revise)
        rounds = revise[revise.index("### Running the rounds") :]
        rounds = rounds[: rounds.index("When the decisions settle,")]
        rounds_contract = " ".join(rounds.split())
        for requirement in (
            "Interactive divergent work only",
            "One question per round",
            "nothing ruled reopens",
            "differ in concept, not decoration",
            "carries a stated cost, the recommended one included",
            "Measure the claim instead of asserting it",
            "operator's eye outranks the measurement",
            "Build only after the direction is ruled",
        ):
            self.assertIn(requirement, rounds_contract)

        changes = revise[revise.index("### Behavior changes") :]
        changes = changes[: changes.index("## 5.")]
        changes_contract = " ".join(changes.split())
        self.assertIn("**Moved:**", changes_contract)
        self.assertIn("same ceremony as a removal", changes_contract)
        # A move keeps its entry: the sweep admits exactly three entry types, so
        # leaving this open reads a moved behavior's absence as a retirement.
        self.assertIn("lands as an amended STORY rather than a retirement", changes_contract)
        for requirement in (
            "under-specifies every selector that names it",
            "presence proxy",
            "blast radius is the repository, not the directory",
        ):
            self.assertIn(requirement, changes_contract)

        # A case nothing blocks on is not a case: the blocking sentence and the
        # landing checks reach a moved behavior and a retirement's premise too.
        self.assertIn(
            "A dropped, changed or moved behavior without that record blocks",
            changes_contract,
        )
        landing = " ".join(revise[revise.index("Before landing, confirm:") :].split())
        self.assertIn("launched by whoever can launch them", landing)
        self.assertIn("every added, changed or moved behavior", landing)
        self.assertIn("everything `behavior-sweep` requires of one", landing)

        sweep_contract = " ".join(sweep.split())
        self.assertIn("asserts the premise the retirement reasoned from", sweep_contract)
        self.assertIn("QUESTION-round trigger asking for a fresh ruling", sweep_contract)
        self.assertIn("not a `replayed-fail`", sweep_contract)
        self.assertIn("premise:  the preset window controls are present", sweep)

        # What a retirement owes is enumerated on exactly one page. Three pages
        # each carrying the list is how the premise obligation reached one of
        # them and not the others; every other page names the case and points.
        self.assertIn("What a retirement owes, in one place", sweep_contract)
        resettle = (
            ROOT / "skills" / "drivers" / "ui-craft" / "reference" / "resettle.md"
        ).read_text(encoding="utf-8")
        pages = {
            "revise.md": revise,
            "resettle.md": resettle,
            "build.md": build,
        }
        for name, text in pages.items():
            with self.subTest(page=name):
                self.assertIn("behavior-sweep", text)
                # The sanction template is the tell that a page restated the list.
                self.assertNotIn("sanction: <", text)
        self.assertEqual(sweep.count("sanction: <"), 1)

        build_contract = " ".join(build.split())
        self.assertIn(
            "*premise* has failed while its behavior stays absent is `re-settle requested`",
            build_contract,
        )


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


class ReviewerRoutingCanonicalContractTests(unittest.TestCase):
    def test_shared_profile_keeps_unchanged_waits_silent_until_news(self):
        text = " ".join((ROOT / "profile" / "base.md").read_text(encoding="utf-8").split())

        self.assertIn(
            "In a wait loop, re-polled unchanged external state, files, result sets, and "
            "result locators are no news, including after three batches. Elapsed time alone "
            "is no news and never a milestone. Emit nothing until the worker completes or "
            "fails, the wait is abandoned, or a predeclared operator-relevant external-state "
            "or coordinator decision/action milestone occurs. The state-change rule below "
            "still reports any external state change the coordinator caused.",
            text,
        )

    def test_ticket_coordinator_keeps_unchanged_worker_waits_silent(self):
        text = " ".join(
            (ROOT / "skills/drivers/ticket/references/coordinator-mode.md")
            .read_text(encoding="utf-8")
            .split()
        )

        self.assertIn(
            "While a dispatched worker is still running, re-polled unchanged worker state, "
            "files, result sets, and result locators produce no update, including after three "
            "batches. Elapsed time alone is no news and never a milestone. Report completion, "
            "failure, an abandoned wait, and a predeclared operator-relevant external-state "
            "or coordinator decision/action milestone immediately. The shared state-change "
            "rule still reports any external state change the coordinator caused.",
            text,
        )


class CodeReviewDispatchTests(unittest.TestCase):
    SKILL = ROOT / "skills" / "tools" / "code-review" / "SKILL.md"

    def setUp(self):
        self.text = self.SKILL.read_text(encoding="utf-8")
        self.dispatch = " ".join(
            self.text.split("### 4. Run both axes in parallel", 1)[1]
            .split("### 5. Aggregate and report", 1)[0]
            .split()
        )

    def test_axes_dispatch_as_read_only_subagents_with_a_named_model(self):
        self.assertIn("The coordinator supplies the reviewer model.", self.dispatch)
        self.assertIn("read-only subagent with that model named on the dispatch", self.dispatch)
        self.assertIn("launch every admitted axis before waiting on any", self.dispatch)
        self.assertIn("must not modify, patch, or stash", self.dispatch)
        self.assertNotIn("codex-worker.py", self.dispatch)
        self.assertNotIn("claude-worker.py", self.dispatch)

    def test_retry_resumes_the_same_reviewer(self):
        self.assertIn("resuming the same subagent (`SendMessage`)", self.dispatch)
        self.assertIn("a retry does not start a replacement reviewer", self.dispatch)

    def test_spec_unavailable_runs_standards_alone_and_reports_it(self):
        self.assertIn("When Spec is unavailable, launch Standards only", self.dispatch)
        self.assertIn("do not launch Spec", self.dispatch)
        self.assertIn("report Spec unavailable", self.dispatch)


class PlanReviewDispatchTests(unittest.TestCase):
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

    def test_cold_reader_prompt_has_exactly_five_allowed_inputs(self):
        text = self.source.decode("utf-8")
        dispatch = text.split("## Cold-reader dispatch\n", 1)[1].split(
            "## Mechanical fix in place\n", 1
        )[0]
        self.assertIn("cold-reader prompt's five allowed inputs", dispatch)

        input_list = dispatch.split("The cold-reader prompt contains exactly:\n", 1)[1].split(
            "\n\n", 1
        )[0]
        self.assertEqual(
            [line for line in input_list.splitlines() if line[:1].isdigit()],
            [
                "1. plan location;",
                "2. the five-axis rubric;",
                "3. stakes tier;",
                "4. a context-free fresh-reviewer phase instruction that requires the reviewer",
                "5. the reviewer-memory store index path printed by `python3 <reviewer-memory-skill-directory>/scripts/memory.py pointer <repo>`.",
            ],
        )

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


class ReviewerMemoryConsumerContractTests(unittest.TestCase):
    TRIAGE = ROOT / "skills" / "drivers" / "ticket" / "verbs" / "triage.md"
    FINALIZE = ROOT / "skills" / "drivers" / "ticket" / "verbs" / "finalize.md"
    CODE_REVIEW = ROOT / "skills" / "tools" / "code-review" / "SKILL.md"
    PLAN_REVIEW = ROOT / "skills" / "tools" / "plan-review" / "SKILL.md"

    def test_triage_ensures_and_consults_memory_under_the_authoritative_failure_rule(self):
        text = " ".join(self.TRIAGE.read_text(encoding="utf-8").split())
        self.assertIn(
            "python3 <reviewer-memory-skill-directory>/scripts/memory.py ensure <repo>",
            text,
        )
        self.assertIn(
            "[reviewer-memory failure rule](../../../tools/reviewer-memory/SKILL.md#failure-rule)",
            text,
        )
        self.assertIn("including its not-installed carve-out", text)
        self.assertIn("slicing records", text)
        self.assertIn(
            "say when a nearby record contradicts the call the rubric points at",
            text,
        )

    def test_code_review_injects_the_pointer_and_appends_rounds_under_the_authoritative_failure_rule(self):
        text = " ".join(self.CODE_REVIEW.read_text(encoding="utf-8").split())
        pointer = "python3 <reviewer-memory-skill-directory>/scripts/memory.py pointer <repo>"
        append = "python3 <reviewer-memory-skill-directory>/scripts/memory.py append-review <repo>"
        self.assertGreaterEqual(text.count(pointer), 2)
        self.assertIn(append, text)
        self.assertIn(
            "[reviewer-memory failure rule](../reviewer-memory/SKILL.md#failure-rule)",
            text,
        )
        self.assertIn("including its not-installed carve-out", text)
        self.assertIn(
            "The object contains the ticket, round, verdict, findings summary, and reviewer model.",
            text,
        )

    def test_finalize_appends_the_record_output_under_the_authoritative_failure_rule(self):
        text = " ".join(self.FINALIZE.read_text(encoding="utf-8").split())
        self.assertIn(
            "python3 <reviewer-memory-skill-directory>/scripts/memory.py append-slicing <repo>",
            text,
        )
        self.assertIn(
            "[reviewer-memory failure rule](../../../tools/reviewer-memory/SKILL.md#failure-rule)",
            text,
        )
        self.assertIn("including its not-installed carve-out", text)
        self.assertIn("Retain a successful record command's standard output in `record_json`", text)
        self.assertIn("without rerunning `record`", text)
        self.assertIn("printf '%s\\n' \"$record_json\" |", text)
        self.assertIn("matching the repository identity resolved from `--project`", text)

    def test_plan_review_injects_the_pointer_and_appends_rounds_under_the_authoritative_failure_rule(self):
        text = " ".join(self.PLAN_REVIEW.read_text(encoding="utf-8").split())
        pointer = "python3 <reviewer-memory-skill-directory>/scripts/memory.py pointer <repo>"
        append = "python3 <reviewer-memory-skill-directory>/scripts/memory.py append-review <repo>"
        self.assertGreaterEqual(text.count(pointer), 2)
        self.assertIn(append, text)
        self.assertIn(
            "[reviewer-memory failure rule](../reviewer-memory/SKILL.md#failure-rule)",
            text,
        )
        self.assertIn("including its not-installed carve-out", text)
        self.assertIn("The cold reviewer reads the bundle at that fifth path before reviewing.", text)

    def test_memory_and_pointer_content_stays_out_of_published_artifacts(self):
        pages = {
            self.TRIAGE: "Keep the index and store content in worker prompts only",
            self.FINALIZE: "Keep the record and store content local",
            self.CODE_REVIEW: "Keep the pointer and store content inside reviewer prompts only",
            self.PLAN_REVIEW: "Keep the pointer and store content inside worker prompts only",
        }
        for path, contract in pages.items():
            with self.subTest(path=path):
                text = " ".join(path.read_text(encoding="utf-8").split())
                self.assertIn(contract, text)
                self.assertIn("pull request bod", text)

        plan_review = self.PLAN_REVIEW.read_text(encoding="utf-8")
        self.assertIn(
            "The cross-ticket reviewer-memory store is neither earlier-round material nor author-session material.",
            " ".join(plan_review.split()),
        )


class AssuranceLevelMatchingContractTests(unittest.TestCase):
    PROFILE = ROOT / "profile" / "base.md"
    PLAN_REVIEW = ROOT / "skills" / "tools" / "plan-review" / "SKILL.md"
    def setUp(self):
        self.profile = " ".join(self.PROFILE.read_text(encoding="utf-8").split())
        self.plan_review = " ".join(
            self.PLAN_REVIEW.read_text(encoding="utf-8").split()
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

    def test_cycle_rereads_settled_decisions_after_compaction(self):
        self.assertIn(
            "If the coordinator session running the review has its context compacted mid-review, "
            "it re-reads the settled decisions in the plan's scope ledger wherever `/ticket triage` "
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
    envelope machinery: plan-review's own review evidence blocks."""

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


class ResearchDispatchTests(unittest.TestCase):
    SKILL = ROOT / "skills" / "tools" / "research" / "SKILL.md"
    AGENT_METADATA = ROOT / "skills" / "tools" / "research" / "agents" / "openai.yaml"

    def setUp(self):
        self.text = self.SKILL.read_text(encoding="utf-8")
        self.agent_metadata = self.AGENT_METADATA.read_text(encoding="utf-8")

    def test_agent_metadata_describes_one_read_only_worker(self):
        self.assertIn(
            'short_description: "Research primary sources through one read-only worker"',
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

    def test_research_requests_hosted_sources_and_defines_exact_refusal_result(self):
        dispatch = " ".join(
            self.text.split("## Research-worker dispatch", 1)[1]
            .split("## The research worker's job", 1)[0]
            .split()
        )
        self.assertIn("read-only subagent with that model named on the dispatch", dispatch)
        self.assertIn("hosted web search and fetch tools allowed", dispatch)
        self.assertIn("`SOURCE_ACCESS_UNAVAILABLE:`", dispatch)
        self.assertIn("no findings document", dispatch)
        self.assertNotIn("WebSearch,WebFetch", dispatch)
        self.assertNotIn("web_search=live", dispatch)

    def test_research_fallback_is_same_worker_cwd_local_and_fail_closed(self):
        normalized = " ".join(self.text.split())
        for requirement in (
            "terminal, resumable session",
            "unique `.research-sources.*` directory under the worker cwd",
            "`manifest.md` mapping each file to its source URL",
            "sole narrow exception to the original-prompt-only rule",
            "resume the same worker",
            "removed after completion",
            "public unauthenticated source files",
            "transcripts, credentials, secrets, `.env`, patient data",
            "authenticated or private source material",
        ):
            self.assertIn(requirement, normalized)
        self.assertIn("If the worker leaves no resumable session", normalized)
        self.assertIn("write no successful findings document", normalized)


class DesignItTwiceDispatchTests(unittest.TestCase):
    REFERENCE = ROOT / "skills" / "tools" / "codebase-design" / "references" / "DESIGN-IT-TWICE.md"

    def setUp(self):
        self.text = " ".join(self.REFERENCE.read_text(encoding="utf-8").split())

    def test_alternatives_dispatch_as_read_only_subagents_with_a_named_model(self):
        self.assertIn(
            "Dispatch each alternative as a read-only subagent with that model named on "
            "the dispatch.",
            self.text,
        )
        self.assertIn("Each worker must not modify, patch, or stash.", self.text)
        self.assertNotIn("codex-worker.py", self.text)

    def test_failed_alternative_resumes_the_same_subagent_once(self):
        self.assertIn("resume that same subagent once (`SendMessage`)", self.text)
        self.assertIn("mark that alternative unavailable", self.text)


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
    AGENTS = ROOT / "AGENTS.md"
    WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"

    def test_documented_and_primary_ci_unittest_selections_match(self):
        agents = self.AGENTS.read_text(encoding="utf-8")
        workflow = self.WORKFLOW.read_text(encoding="utf-8")

        documented_command = re.search(r"^- Test: `([^`]+)`", agents, re.MULTILINE).group(1)
        primary_ci_step = re.search(
            r"^      - name: Run public-interface behavior tests\n"
            r"(?P<body>.*?)(?=^      - name: )",
            workflow,
            re.MULTILINE | re.DOTALL,
        ).group("body")

        named_test_module = r"tests\.test_[A-Za-z0-9_]+"
        self.assertSetEqual(
            set(re.findall(named_test_module, documented_command)),
            set(re.findall(named_test_module, primary_ci_step)),
        )

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
        self.assertIn("Cut a dedicated archive branch there", config)
        self.assertIn(
            "Open that archive branch as a reviewed follow-up pull request to main",
            config,
        )
        self.assertIn(
            "Never push an archive commit directly or forcibly to main", config
        )
        self.assertNotIn("Push main directly", config)

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

    def test_build_admission_requires_adrs_and_selected_ui_lifecycle(self):
        self.require(self.EPIC, r"load-bearing.*ADR")
        self.require(self.EPIC, r"user-facing.*selected.*ui-craft")
        self.require(self.EPIC, r"greenfield.*locked")
        self.require(self.EPIC, r"shipped.*revision.*behavior.*ledger.*replay")

    def test_research_handoff_returns_to_an_attended_operator_session(self):
        self.require(self.EPIC, r"research.*attended.*operator")
        self.require(self.EPIC, r"record.*tracker result.*design\.md")

    def test_research_close_uses_verified_tracker_evidence(self):
        self.require(self.EPIC, r"close.*spike.*only after.*tracker.*result")
        self.require(self.EPIC, r"failed.*attended session.*spike.*open")

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


class EpicHumanDispatchContractTests(unittest.TestCase):
    SURFACES = {
        "skill": ROOT / "skills" / "drivers" / "epic" / "SKILL.md",
        "guide": ROOT / "docs" / "epic-flow.md",
        "readme": ROOT / "README.md",
        "metadata": ROOT / "skills" / "drivers" / "epic" / "agents" / "openai.yaml",
    }

    def setUp(self):
        self.text = {
            name: " ".join(path.read_text(encoding="utf-8").split())
            for name, path in self.SURFACES.items()
        }

    def test_public_surfaces_describe_operator_triage_instead_of_epic_execution(self):
        for name, text in self.text.items():
            with self.subTest(surface=name):
                self.assertRegex(text, r"(?i)operator.{0,180}ticket triage")
                self.assertNotRegex(text, r"(?i)delegate a (?:locked|settled) epic subtree")
                self.assertNotRegex(text, r"(?i)epic.{0,120}(?:worker adapter|adapter state|execution wave)")

    def test_epic_surfaces_remove_every_epic_owned_execution_mechanism(self):
        removed_promises = (
            "## Delegated execution",
            "## Worker dispatch",
            "temporary per-spike worktree",
            "home session dispatches",
            "pack adapters",
            "fan-out",
            "Collect child results",
            "applicable routing ladder is exhausted",
            "coordinator-owned state file",
            "same-session retry",
            "unfinished delegated worker",
            "create chunk waves",
            "write and collect adapter state",
            "verify worker results",
        )

        for surface in ("skill", "guide"):
            with self.subTest(surface=surface):
                for promise in removed_promises:
                    self.assertNotIn(promise.lower(), self.text[surface].lower())

    def test_epic_skill_pins_the_parent_plan_and_stops_before_the_lock(self):
        epic = self.text["skill"]
        self.assertIn("Parent plan base:", epic)
        self.assertRegex(epic, r"(?i)pushed epic planning branch.{0,180}full commit")
        self.assertRegex(epic, r"(?i)does not post.{0,120}fenced.{0,80}work order")
        self.assertRegex(epic, r"(?i)does not invoke.{0,120}/ticket triage")

    def test_epic_skill_limits_children_and_serializes_handoffs(self):
        epic = self.text["skill"]
        self.assertRegex(epic, r"(?i)(?:three or fewer|at most three).{0,180}child")
        self.assertRegex(epic, r"(?i)fourth or later.{0,180}design\.md.{0,220}(?:capability boundary|dependency)")
        self.assertRegex(epic, r"(?i)one.{0,80}in-flight.{0,80}child")
        self.assertRegex(epic, r"(?i)human-merged.{0,220}updated remote default")

    def test_epic_skill_bans_planning_only_pull_requests(self):
        epic = self.text["skill"]
        self.assertRegex(epic, r"(?i)never opens a pull request")
        self.assertRegex(epic, r"(?i)planning-only pull request.{0,120}unsupported")
        self.assertRegex(epic, r"(?i)planning artifacts.{0,180}implementation pull request")


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
        for other_route in ("plan", "security"):
            self.assertNotIn(other_route, result.stdout)
        for other_skill in ("plan-review", "security-review"):
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
        for route in ("code", "plan", "security"):
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

    def test_shipped_routes_are_exactly_three_and_each_names_a_for_sentence(self):
        rows = json.loads(self.ROUTES_JSON.read_text(encoding="utf-8"))
        routes = {row["route"] for row in rows}

        self.assertEqual(routes, {"code", "plan", "security"})
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


class CoordinatorOwnedReviewContractTests(unittest.TestCase):
    TICKET = ROOT / "skills" / "drivers" / "ticket" / "SKILL.md"
    TICKET_VERBS = {
        "triage": ROOT / "skills" / "drivers" / "ticket" / "verbs" / "triage.md",
        "start": ROOT / "skills" / "drivers" / "ticket" / "verbs" / "start.md",
        "revise": ROOT / "skills" / "drivers" / "ticket" / "verbs" / "revise.md",
    }
    OPENAI_PROMPTS = (
        ROOT / "skills" / "drivers" / "ticket" / "agents" / "openai.yaml",
    )
    BASELINE_SPECS = (
        ROOT / "openspec" / "specs" / "ticket-workflow" / "spec.md",
    )

    @staticmethod
    def compact(text: str) -> str:
        return " ".join(text.split()).lower()

    @staticmethod
    def frontmatter_description(path: Path) -> str:
        source = path.read_text(encoding="utf-8")
        frontmatter = source.split("---\n", 2)[1]
        return next(
            line.removeprefix("description:").strip().strip('"')
            for line in frontmatter.splitlines()
            if line.startswith("description:")
        )

    @staticmethod
    def section(path: Path, heading: str) -> str:
        source = path.read_text(encoding="utf-8")
        anchor = f"{heading}\n\n"
        assert anchor in source
        return source.split(anchor, 1)[1].split("\n\n## ", 1)[0]

    def assert_catalog_handoff(self, description: str) -> None:
        description = self.compact(description)
        self.assertIn("coordinator dispatches every mandatory reviewer", description)
        self.assertIn("resumes the same worker", description)
        self.assertNotIn("worker launches a nested reviewer", description)

    def assert_unavailable_review_is_not_clean(self, contract: str) -> None:
        contract = self.compact(contract)
        for term in (
            "failed launch",
            "nonzero exit",
            "missing result artifact",
            "missing verdict",
            "reported as unavailable",
            "never interpreted as an empty finding list",
            "blocks the workflow from advancing as reviewed",
        ):
            self.assertIn(term, contract)

    def test_catalogs_assign_delegated_mandatory_review_to_the_coordinator(self):
        self.assert_catalog_handoff(self.frontmatter_description(self.TICKET))

    def test_ticket_authority_defines_the_fail_closed_review_handoff(self):
        ticket = self.compact(self.section(self.TICKET, "## Delegation authority"))
        for term in (
            "delegation prompt identifies the mandatory-review handoff",
            "coordinator-recorded durable result locator",
            "coordinator dispatches every mandatory reviewer",
            "verifies the returned verdict",
            "resumes the same worker",
            "failed launch",
            "nonzero exit",
            "missing result artifact",
            "missing verdict",
            "reported as unavailable",
            "blocks the workflow from advancing as reviewed",
            "direct nested adapter dispatch by the worker is unsupported",
        ):
            with self.subTest(term=term):
                self.assertIn(term, ticket)

    def test_delegated_ticket_verbs_return_review_ready_work_to_the_coordinator(self):
        for verb, path in self.TICKET_VERBS.items():
            with self.subTest(verb=verb):
                procedure = self.compact(path.read_text(encoding="utf-8"))
                self.assertIn(f"delegated `{verb}` worker", procedure)
                self.assertIn("returns its review-ready", procedure)
                self.assertIn("coordinator-recorded durable result locator", procedure)
                self.assertIn("to its coordinator", procedure)
                self.assertIn("resumes the same worker", procedure)
                self.assertIn("must not launch a nested reviewer", procedure)

    def test_openai_prompts_assign_delegated_review_to_the_coordinator(self):
        for path in self.OPENAI_PROMPTS:
            with self.subTest(path=path):
                prompt = self.compact(path.read_text(encoding="utf-8"))
                self.assert_catalog_handoff(prompt)
                self.assertIn("missing review evidence is unavailable", prompt)

    def test_baseline_specs_reject_every_unavailable_review_shape(self):
        for path in self.BASELINE_SPECS:
            with self.subTest(path=path):
                spec = self.compact(path.read_text(encoding="utf-8"))
                for term in (
                    "failed launch",
                    "nonzero exit",
                    "missing result artifact",
                    "missing verdict",
                    "unavailable",
                    "does not advance the workflow as reviewed",
                ):
                    self.assertIn(term, spec)

    def test_old_worker_owned_and_missing_verdict_wording_fail_the_contract(self):
        catalog = self.frontmatter_description(self.TICKET).replace(
            "the coordinator dispatches every mandatory reviewer",
            "the worker launches a nested reviewer",
        )
        with self.assertRaises(AssertionError):
            self.assert_catalog_handoff(catalog)


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

    def test_ticket_authority_covers_triage_plan_review(self):
        self.assertIn("triage's mandatory `/plan-review`", self.TICKET)

    def test_triage_points_to_ticket_authority_without_repeating_it(self):
        self.assertIn("ticket skill page's `## Delegation authority` section", self.TRIAGE)
        self.assertNotIn(self.AUTHORIZATION, self.TRIAGE)


class DurableWorkerOrderContractTests(unittest.TestCase):
    COORDINATOR_MODE = (
        ROOT / "skills" / "drivers" / "ticket" / "references" / "coordinator-mode.md"
    )
    FINALIZE = ROOT / "skills" / "drivers" / "ticket" / "verbs" / "finalize.md"
    REVISE = ROOT / "skills" / "drivers" / "ticket" / "verbs" / "revise.md"
    TEMPLATE = ROOT / "skills" / "drivers" / "ticket" / "templates" / "work-order.md"

    @staticmethod
    def compact(text: str) -> str:
        return " ".join(text.split()).lower()

    @staticmethod
    def section(path: Path, heading: str) -> str:
        source = path.read_text(encoding="utf-8")
        anchor = f"{heading}\n\n"
        assert anchor in source
        return source.split(anchor, 1)[1].split("\n\n## ", 1)[0]


    def test_write_mode_workers_keep_and_recover_their_closed_order(self):
        coordinator_mode = self.compact(
            self.COORDINATOR_MODE.read_text(encoding="utf-8")
        )
        for term in (
            "the prompt carries the sub-lock plus verified source coordinates and "
            "selected identifiers, never restated plan prose",
            "a chunk agent that cannot read the sub-lock's pinned source from its "
            "own worktree stops and reports",
            "the coordinator does not restate the source's plan prose to make the "
            "prompt self-contained",
        ):
            with self.subTest(coordinator_mode_term=term):
                self.assertIn(term, coordinator_mode)

        template = self.TEMPLATE.read_text(encoding="utf-8")
        flat = template.split("## Flat\n", 1)[1].split("\n---\n\n## Chunked", 1)[0]
        chunked = template.split("## Chunked\n", 1)[1]
        chunked_header, sub_order = chunked.split("SUB-ORDER 1/<n>", 1)
        flat = self.compact(flat)
        chunked_header = self.compact(chunked_header)
        sub_order = self.compact(sub_order)
        standing_instruction = (
            "re-read `order.md` before each commit and again before declaring the work done"
        )
        self.assertIn(standing_instruction, sub_order)
        self.assertIn("`done when` is closed", sub_order)
        self.assertIn("propose any further improvement rather than making it", sub_order)
        self.assertIn("stop and report rather than continuing from memory", sub_order)
        self.assertNotIn(standing_instruction, flat)
        self.assertNotIn(standing_instruction, chunked_header)

        teardown_checks = (
            (self.COORDINATOR_MODE, "<path>/ORDER.md", "worktree remove <path>"),
            (self.FINALIZE, "<worktree path>/ORDER.md", "worktree remove <worktree path>"),
            (self.REVISE, "<path>/ORDER.md", "status --short"),
        )
        for path, order_file, later_step in teardown_checks:
            with self.subTest(teardown=path):
                source = path.read_text(encoding="utf-8")
                self.assertIn(order_file, source)
                self.assertLess(source.index(order_file), source.index(later_step))


class LiveProseContractTests(unittest.TestCase):
    def test_review_depth_and_slicing_keep_their_load_bearing_rules(self):
        depth = (ROOT / "skills/drivers/ticket/references/review-depth.md").read_text(encoding="utf-8")
        slicing = (ROOT / "skills/drivers/ticket/references/slicing.md").read_text(encoding="utf-8")
        self.assertIn("Full-depth orders keep one review round", " ".join(depth.split()))
        self.assertIn(
            "The coordinator never launches an agent smarter than itself.",
            " ".join(slicing.split()),
        )


if __name__ == "__main__":
    unittest.main()
