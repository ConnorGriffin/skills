from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TICKET_SCRIPT = ROOT / "skills" / "drivers" / "ticket" / "scripts" / "ticket.py"
TICKET_DIRECTORY = ROOT / "skills" / "drivers" / "ticket"
DISCOVERY_POLICY = ROOT / "skills" / "tools" / "codebase-memory" / "reminder.md"
# Both installed artifacts state this rule independently, because an agent may hold
# either one without the other. Pinning one vocabulary is what keeps them from
# drifting into two different rules.
GRAPH_SELECTION_TRAPS = (
    "project name",
    "branch-like label",
    "list order",
    "apparent recency",
    "only result",
)

def run(command: list[str], *, cwd: Path, env: Optional[dict[str, str]] = None):
    return subprocess.run(
        command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )


def directory_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def git_directory_digest(repo: Path, revision: str, root: str) -> str:
    listed = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", revision, "--", root],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    digest = hashlib.sha256()
    for name in listed.stdout.splitlines():
        blob = subprocess.run(
            ["git", "show", f"{revision}:{name}"],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(blob.stdout)
    return digest.hexdigest()


def user_line(text: str, timestamp: str = "2026-01-01T00:00:00Z") -> str:
    return json.dumps({"type": "user", "timestamp": timestamp, "message": {"content": [{"type": "text", "text": text}]}})


def codex_meta_line(session_id: str, timestamp: str = "2026-01-01T00:00:00Z") -> str:
    return json.dumps({"timestamp": timestamp, "type": "session_meta", "payload": {"session_id": session_id, "cwd": "/tmp/worktree"}})


def codex_token_line(input_tokens: int, cached: int = 0, timestamp: str = "2026-01-01T00:00:01Z") -> str:
    return json.dumps({"timestamp": timestamp, "type": "event_msg", "payload": {"type": "token_count", "info": {"last_token_usage": {"input_tokens": input_tokens, "cached_input_tokens": cached}}}})


def assistant_line(peak: int, *, subagent: bool = False, timestamp: str = "2026-01-01T00:00:01Z") -> str:
    return json.dumps({"type": "assistant", "timestamp": timestamp, "isSidechain": subagent, "message": {"usage": {"input_tokens": peak, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}}})
class TicketSkillContractTests(unittest.TestCase):
    def test_drafting_conventions_instruction_is_inside_flat_and_sub_order_fences(self):
        template = (TICKET_DIRECTORY / "templates" / "work-order.md").read_bytes()

        flat_region = template.split(b"## Flat\n", 1)[1].split(b"## Chunked\n", 1)[0]
        flat_fence = flat_region.split(b"```\n", 1)[1].split(b"\n```", 1)[0]
        sub_region = template.split(b"SUB-ORDER 1/<n>", 1)[1]
        sub_order_fence = b"SUB-ORDER 1/<n>" + sub_region.split(b"\n```", 1)[0]

        instruction = b"Drafting conventions: Read `skills/drivers/ticket/references/drafting-conventions.md` before acting on this order."
        self.assertIn(instruction, flat_fence)
        self.assertIn(instruction, sub_order_fence)

    def test_ticket_verb_consumers_point_to_drafting_conventions(self):
        for verb in ("triage", "start", "revise"):
            source = (TICKET_DIRECTORY / "verbs" / f"{verb}.md").read_bytes()
            with self.subTest(verb=verb):
                self.assertIn(b"drafting-conventions.md", source)

    def test_chunk_contract_owns_capabilities_and_shared_contracts_once(self):
        slicing = (TICKET_DIRECTORY / "references" / "slicing.md").read_text(
            encoding="utf-8"
        )
        template = (TICKET_DIRECTORY / "templates" / "work-order.md").read_text(
            encoding="utf-8"
        )
        triage = (TICKET_DIRECTORY / "verbs" / "triage.md").read_text(
            encoding="utf-8"
        )
        trait_rubric = slicing.split("## The trait rubric", 1)[1].split(
            "## Anchor table", 1
        )[0]
        chunk_shape = slicing.split("## Chunk shape", 1)[1].split(
            "## Orchestrator tier", 1
        )[0]
        triage_shape = triage.split("8. **Decide the shape", 1)[1].split(
            "9. **Stamp the review depth", 1
        )[0]
        sub_order = template.split("SUB-ORDER 1/<n>", 1)[1].split("```", 1)[0]

        self.assertRegex(
            trait_rubric,
            r"Slice when \*\*two or more\*\* of these hold\. One or zero: the order stays flat\.",
        )
        for heading in (
            "**File ownership**",
            "**Capability ownership**",
            "**Shared-contract ownership**",
            "**Parallel isolation**",
        ):
            self.assertIn(heading, chunk_shape)
        self.assertLess(
            chunk_shape.index("**Capability ownership**"),
            chunk_shape.index("**Shared-contract ownership**"),
        )
        self.assertLess(
            chunk_shape.index("**Shared-contract ownership**"),
            chunk_shape.index("**Parallel isolation**"),
        )
        self.assertIn("capability ownership", triage_shape)
        self.assertIn("shared-contract ownership", triage_shape)

        self.assertEqual(template.count("Capability owned:"), 1)
        self.assertEqual(template.count("Shared contracts owned:"), 1)
        self.assertLess(
            sub_order.index("Review depth:"), sub_order.index("Capability owned:")
        )
        self.assertLess(
            sub_order.index("Shared contracts owned:"), sub_order.index("Context")
        )
        for heading in ("Context", "Do", "Done when", "Boundaries"):
            self.assertIn(heading, sub_order)

        parallel_isolation = chunk_shape.split("**Parallel isolation**", 1)[1].split(
            "**Agent tier**", 1
        )[0]
        for contract in (parallel_isolation, triage_shape, sub_order):
            normalized = " ".join(contract.lower().split())
            for requirement in ("parallel", "implement", "revise", "depend", "private capability"):
                self.assertIn(requirement, normalized)

        ticket_contract = "\n".join((slicing, template, triage))
        for forbidden in ("@x", "Feature-Sliced", "Steiger"):
            self.assertNotIn(forbidden, ticket_contract)

    def test_trait_explanation_ordinals_still_point_at_their_rows(self):
        # The paragraph under the trait table explains traits by position ("The
        # fifth asks..."), so inserting or reordering a row silently re-points
        # every later ordinal at a trait it does not describe. That is how the
        # table and its explanation drift apart without either looking wrong.
        slicing = (TICKET_DIRECTORY / "references" / "slicing.md").read_text(
            encoding="utf-8"
        )
        trait_rubric = slicing.split("## The trait rubric", 1)[1].split(
            "## Anchor table", 1
        )[0]
        rows = [
            line.split("|")[1].strip()
            for line in trait_rubric.splitlines()
            if line.startswith("|") and not line.startswith("|---")
        ][1:]
        explanation = " ".join(trait_rubric.split("|\n\n", 1)[1].split())

        ordinals = {
            "first four": 4,
            "fifth": 5,
            "sixth": 6,
            "seventh": 7,
        }
        expected = {
            5: "Live run inside the ticket",
            6: "Split-path evidence",
            7: "Lockstep copies of one fact",
        }
        for word, position in ordinals.items():
            self.assertIn(
                f"The {word}",
                explanation,
                f"the explanation no longer refers to the {word} trait",
            )
            self.assertGreaterEqual(len(rows), position)
            if position in expected:
                self.assertEqual(
                    rows[position - 1],
                    expected[position],
                    f"the {word} trait row is no longer {expected[position]!r};"
                    " the explanation's ordinal now describes the wrong trait",
                )

    def test_surface_lifecycle_is_produced_and_consumed_across_ticket_paths(self):
        triage = (TICKET_DIRECTORY / "verbs" / "triage.md").read_text(encoding="utf-8")
        start = (TICKET_DIRECTORY / "verbs" / "start.md").read_text(encoding="utf-8")
        template = (TICKET_DIRECTORY / "templates" / "work-order.md").read_text(
            encoding="utf-8"
        )
        coordinator = (
            TICKET_DIRECTORY / "references" / "coordinator-mode.md"
        ).read_text(encoding="utf-8")
        orchestrate = (
            ROOT / "skills" / "drivers" / "orchestrate" / "SKILL.md"
        ).read_text(encoding="utf-8")
        ui_craft = (ROOT / "skills" / "drivers" / "ui-craft" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Surface lifecycle: <none | build | revise>", template)
        self.assertEqual(
            template.count("Surface lifecycle: <none | build | revise>"), 3
        )
        for lifecycle in ("`none`", "`build`", "`revise`"):
            self.assertIn(lifecycle, triage)
            self.assertIn(lifecycle, start)
        self.assertIn("legacy order", start)
        self.assertIn("locked manifest", start)
        self.assertIn("behavior ledger", start)
        self.assertIn("before/after", start)
        self.assertIn("Surface lifecycle:", coordinator)
        self.assertIn("Shipped-surface revision", orchestrate)
        self.assertIn("/ui-craft", " ".join(start.split()))
        self.assertIn(
            "[reference/web-implementation.md](reference/web-implementation.md)",
            ui_craft,
        )

    def test_every_verb_binds_its_own_checkout_graph_before_it_reads_code(self):
        shared = (TICKET_DIRECTORY / "SKILL.md").read_text(encoding="utf-8")
        triage = (TICKET_DIRECTORY / "verbs" / "triage.md").read_text(encoding="utf-8")
        start = (TICKET_DIRECTORY / "verbs" / "start.md").read_text(encoding="utf-8")
        revise = (TICKET_DIRECTORY / "verbs" / "revise.md").read_text(encoding="utf-8")
        rule = shared.split("## The graph identity", 1)[1].split("## Standing decisions", 1)[0]

        self.assertIn("cbm-lifecycle.py ensure", rule)
        for state in ("`ready`", "`indexed`", "`unavailable`"):
            self.assertIn(state, rule)
        normalized = " ".join(rule.lower().split())
        for trap in GRAPH_SELECTION_TRAPS:
            self.assertIn(trap, normalized)
        self.assertIn("recomputes", normalized)
        self.assertIn("ordinary discovery", normalized)
        self.assertIn("no exit code", normalized)
        self.assertIn("harness or sandbox", normalized)
        self.assertIn("refused it", normalized)
        self.assertEqual(
            normalized.count("ordinary discovery"),
            2,
            "the never-ran outcome must reuse the unavailable outcome's rule, not restate it",
        )

        for page, worktree, code in (
            (triage, "Cut or reuse the worktree", "5. **Ground.**"),
            (start, "Worktree and branch", "Sufficiency check"),
            (revise, "2. **Worktree.**", "4. **Collect the round.**"),
        ):
            binding = page.index("graph-identity rule")
            self.assertLess(page.index(worktree), binding)
            self.assertLess(binding, page.index(code))

    def test_the_graph_identity_never_travels_in_a_tracker_artifact(self):
        shared = (TICKET_DIRECTORY / "SKILL.md").read_text(encoding="utf-8")
        template = (TICKET_DIRECTORY / "templates" / "work-order.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("never goes into a work order", " ".join(shared.split()))
        for machine_local in ("cbm-onboard-v1-", "root_path", "cbm-lifecycle.py"):
            self.assertNotIn(machine_local, template)

    def test_a_chunk_agent_is_handed_its_own_graph_identity_and_no_other(self):
        coordinator = (
            TICKET_DIRECTORY / "references" / "coordinator-mode.md"
        ).read_text(encoding="utf-8")
        dispatch = coordinator.split("## Chunk-worker dispatch", 1)[1].split(
            "## Worker accounting", 1
        )[0]

        self.assertIn("graph-identity rule", dispatch)
        self.assertIn("`root_path`", dispatch)
        self.assertIn("`project`", dispatch)
        normalized = " ".join(dispatch.lower().split())
        self.assertIn("uses as given", normalized)
        self.assertIn("never receives the ticket worktree's identity or a sibling's", normalized)

    def test_chunk_preparation_retains_ui_lifecycle_validation(self):
        coordinator = (
            TICKET_DIRECTORY / "references" / "coordinator-mode.md"
        ).read_text(encoding="utf-8")
        preparation = coordinator.split("## Chunk preparation", 1)[1].split(
            "## Chunk-worker dispatch", 1
        )[0]

        self.assertIn("`Surface lifecycle:`", preparation)
        self.assertIn("`build` or `revise`", preparation)
        self.assertIn(
            "names the lock manifest or shipped behavior ledger/replay that mode consumes",
            " ".join(preparation.split()),
        )
        self.assertIn("non-UI chunks keep `none`", preparation)

    def test_worker_accounting_remains_after_dispatch(self):
        coordinator = (
            TICKET_DIRECTORY / "references" / "coordinator-mode.md"
        ).read_text(encoding="utf-8")
        accounting = coordinator.split("## Worker accounting", 1)[1].split(
            "## Reviewer selection", 1
        )[0]
        operative_arguments = accounting.split(
            "through the shared claim rule, passing\n", 1
        )[1].split(". The role", 1)[0]
        normalized = " ".join(accounting.split())

        self.assertIn("stable transcript id", accounting)
        for argument in (
            "--verb start",
            "--role worker",
            "--session <id>",
            "--agent <agent>",
            "--project <chunk-worktree>",
        ):
            self.assertIn(argument, operative_arguments)
        self.assertIn("report the omitted claim in one line and continue", normalized)
        self.assertIn("shared visible, non-blocking rule", normalized)

    def test_reviewer_selection_retains_the_existing_review_route(self):
        coordinator = (
            TICKET_DIRECTORY / "references" / "coordinator-mode.md"
        ).read_text(encoding="utf-8")
        reviewer_selection = coordinator.split("## Reviewer selection", 1)[1]
        review_instruction = reviewer_selection.split("   a. ", 1)[1].split(
            "\n\n   b.", 1
        )[0]

        self.assertIn("Run `/review` for the chunk diff", review_instruction)
        self.assertIn("review-routing.md", review_instruction)

    def test_every_ticket_authored_worktree_removal_tears_the_graph_down_first(self):
        pages = {
            name: (TICKET_DIRECTORY / relative).read_text(encoding="utf-8")
            for name, relative in (
                ("revise", Path("verbs") / "revise.md"),
                ("finalize", Path("verbs") / "finalize.md"),
                ("coordinator", Path("references") / "coordinator-mode.md"),
            )
        }

        for name, page in pages.items():
            removals = [match.start() for match in re.finditer(r"worktree remove", page)]
            self.assertTrue(removals, name)
            for removal in removals:
                self.assertIn("cbm-teardown.sh", page[max(0, removal - 400) : removal], name)

    def test_discovery_uses_a_supplied_project_and_otherwise_resolves_the_checkout(self):
        reminder = DISCOVERY_POLICY.read_text(encoding="utf-8")
        normalized = " ".join(reminder.split())

        self.assertIn("use exactly that name as given", normalized)
        self.assertIn("cbm-lifecycle.py ensure", normalized)
        self.assertIn("Activating this skill never indexes a project.", normalized)
        for trap in GRAPH_SELECTION_TRAPS:
            self.assertIn(trap, normalized.lower())

    def test_a_failed_graph_teardown_is_said_once_and_never_stops_the_removal(self):
        shared = (TICKET_DIRECTORY / "SKILL.md").read_text(encoding="utf-8")
        rule = " ".join(
            shared.split("## The graph identity", 1)[1]
            .split("## Standing decisions", 1)[0]
            .split()
        )
        pages = [
            (TICKET_DIRECTORY / relative).read_text(encoding="utf-8")
            for relative in (
                Path("verbs") / "revise.md",
                Path("verbs") / "finalize.md",
                Path("references") / "coordinator-mode.md",
            )
        ]

        self.assertIn("report it in one line and carry on with the removal", rule)
        self.assertIn("never holds up the removal", rule)
        self.assertIn("never retried", rule)
        self.assertIn("no Codebase Memory installed", rule)
        # One authority for the disposition; the call sites carry only the command,
        # so a teardown that fails cannot be handled two ways in one lifecycle.
        self.assertEqual(
            sum(page.count("holds up the removal") for page in pages) + rule.count("holds up the removal"),
            1,
        )

    def test_hardening_profile_is_produced_and_consumed_across_ticket_paths(self):
        template = (TICKET_DIRECTORY / "templates" / "work-order.md").read_text(
            encoding="utf-8"
        )
        triage = (TICKET_DIRECTORY / "verbs" / "triage.md").read_text(
            encoding="utf-8"
        )
        start = (TICKET_DIRECTORY / "verbs" / "start.md").read_text(
            encoding="utf-8"
        )
        revise = (TICKET_DIRECTORY / "verbs" / "revise.md").read_text(
            encoding="utf-8"
        )
        shared = (TICKET_DIRECTORY / "SKILL.md").read_text(encoding="utf-8")

        flat_order = template.split("## Flat", 1)[1].split("## Chunked", 1)[0]
        chunked_header = template.split("## Chunked", 1)[1].split(
            "SUB-ORDER 1/<n>", 1
        )[0]
        sub_order = template.split("SUB-ORDER 1/<n>", 1)[1].split("```", 1)[0]
        self.assertIn("Profile: <none | hardening>", flat_order)
        self.assertIn("Profile: <none | hardening>", chunked_header)
        self.assertIn("QA script", flat_order)
        # Triage stamps Profile: none on every chunked order, so a sub-order
        # QA script section could never fire.
        self.assertNotIn("QA script", sub_order)
        self.assertIn("Stamp the profile", triage)
        self.assertIn("Harden:", triage)
        for requirement in (
            "/clean",
            "Harden:",
            "three passes",
            "never a pass",
            "no `Profile:` line",
        ):
            self.assertIn(requirement, start)
        self.assertIn("Harden:", revise)
        self.assertIn("Harden:", shared)
        self.assertIn("Profile: hardening", shared)

    def test_start_opens_with_summary_and_claim_before_fetching_the_order(self):
        shared = (TICKET_DIRECTORY / "SKILL.md").read_text(encoding="utf-8")
        start = (TICKET_DIRECTORY / "verbs" / "start.md").read_text(encoding="utf-8")

        self.assertLess(shared.index("Open with the ticket summary"), shared.index("Claim the session"))
        opening = start.index("Complete shared rules 1–2")
        fetch = start.index("Fetch the order")
        self.assertLess(opening, fetch)
        self.assertLess(start.index("Worktree and branch"), start.index("Sufficiency check"))
        self.assertIn("never blocks the verb", shared)

    def test_coordinator_claims_workers_and_reviewers_under_their_own_roles(self):
        coordinator = (TICKET_DIRECTORY / "references" / "coordinator-mode.md").read_text(
            encoding="utf-8"
        )
        contract = " ".join(coordinator.split())

        for requirement in (
            "each unique implementation-worker session",
            "`--verb start`",
            "`--role worker`",
            "`--session <id>`",
            "`--agent <agent>`",
            "`--project <chunk-worktree>`",
            "Same-session retries are not re-claimed",
            "fresh implementation escalation",
            "Claim each dispatched reviewer session",
            "`--role reviewer`",
            "stable transcript id",
            "one line and continue",
        ):
            self.assertIn(requirement, contract)
        # The deferral this ticket closed: review-only sessions are claimed now.
        self.assertNotIn("Review-only sessions are not claimed", contract)
        self.assertNotIn("belongs to ticket 77", contract)

    def test_workflow_claims_are_bound_to_one_lifecycle_verb_per_session(self):
        shared = " ".join(
            (TICKET_DIRECTORY / "SKILL.md").read_text(encoding="utf-8").split()
        )
        start = " ".join(
            (TICKET_DIRECTORY / "verbs" / "start.md").read_text(encoding="utf-8").split()
        )
        revise = " ".join(
            (TICKET_DIRECTORY / "verbs" / "revise.md").read_text(encoding="utf-8").split()
        )
        finalize = " ".join(
            (TICKET_DIRECTORY / "verbs" / "finalize.md").read_text(encoding="utf-8").split()
        )

        self.assertIn("--verb <current verb>", shared)
        for verb in ("triage", "start", "revise", "finalize"):
            self.assertIn(f"`{verb}`", shared)
        self.assertIn("same-verb resumes reuse the claim", shared)
        self.assertIn("changing verbs requires a fresh session", shared)
        self.assertIn("persisted and submitted verbs", shared)
        self.assertIn("`--verb start --role coordinator`", start)
        self.assertIn("`--verb revise`", revise)
        self.assertIn("must not reuse a session claimed by start or finalize", revise)
        self.assertIn("`--verb finalize`", finalize)
        self.assertIn("never reuses the session that ran start or revise", finalize)

    def test_triage_requires_the_brief_quality_checklist(self):
        triage = (TICKET_DIRECTORY / "verbs" / "triage.md").read_text(encoding="utf-8")
        checklist = TICKET_DIRECTORY / "references" / "brief-quality.md"

        self.assertTrue(checklist.is_file())
        self.assertIn("[references/brief-quality.md](../references/brief-quality.md)", triage)

    def test_revise_requires_the_four_review_action_dispositions(self):
        revise = (TICKET_DIRECTORY / "verbs" / "revise.md").read_text(encoding="utf-8")
        actions = (TICKET_DIRECTORY / "references" / "review-actions.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("[references/review-actions.md](../references/review-actions.md)", revise)
        for disposition in (
            "Fix before completion",
            "Necessary follow-up",
            "Ask the maintainer",
            "Discard as preference",
        ):
            self.assertIn(disposition, actions)

    def test_under_epic_followups_use_the_epic_tracker_creation_interface(self):
        actions = (TICKET_DIRECTORY / "references" / "review-actions.md").read_text(
            encoding="utf-8"
        )
        tracker_path = (
            ROOT / "skills" / "drivers" / "epic" / "bindings" / "github-issues.md"
        )
        tracker = tracker_path.read_text(encoding="utf-8")

        self.assertIn("../../epic/references/tracker-contract.md", actions)
        self.assertIn("Necessary follow-up", actions)
        self.assertRegex(
            tracker,
            r"gh issue create .*--repo OWNER/REPO.*--title .*--body-file .*--label (spike|build).*--parent EPIC_NUMBER",
        )

    def test_every_epic_child_change_record_consumer_uses_the_epic_record(self):
        consumers = {
            "shared": TICKET_DIRECTORY / "SKILL.md",
            "triage": TICKET_DIRECTORY / "verbs" / "triage.md",
            "start": TICKET_DIRECTORY / "verbs" / "start.md",
            "revise": TICKET_DIRECTORY / "verbs" / "revise.md",
            "finalize": TICKET_DIRECTORY / "verbs" / "finalize.md",
            "coordinator": TICKET_DIRECTORY / "references" / "coordinator-mode.md",
        }

        for name, path in consumers.items():
            with self.subTest(consumer=name):
                text = " ".join(path.read_text(encoding="utf-8").lower().split())
                self.assertIn("epic child", text)
                self.assertIn("change record", text)

    def test_epic_child_scope_instrumentation_never_creates_a_scope_ledger(self):
        triage = (TICKET_DIRECTORY / "verbs" / "triage.md").read_text(encoding="utf-8")
        scope = (ROOT / "skills" / "workflows" / "scope" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        contract = " ".join((triage + "\n" + scope).lower().split())

        self.assertIn("epic child", contract)
        self.assertIn("session scratch", contract)
        self.assertIn("every specialist", contract)
        self.assertIn("no scope ledger", contract)

    def test_triaged_build_label_is_conditioned_on_code_classification(self):
        tracker = (TICKET_DIRECTORY / "references" / "tracker-contract.md").read_text(
            encoding="utf-8"
        )
        binding = (TICKET_DIRECTORY / "bindings" / "github-issues.md").read_text(
            encoding="utf-8"
        )
        contract = " ".join((tracker + "\n" + binding).lower().split())

        for classification in ("code", "investigation", "manual"):
            self.assertIn(classification, contract)
        self.assertRegex(contract, r"code classification.{0,240}build")
        self.assertRegex(contract, r"investigation.{0,240}(does not|do not|without).{0,120}build")
        self.assertRegex(contract, r"manual.{0,240}(does not|do not|without).{0,120}build")
        self.assertIn("ticket:triaged", contract)

    def test_ticket_read_supplies_parent_and_labels_for_epic_child_detection(self):
        binding = (
            TICKET_DIRECTORY / "bindings" / "github-issues.md"
        ).read_text(encoding="utf-8")
        triage = " ".join(
            (TICKET_DIRECTORY / "verbs" / "triage.md")
            .read_text(encoding="utf-8")
            .lower()
            .split()
        )

        self.assertIn(
            "--json number,title,body,state,labels,parent,comments",
            binding,
        )
        self.assertIn("parent is only an epic-child candidate", triage)
        self.assertIn("read that parent through the tracker contract", triage)
        self.assertIn("`epic` label", triage)
        self.assertIn("ordinary ticket", triage)

    def test_code_triage_stops_before_status_when_build_creation_or_attachment_fails(self):
        binding = (TICKET_DIRECTORY / "bindings" / "github-issues.md").read_text(
            encoding="utf-8"
        ).lower()

        self.assertIn("creation failure or attachment failure", binding)
        self.assertIn("do not run the later", binding)
        self.assertIn("retain the posted work order", binding)

    def test_promotion_requires_both_oversize_and_an_unsettled_decision(self):
        slicing = (TICKET_DIRECTORY / "references" / "slicing.md").read_text(
            encoding="utf-8"
        ).lower()

        contract = " ".join(slicing.split())
        self.assertRegex(contract, r"more than four.*decision unsettled")
        self.assertIn("mechanical oversize", contract)
        self.assertIn("serial `build` tickets", contract)

    def test_epic_child_change_record_consumers_state_their_phase_boundary(self):
        expected = {
            "start.md": "preserves the parent-plan bytes",
            "revise.md": "preserve the parent-plan bytes",
            "finalize.md": "leaves the parent active and unarchived",
            "coordinator-mode.md": "preserves the parent-plan bytes",
        }

        for filename, boundary in expected.items():
            path = (
                TICKET_DIRECTORY / "references" / filename
                if filename == "coordinator-mode.md"
                else TICKET_DIRECTORY / "verbs" / filename
            )
            with self.subTest(consumer=filename):
                self.assertIn(
                    boundary,
                    " ".join(path.read_text(encoding="utf-8").lower().split()),
                )

    def test_openspec_changes_remain_active_through_pr_review_and_archive_after_merge(self):
        shared = (TICKET_DIRECTORY / "SKILL.md").read_text(encoding="utf-8")
        start = (TICKET_DIRECTORY / "verbs" / "start.md").read_text(encoding="utf-8")
        revise = (TICKET_DIRECTORY / "verbs" / "revise.md").read_text(encoding="utf-8")
        finalize = (TICKET_DIRECTORY / "verbs" / "finalize.md").read_text(encoding="utf-8")
        coordinator = (
            TICKET_DIRECTORY / "references" / "coordinator-mode.md"
        ).read_text(encoding="utf-8")
        shared_contract = " ".join(shared.split())
        start_contract = " ".join(start.split())
        revise_contract = " ".join(revise.split())
        finalize_contract = " ".join(finalize.split())
        coordinator_contract = " ".join(coordinator.split())

        self.assertIn("keep the active change and its deltas reviewable", shared_contract)
        self.assertIn("do not fold or archive it before merge", shared_contract)
        self.assertIn("active change and its deltas remain reviewable", start_contract)
        self.assertIn("its active change and deltas remain reviewable", revise_contract)
        self.assertIn("operations.archive.guidance", finalize_contract)
        self.assertIn("clean `main` checkout updated to `origin/main`", finalize_contract)
        self.assertIn("openspec archive <change-name> --json --yes", finalize_contract)
        self.assertIn("openspec validate --all --strict", finalize_contract)
        self.assertIn("Signed-off-by archive commit", finalize_contract)
        self.assertIn("push `main` directly", finalize_contract)
        self.assertIn("post-push workflow", finalize_contract)
        self.assertLess(finalize_contract.index("openspec archive"), finalize_contract.index("Comment on the ticket"))
        self.assertLess(finalize_contract.index("post-push workflow"), finalize_contract.index("Move the ticket to done"))
        self.assertLess(finalize_contract.index("Move the ticket to done"), finalize_contract.index("**Record the actuals.**"))
        self.assertLess(finalize_contract.index("**Record the actuals.**"), finalize_contract.index("**Tear the worktree and branch down.**"))
        self.assertIn("leaves the parent active and unarchived", finalize_contract)
        self.assertIn("no child change", finalize_contract)
        self.assertIn("active change", coordinator_contract)
        self.assertNotIn("standing planning-pull-request", coordinator_contract)

        live = "\n".join((shared, start, revise, finalize, coordinator)).lower()
        self.assertNotRegex(live, r"fold.{0,100}(?:last|finishing).{0,100}pull request")
        self.assertNotRegex(live, r"archive.{0,100}(?:last|finishing).{0,100}pull request")

    def test_status_binding_orders_code_prerequisites_before_triaged_and_excludes_them_otherwise(self):
        binding = " ".join(
            (TICKET_DIRECTORY / "bindings" / "github-issues.md")
            .read_text(encoding="utf-8")
            .lower()
            .split()
        )

        triaged_command = "gh issue edit <id> --repo <org/repo> --add-label ticket:triaged"
        self.assertLess(binding.index("gh label create build"), binding.index(triaged_command))
        self.assertLess(binding.index("--add-label build"), binding.index(triaged_command))
        for classification in ("investigation", "manual"):
            self.assertIn(f"`{classification}` does not create or attach `build`", binding)

    def test_epic_child_triage_verifies_the_pinned_remote_parent_plan_before_worktree(self):
        triage = (TICKET_DIRECTORY / "verbs" / "triage.md").read_text(encoding="utf-8")
        contract = " ".join(triage.split())

        self.assertIn("Parent plan base:", contract)
        self.assertIn("git -C <control checkout> fetch origin", contract)
        self.assertIn("origin/<parent-plan branch>", contract)
        self.assertIn("pinned full commit", contract)
        self.assertIn("--base <parent-plan branch>", contract)
        self.assertRegex(contract.lower(), r"stale draft.{0,180}post nothing.{0,180}attended epic")
        self.assertLess(
            contract.index("git -C <control checkout> fetch origin"),
            contract.index("spin-worktree.py"),
        )

    def test_epic_issue_draft_routes_through_operator_triage_to_the_only_lock(self):
        epic = " ".join(
            (ROOT / "skills" / "drivers" / "epic" / "SKILL.md")
            .read_text(encoding="utf-8")
            .split()
        )
        triage = " ".join(
            (TICKET_DIRECTORY / "verbs" / "triage.md")
            .read_text(encoding="utf-8")
            .split()
        )

        self.assertRegex(epic, r"issue body.{0,120}draft")
        self.assertRegex(epic, r"operator.{0,100}/ticket triage")
        self.assertRegex(epic, r"does not post.{0,120}fenced")
        self.assertRegex(triage, r"issue-body draft.{0,200}ordinary grounding")
        self.assertRegex(triage, r"only fenced.{0,100}execution lock")

    def test_epic_child_parent_plan_amendment_rides_the_implementation_pull_request(self):
        consumers = [
            TICKET_DIRECTORY / "SKILL.md",
            TICKET_DIRECTORY / "verbs" / "triage.md",
            TICKET_DIRECTORY / "verbs" / "start.md",
            TICKET_DIRECTORY / "verbs" / "revise.md",
            TICKET_DIRECTORY / "verbs" / "finalize.md",
            TICKET_DIRECTORY / "references" / "coordinator-mode.md",
        ]
        live = "\n".join(path.read_text(encoding="utf-8") for path in consumers)
        normalized = " ".join(live.split())

        self.assertRegex(
            normalized,
            r"parent-plan amendment.{0,220}child worktree.{0,220}implementation pull request",
        )
        self.assertIn("preserves the parent-plan bytes", normalized)
        self.assertIn("leaves the parent active and unarchived", normalized)
        self.assertNotIn("separate docs-only pull request", live.lower())
        self.assertNotIn("epic child carries shipping code only", live.lower())

    def test_epic_serial_child_handoff_advances_the_plan_after_human_merge(self):
        epic = " ".join(
            (ROOT / "skills" / "drivers" / "epic" / "SKILL.md")
            .read_text(encoding="utf-8")
            .split()
        )

        self.assertRegex(epic, r"only one in-flight epic child")
        self.assertRegex(epic, r"Refuse every later handoff.{0,180}human-merged")
        self.assertRegex(epic, r"updated remote default branch.{0,220}new full-commit pin")

    def test_revise_requires_a_base_currency_and_mergeability_refresh(self):
        revise = (TICKET_DIRECTORY / "verbs" / "revise.md").read_text(encoding="utf-8")

        self.assertIn("mergeStateStatus", revise)
        self.assertIn("rebase once", revise)
        self.assertIn("stamped review depth", revise)
        self.assertIn("semantic conflict", revise)


class ReviewDepthSensitivityFloorTests(unittest.TestCase):
    def test_sensitivity_floor_forces_full_depth_non_negotiably(self):
        text = " ".join(
            (TICKET_DIRECTORY / "references" / "review-depth.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn(
            "A change is **Full**, non-negotiably, when it touches any of:", text
        )
        self.assertIn(
            "authentication, authorization, or identity (trust policies, role assumption, "
            "single sign-on, token scope)",
            text,
        )
        self.assertIn(
            "destructive or irreversible operations (deletes, replaces, force-applies, "
            "data-bearing resources)",
            text,
        )
        self.assertIn("These override a lower stamp without discussion.", text)


class TicketChunkWorkerAdapterDispatchTests(unittest.TestCase):
    def test_chunk_worker_dispatch_stays_on_the_worker_adapters_only(self):
        text = " ".join(
            (TICKET_DIRECTORY / "references" / "coordinator-mode.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn(
            "Dispatch one agent per chunk** at the tier its `Agent:` line names.", text
        )
        self.assertIn(
            "Dispatch only through `skills/drivers/orchestrate/scripts/codex-worker.py` or "
            "`skills/drivers/orchestrate/scripts/claude-worker.py`. Never use the built-in "
            "Agent tool, Workflow tool, background-agent machinery, or native agent dispatch.",
            text,
        )

    def test_chunk_worker_dispatch_isolates_each_chunks_identity(self):
        text = " ".join(
            (TICKET_DIRECTORY / "references" / "coordinator-mode.md")
            .read_text(encoding="utf-8")
            .split()
        )
        self.assertIn(
            "A chunk never receives the ticket worktree's identity or a sibling's, and never "
            "coordinator commentary.",
            text,
        )


class TicketTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.scratch = Path(self.temporary.name)
        self.projects = self.scratch / "projects"
        self.projects.mkdir()
        self.codex_home = self.scratch / "codex-home"
        self.claims = self.scratch / "config" / "ticket" / "claims.jsonl"
        self.environment = os.environ.copy()
        self.environment.pop("CLAUDE_CODE_SESSION_ID", None)
        self.environment.pop("CODEX_SESSION_ID", None)
        self.environment["CLAUDE_PROJECTS_DIR"] = str(self.projects)
        self.environment["CODEX_HOME"] = str(self.codex_home)
        self.environment["TICKET_CLAIMS"] = str(self.claims)

    def tearDown(self):
        self.temporary.cleanup()

    def ticket(self, *arguments: str, environment: Optional[dict] = None, cwd: Optional[Path] = None):
        return run(
            ["python3", str(TICKET_SCRIPT), *arguments],
            cwd=cwd or ROOT,
            env=environment or self.environment,
        )

    def write_session(self, project: str, session_id: str, lines: list[str]) -> Path:
        directory = self.projects / project
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{session_id}.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def write_codex_session(self, session_id: str, lines: list[str]) -> Path:
        directory = self.codex_home / "sessions" / "2026" / "01" / "01"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"rollout-2026-01-01T00-00-00-{session_id}.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def claim(
        self,
        ticket_id: str,
        session_id: str,
        agent: str = "claude",
        role: Optional[str] = None,
        verb: str = "start",
    ):
        result = self.ticket(
            "claim", ticket_id, "--session", session_id, "--agent", agent,
            "--verb", verb,
            *(("--role", role) if role else ()),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def worked(
        self,
        ticket_id: str,
        project: str,
        session_id: str,
        lines: list[str],
        role: Optional[str] = None,
        verb: str = "start",
    ):
        """The ordinary case: a session ran the ticket, so it claimed it."""
        self.write_session(project, session_id, lines)
        self.claim(ticket_id, session_id, role=role, verb=verb)

    def test_claim_records_the_running_session_without_being_told_which(self):
        environment = self.environment.copy()
        environment["CLAUDE_CODE_SESSION_ID"] = "session-1"

        result = self.ticket("claim", "TICKET-1", "--verb", "start", environment=environment)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_id"], "session-1")
        self.assertEqual(payload["agent"], "claude")
        self.assertFalse(payload["already_claimed"])

    def test_claiming_the_same_session_twice_records_it_once(self):
        self.claim("TICKET-2", "session-1")

        second = self.ticket(
            "claim", "TICKET-2", "--session", "session-1", "--agent", "claude",
            "--verb", "start",
        )

        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue(json.loads(second.stdout)["already_claimed"])
        lines = self.claims.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len([line for line in lines if line.strip()]), 1)

    def test_claim_write_denied_by_sandbox_reports_and_exits_zero(self):
        # A Codex workspace-write sandbox cannot reach ~/.config/ticket. The
        # denial must not crash the verb, and the claim JSON must not lie
        # about a claim being on record.
        denied_root = self.scratch / "no-write"
        denied_root.mkdir()
        denied_root.chmod(0o500)
        denied_path = denied_root / "claims" / "claims.jsonl"
        environment = self.environment.copy()
        environment["TICKET_CLAIMS"] = str(denied_path)

        result = self.ticket(
            "claim", "TICKET-40", "--session", "session-1", "--agent", "claude",
            "--verb", "start",
            environment=environment,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_id"], "session-1")
        self.assertFalse(payload["already_claimed"])
        self.assertIn(str(denied_path), result.stderr)
        self.assertIn("escalated", result.stderr)
        self.assertFalse((denied_root / "claims").exists())

    def test_claim_without_a_session_id_anywhere_says_how_to_supply_one(self):
        result = self.ticket("claim", "TICKET-3", "--verb", "start")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CLAUDE_CODE_SESSION_ID", result.stderr)
        self.assertIn("CODEX_SESSION_ID", result.stderr)
        self.assertFalse(self.claims.exists())

    def test_a_session_that_never_claimed_the_ticket_is_not_counted(self):
        # The whole point of claiming: prose is no longer evidence. This session
        # names the ticket in operator prose and still does not count.
        self.write_session(
            "proj-a",
            "session-1",
            [user_line("TICKET-4 is the one I mean"), assistant_line(300_000)],
        )
        self.worked("TICKET-4", "proj-a", "session-2", [assistant_line(90_000)])

        result = self.ticket("scan", "TICKET-4")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_count"], 1)
        self.assertEqual(payload["peak_context"], 90_000)
        self.assertEqual(payload["sessions"][0]["session_id"], "session-2")

    def test_a_codex_session_is_resolved_from_its_rollout_file(self):
        self.write_codex_session(
            "codex-1",
            [
                codex_meta_line("codex-1"),
                codex_token_line(40_000, 10_000),
                codex_token_line(120_000, 90_000),
            ],
        )
        self.claim("TICKET-5", "codex-1", agent="codex")

        result = self.ticket("scan", "TICKET-5")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_count"], 1)
        session = payload["sessions"][0]
        self.assertEqual(session["agent"], "codex")
        # Codex counts its cached input inside input_tokens; adding it back
        # would report 210,000 for a turn that cost 120,000.
        self.assertEqual(session["peak_context"], 120_000)

    def test_a_claimed_native_claude_worker_is_measured_as_its_own_session(self):
        worker_id = "worker-synthetic-1"
        directory = self.projects / "synthetic-project" / "parent-synthetic" / "subagents"
        directory.mkdir(parents=True)
        claimed_path = directory / f"agent-{worker_id}.jsonl"
        claimed_path.write_text(assistant_line(130_000, subagent=True) + "\n", encoding="utf-8")
        (directory / f"agent-{worker_id}-near-collision.jsonl").write_text(
            assistant_line(260_000, subagent=True) + "\n", encoding="utf-8"
        )
        # A synthetic chunk worktree of *this* repository: same origin as the
        # real checkout, read at test time rather than hardcoded, so its
        # resolved repository identity collides with the one `scan` (running
        # with cwd=ROOT) resolves for itself. A bare `/tmp` path, or a
        # toplevel-only fixture with no origin, resolves to a repository
        # identity that can never collide with ROOT's — the claim then lands
        # in `excluded_claims` instead of `sessions`, and this test would pass
        # while measuring nothing.
        origin = subprocess.run(
            ["git", "-C", str(ROOT), "remote", "get-url", "origin"],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        ).stdout.strip()
        worker_project = self.scratch / "synthetic-chunk-worktree"
        worker_project.mkdir()
        subprocess.run(
            ["git", "init"], cwd=worker_project, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, check=True,
        )
        subprocess.run(
            ["git", "remote", "add", "origin", origin], cwd=worker_project, check=True,
        )
        worker_project = str(worker_project)
        claim = self.ticket(
            "claim",
            "TICKET-20",
            "--session",
            worker_id,
            "--agent",
            "claude",
            "--project",
            worker_project,
            "--verb",
            "start",
        )
        self.assertEqual(claim.returncode, 0, claim.stderr)

        result = self.ticket("scan", "TICKET-20")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_count"], 1)
        self.assertEqual(payload["peak_context"], 130_000)
        self.assertEqual(payload["subagent_peak"], 0)
        session = payload["sessions"][0]
        self.assertEqual(session["project"], worker_project)
        self.assertEqual(session["transcripts"], [str(claimed_path)])
        self.assertEqual(session["peak_context"], 130_000)
        self.assertEqual(session["subagent_peak"], 0)

    def test_a_claim_whose_transcript_is_missing_is_reported_not_dropped(self):
        self.claim("TICKET-6", "session-gone")

        result = self.ticket("scan", "TICKET-6")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["claim_count"], 1)
        self.assertEqual(payload["session_count"], 0)
        self.assertEqual(payload["unreadable"], ["session-gone"])

        gone = self.ticket(
            "record", "TICKET-6", "--verb", "start", "--trait", "any", "--depth", "deep"
        )

        self.assertEqual(json.loads(gone.stdout)["verdict"], "unmeasurable")
        self.assertIn("transcripts are gone", json.loads(gone.stdout)["reason"])

        # A deleted transcript must not reach the durable record as a session
        # that cost nothing: that is the reading adr-70 rules out.
        self.worked("TICKET-6", "proj-a", "session-2", [assistant_line(190_000)])
        recorded = self.ticket(
            "record", "TICKET-6", "--verb", "start", "--trait", "any", "--depth", "deep"
        )

        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        record = json.loads(recorded.stdout)
        self.assertEqual(record["session_peaks"], [190_000])
        self.assertEqual(record["claim_count"], 2)
        self.assertEqual(record["unreadable"], ["session-gone"])

    def test_two_visible_agent_sessions_refuse_to_guess_which_is_running(self):
        # A Codex worker launched from a Claude session inherits that session's
        # variable. Guessing here would measure the coordinator's transcript.
        environment = self.environment.copy()
        environment["CLAUDE_CODE_SESSION_ID"] = "claude-1"
        environment["CODEX_SESSION_ID"] = "codex-1"

        result = self.ticket("claim", "TICKET-17", "--verb", "start", environment=environment)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--agent", result.stderr)
        self.assertFalse(self.claims.exists())

        chosen = self.ticket(
            "claim", "TICKET-17", "--session", "codex-1", "--agent", "codex",
            "--verb", "start",
            environment=environment,
        )

        self.assertEqual(chosen.returncode, 0, chosen.stderr)
        self.assertEqual(json.loads(chosen.stdout)["agent"], "codex")

    def test_a_session_id_carrying_glob_syntax_is_refused(self):
        # The id reaches a filesystem glob, so "*" would resolve to every
        # transcript on the machine and report their maximum as one session.
        self.write_session("proj-a", "session-1", [assistant_line(200_000)])

        for bad in ("*", "ses?ion-1", "../escape", "a[bc]"):
            with self.subTest(bad=bad):
                result = self.ticket(
                    "claim", "TICKET-19", "--session", bad, "--agent", "claude",
                    "--verb", "start",
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("session id", result.stderr)
        self.assertFalse(self.claims.exists())

    def test_a_resumed_session_is_measured_across_every_file_it_wrote(self):
        directory = self.codex_home / "sessions" / "2026" / "01" / "01"
        directory.mkdir(parents=True, exist_ok=True)
        for stamp, peak in (("00-00-00", 5_000), ("11-00-00", 200_000)):
            (directory / f"rollout-2026-01-01T{stamp}-codex-2.jsonl").write_text(
                "\n".join([codex_meta_line("codex-2"), codex_token_line(peak)]) + "\n",
                encoding="utf-8",
            )
        self.claim("TICKET-18", "codex-2", agent="codex")

        result = self.ticket("scan", "TICKET-18")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["sessions"][0]["transcripts"]), 2)
        self.assertEqual(payload["peak_context"], 200_000)

    def test_record_flat_order_above_degradation_band_is_under_sliced(self):
        self.worked("TICKET-7", "proj-a", "session-1", [assistant_line(200_000)])

        result = self.ticket(
            "record", "TICKET-7", "--verb", "start", "--trait", "large-diff", "--depth", "deep"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "under-sliced")

        record = payload
        self.assertEqual(record["ticket_id"], "TICKET-7")
        self.assertEqual(record["verbs"], ["start"])
        self.assertEqual(record["traits"], ["large-diff"])
        self.assertEqual(record["depth"], "deep")
        self.assertEqual(record["chunked"], False)
        self.assertEqual(record["chunks"], 1)
        self.assertEqual(record["peak_context"], 200_000)
        self.assertEqual(record["verdict"], "under-sliced")
        self.assertIn("recorded_at", record)

    def test_record_without_traits_emits_an_empty_trait_list(self):
        result = self.ticket(
            "record", "TICKET-264", "--verb", "start", "--depth", "targeted"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["traits"], [])

    def test_record_preserves_multiple_traits_in_supplied_order(self):
        result = self.ticket(
            "record", "TICKET-264", "--verb", "start",
            "--trait", "wide-scope", "--trait", "shared-contract",
            "--depth", "targeted",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout)["traits"], ["wide-scope", "shared-contract"]
        )

    def test_record_flat_order_below_band_is_ok(self):
        self.worked("TICKET-8", "proj-a", "session-1", [assistant_line(50_000)])

        result = self.ticket(
            "record", "TICKET-8", "--verb", "start", "--trait", "small-diff", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "ok")

    def test_flat_verdict_uses_only_non_reviewer_start_execution(self):
        self.worked(
            "TICKET-38", "proj-a", "triage-1", [assistant_line(200_000)], verb="triage"
        )
        self.worked(
            "TICKET-38", "proj-a", "start-1", [assistant_line(50_000)], verb="start"
        )
        self.worked(
            "TICKET-38", "proj-a", "review-1", [assistant_line(260_000)],
            role="reviewer", verb="start",
        )
        self.worked(
            "TICKET-38", "proj-a", "revise-1", [assistant_line(230_000)], verb="revise"
        )
        self.worked(
            "TICKET-38", "proj-a", "finalize-1", [assistant_line(240_000)], verb="finalize"
        )

        result = self.ticket(
            "record", "TICKET-38", "--verb", "start", "--trait", "lockstep-copies",
            "--depth", "full",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "ok")
        self.assertIn("50,000", payload["reason"])
        self.assertEqual(payload["peak_context"], 260_000)
        self.assertEqual(
            payload["verb_peaks"],
            {"triage": 200_000, "start": 260_000, "revise": 230_000,
             "finalize": 240_000, "legacy": 0},
        )

    def test_record_without_a_usable_peak_is_unmeasurable(self):
        # A rollout can name its session yet contain no token-count event. It
        # is not evidence that a flat order cost zero tokens.
        self.write_codex_session("codex-no-peak", [codex_meta_line("codex-no-peak")])
        self.claim("TICKET-129A", "codex-no-peak", agent="codex")

        result = self.ticket(
            "record", "TICKET-129A", "--verb", "start", "--trait", "any", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "unmeasurable")
        self.assertIn("no usable context peak", payload["reason"])

    def test_flat_claims_without_measurable_start_execution_are_unmeasurable(self):
        self.worked(
            "TICKET-39A", "proj-a", "triage-only", [assistant_line(200_000)], verb="triage"
        )
        self.claim("TICKET-39B", "start-gone", verb="start")
        self.write_codex_session("start-zero", [codex_meta_line("start-zero")])
        self.claim("TICKET-39C", "start-zero", agent="codex", verb="start")
        self.worked(
            "TICKET-39D", "proj-a", "legacy-only", [assistant_line(220_000)], verb="triage"
        )
        claims = [json.loads(line) for line in self.claims.read_text(encoding="utf-8").splitlines()]
        for claim in claims:
            if claim["ticket_id"] == "TICKET-39D":
                claim.pop("verb")
        self.claims.write_text(
            "\n".join(json.dumps(claim) for claim in claims) + "\n", encoding="utf-8"
        )

        cases = {
            "TICKET-39A": "eligible non-reviewer start",
            "TICKET-39B": "unreadable",
            "TICKET-39C": "no usable context peak",
            "TICKET-39D": "legacy",
        }
        for ticket_id, reason_fragment in cases.items():
            with self.subTest(ticket_id=ticket_id):
                result = self.ticket(
                    "record", ticket_id, "--verb", "finalize", "--trait", "any",
                    "--depth", "full",
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["verdict"], "unmeasurable")
                self.assertIn(reason_fragment, payload["reason"])

    def test_missing_codex_rollout_is_unmeasurable_not_no_data(self):
        self.claim("TICKET-129B", "codex-gone", agent="codex")

        result = self.ticket(
            "record", "TICKET-129B", "--verb", "start", "--trait", "any", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "unmeasurable")
        self.assertIn("Codex session", payload["reason"])
        self.assertIn("rollout files", payload["reason"])

    def test_record_chunked_order_still_degraded_when_a_chunk_peaks_high(self):
        # The chunk's cost is its own claimed worker session, not a sidechain
        # turn in the coordinator's transcript: only an explicit worker claim
        # says a peak belongs to chunk-building work.
        self.worked("TICKET-9", "proj-a", "coordinator-1", [assistant_line(30_000)])
        self.worked(
            "TICKET-9", "proj-a", "worker-1", [assistant_line(190_000)], role="worker"
        )

        result = self.ticket(
            "record", "TICKET-9", "--verb", "start", "--trait", "wide-scope",
            "--depth", "deep", "--chunked", "--chunks", "3",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "still-degraded")

    def test_record_chunked_order_over_sliced_when_every_chunk_is_small(self):
        self.worked("TICKET-10", "proj-a", "coordinator-1", [assistant_line(40_000)])
        for chunk, peak in enumerate((50_000, 45_000, 60_000), start=1):
            self.worked(
                "TICKET-10", "proj-a", f"worker-{chunk}", [assistant_line(peak)], role="worker"
            )

        result = self.ticket(
            "record", "TICKET-10", "--verb", "start", "--trait", "narrow-scope",
            "--depth", "light", "--chunked", "--chunks", "3",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "over-sliced")

    def test_record_chunked_order_with_no_measured_worker_is_coordinator_only(self):
        # The calibration case: a coordinator measured at 387k with no chunk
        # worker measured at all. Reading its peak as chunk size returned
        # still-degraded and drafted a rubric amendment against work that was
        # sliced correctly.
        self.worked("TICKET-24", "proj-a", "coordinator-1", [assistant_line(387_156)])

        result = self.ticket(
            "record", "TICKET-24", "--verb", "start", "--trait", "wide-scope",
            "--depth", "deep", "--chunked", "--chunks", "4",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "coordinator-only")
        self.assertIn("chunk size was not measured", payload["reason"])
        self.assertIn("0 claim(s) carried an implementation-worker role", payload["reason"])
        self.assertEqual(payload["coordinator_peak"], 387_156)
        self.assertEqual(payload["worker_peaks"], [])

    def test_a_coordinator_over_the_band_degrades_an_otherwise_held_slice(self):
        self.worked("TICKET-25", "proj-a", "coordinator-1", [assistant_line(300_000)])
        for chunk, peak in enumerate((150_000, 140_000), start=1):
            self.worked(
                "TICKET-25", "proj-a", f"worker-{chunk}", [assistant_line(peak)], role="worker"
            )

        result = self.ticket(
            "record", "TICKET-25", "--verb", "start", "--trait", "wide-scope",
            "--depth", "deep", "--chunked", "--chunks", "2",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "coordination-degraded")
        self.assertIn("300,000", payload["reason"])
        self.assertIn("180,000", payload["reason"])
        self.assertIn("slice was right", payload["reason"])
        self.assertEqual(payload["coordinator_peak"], 300_000)
        self.assertEqual(payload["worker_peaks"], [150_000, 140_000])

    def test_degraded_worker_wins_over_degraded_coordinator(self):
        self.worked("TICKET-125B", "proj-a", "coordinator-1", [assistant_line(299_000)])
        for chunk, peak in enumerate((190_000, 138_000), start=1):
            self.worked(
                "TICKET-125B", "proj-a", f"worker-{chunk}", [assistant_line(peak)], role="worker"
            )

        result = self.ticket(
            "record", "TICKET-125B", "--verb", "start", "--trait", "wide-scope",
            "--depth", "deep", "--chunked", "--chunks", "2",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "still-degraded")

    def test_over_sliced_workers_win_over_degraded_coordinator(self):
        self.worked("TICKET-125C", "proj-a", "coordinator-1", [assistant_line(299_000)])
        for chunk, peak in enumerate((50_000, 60_000), start=1):
            self.worked(
                "TICKET-125C", "proj-a", f"worker-{chunk}", [assistant_line(peak)], role="worker"
            )

        result = self.ticket(
            "record", "TICKET-125C", "--verb", "start", "--trait", "narrow-scope",
            "--depth", "light", "--chunked", "--chunks", "2",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "over-sliced")

    def test_chunked_order_with_held_workers_and_coordinator_is_ok(self):
        self.worked("TICKET-125D", "proj-a", "coordinator-1", [assistant_line(150_000)])
        for chunk, peak in enumerate((162_000, 138_000), start=1):
            self.worked(
                "TICKET-125D", "proj-a", f"worker-{chunk}", [assistant_line(peak)], role="worker"
            )

        result = self.ticket(
            "record", "TICKET-125D", "--verb", "start", "--trait", "wide-scope",
            "--depth", "deep", "--chunked", "--chunks", "2",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "ok")

    def test_chunked_order_with_held_workers_and_no_coordinator_is_ok(self):
        for chunk, peak in enumerate((162_000, 138_000), start=1):
            self.worked(
                "TICKET-125E", "proj-a", f"worker-{chunk}", [assistant_line(peak)], role="worker"
            )

        result = self.ticket(
            "record", "TICKET-125E", "--verb", "start", "--trait", "wide-scope",
            "--depth", "deep", "--chunked", "--chunks", "2",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "ok")
        self.assertEqual(payload["coordinator_peak"], 0)

    def test_partial_worker_coverage_with_degraded_coordinator_is_ok(self):
        self.worked("TICKET-125F", "proj-a", "coordinator-1", [assistant_line(299_000)])
        self.worked(
            "TICKET-125F", "proj-a", "worker-1", [assistant_line(162_000)], role="worker"
        )

        result = self.ticket(
            "record", "TICKET-125F", "--verb", "start", "--trait", "wide-scope",
            "--depth", "deep", "--chunked", "--chunks", "2",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "ok")

    def test_one_worker_over_the_band_is_still_degraded_under_a_small_coordinator(self):
        self.worked("TICKET-26", "proj-a", "coordinator-1", [assistant_line(60_000)])
        for chunk, peak in enumerate((200_000, 130_000), start=1):
            self.worked(
                "TICKET-26", "proj-a", f"worker-{chunk}", [assistant_line(peak)], role="worker"
            )

        result = self.ticket(
            "record", "TICKET-26", "--verb", "start", "--trait", "wide-scope",
            "--depth", "deep", "--chunked", "--chunks", "2",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "still-degraded")
        self.assertIn("200,000", payload["reason"])

    def test_a_reviewer_peak_changes_no_verdict_on_either_branch(self):
        # Review overhead runs on nearly every ticket and says nothing about
        # how big the work was.
        self.worked("TICKET-27", "proj-a", "flat-1", [assistant_line(90_000)])
        self.worked(
            "TICKET-27", "proj-a", "reviewer-1", [assistant_line(250_000)], role="reviewer"
        )
        self.worked("TICKET-28", "proj-a", "coordinator-1", [assistant_line(70_000)])
        self.worked(
            "TICKET-28", "proj-a", "worker-1", [assistant_line(150_000)], role="worker"
        )
        self.worked(
            "TICKET-28", "proj-a", "reviewer-2", [assistant_line(250_000)], role="reviewer"
        )

        flat = self.ticket(
            "record", "TICKET-27", "--verb", "start", "--trait", "any", "--depth", "light"
        )
        chunked = self.ticket(
            "record", "TICKET-28", "--verb", "start", "--trait", "any", "--depth", "light",
            "--chunked", "--chunks", "2",
        )

        self.assertEqual(json.loads(flat.stdout)["verdict"], "ok")
        self.assertEqual(json.loads(flat.stdout)["reviewer_peak"], 250_000)
        self.assertEqual(json.loads(chunked.stdout)["verdict"], "ok")
        self.assertEqual(json.loads(chunked.stdout)["reviewer_peak"], 250_000)

    def test_a_chunked_order_measuring_only_reviewers_names_that_in_its_reason(self):
        self.worked(
            "TICKET-29", "proj-a", "reviewer-1", [assistant_line(60_000)], role="reviewer"
        )

        result = self.ticket(
            "record", "TICKET-29", "--verb", "start", "--trait", "any", "--depth", "light",
            "--chunked", "--chunks", "2",
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "coordinator-only")
        self.assertIn("only review-only sessions were measured", payload["reason"])

    def test_chunked_claims_written_before_roles_existed_are_coordinator_only(self):
        # A pre-role claim cannot be told apart from a coordinator's, so it is
        # read as `legacy` and never guessed into a worker role.
        self.worked("TICKET-30", "proj-a", "legacy-1", [assistant_line(200_000)])
        # Strip the field back out, which is exactly what a claim written
        # before this field existed looks like on disk.
        self.claims.write_text(
            "\n".join(
                json.dumps({k: v for k, v in json.loads(line).items() if k != "role"})
                for line in self.claims.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
            + "\n",
            encoding="utf-8",
        )

        result = self.ticket(
            "record", "TICKET-30", "--verb", "start", "--trait", "any", "--depth", "deep",
            "--chunked", "--chunks", "3",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "coordinator-only")
        self.assertEqual(payload["legacy_peak"], 200_000)
        self.assertEqual(payload["worker_peaks"], [])

    def test_over_sliced_needs_one_measured_worker_per_chunk(self):
        # An unreadable or never-claimed worker leaves a chunk whose cost is
        # unknown, and an unknown chunk cannot be one of the small ones.
        self.worked("TICKET-31", "proj-a", "coordinator-1", [assistant_line(40_000)])
        self.worked(
            "TICKET-31", "proj-a", "worker-1", [assistant_line(50_000)], role="worker"
        )
        self.claim("TICKET-31", "worker-gone", role="worker")

        result = self.ticket(
            "record", "TICKET-31", "--verb", "start", "--trait", "any", "--depth", "light",
            "--chunked", "--chunks", "3",
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "ok")
        self.assertIn("1 of 3 chunk(s)", payload["reason"])
        self.assertEqual(payload["unreadable"], ["worker-gone"])

        # Same shortfall, no unreadable claim at all: two chunks simply never
        # claimed a worker.
        self.worked("TICKET-32", "proj-a", "coordinator-2", [assistant_line(40_000)])
        self.worked(
            "TICKET-32", "proj-a", "worker-2", [assistant_line(50_000)], role="worker"
        )
        second = self.ticket(
            "record", "TICKET-32", "--verb", "start", "--trait", "any", "--depth", "light",
            "--chunked", "--chunks", "3",
        )

        self.assertEqual(json.loads(second.stdout)["verdict"], "ok")
        self.assertIn("too few to call it over-sliced", json.loads(second.stdout)["reason"])

    def test_a_chunk_that_escalated_a_tier_still_reads_as_over_sliced(self):
        # A chunk whose first agent failed verification escalates, and the
        # escalation is claimed as its own worker session. Two chunks can
        # therefore measure three workers, which is coverage of every chunk,
        # not evidence that a chunk went unmeasured.
        self.worked("TICKET-34", "proj-a", "coordinator-1", [assistant_line(40_000)])
        for chunk, peak in enumerate((50_000, 45_000, 60_000), start=1):
            self.worked(
                "TICKET-34", "proj-a", f"worker-{chunk}", [assistant_line(peak)], role="worker"
            )

        result = self.ticket(
            "record", "TICKET-34", "--verb", "start", "--trait", "any", "--depth", "light",
            "--chunked", "--chunks", "2",
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "over-sliced")
        self.assertIn("60,000", payload["reason"])

    def test_claim_defaults_to_the_coordinator_role_and_rejects_an_invented_one(self):
        claimed = self.claim("TICKET-33", "session-1")

        self.assertEqual(claimed["role"], "coordinator")

        invented = self.ticket(
            "claim", "TICKET-33", "--session", "session-2", "--agent", "claude",
            "--role", "supervisor", "--verb", "start",
        )

        self.assertNotEqual(invented.returncode, 0)
        self.assertIn("--role", invented.stderr)

    def test_claim_requires_a_closed_lifecycle_verb(self):
        missing = self.ticket(
            "claim", "TICKET-35", "--session", "session-1", "--agent", "claude"
        )
        invented = self.ticket(
            "claim", "TICKET-35", "--session", "session-1", "--agent", "claude",
            "--verb", "deploy",
        )

        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("--verb", missing.stderr)
        self.assertNotEqual(invented.returncode, 0)
        self.assertIn("invalid choice", invented.stderr)
        self.assertFalse(self.claims.exists())

    def test_cross_verb_reclaim_keeps_and_prints_the_persisted_claim(self):
        original = self.claim("TICKET-36", "session-1", verb="start")

        result = self.ticket(
            "claim", "TICKET-36", "--session", "session-1", "--agent", "claude",
            "--verb", "revise",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verb"], "start")
        self.assertEqual(payload["claimed_at"], original["claimed_at"])
        self.assertTrue(payload["already_claimed"])
        self.assertIn("persisted verb 'start'", result.stderr)
        self.assertIn("submitted verb 'revise'", result.stderr)
        lines = self.claims.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len([line for line in lines if line.strip()]), 1)

    def test_scan_reports_session_verbs_and_fixed_peak_maxima(self):
        self.worked(
            "TICKET-37", "proj-a", "triage-1", [assistant_line(200_000)], verb="triage"
        )
        self.worked(
            "TICKET-37", "proj-a", "start-1", [assistant_line(50_000)], verb="start"
        )
        self.worked(
            "TICKET-37", "proj-a", "start-2", [assistant_line(70_000)], verb="start"
        )
        self.worked(
            "TICKET-37", "proj-a", "legacy-1", [assistant_line(90_000)], verb="finalize"
        )
        claims = [json.loads(line) for line in self.claims.read_text(encoding="utf-8").splitlines()]
        for claim in claims:
            if claim["session_id"] == "legacy-1":
                claim.pop("verb")
        self.claims.write_text(
            "\n".join(json.dumps(claim) for claim in claims) + "\n", encoding="utf-8"
        )

        result = self.ticket("scan", "TICKET-37")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["verb_peaks"],
            {"triage": 200_000, "start": 70_000, "revise": 0, "finalize": 0, "legacy": 90_000},
        )
        self.assertEqual(
            {session["session_id"]: session["verb"] for session in payload["sessions"]},
            {"triage-1": "triage", "start-1": "start", "start-2": "start", "legacy-1": "legacy"},
        )

    def test_record_with_no_claim_is_no_data(self):
        result = self.ticket(
            "record", "TICKET-11", "--verb", "start", "--trait", "any", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "no-data")

    def test_subagent_peak_is_counted_separately_from_the_main_session_peak(self):
        self.worked(
            "TICKET-12",
            "proj-a",
            "session-1",
            [assistant_line(60_000), assistant_line(140_000, subagent=True)],
        )

        result = self.ticket("scan", "TICKET-12")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["sessions"][0]["peak_context"], 60_000)
        self.assertEqual(payload["sessions"][0]["subagent_peak"], 140_000)

    def test_malformed_line_is_skipped_and_the_rest_of_the_session_still_scans(self):
        # A malformed line is external input (a local file this process did not
        # write): the scan skips it and keeps reading the rest of the file
        # rather than failing the whole session.
        self.worked(
            "TICKET-13",
            "proj-a",
            "session-1",
            ["not valid json", assistant_line(70_000)],
        )

        result = self.ticket("scan", "TICKET-13")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_count"], 1)
        self.assertEqual(payload["sessions"][0]["peak_context"], 70_000)

    def test_empty_and_whitespace_ids_are_rejected(self):
        for bad_id in ("", "TICKET 14", " "):
            with self.subTest(bad_id=bad_id):
                result = self.ticket(
                    "record", bad_id, "--verb", "start", "--trait", "any", "--depth", "light"
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ticket:", result.stderr)

    def test_record_stdout_carries_no_prose_from_the_session(self):
        secret_prose = "quietly worried this deadline is unrealistic and stressful"
        self.worked(
            "TICKET-16",
            "proj-a",
            "session-1",
            [user_line(secret_prose), assistant_line(10_000)],
        )

        result = self.ticket(
            "record", "TICKET-16", "--verb", "start", "--trait", "any", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("unrealistic", result.stdout)
        self.assertNotIn(secret_prose, result.stdout)
        claimed = self.claims.read_text(encoding="utf-8")
        self.assertNotIn("unrealistic", claimed)
        self.assertNotIn(secret_prose, claimed)

    def make_repo_checkout(self, name: str, origin_url: str) -> Path:
        checkout = self.scratch / name
        checkout.mkdir()
        subprocess.run(
            ["git", "init"], cwd=checkout, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, check=True,
        )
        subprocess.run(
            ["git", "remote", "add", "origin", origin_url], cwd=checkout, check=True,
        )
        return checkout

    def test_scan_partitions_claims_by_repository(self):
        # Two repositories sharing one ticket id: each one's own scan must see
        # only its own session, and count the other repository's claim
        # without folding it in. A plain temp directory with no `git init`
        # cannot stand in for either side here, because two origin-less
        # checkouts both resolve to `None` and would be indistinguishable.
        repo_a = self.make_repo_checkout("repo-a", "https://example.com/org/repo-a.git")
        repo_b = self.make_repo_checkout("repo-b", "https://example.com/org/repo-b.git")

        self.write_session("proj-a", "session-a", [assistant_line(40_000)])
        self.write_session("proj-b", "session-b", [assistant_line(70_000)])

        claim_a = self.ticket(
            "claim", "TICKET-21", "--session", "session-a", "--agent", "claude",
            "--verb", "start",
            "--project", str(repo_a),
        )
        self.assertEqual(claim_a.returncode, 0, claim_a.stderr)
        claim_b = self.ticket(
            "claim", "TICKET-21", "--session", "session-b", "--agent", "claude",
            "--verb", "start",
            "--project", str(repo_b),
        )
        self.assertEqual(claim_b.returncode, 0, claim_b.stderr)

        scan_a = self.ticket("scan", "TICKET-21", cwd=repo_a)
        scan_b = self.ticket("scan", "TICKET-21", cwd=repo_b)

        self.assertEqual(scan_a.returncode, 0, scan_a.stderr)
        self.assertEqual(scan_b.returncode, 0, scan_b.stderr)
        payload_a = json.loads(scan_a.stdout)
        payload_b = json.loads(scan_b.stdout)

        self.assertEqual([s["session_id"] for s in payload_a["sessions"]], ["session-a"])
        self.assertEqual(payload_a["peak_context"], 40_000)
        self.assertEqual(payload_a["excluded_claims"], 1)
        self.assertEqual(payload_a["unattributable"], [])

        self.assertEqual([s["session_id"] for s in payload_b["sessions"]], ["session-b"])
        self.assertEqual(payload_b["peak_context"], 70_000)
        self.assertEqual(payload_b["excluded_claims"], 1)
        self.assertEqual(payload_b["unattributable"], [])

    def test_scan_and_record_can_target_a_claimed_worktree_from_another_checkout(self):
        repo_a = self.make_repo_checkout("target-repo", "https://example.com/org/target.git")
        repo_b = self.make_repo_checkout("coordinator-repo", "https://example.com/org/coordinator.git")
        self.write_session("proj-a", "target-session", [assistant_line(200_000)])

        claimed = self.ticket(
            "claim", "TICKET-129C", "--session", "target-session", "--agent", "claude",
            "--verb", "start",
            "--project", str(repo_a),
        )
        self.assertEqual(claimed.returncode, 0, claimed.stderr)

        wrong_scan = self.ticket("scan", "TICKET-129C", cwd=repo_b)
        self.assertEqual(wrong_scan.returncode, 0, wrong_scan.stderr)
        self.assertEqual(json.loads(wrong_scan.stdout)["excluded_claims"], 1)
        self.assertEqual(json.loads(wrong_scan.stdout)["session_count"], 0)

        scan = self.ticket("scan", "TICKET-129C", "--project", str(repo_a), cwd=repo_b)
        self.assertEqual(scan.returncode, 0, scan.stderr)
        self.assertEqual(json.loads(scan.stdout)["session_count"], 1)
        self.assertEqual(json.loads(scan.stdout)["excluded_claims"], 0)

        wrong_record = self.ticket(
            "record", "TICKET-129C", "--verb", "start", "--trait", "any", "--depth", "deep",
            cwd=repo_b,
        )
        self.assertEqual(wrong_record.returncode, 0, wrong_record.stderr)
        self.assertEqual(json.loads(wrong_record.stdout)["verdict"], "no-data")

        record = self.ticket(
            "record", "TICKET-129C", "--verb", "start", "--trait", "any", "--depth", "deep",
            "--project", str(repo_a), cwd=repo_b,
        )
        self.assertEqual(record.returncode, 0, record.stderr)
        payload = json.loads(record.stdout)
        self.assertEqual(payload["verdict"], "under-sliced")
        self.assertEqual(payload["excluded_claims"], 0)
        self.assertEqual(payload["repo"], "example.com/org/target")

    def test_unlabelled_legacy_claim_is_unattributable_not_counted(self):
        # A claim written before `repo` existed carries no such key at all.
        # It must be named, not folded into either "nothing claimed this" or
        # a real session count.
        self.claims.parent.mkdir(parents=True, exist_ok=True)
        legacy_claim = {
            "ticket_id": "TICKET-22",
            "session_id": "legacy-session",
            "agent": "claude",
            "project": "/some/old/path",
            "claimed_at": "2026-01-01T00:00:00+00:00",
        }
        with self.claims.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(legacy_claim) + "\n")

        scan_result = self.ticket("scan", "TICKET-22")
        self.assertEqual(scan_result.returncode, 0, scan_result.stderr)
        payload = json.loads(scan_result.stdout)
        self.assertEqual(payload["session_count"], 0)
        self.assertEqual(payload["claim_count"], 0)
        self.assertEqual(payload["unattributable"], ["legacy-session"])

        # `verdict` returns `no-data` for an unlabelled claim alone, and
        # `command_record` never persists a `no-data` record — so a second,
        # ordinary same-repository claim is needed for `record` to persist
        # anything the `unattributable` field can be asserted against.
        self.worked("TICKET-22", "proj-a", "session-real", [assistant_line(55_000)])

        record_result = self.ticket(
            "record", "TICKET-22", "--verb", "start", "--trait", "any", "--depth", "light"
        )
        self.assertEqual(record_result.returncode, 0, record_result.stderr)
        payload = json.loads(record_result.stdout)
        self.assertNotEqual(payload["verdict"], "no-data")
        self.assertEqual(payload["unattributable"], ["legacy-session"])
        self.assertEqual(payload["session_count"], 1)
        self.assertEqual(payload["peak_context"], 55_000)

    def test_ssh_and_https_remotes_for_one_repository_collide_to_the_same_identity(self):
        # An ssh remote and an https remote naming the same repository must
        # resolve to one identity, or a claim made through one form and a
        # scan run from a checkout using the other form would wrongly land
        # in excluded_claims instead of being recognised as the same
        # repository. Exercised through claim/scan (the public interface),
        # not by calling _normalize_remote directly.
        ssh_checkout = self.make_repo_checkout(
            "ssh-checkout", "git@github.com:fixture/repo.git"
        )
        https_checkout = self.make_repo_checkout(
            "https-checkout", "https://github.com/fixture/repo.git"
        )

        self.write_session("proj-a", "session-ssh", [assistant_line(45_000)])

        claimed = self.ticket(
            "claim", "TICKET-23", "--session", "session-ssh", "--agent", "claude",
            "--verb", "start",
            "--project", str(ssh_checkout),
        )
        self.assertEqual(claimed.returncode, 0, claimed.stderr)

        scanned = self.ticket("scan", "TICKET-23", cwd=https_checkout)

        self.assertEqual(scanned.returncode, 0, scanned.stderr)
        payload = json.loads(scanned.stdout)
        self.assertEqual([s["session_id"] for s in payload["sessions"]], ["session-ssh"])
        self.assertEqual(payload["peak_context"], 45_000)
        self.assertEqual(payload["excluded_claims"], 0)
        self.assertEqual(payload["unattributable"], [])


class TicketOpenSpecPreflightTests(unittest.TestCase):
    """Exercise the shipped command against disposable Git and OpenSpec inputs."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.preflight_tmp = Path(self.temporary.name) / "preflight-tmp"
        self.preflight_tmp.mkdir()
        self.repo = Path(self.temporary.name) / "ticket"
        self.repo.mkdir()
        for command in (
            ["git", "init", "-b", "main"],
            ["git", "config", "user.email", "ticket@example.test"],
            ["git", "config", "user.name", "Ticket test"],
        ):
            subprocess.run(command, cwd=self.repo, check=True, stdout=subprocess.DEVNULL)
        (self.repo / "openspec/specs/widget").mkdir(parents=True)
        (self.repo / "openspec/specs/widget/spec.md").write_text("# Widget\n", encoding="utf-8")
        self.git("add", "openspec")
        self.git("commit", "-m", "base")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        self.change("one")
        self.git("add", "openspec")
        self.git("commit", "-m", "change one")
        self.bin = Path(self.temporary.name) / "bin"
        self.bin.mkdir()
        fake = self.bin / "openspec"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "mode = os.environ.get('FAKE_OPENSPEC_MODE', 'ok')\n"
            "if mode == 'launch': raise OSError('launch denied')\n"
            "if mode == 'nonjson': print('not json')\n"
            "elif mode == 'nonjson-stderr': print('not json'); "
            "print('archive parser failed\\ninspect change delta', file=sys.stderr)\n"
            "elif mode == 'array': print('[]')\n"
            "elif mode == 'nostatus': print(json.dumps({'archive': {}}))\n"
            "elif mode == 'missing': print(json.dumps({'status': []}))\n"
            "elif mode == 'nullarchive': print(json.dumps({'status': [], 'archive': None}))\n"
            "elif mode == 'badarchive': print(json.dumps({'status': [], 'archive': 'wrong'}))\n"
            "elif mode == 'badstatus': print(json.dumps({'status': [1], 'archive': {}}))\n"
            "elif mode == 'error': print(json.dumps({'status': [{'severity': 'error', 'message': 'archive failed'}], 'archive': {}}))\n"
            "elif mode == 'rename': print(json.dumps({'status': [{'severity': 'error', 'code': 'archive_spec_update_failed', 'message': 'unmatched requirement'}], 'archive': {}}))\n"
            "elif mode == 'base-sensitive' and 'new baseline' in open('openspec/specs/widget/spec.md').read(): print(json.dumps({'status': [{'severity': 'error', 'message': 'base advanced'}], 'archive': {}}))\n"
            "else: print(json.dumps({'status': [], 'archive': {}}))\n"
            "sys.exit(7 if mode == 'nonzero' else 0)\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        self.environment = os.environ.copy()
        self.environment["PATH"] = f"{self.bin}{os.pathsep}{self.environment['PATH']}"
        self.environment["TMPDIR"] = str(self.preflight_tmp)

    def tearDown(self):
        self.temporary.cleanup()

    def git(self, *arguments: str):
        return run(["git", *arguments], cwd=self.repo)

    def change(self, name: str):
        directory = self.repo / "openspec/changes" / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "proposal.md").write_text("# Change\n", encoding="utf-8")

    def preflight(self, base: str | None = None, mode: str = "ok"):
        environment = self.environment.copy()
        environment["FAKE_OPENSPEC_MODE"] = mode
        base_argument = f"--base-ref={base}" if (base or "").startswith("-") else "--base-ref"
        result = run(
            [sys.executable, str(TICKET_SCRIPT), "preflight-openspec", "--repo", str(self.repo),
             base_argument, *( [base] if base_argument == "--base-ref" else [])] if base else
            [sys.executable, str(TICKET_SCRIPT), "preflight-openspec", "--repo", str(self.repo),
             "--base-ref", self.base],
            cwd=self.repo,
            env=environment,
        )
        self.assertEqual(list(self.preflight_tmp.glob("ticket-openspec-preflight-*")), [])
        return result

    def tree(self, revision: str = "HEAD") -> str:
        return self.git("rev-parse", f"{revision}:openspec").stdout.strip()

    def install_command_recorders(self, calls: Path):
        for name, executable in (("git", "/usr/bin/git"), ("openspec", None)):
            wrapper = self.bin / name
            wrapper.write_text(
                "#!/bin/sh\n"
                f"printf '%s\\n' \"{name} $*\" >> {calls}\n"
                + (f'exec {executable} "$@"\n' if executable else "exit 0\n"),
                encoding="utf-8",
            )
            wrapper.chmod(0o755)

    def test_success_resolves_local_non_main_base_and_keeps_both_trees_unchanged(self):
        self.git("branch", "release-base", self.base)
        ticket_tree, base_tree = self.tree(), self.tree("release-base")
        result = self.preflight("release-base")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OpenSpec change one applies cleanly", result.stdout)
        self.assertEqual((ticket_tree, base_tree), (self.tree(), self.tree("release-base")))
        self.assertEqual(self.git("status", "--short").stdout, "")

    def test_filter_capable_tar_api_keeps_public_stderr_clean(self):
        hooks = Path(self.temporary.name) / "filter-capable-tar"
        hooks.mkdir()
        (hooks / "sitecustomize.py").write_text(
            "import inspect, tarfile, warnings\n"
            "original_extract = tarfile.TarFile.extract\n"
            "missing = object()\n"
            "def extract(self, member, path='', set_attrs=True, *, "
            "numeric_owner=False, filter=missing):\n"
            "    if filter is missing:\n"
            "        warnings.warn('default extraction filter used', DeprecationWarning)\n"
            "    options = ({'filter': filter} if "
            "'filter' in inspect.signature(original_extract).parameters else {})\n"
            "    return original_extract(self, member, path, set_attrs, "
            "numeric_owner=numeric_owner, **options)\n"
            "tarfile.TarFile.extract = extract\n",
            encoding="utf-8",
        )
        self.environment["PYTHONPATH"] = str(hooks)
        self.environment["PYTHONWARNINGS"] = "error::DeprecationWarning"

        result = self.preflight()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def test_legacy_tar_api_keeps_public_stderr_clean(self):
        hooks = Path(self.temporary.name) / "legacy-tar"
        hooks.mkdir()
        (hooks / "sitecustomize.py").write_text(
            "import inspect, tarfile\n"
            "original_extract = tarfile.TarFile.extract\n"
            "options = ({'filter': 'data'} if "
            "'filter' in inspect.signature(original_extract).parameters else {})\n"
            "def extract(self, member, path='', set_attrs=True, *, numeric_owner=False):\n"
            "    return original_extract(self, member, path, set_attrs, "
            "numeric_owner=numeric_owner, **options)\n"
            "tarfile.TarFile.extract = extract\n",
            encoding="utf-8",
        )
        self.environment["PYTHONPATH"] = str(hooks)

        result = self.preflight()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def test_unresolved_and_option_shaped_bases_do_not_invoke_a_remote(self):
        calls = Path(self.temporary.name) / "git-calls"
        real_git = subprocess.run(["git", "--exec-path"], text=True, capture_output=True).returncode
        self.assertEqual(real_git, 0)
        wrapper = self.bin / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' \"$*\" >> {calls}\n"
            "exec /usr/bin/git \"$@\"\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        for base in ("missing", "--not-a-ref", "HEAD^{tree}"):
            with self.subTest(base=base):
                result = self.preflight(base)
                self.assertEqual(result.returncode, 2)
                self.assertIn(f"base ref does not resolve to a local commit: {base}", result.stderr)
        recorded = calls.read_text(encoding="utf-8")
        self.assertNotRegex(recorded, r"(?:fetch|pull|push|ls-remote|remote)")

    def test_discovery_handles_zero_deleted_and_multiple_active_changes(self):
        active = self.repo / "openspec/changes/one"
        (self.repo / "openspec/changes/archive").mkdir()
        active.rename(self.repo / "openspec/changes/archive/one")
        self.git("add", "-A")
        self.git("commit", "-m", "archive change")
        deleted = self.preflight()
        self.assertEqual(deleted.returncode, 0)
        self.assertIn("no changed active OpenSpec change", deleted.stdout)
        self.change("two")
        self.git("add", "openspec")
        self.git("commit", "-m", "change two")
        self.change("three")
        self.git("add", "openspec")
        self.git("commit", "-m", "change three")
        multiple = self.preflight()
        self.assertEqual(multiple.returncode, 2)
        self.assertIn("more than one changed active OpenSpec change: three, two", multiple.stderr)

    def test_archive_json_contract_and_rename_diagnostic_leave_authoritative_trees_intact(self):
        for mode, diagnostic in (
            ("nonjson", "ticket: OpenSpec archive returned invalid JSON\n"),
            ("array", "ticket: OpenSpec archive JSON must be an object\n"),
            ("nostatus", None),
            ("missing", "ticket: OpenSpec archive result must be a non-null object\n"),
            ("nullarchive", "ticket: OpenSpec archive result must be a non-null object\n"),
            ("badarchive", "ticket: OpenSpec archive result must be a non-null object\n"),
            ("badstatus", "ticket: OpenSpec archive status must be a list of objects\n"),
            ("error", "ticket: archive failed\n"),
            ("nonzero", "ticket: OpenSpec archive exited with status 7\n"),
            (
                "rename",
                "ticket: unmatched requirement\n"
                "ticket: if this requirement was renamed, add a `## RENAMED Requirements` "
                "mapping from its current baseline header to the unmatched delta header; "
                "otherwise correct the MODIFIED header.\n",
            ),
        ):
            with self.subTest(mode=mode):
                before = (self.tree(), self.tree(self.base))
                result = self.preflight(mode=mode)
                if diagnostic is None:
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stderr, diagnostic)
                self.assertEqual(before, (self.tree(), self.tree(self.base)))
                self.assertEqual(self.git("status", "--short").stdout, "")

    def test_malformed_archive_stdout_preserves_stderr_in_one_diagnostic(self):
        result = self.preflight(mode="nonjson-stderr")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "ticket: OpenSpec archive returned invalid JSON: "
            "archive parser failed\\ninspect change delta\n",
        )
        self.assertEqual(result.stderr.count("ticket:"), 1)
        self.assertNotIn("Traceback", result.stderr)

    def test_launch_export_and_symlink_failures_are_clean_and_disposable(self):
        fake = self.bin / "openspec"
        fake.rename(self.bin / "openspec.saved")
        fake.mkdir()
        (self.bin / "git").symlink_to("/usr/bin/git")
        self.environment["PATH"] = str(self.bin)
        launch = self.preflight()
        self.assertNotEqual(launch.returncode, 0)
        self.assertIn("could not launch OpenSpec archive", launch.stderr)
        self.assertNotIn("Traceback", launch.stderr)

        fake.rmdir()
        (self.bin / "openspec.saved").rename(fake)
        (self.bin / "git").unlink()
        self.environment["PATH"] = f"{self.bin}{os.pathsep}{os.environ['PATH']}"
        wrapper = self.bin / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = archive ]; then exit 9; fi\n"
            "exec /usr/bin/git \"$@\"\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        exported = self.preflight()
        self.assertNotEqual(exported.returncode, 0)
        self.assertIn("could not export the base OpenSpec tree", exported.stderr)
        self.assertNotIn("Traceback", exported.stderr)

        wrapper.unlink()
        link = self.repo / "openspec/changes/one/link"
        link.symlink_to("proposal.md")
        linked = self.preflight()
        self.assertEqual(linked.returncode, 2)
        self.assertIn("active OpenSpec change contains a symlink", linked.stderr)
        self.assertNotIn("Traceback", linked.stderr)

    def test_symlinked_openspec_root_is_rejected_before_external_reads_or_commands(self):
        external = Path(self.temporary.name) / "external-openspec"
        shutil.copytree(self.repo / "openspec", external)
        external_before = directory_digest(external)
        base_before = git_directory_digest(self.repo, self.base, "openspec")
        shutil.rmtree(self.repo / "openspec")
        (self.repo / "openspec").symlink_to(external, target_is_directory=True)

        calls = Path(self.temporary.name) / "external-calls"
        self.install_command_recorders(calls)

        result = self.preflight()

        self.assertEqual(
            result.returncode,
            2,
            result.stdout
            + result.stderr
            + (calls.read_text(encoding="utf-8") if calls.exists() else ""),
        )
        self.assertEqual(
            result.stderr,
            f"ticket: OpenSpec root must not be a symlink: {self.repo.resolve() / 'openspec'}\n",
        )
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(calls.exists())
        self.assertEqual(external_before, directory_digest(external))
        self.assertEqual(
            base_before, git_directory_digest(self.repo, self.base, "openspec")
        )

    def test_symlinked_active_change_is_rejected_before_export_or_archive(self):
        active = self.repo / "openspec/changes/one"
        external = Path(self.temporary.name) / "external-change"
        shutil.copytree(active, external)
        external_before = directory_digest(external)
        base_before = git_directory_digest(self.repo, self.base, "openspec")
        shutil.rmtree(active)
        active.symlink_to(external, target_is_directory=True)
        self.git("add", "-A")
        self.git("commit", "-m", "replace active change with symlink")

        calls = Path(self.temporary.name) / "external-calls"
        self.install_command_recorders(calls)

        result = self.preflight()

        self.assertEqual(
            result.returncode,
            2,
            result.stdout
            + result.stderr
            + (calls.read_text(encoding="utf-8") if calls.exists() else ""),
        )
        self.assertEqual(
            result.stderr,
            "ticket: active OpenSpec change contains a symlink\n",
        )
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)
        recorded = calls.read_text(encoding="utf-8")
        self.assertNotIn("git archive ", recorded)
        self.assertNotIn("openspec ", recorded)
        self.assertEqual(external_before, directory_digest(external))
        self.assertEqual(
            base_before, git_directory_digest(self.repo, self.base, "openspec")
        )

    def test_overlay_failure_is_diagnostic_and_cleans_the_disposable_tree(self):
        wrapper = self.bin / "git"
        moved_change = Path(self.temporary.name) / "moved-change"
        ticket_before = directory_digest(self.repo / "openspec")
        base_before = git_directory_digest(self.repo, self.base, "openspec")
        wrapper.write_text(
            "#!/bin/sh\n"
            "/usr/bin/git \"$@\"\n"
            "status=$?\n"
            f"if [ \"$1\" = archive ]; then mv {self.repo / 'openspec/changes/one'} {moved_change}; fi\n"
            "exit $status\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

        environment = self.environment.copy()
        environment["FAKE_OPENSPEC_MODE"] = "ok"
        try:
            result = run(
                [
                    sys.executable,
                    str(TICKET_SCRIPT),
                    "preflight-openspec",
                    "--repo",
                    str(self.repo),
                    "--base-ref",
                    self.base,
                ],
                cwd=self.repo,
                env=environment,
            )
        finally:
            if moved_change.exists():
                moved_change.rename(self.repo / "openspec/changes/one")

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "ticket: could not overlay the active OpenSpec change\n")
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(ticket_before, directory_digest(self.repo / "openspec"))
        self.assertEqual(base_before, git_directory_digest(self.repo, self.base, "openspec"))
        self.assertEqual(list(self.preflight_tmp.glob("ticket-openspec-preflight-*")), [])

    def test_stale_tracking_base_passes_until_a_real_fetch_refreshes_it(self):
        remote = Path(self.temporary.name) / "remote.git"
        upstream = Path(self.temporary.name) / "upstream"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "clone", str(self.repo), str(upstream)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(upstream), "remote", "set-url", "origin", str(remote)], check=True)
        subprocess.run(["git", "-C", str(upstream), "config", "user.email", "ticket@example.test"], check=True)
        subprocess.run(["git", "-C", str(upstream), "config", "user.name", "Ticket test"], check=True)
        subprocess.run(["git", "-C", str(upstream), "push", "-u", "origin", "main"], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"], check=True)
        ticket = Path(self.temporary.name) / "ticket-clone"
        subprocess.run(["git", "clone", str(remote), str(ticket)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(ticket), "config", "user.email", "ticket@example.test"], check=True)
        subprocess.run(["git", "-C", str(ticket), "config", "user.name", "Ticket test"], check=True)
        change = ticket / "openspec/changes/gate"
        change.mkdir(parents=True)
        (change / "proposal.md").write_text("# Gate\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(ticket), "add", "openspec"], check=True)
        subprocess.run(["git", "-C", str(ticket), "commit", "-m", "gate"], check=True, stdout=subprocess.DEVNULL)
        (upstream / "openspec/specs/widget/spec.md").write_text("# Widget\nnew baseline\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(upstream), "add", "openspec"], check=True)
        identity_environment = os.environ.copy()
        identity_environment["GIT_CONFIG_GLOBAL"] = os.devnull
        identity_environment["GIT_CONFIG_NOSYSTEM"] = "1"
        subprocess.run(
            ["git", "-C", str(upstream), "commit", "-m", "advance"],
            check=True,
            stdout=subprocess.DEVNULL,
            env=identity_environment,
        )
        subprocess.run(["git", "-C", str(upstream), "push"], check=True, stdout=subprocess.DEVNULL)
        original_repo = self.repo
        self.repo = ticket
        try:
            stale = self.preflight("origin/main", "base-sensitive")
            self.assertEqual(stale.returncode, 0, stale.stderr)
            subprocess.run(["git", "-C", str(ticket), "fetch", "origin"], check=True, stdout=subprocess.DEVNULL)
            refreshed = self.preflight("origin/main", "base-sensitive")
        finally:
            self.repo = original_repo
        self.assertNotEqual(refreshed.returncode, 0)
        self.assertIn("base advanced", refreshed.stderr)


class TicketOpenSpecRealSemanticTests(unittest.TestCase):
    BASELINE = """# Widget

## Purpose

Define the manufactured widget behavior.

## Requirements

### Requirement: Existing behavior

The widget MUST preserve its existing behavior.

#### Scenario: Existing behavior is requested

- **WHEN** a caller requests existing behavior
- **THEN** the widget preserves it

### Requirement: Stable behavior

The widget MUST preserve its stable behavior.

#### Scenario: Stable behavior is requested

- **WHEN** a caller requests stable behavior
- **THEN** the widget preserves it
"""
    ISSUE_259_DELTA = """## MODIFIED Requirements

### Requirement: Renamed behavior

The widget MUST preserve its renamed behavior.

#### Scenario: Renamed behavior is requested

- **WHEN** a caller requests renamed behavior
- **THEN** the widget preserves it
"""
    APPLICABLE_DELTAS = {
        "added": """## ADDED Requirements

### Requirement: Added behavior

The widget MUST provide added behavior.

#### Scenario: Added behavior is requested

- **WHEN** a caller requests added behavior
- **THEN** the widget provides it
""",
        "modified": """## MODIFIED Requirements

### Requirement: Existing behavior

The widget MUST preserve its updated existing behavior.

#### Scenario: Existing behavior is requested

- **WHEN** a caller requests updated existing behavior
- **THEN** the widget preserves the updated behavior
""",
        "removed": """## REMOVED Requirements

### Requirement: Existing behavior

**Reason**: The manufactured behavior is no longer required.
""",
        "renamed": """## MODIFIED Requirements

### Requirement: Renamed behavior

The widget MUST preserve its renamed behavior.

#### Scenario: Existing behavior is requested

- **WHEN** a caller requests renamed behavior
- **THEN** the widget preserves it

## RENAMED Requirements

- FROM: `### Requirement: Existing behavior`
- TO: `### Requirement: Renamed behavior`
""",
    }

    @classmethod
    def setUpClass(cls):
        executable = shutil.which("openspec")
        if executable is None:
            raise unittest.SkipTest("real installed OpenSpec executable is required")
        cls.openspec = Path(executable)
        version = subprocess.run(
            [str(cls.openspec), "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if version.returncode or version.stdout.strip() != "1.11.0":
            raise AssertionError(
                f"OpenSpec 1.11.0 is required, got {version.stdout.strip()!r}: {version.stderr}"
            )

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.preflight_tmp = self.root / "preflight-tmp"
        self.preflight_tmp.mkdir()
        self.environment = os.environ.copy()
        self.environment["PATH"] = (
            f"{self.openspec.parent}{os.pathsep}{self.environment['PATH']}"
        )
        self.environment["TMPDIR"] = str(self.preflight_tmp)

    def tearDown(self):
        self.temporary.cleanup()

    def make_repo(self, change: str, delta: str) -> tuple[Path, str]:
        repo = self.root / change
        repo.mkdir()
        for command in (
            ["git", "init", "-b", "main"],
            ["git", "config", "user.email", "ticket@example.test"],
            ["git", "config", "user.name", "Ticket test"],
        ):
            subprocess.run(command, cwd=repo, check=True, stdout=subprocess.DEVNULL)
        (repo / "openspec/specs/widget").mkdir(parents=True)
        (repo / "openspec/config.yaml").write_text("schema: spec-driven\n", encoding="utf-8")
        (repo / "openspec/specs/widget/spec.md").write_text(
            self.BASELINE, encoding="utf-8"
        )
        subprocess.run(["git", "add", "openspec"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "baseline"],
            cwd=repo,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.strip()
        change_root = repo / "openspec/changes" / change
        (change_root / "specs/widget").mkdir(parents=True)
        (change_root / "proposal.md").write_text(
            f"# {change}\n\n## Why\n\nManufactured semantic regression.\n\n"
            "## What Changes\n\n- Exercise real OpenSpec composition.\n",
            encoding="utf-8",
        )
        (change_root / "tasks.md").write_text(
            "## 1. Verification\n\n- [ ] Exercise the manufactured delta.\n",
            encoding="utf-8",
        )
        (change_root / "specs/widget/spec.md").write_text(delta, encoding="utf-8")
        subprocess.run(["git", "add", "openspec"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", change],
            cwd=repo,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        return repo, base

    def validate(self, repo: Path, change: str):
        return run(
            [str(self.openspec), "validate", change, "--strict"],
            cwd=repo,
            env=self.environment,
        )

    def preflight(self, repo: Path, base: str):
        result = run(
            [
                sys.executable,
                str(TICKET_SCRIPT),
                "preflight-openspec",
                "--repo",
                str(repo),
                "--base-ref",
                base,
            ],
            cwd=repo,
            env=self.environment,
        )
        self.assertEqual(list(self.preflight_tmp.glob("ticket-openspec-preflight-*")), [])
        return result

    def test_real_issue_259_delta_validates_strictly_but_fails_archive_applicability(self):
        change = "issue-259"
        repo, base = self.make_repo(change, self.ISSUE_259_DELTA)
        ticket_before = directory_digest(repo / "openspec")
        base_before = git_directory_digest(repo, base, "openspec")

        validated = self.validate(repo, change)
        result = self.preflight(repo, base)

        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(validated.stdout, "Change 'issue-259' is valid\n")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr,
            "ticket: widget MODIFIED failed for header \"### Requirement: Renamed behavior\" - not found\n"
            "ticket: if this requirement was renamed, add a `## RENAMED Requirements` "
            "mapping from its current baseline header to the unmatched delta header; "
            "otherwise correct the MODIFIED header.\n",
        )
        self.assertEqual(ticket_before, directory_digest(repo / "openspec"))
        self.assertEqual(base_before, git_directory_digest(repo, base, "openspec"))

    def test_real_added_modified_removed_and_renamed_deltas_apply_cleanly(self):
        for operation, delta in self.APPLICABLE_DELTAS.items():
            with self.subTest(operation=operation):
                repo, base = self.make_repo(operation, delta)
                ticket_before = directory_digest(repo / "openspec")
                base_before = git_directory_digest(repo, base, "openspec")

                validated = self.validate(repo, operation)
                result = self.preflight(repo, base)

                self.assertEqual(validated.returncode, 0, validated.stderr)
                self.assertEqual(validated.stdout, f"Change '{operation}' is valid\n")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(
                    result.stdout,
                    f"ticket: OpenSpec change {operation} applies cleanly in a disposable copy\n",
                )
                self.assertEqual(ticket_before, directory_digest(repo / "openspec"))
                self.assertEqual(base_before, git_directory_digest(repo, base, "openspec"))


class TicketOpenSpecRealSemanticSetupTests(unittest.TestCase):
    def test_missing_openspec_skips_real_semantic_tests(self):
        with mock.patch.object(shutil, "which", return_value=None):
            with self.assertRaisesRegex(
                unittest.SkipTest, "real installed OpenSpec executable is required"
            ):
                TicketOpenSpecRealSemanticTests.setUpClass()

    def test_wrong_or_failing_openspec_version_remains_a_hard_failure(self):
        versions = (
            subprocess.CompletedProcess(
                ["openspec", "--version"], 0, stdout="1.10.0\n", stderr=""
            ),
            subprocess.CompletedProcess(
                ["openspec", "--version"], 7, stdout="", stderr="version failed\n"
            ),
        )
        for version in versions:
            with self.subTest(returncode=version.returncode, stdout=version.stdout):
                with mock.patch.object(shutil, "which", return_value="/tmp/openspec"):
                    with mock.patch.object(subprocess, "run", return_value=version):
                        with self.assertRaisesRegex(
                            AssertionError, "OpenSpec 1.11.0 is required"
                        ):
                            TicketOpenSpecRealSemanticTests.setUpClass()


class TicketLiveProseContractTests(unittest.TestCase):
    def test_openspec_preflight_callers_gate_only_ordinary_openspec_tickets_at_exit(self):
        start = (TICKET_DIRECTORY / "verbs/start.md").read_text(encoding="utf-8")
        coordinator = (TICKET_DIRECTORY / "references/coordinator-mode.md").read_text(
            encoding="utf-8"
        )
        revise = (TICKET_DIRECTORY / "verbs/revise.md").read_text(encoding="utf-8")
        finalize = (TICKET_DIRECTORY / "verbs/finalize.md").read_text(encoding="utf-8")

        start_gate = start.split("12. **Preflight the outbound OpenSpec change.**", 1)[1].split(
            "13. **Open the pull request.**", 1
        )[0]
        coordinator_gate = coordinator.split(
            "9. **Preflight the outbound OpenSpec change.**", 1
        )[1]
        revise_gate = revise.split("   **Preflight the outbound OpenSpec change.**", 1)[1].split(
            "   After the gate succeeds, push", 1
        )[0]

        for gate, base_ref in (
            (start_gate, "refs/remotes/origin/HEAD"),
            (coordinator_gate, "refs/remotes/origin/HEAD"),
            (revise_gate, "origin/<baseRefName>"),
        ):
            with self.subTest(base_ref=base_ref):
                normalized_gate = " ".join(gate.split())
                self.assertIn("ordinary OpenSpec-backed", gate)
                self.assertIn("other or no change-record convention", gate)
                self.assertIn("epic child", gate)
                self.assertEqual(gate.count("git fetch origin"), 1)
                self.assertEqual(gate.count("preflight-openspec"), 1)
                self.assertIn(base_ref, gate)
                self.assertLess(gate.index("git fetch origin"), gate.index("preflight-openspec"))
                self.assertIn("fetch, ref, or preflight failure stops", gate.lower())
                self.assertIn("sole authoritative archive owner", normalized_gate.lower())
                self.assertNotIn("openspec archive ", gate.lower())

        self.assertIn("implementation, review, and all active-change fixes", start_gate)
        self.assertIn("immediately before the command", start_gate)
        self.assertIn("After all chunks merge, whole-diff review and fixes finish", coordinator_gate)
        self.assertIn("the coordinator records the active change", coordinator_gate)
        self.assertIn("immediately\n   before", coordinator_gate)
        self.assertIn("After the rebase and every active-change, checklist, and\n   decision edit", revise_gate)
        self.assertIn("again immediately before", revise_gate)
        self.assertIn("earlier rebase fetch does not satisfy this final refresh", revise_gate)
        self.assertIn("do not open the pull\n   request", start_gate)
        self.assertIn("do not rejoin pull\n   request creation", coordinator_gate)
        self.assertIn("do not push", revise_gate)
        self.assertIn("openspec archive <change-name> --json --yes", finalize.lower())

    def test_triage_selected_ticket_mutation_boundary_admits_lifecycle_state_and_reauthorizes_external_work(self):
        shared = (TICKET_DIRECTORY / "SKILL.md").read_text(encoding="utf-8")
        triage = (TICKET_DIRECTORY / "verbs/triage.md").read_text(encoding="utf-8")
        shared_contract = " ".join(shared.split())
        triage_contract = " ".join(triage.split())

        self.assertEqual(shared.count("## Selected-ticket mutation boundary"), 1)
        self.assertNotIn("Everything outside this allowance is external.", shared)
        self.assertIn("operator-local workflow state", shared_contract)
        self.assertIn("required by the installed workflow", shared_contract)
        for mechanism in (
            "lifecycle claim",
            "exact-worktree Codebase Memory state",
            "reviewer-memory store",
            "local remote-tracking refs",
        ):
            with self.subTest(mechanism=mechanism):
                self.assertIn(mechanism, shared_contract)

        self.assertIn("repository or tracker state belonging to the selected ticket lifecycle", shared_contract)
        self.assertIn("selected worktree and branch", shared_contract)
        self.assertIn("ordinary ticket's active change", shared_contract)
        self.assertIn("selected ticket's comment and status", shared_contract)
        self.assertIn("Epic-child parent-plan amendment", shared_contract)

        self.assertIn("distinct external concern", shared_contract)
        self.assertIn("Broad read-only grounding never authorizes it.", shared_contract)
        self.assertIn("Use the shared selected-ticket mutation boundary.", triage_contract)
        self.assertIn(
            "destination, constraint, acceptance criterion, risk, or sequence",
            triage_contract,
        )
        self.assertIn("cite that clause", triage_contract)
        self.assertIn("exact external target and mutation", triage_contract)
        self.assertIn("stop before mutation", triage_contract)
        self.assertIn(
            "subsequent operator response explicitly authorizes the previously disclosed "
            "target and exact mutation",
            triage_contract,
        )

    def test_builder_self_check_matches_its_live_template_copy(self):
        start = (TICKET_DIRECTORY / "verbs/start.md").read_text(encoding="utf-8")
        template = (TICKET_DIRECTORY / "templates/work-order.md").read_text(encoding="utf-8")
        start_body = start.split("### Builder self-check\n\n", 1)[1].split("\n\n8. **Implement.**", 1)[0]
        template_body = template.split("### Builder self-check\n\n", 1)[1].split(
            "\n\nDo\n", 1
        )[0]
        # Both live copies are the consumer-dependent builder self-check contract.
        self.assertEqual(start_body, template_body)

    def test_session_fit_rules_are_produced_and_consumed(self):
        template = (TICKET_DIRECTORY / "templates/work-order.md").read_text(encoding="utf-8")
        triage = (TICKET_DIRECTORY / "verbs/triage.md").read_text(encoding="utf-8")
        start = (TICKET_DIRECTORY / "verbs/start.md").read_text(encoding="utf-8")
        slicing = (TICKET_DIRECTORY / "references/slicing.md").read_text(encoding="utf-8")
        self.assertIn("Session fit:", template)
        self.assertIn("copy the already-selected execution row", triage)
        self.assertIn("skipping the remainder of Model-check", start)

        # Chunked triage is fail-closed: a bad ladder or rung returns through
        # /scope rather than shipping a draft.
        self.assertIn(
            "A missing, duplicate, malformed, unresolved, or ineligible ladder "
            "or selected rung returns through `/scope` and produces no draft "
            "or comment.",
            triage,
        )
        self.assertIn("selected Agent rung:", triage)
        self.assertIn("selected Agent rung:", template)

        # start.md's Model-check consumes the produced paragraph: it must be
        # byte-identical across every SUB-ORDER before the fast path applies.
        self.assertIn(
            "whose ladder is an ordered non-empty sequence of display-name "
            "rungs byte-identical across every `SUB-ORDER`",
            start,
        )

        # The coordinator-strength invariant is stated once, in slicing.md.
        self.assertIn(
            "The coordinator never launches an agent smarter than itself.",
            " ".join(slicing.split()),
        )

        # Structural shape: the flat fence carries exactly one Session fit
        # paragraph; the chunked header fence carries none (it lives only in
        # each SUB-ORDER fence).
        flat_fence = template.split("## Flat", 1)[1].split("## Chunked", 1)[0]
        self.assertEqual(flat_fence.count("Session fit:"), 1)

        chunked_section = template.split("## Chunked", 1)[1]
        chunked_header_fence = chunked_section.split("```\n", 1)[1].split("\n```", 1)[0]
        self.assertEqual(chunked_header_fence.count("Session fit:"), 0)


class TicketExecutionLockAdmissionTests(unittest.TestCase):
    """The fail-closed matrix `start` (and `revise`, by reuse) enforce before any
    implementation or worker dispatch. One subTest per refusal row, each pinning
    that row's own prose so a future edit cannot silently drop or reword a
    refusal without failing here."""

    @classmethod
    def setUpClass(cls):
        cls.start = (TICKET_DIRECTORY / "verbs" / "start.md").read_text(encoding="utf-8")
        cls.revise = (TICKET_DIRECTORY / "verbs" / "revise.md").read_text(encoding="utf-8")
        cls.skill = (TICKET_DIRECTORY / "SKILL.md").read_text(encoding="utf-8")
        cls.contract = (TICKET_DIRECTORY / "references" / "tracker-contract.md").read_text(
            encoding="utf-8"
        )
        cls.start_norm = " ".join(cls.start.split())
        cls.revise_norm = " ".join(cls.revise.split())
        cls.skill_norm = " ".join(cls.skill.split())
        cls.contract_norm = " ".join(cls.contract.split())
        cls.sufficiency_norm = " ".join(
            cls.start.split("5. **Sufficiency check.**", 1)[1]
            .split("6. **Chunked order: switch to coordinator mode.**", 1)[0]
            .split()
        )

    def test_missing_lock_refuses_and_routes_to_triage(self):
        self.assertIn(
            'say "no work order on `<ticket-id>`; run /ticket triage `<ticket-id>`", and stop.',
            self.start_norm,
        )

    def test_bad_version_or_source_mode_refuses(self):
        self.assertIn(
            "An unrecognized `EXECUTION LOCK` version, or a `Source:` mode this protocol does not define, refuses execution",
            self.sufficiency_norm,
        )
        self.assertIn("bad version or mode", self.sufficiency_norm)

    def test_short_or_unresolvable_oid_refuses(self):
        self.assertIn("a short or unresolvable OID refuses", self.sufficiency_norm)
        self.assertIn("git cat-file -e", self.sufficiency_norm)

    def test_missing_source_path_refuses(self):
        self.assertIn("an empty result is a missing path and refuses", self.sufficiency_norm)
        self.assertIn("git ls-tree", self.sufficiency_norm)

    def test_archived_change_refuses(self):
        self.assertIn("not archived); an archived change refuses", self.sufficiency_norm)

    def test_invalid_change_refuses(self):
        self.assertIn(
            "a change that fails strict validation refuses: invalid change.",
            self.sufficiency_norm,
        )
        self.assertIn("openspec validate <change> --strict", self.sufficiency_norm)

    def test_absent_acceptance_anchors_refuse(self):
        self.assertIn("absent anchors", self.sufficiency_norm)
        self.assertIn("An empty selection refuses the same way.", self.sufficiency_norm)

    def test_branch_missing_the_pin_refuses_and_never_substitutes_head(self):
        self.assertIn("branch missing the pin", self.sufficiency_norm)
        self.assertIn(
            "Never substitute the branch head for the pin, even when the head is newer.",
            self.sufficiency_norm,
        )

    def test_amended_source_without_a_newer_lock_refuses(self):
        self.assertIn(
            "refuse: the amendment is unauthorized until a newer lock pins it.",
            self.sufficiency_norm,
        )
        self.assertIn("git log --oneline <oid>..<ticket-branch-head>", self.sufficiency_norm)

    def test_every_row_shares_one_refusal_route(self):
        # Each row above fails distinctly, but they all land on the same route:
        # named, reported, and re-triaged, never a silent substitution.
        self.assertIn(
            "name the row, report it, and route to `/ticket triage <ticket-id>`",
            self.sufficiency_norm,
        )
        self.assertIn("admission never merges", self.sufficiency_norm)

    def test_legacy_work_order_keeps_its_sufficiency_rules_with_no_inferred_pin(self):
        for source in (self.start_norm, self.skill_norm):
            self.assertIn("no inferred pin, forever", source)
        self.assertIn("drifted", self.start_norm)
        self.assertIn("re-triage, not improvisation", self.start_norm)

    def test_newest_wins_across_mixed_legacy_and_v2_lock_comments(self):
        self.assertIn(
            "Newest wins across both protocols by comment time, regardless of which protocol is newer; "
            "older orders of either protocol are superseded, never merged, and no field is "
            "ever merged from an older comment into a newer one, protocol boundary or not.",
            self.contract_norm,
        )
        self.assertIn(
            "newest comment wins by post time across both protocols, and no field is ever merged "
            "from an older comment into a newer one",
            self.skill_norm,
        )

    def test_revise_relocates_the_newest_lock_every_round_rather_than_caching_it(self):
        self.assertIn(
            "every round re-locates fresh; nothing is cached from the round that opened this pull request",
            self.revise_norm,
        )
        self.assertIn("revise` never posts a lock itself", self.revise_norm)

    def test_revise_admission_runs_against_starts_matrix_never_a_restated_copy(self):
        # NON-BLOCKING 3 (round 2): the split by checkout (BLOCKING 2 below)
        # forces revise to name each row so it can say which checkout it runs
        # from, but it must still point at start's own refusal conditions
        # rather than restating them a second time.
        self.assertIn("[start](start.md) step 5's matrix", self.revise_norm)
        self.assertIn(
            "exactly as [start](start.md) step 5 runs them",
            self.revise_norm,
        )
        for restated_condition in (
            "resolving to a real object",
            "git cat-file -e",
            "git merge-base --is-ancestor",
            "openspec validate <change> --strict",
        ):
            self.assertNotIn(restated_condition, self.revise_norm)

    def test_revise_splits_admission_by_which_checkout_each_row_needs(self):
        # BLOCKING 2: step 1 has no worktree yet, so it may only admit the
        # rows that read the located comment alone; the rows that read the
        # ticket branch and the pinned commit must wait for step 2's worktree.
        step1 = self.revise.split("1. **Reload context.**", 1)[1].split(
            "2. **Worktree.**", 1
        )[0]
        step2 = self.revise.split("2. **Worktree.**", 1)[1].split(
            "3. **Read the standing decisions**", 1
        )[0]
        step1_norm = " ".join(step1.split())
        step2_norm = " ".join(step2.split())

        self.assertIn(
            "with no checkout beyond the located comment itself, admit the "
            "checkout-independent rows",
            step1_norm,
        )
        for checkout_independent_row in (
            "recognized version and mode",
            "grammar",
            "delivery fields",
            "ownership",
        ):
            self.assertIn(checkout_independent_row, step1_norm)
        # Model fit is start step 3's check; revise has no model-check step, so
        # listing it here would be a row nothing performs.
        self.assertIn(
            "Model fit is not among them: `start` step 3 owns that check, and `revise` "
            "has no model-check step to re-run it in.",
            step1_norm,
        )

        self.assertIn("finish the `EXECUTION LOCK` admission step 1 deferred", step2_norm)
        self.assertIn("all against this worktree specifically", step2_norm)
        self.assertIn(
            "never the control checkout, which never switches branches and may be on anything",
            step2_norm,
        )
        for checkout_dependent_row in (
            "commit resolution",
            "branch pin",
            "change state",
            "selection completeness",
            "unauthorized amendment",
        ):
            self.assertIn(checkout_dependent_row, step2_norm)

        # Neither half is optional: the deferral is a named handoff, never a
        # silent skip, and a legacy order has nothing left for step 2 to do.
        self.assertIn(
            "Skipping this half silently, or running it against the control checkout "
            "instead of this worktree, both leave the matrix unenforced; neither is "
            "acceptable.",
            step2_norm,
        )
        self.assertIn("A legacy `WORK ORDER` has nothing further to admit.", step2_norm)

    def test_the_newest_recognized_lock_always_wins_reconciling_reuse_with_amendment(self):
        # BLOCKING 2: "reuses the same lock and pin" (unchanged round) and "a
        # newer lock authorizes an amendment" (changed round) must resolve to
        # one rule, not two different locks in adjacent sentences.
        self.assertIn(
            "The newest recognized lock always wins, which is what reconciles "
            '"reuses the same lock and pin" with a mid-round amendment: when nothing has '
            "changed since `start`, the newest lock is still the one it admitted, so this "
            "round reuses the same pin.",
            self.revise_norm,
        )
        self.assertIn(
            "When triage posted a newer lock since, authorizing an amendment or an "
            "expanded selection, that newer lock is now the newest and is what this round "
            "admits instead.",
            self.revise_norm,
        )
        self.assertIn(
            "When no newer lock exists, the newest lock is still the old one, pinning the "
            "old commit",
            self.revise_norm,
        )
        self.assertIn(
            'never on a comparison against "the lock that opened this pull request" as a '
            "separate, cached reference",
            self.revise_norm,
        )

    def test_revise_refuses_source_scope_expansion_without_a_newer_lock(self):
        self.assertIn(
            "An item that asks to touch the pinned source outside that selection is scope "
            "expansion: refuse it here",
            self.revise_norm,
        )

    def test_delivery_fields_row_refuses_when_a_delivery_field_is_missing(self):
        # The expected diff is a delivery field like the other two: without the
        # closed allowlist nothing bounds what the executor may touch, which is
        # the change's own must-prevent "expanded scope".
        self.assertIn(
            "`Verification:`, `Expectation:`, and `Expected diff` are each present and "
            "non-empty; any one missing refuses.",
            self.sufficiency_norm,
        )

    def test_ticking_a_task_checkbox_is_bookkeeping_not_an_amendment(self):
        # The executor is required to tick tasks.md as work completes, so those
        # commits land in the pinned path after the pin. Without this carve-out
        # the amendment row refuses every revise round that follows the first
        # completed task.
        self.assertIn(
            "an **amendment** is any edit to what the source authorizes — its prose, its "
            "requirements and scenarios, the text of a task, or a task added or removed.",
            self.sufficiency_norm,
        )
        self.assertIn(
            "Ticking or unticking a `tasks.md` checkbox is not an amendment but the "
            "executor's own bookkeeping, which the workflow requires of it as work "
            "completes, so those commits pass this row.",
            self.sufficiency_norm,
        )

    def test_chunked_ownership_overlap_row_refuses(self):
        self.assertIn(
            "confirm the chunks' declared file and target ownership is still disjoint; an "
            "overlap refuses, whether triage stated it wrong or drift introduced it since.",
            self.sufficiency_norm,
        )

    def test_model_fit_row_defers_to_step_3_and_is_not_relitigated(self):
        self.assertIn(
            "Checked at step 3; a mismatch found there stands as this row's refusal and is "
            "not re-litigated here.",
            self.sufficiency_norm,
        )

    def test_admission_precedes_implementation_and_coordinator_dispatch(self):
        implement = self.start.index("8. **Implement.**")
        coordinator_switch = self.start.index(
            "6. **Chunked order: switch to coordinator mode.**"
        )
        sufficiency = self.start.index("5. **Sufficiency check.**")
        self.assertLess(sufficiency, coordinator_switch)
        self.assertLess(coordinator_switch, implement)
        self.assertIn(
            "before any implementation or worker dispatch, including the coordinator-mode switch in step 6.",
            self.start_norm,
        )

    def test_fresh_session_self_sufficiency_covers_all_three_source_modes(self):
        # BLOCKING 1: rule 10 must not define self-sufficiency only in terms of
        # a pinned commit OID, or a valid `inline` lock (no OID to resolve) reads
        # as insufficient to a fresh `start` that step 5 would actually admit.
        rule10 = self.skill.split("10. **Fresh-session contract.**", 1)[1].split(
            "## The verification step", 1
        )[0]
        rule10_norm = " ".join(rule10.split())

        self.assertIn("For `openspec` and `repository-native`,", rule10_norm)
        self.assertIn("the pinned commit OID", rule10_norm)
        self.assertIn(
            "For `inline`, there is no commit to resolve: the fence's own "
            "`Context`/`Do`/`Done when` payload is the self-sufficient copy, the "
            "same as a legacy order's.",
            rule10_norm,
        )
        self.assertIn(
            "that is a triage defect: refuse and say what is missing", rule10_norm
        )

    def test_inline_source_skips_only_the_pinned_commit_rows(self):
        inline_carve_out = self.sufficiency_norm.split(
            "`inline` sources carry no pinned commit:", 1
        )[1].split(".", 1)[0]
        for skipped in (
            "commit resolution",
            "branch pin",
            "change state",
            "selection completeness",
            "unauthorized amendment",
        ):
            self.assertIn(skipped, inline_carve_out)
        self.assertIn(
            "Grammar, delivery fields, ownership, and model fit still apply.",
            self.sufficiency_norm,
        )


if __name__ == "__main__":
    unittest.main()
