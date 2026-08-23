from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional


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
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def user_line(text: str, timestamp: str = "2026-01-01T00:00:00Z") -> str:
    return json.dumps(
        {
            "type": "user",
            "timestamp": timestamp,
            "message": {"content": [{"type": "text", "text": text}]},
        }
    )


def codex_meta_line(session_id: str, timestamp: str = "2026-01-01T00:00:00Z") -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "session_meta",
            "payload": {"session_id": session_id, "cwd": "/tmp/worktree"},
        }
    )


def codex_token_line(
    input_tokens: int, cached: int = 0, timestamp: str = "2026-01-01T00:00:01Z"
) -> str:
    return json.dumps(
        {
            "timestamp": timestamp,
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": {
                    "last_token_usage": {
                        "input_tokens": input_tokens,
                        "cached_input_tokens": cached,
                    }
                },
            },
        }
    )


def assistant_line(
    peak: int, *, subagent: bool = False, timestamp: str = "2026-01-01T00:00:01Z"
) -> str:
    return json.dumps(
        {
            "type": "assistant",
            "timestamp": timestamp,
            "isSidechain": subagent,
            "message": {
                "usage": {
                    "input_tokens": peak,
                    "cache_read_input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                }
            },
        }
    )


class TicketSkillContractTests(unittest.TestCase):
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
        dispatch = coordinator.split("3. **Dispatch one agent per chunk", 1)[1].split(
            "\n4. **", 1
        )[0]

        self.assertIn("graph-identity rule", dispatch)
        self.assertIn("`root_path`", dispatch)
        self.assertIn("`project`", dispatch)
        normalized = " ".join(dispatch.lower().split())
        self.assertIn("uses as given", normalized)
        self.assertIn("never receives the ticket worktree's identity or a sibling's", normalized)

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

    def test_coordinator_claims_unique_implementation_workers_not_reviewers(self):
        coordinator = (TICKET_DIRECTORY / "references" / "coordinator-mode.md").read_text(
            encoding="utf-8"
        )
        contract = " ".join(coordinator.split())

        for requirement in (
            "each unique implementation-worker session",
            "`--session <id>`",
            "`--agent <agent>`",
            "`--project <chunk-worktree>`",
            "Same-session retries are not re-claimed",
            "fresh implementation escalation",
            "Review-only sessions are not claimed",
            "stable transcript id",
            "one line and continue",
        ):
            self.assertIn(requirement, contract)

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

    def test_revise_requires_a_base_currency_and_mergeability_refresh(self):
        revise = (TICKET_DIRECTORY / "verbs" / "revise.md").read_text(encoding="utf-8")

        self.assertIn("mergeStateStatus", revise)
        self.assertIn("rebase once", revise)
        self.assertIn("stamped review depth", revise)
        self.assertIn("semantic conflict", revise)


class TicketTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.scratch = Path(self.temporary.name)
        self.projects = self.scratch / "projects"
        self.projects.mkdir()
        self.codex_home = self.scratch / "codex-home"
        self.telemetry = self.scratch / "config" / "ticket" / "telemetry.jsonl"
        self.claims = self.scratch / "config" / "ticket" / "claims.jsonl"
        self.environment = os.environ.copy()
        self.environment.pop("CLAUDE_CODE_SESSION_ID", None)
        self.environment.pop("CODEX_SESSION_ID", None)
        self.environment["CLAUDE_PROJECTS_DIR"] = str(self.projects)
        self.environment["CODEX_HOME"] = str(self.codex_home)
        self.environment["TICKET_TELEMETRY"] = str(self.telemetry)
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

    def claim(self, ticket_id: str, session_id: str, agent: str = "claude"):
        result = self.ticket(
            "claim", ticket_id, "--session", session_id, "--agent", agent
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def worked(self, ticket_id: str, project: str, session_id: str, lines: list[str]):
        """The ordinary case: a session ran the ticket, so it claimed it."""
        self.write_session(project, session_id, lines)
        self.claim(ticket_id, session_id)

    def telemetry_records(self) -> list[dict]:
        if not self.telemetry.exists():
            return []
        return [
            json.loads(line)
            for line in self.telemetry.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_claim_records_the_running_session_without_being_told_which(self):
        environment = self.environment.copy()
        environment["CLAUDE_CODE_SESSION_ID"] = "session-1"

        result = self.ticket("claim", "TICKET-1", environment=environment)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_id"], "session-1")
        self.assertEqual(payload["agent"], "claude")
        self.assertFalse(payload["already_claimed"])

    def test_claiming_the_same_session_twice_records_it_once(self):
        self.claim("TICKET-2", "session-1")

        second = self.ticket("claim", "TICKET-2", "--session", "session-1", "--agent", "claude")

        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue(json.loads(second.stdout)["already_claimed"])
        lines = self.claims.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len([line for line in lines if line.strip()]), 1)

    def test_claim_without_a_session_id_anywhere_says_how_to_supply_one(self):
        result = self.ticket("claim", "TICKET-3")

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

        self.assertEqual(json.loads(gone.stdout)["verdict"], "no-data")
        self.assertIn("transcripts are gone", json.loads(gone.stdout)["reason"])
        self.assertEqual(self.telemetry_records(), [])

        # A deleted transcript must not reach the durable record as a session
        # that cost nothing: that is the reading adr-70 rules out.
        self.worked("TICKET-6", "proj-a", "session-2", [assistant_line(190_000)])
        recorded = self.ticket(
            "record", "TICKET-6", "--verb", "start", "--trait", "any", "--depth", "deep"
        )

        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        record = self.telemetry_records()[0]
        self.assertEqual(record["session_peaks"], [190_000])
        self.assertEqual(record["claim_count"], 2)
        self.assertEqual(record["unreadable"], ["session-gone"])

    def test_two_visible_agent_sessions_refuse_to_guess_which_is_running(self):
        # A Codex worker launched from a Claude session inherits that session's
        # variable. Guessing here would measure the coordinator's transcript.
        environment = self.environment.copy()
        environment["CLAUDE_CODE_SESSION_ID"] = "claude-1"
        environment["CODEX_SESSION_ID"] = "codex-1"

        result = self.ticket("claim", "TICKET-17", environment=environment)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--agent", result.stderr)
        self.assertFalse(self.claims.exists())

        chosen = self.ticket(
            "claim", "TICKET-17", "--session", "codex-1", "--agent", "codex",
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
                result = self.ticket("claim", "TICKET-19", "--session", bad, "--agent", "claude")

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

        records = self.telemetry_records()
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["ticket_id"], "TICKET-7")
        self.assertEqual(record["verbs"], ["start"])
        self.assertEqual(record["traits"], ["large-diff"])
        self.assertEqual(record["depth"], "deep")
        self.assertEqual(record["chunked"], False)
        self.assertEqual(record["chunks"], 1)
        self.assertEqual(record["peak_context"], 200_000)
        self.assertEqual(record["verdict"], "under-sliced")
        self.assertIn("recorded_at", record)

    def test_record_flat_order_below_band_is_ok(self):
        self.worked("TICKET-8", "proj-a", "session-1", [assistant_line(50_000)])

        result = self.ticket(
            "record", "TICKET-8", "--verb", "start", "--trait", "small-diff", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "ok")
        self.assertEqual(self.telemetry_records()[0]["verdict"], "ok")

    def test_record_chunked_order_still_degraded_when_a_chunk_peaks_high(self):
        self.worked(
            "TICKET-9",
            "proj-a",
            "session-1",
            [assistant_line(30_000), assistant_line(190_000, subagent=True)],
        )

        result = self.ticket(
            "record", "TICKET-9", "--verb", "start", "--trait", "wide-scope",
            "--depth", "deep", "--chunked", "--chunks", "3",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "still-degraded")

    def test_record_chunked_order_over_sliced_when_every_chunk_is_small(self):
        self.worked(
            "TICKET-10",
            "proj-a",
            "session-1",
            [assistant_line(40_000), assistant_line(50_000, subagent=True)],
        )

        result = self.ticket(
            "record", "TICKET-10", "--verb", "start", "--trait", "narrow-scope",
            "--depth", "light", "--chunked", "--chunks", "3",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "over-sliced")

    def test_record_with_no_claim_is_no_data_and_writes_nothing(self):
        result = self.ticket(
            "record", "TICKET-11", "--verb", "start", "--trait", "any", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "no-data")
        self.assertEqual(self.telemetry_records(), [])
        self.assertFalse(self.telemetry.exists())

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

    def test_empty_and_whitespace_ids_are_rejected_and_write_nothing(self):
        for bad_id in ("", "TICKET 14", " "):
            with self.subTest(bad_id=bad_id):
                result = self.ticket(
                    "record", bad_id, "--verb", "start", "--trait", "any", "--depth", "light"
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ticket:", result.stderr)
                self.assertEqual(self.telemetry_records(), [])

    def test_telemetry_parent_directory_is_created_when_absent(self):
        # The claim already created the shared parent, so this asserts the
        # record path creates what it needs from a clean directory.
        self.worked("TICKET-15", "proj-a", "session-1", [assistant_line(10_000)])
        self.assertFalse(self.telemetry.exists())

        result = self.ticket(
            "record", "TICKET-15", "--verb", "start", "--trait", "any", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.telemetry.parent.exists())
        self.assertEqual(len(self.telemetry_records()), 1)

    def test_appended_record_carries_no_prose_from_the_session(self):
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
        written = self.telemetry.read_text(encoding="utf-8")
        self.assertNotIn("unrealistic", written)
        self.assertNotIn(secret_prose, written)
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
            "--project", str(repo_a),
        )
        self.assertEqual(claim_a.returncode, 0, claim_a.stderr)
        claim_b = self.ticket(
            "claim", "TICKET-21", "--session", "session-b", "--agent", "claude",
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

        persisted = self.telemetry_records()[0]
        self.assertEqual(persisted["unattributable"], ["legacy-session"])
        self.assertEqual(persisted["session_count"], 1)
        self.assertEqual(persisted["peak_context"], 55_000)


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


if __name__ == "__main__":
    unittest.main()
