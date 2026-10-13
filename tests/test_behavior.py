from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
UI_CRAFT = ROOT / "skills" / "drivers" / "ui-craft"
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
    """The design session settles structure, locks one page, and never builds."""

    SKILL_DIR = UI_CRAFT

    def read(self, *parts: str) -> str:
        return " ".join(self.SKILL_DIR.joinpath(*parts).read_text(encoding="utf-8").split())

    def test_structure_step_is_approved_before_any_visual_work(self):
        lock = self.read("reference", "lock.md")
        self.assertLess(lock.index("## 1. Structure (no pixels)"), lock.index("## 3. Directions (concept only)"))
        for requirement in (
            "every tab and navigation name",
            "what each screen owns, and only that",
            "empty, loading, and error states, plus each transient state",
            "every touch gesture and its desktop equivalent",
            "every user-facing noun and verb",
            "A label nobody serves does not appear on any screen",
            "**one numbered round**",
            "The operator approves the structure before any pixel exists",
        ):
            self.assertIn(requirement, lock)

    def test_lock_is_one_page_in_the_repo_with_its_absolute_bans(self):
        skill = self.read("SKILL.md")
        lock = self.read("reference", "lock.md")
        self.assertIn("**One page, in the repo.**", skill)
        self.assertIn("It never lives in a scratchpad, a temp folder, or a canvas", skill)
        self.assertIn("**Checked against the page and nothing else.**", skill)
        for section in (
            "## Navigation", "## Screens", "## States", "## Interaction map", "## Glossary",
            "## Served vocabulary", "## Allowed strings", "## Tokens", "## Components",
            "## Bans", "## Must survive", "## Approved screens", "## Amendments",
        ):
            self.assertIn(section, lock)
        for ban in (
            "No microcopy", "No predictions", "No invented labels or data",
            "Color is never the only signal", "At most one primary action per screen",
            "No content on a screen that does not own it",
        ):
            self.assertIn(ban, lock)
        self.assertIn("Tokens** come from the running app's stylesheet", lock)
        self.assertIn("one size per role", lock)

    def test_stages_run_in_order_at_component_grain(self):
        lock = self.read("reference", "lock.md")
        stages = [
            "## 1. Structure (no pixels)",
            "## 2. Lock prep",
            "## 3. Directions (concept only)",
            "## 4. Component inventory",
            "## 5. Library",
            "## 6. Sync",
            "## 7. Compose",
            '## 8. "Locked", per screen',
        ]
        positions = [lock.index(stage) for stage in stages]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("**The review grain is a component, not a screen.**", lock)
        self.assertIn("The gate passes when **the operator picks one**", lock)
        for field in ("its states", "the served data fields it may show",
                      "its desktop equivalent for each touch gesture", "one size per role"):
            self.assertIn(field, lock)
        self.assertIn("The inventory is a gated deliverable", lock)
        self.assertIn("**in isolation, in batches of three to five, never as a full screen**", lock)
        self.assertIn("**from approved components only**", lock)
        self.assertIn("Never draw a one-off", lock)

        library = self.read("reference", "library.md")
        self.assertIn("**one story per state**", library)
        self.assertIn("**one screenshot per story**", library)
        self.assertIn("Run `precheck.py` on each story's saved HTML", library)
        self.assertIn("**in isolation, in batches of three to five, never composed into a screen**", library)
        self.assertIn("record the stack choice as an ADR in this ticket first", library)

    def test_every_gate_prechecks_critiques_and_caps_rounds(self):
        lock = self.read("reference", "lock.md")
        gates = lock[lock.index("## How every gate runs"):lock.index("## 0. Embodiment")]
        self.assertIn("**Before the operator sees anything**, the stage's renders pass `precheck.py`", gates)
        self.assertIn("A failing check means the operator does not see that render", gates)
        self.assertIn("a cold critique has run", gates)
        self.assertIn("fresh, read-only subagent with a named model", gates)
        self.assertIn("only the lock doc and the stage's renders", gates)
        self.assertIn("**At most three refinement rounds per stage.** After the third, stop.", gates)
        self.assertIn("Never run a fourth round on your own", gates)
        self.assertIn("**Echo every comment and instruction received**", gates)

    def test_locked_gate_is_per_screen_and_hands_off_to_a_build_ticket(self):
        lock = self.read("reference", "lock.md")
        skill = self.read("SKILL.md")
        build = self.read("reference", "build.md")
        self.assertIn('The operator saying **"locked"** about a screen is the only approval', lock)
        self.assertIn("**separate build ticket**", lock)
        self.assertIn("**Screens are never built in a design session.**", lock)
        self.assertIn("A design session never builds screens", skill)
        self.assertIn("from the approved component library", build)
        self.assertIn("side by side, with the screen's locked canvas artboard", build)
        self.assertIn(
            "- <surface> · <draft | locked | shipped> · <issue> · <lock doc path> · <canvas or artifact URL>",
            skill,
        )

    def test_plain_dom_path_skips_the_library_and_names_its_losses(self):
        lock = self.read("reference", "lock.md")
        plain = lock[lock.index("## Plain-DOM path (no library)"):lock.index("## Lock doc format")]
        self.assertIn("skips stages 4 to 6", plain)
        self.assertIn("composes screens straight from `Tokens`", plain)
        self.assertIn("**component review grain:**", plain)
        self.assertIn("**sync:**", plain)

    def test_revise_keeps_shipped_behavior_without_ledger_machinery(self):
        revise = self.read("reference", "revise.md")
        self.assertIn("**Never rebuild a shipped surface as a from-scratch mock** (ADR 48)", revise)
        self.assertIn("at most one page", revise)
        self.assertIn("There is no replay script and no per-story ledger", revise)
        self.assertIn("Do not start the app to find out what it reads", revise)
        self.assertIn("A dropped, changed, or moved behavior without its amendment blocks the PR", revise)
        self.assertIn("Before and after render pairs", revise)

    def test_ledger_replay_and_detector_machinery_is_gone(self):
        files = sorted(p.relative_to(self.SKILL_DIR).as_posix() for p in self.SKILL_DIR.rglob("*") if p.is_file())
        self.assertEqual(
            files,
            [
                "SKILL.md", "agents/openai.yaml",
                "reference/brand.md", "reference/build.md", "reference/design-rules.md",
                "reference/library.md", "reference/lock.md", "reference/product.md", "reference/review.md",
                "reference/revise.md", "reference/tools.md", "reference/web-implementation.md",
                "scripts/precheck.py",
            ],
        )
        for path in self.SKILL_DIR.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for retired in ("behavior-sweep", "resettle", "fidelity ledger", "behavior ledger", "context.mjs"):
                with self.subTest(page=path.name, term=retired):
                    self.assertNotIn(retired, text)
        self.assertLess(len((self.SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").splitlines()), 150)

    def test_tool_instructions_and_privacy_bounds(self):
        tools = self.read("reference", "tools.md")
        skill = self.read("SKILL.md")
        self.assertIn("**Once the project has a component library**", tools)
        self.assertIn("`/design-sync` has nothing to mirror, so skip it", tools)
        self.assertIn("**Best supported: React + TypeScript + Storybook.**", tools)
        self.assertIn("Storybook MCP", tools)
        self.assertIn("**No-framework alternative: Web Components with Storybook.**", tools)
        self.assertIn("tool support is weaker", tools)
        self.assertIn("records the stack choice as an ADR in the build ticket before the library stage", tools)
        self.assertIn("**Design System** artifact", tools)
        self.assertIn("the Artifact tool's **Design** type", tools)
        self.assertIn("**Fallback when the Design type is unavailable**", tools)
        self.assertIn("**Echo every received comment back to the operator before acting**", tools)
        self.assertIn("Claude in Chrome or the desktop app's built-in browser", tools)
        self.assertIn("**Never put real personal, health, or customer data on a canvas or artifact.**", skill)
        self.assertIn("**Real-data inversion is repo-scoped and opt-in.**", skill)
        self.assertIn("real-data renders **stay local**", skill)
        self.assertIn("**Repo personas win:**", skill)
        self.assertIn("*interface* means a module's API", skill)

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
            "lock doc",
            "must-survive list",
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

    def test_cold_reader_prompt_has_exactly_four_allowed_inputs(self):
        text = self.source.decode("utf-8")
        dispatch = text.split("## Cold-reader dispatch\n", 1)[1].split(
            "## Mechanical fix in place\n", 1
        )[0]
        self.assertIn("cold-reader prompt's four allowed inputs", dispatch)

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
            "it re-reads the settled decisions and risk contract `/ticket triage` recorded in the "
            "plan (the order's Context or the change's `design.md` and `proposal.md`) before "
            "evaluating the reviewer's deltas. It treats decisions "
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


class UiCraftPrecheckTests(unittest.TestCase):
    """The precheck runs on fixture renders, including through a symlinked skill dir."""

    FIXTURES = ROOT / "tests" / "fixtures" / "ui-craft-prechecks"

    def precheck(self, render: Path, script: Path = UI_CRAFT / "scripts" / "precheck.py"):
        return run(["python3", str(script), str(render), str(self.FIXTURES / "lock.md")], cwd=ROOT)

    def counts(self, stdout: str) -> dict:
        return {name: int(count) for name, count in re.findall(r"^(?:pass|FAIL)  ([a-z ]+): (\d+)$", stdout, re.MULTILINE)}

    def test_a_render_that_honors_the_lock_passes_every_check(self):
        result = self.precheck(self.FIXTURES / "clean")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            self.counts(result.stdout),
            {"microcopy": 0, "provenance": 0, "primary actions": 0, "frame fit": 0,
             "button sizes": 0, "glossary": 0},
        )

    def test_each_violation_fails_its_check_and_blocks_the_render(self):
        result = self.precheck(self.FIXTURES / "dirty" / "library.html")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(
            self.counts(result.stdout),
            {"microcopy": 2, "provenance": 1, "primary actions": 1, "frame fit": 1,
             "button sizes": 1, "glossary": 1},
        )
        for finding in ("'Ready to start reading?'", "'Reading streak'", "2 primary actions",
                        "480px exceeds the 390px frame", "2 button sizes, lock allows 1", "'Bookcase'"):
            self.assertIn(finding, result.stdout)
        self.assertIn("static markup only", result.stdout)

    def test_runs_through_a_symlinked_skill_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            linked = Path(temporary) / "ui-craft-link"
            linked.symlink_to(UI_CRAFT, target_is_directory=True)
            result = self.precheck(self.FIXTURES / "clean", linked / "scripts" / "precheck.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 render(s) checked", result.stdout)

    def test_missing_input_is_a_usage_error_not_a_pass(self):
        result = run(["python3", str(UI_CRAFT / "scripts" / "precheck.py"), "no-such-render", "no-such-lock"], cwd=ROOT)
        self.assertEqual(result.returncode, 2)


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
        self.assertIn("triage's mandatory `/plan-review` at Full depth", self.TICKET)

if __name__ == "__main__":
    unittest.main()
