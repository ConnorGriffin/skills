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


class TicketSkillStructureTests(unittest.TestCase):
    """A small structural floor for the ticket prose; behavior lives in the CLI tests."""

    VERBS = ("triage", "start", "revise", "finalize")

    @staticmethod
    def read(relative: str) -> str:
        return " ".join((TICKET_DIRECTORY / relative).read_text(encoding="utf-8").split())

    def test_the_four_verbs_each_have_a_procedure_the_skill_page_links(self):
        skill = self.read("SKILL.md")
        for verb in self.VERBS:
            with self.subTest(verb=verb):
                self.assertTrue((TICKET_DIRECTORY / "verbs" / f"{verb}.md").is_file())
                self.assertIn(f"[{verb}](verbs/{verb}.md)", skill)

    def test_every_relative_link_in_the_ticket_prose_resolves(self):
        for page in TICKET_DIRECTORY.rglob("*.md"):
            for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", page.read_text(encoding="utf-8")):
                if "://" in target:
                    continue
                with self.subTest(page=page.relative_to(TICKET_DIRECTORY), target=target):
                    self.assertTrue((page.parent / target).exists())

    def test_agents_never_merge(self):
        self.assertIn("**Agents never merge.**", self.read("SKILL.md"))
        self.assertIn("Do not merge", self.read("verbs/start.md"))
        self.assertIn("Do not merge", self.read("templates/work-order.md"))

    def test_start_refuses_without_a_locked_order(self):
        start = self.read("verbs/start.md")
        self.assertIn("no work order on `<ticket-id>`; run /ticket triage `<ticket-id>`", start)
        self.assertIn("Never fall back to an older comment", start)
        self.assertIn("git merge-base --is-ancestor <oid> HEAD", start)

    def test_plan_review_runs_once_and_only_at_full_depth(self):
        triage = self.read("verbs/triage.md")
        self.assertIn("At Full depth, run `/plan-review` once", triage)
        self.assertIn("one round", triage)

    def test_the_sensitivity_floor_forces_full_depth(self):
        skill = self.read("SKILL.md")
        for term in ("Authentication or authorization", "secrets", "destructive or irreversible", "never downgrades"):
            self.assertIn(term, skill)

    def test_every_script_subcommand_the_prose_names_exists(self):
        prose = " ".join(page.read_text(encoding="utf-8") for page in TICKET_DIRECTORY.rglob("*.md"))
        named = set(re.findall(r"ticket\.py\s+(?:\\\s+)?([a-z][a-z-]+)", prose))
        self.assertEqual(named, {"claim", "record", "scan", "preflight-openspec"})
        help_text = run(["python3", str(TICKET_SCRIPT), "--help"], cwd=ROOT).stdout
        for subcommand in named:
            self.assertIn(subcommand, help_text)

    def test_no_removed_machinery_is_named(self):
        prose = " ".join(
            page.read_text(encoding="utf-8")
            for page in TICKET_DIRECTORY.rglob("*")
            if page.suffix in {".md", ".yaml"}
        )
        for removed in ("/scope", "/orchestrate", "/preflight", "persona", "cbm-", "Codebase Memory", "ORDER.md", "SUB-ORDER", "Session fit", "epic"):
            with self.subTest(removed=removed):
                self.assertNotIn(removed, prose)


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

    def write_codex_session(
        self, session_id: str, lines: list[str], root: str = "sessions"
    ) -> Path:
        directory = self.codex_home / root / "2026" / "01" / "01"
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

    def test_archived_codex_rollout_is_measured_by_scan_and_record(self):
        archived = self.write_codex_session(
            "codex-archived", [codex_meta_line("codex-archived"), codex_token_line(228_055)],
            root="archived_sessions",
        )
        self.claim("TICKET-290", "codex-archived", agent="codex")

        scanned = self.ticket("scan", "TICKET-290")

        self.assertEqual(scanned.returncode, 0, scanned.stderr)
        scan_payload = json.loads(scanned.stdout)
        self.assertEqual(scan_payload["session_count"], 1)
        self.assertEqual(scan_payload["peak_context"], 228_055)
        self.assertEqual(scan_payload["sessions"][0]["transcripts"], [str(archived)])

        recorded = self.ticket(
            "record", "TICKET-290", "--verb", "start", "--trait", "shared-contract",
            "--depth", "full",
        )

        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        record_payload = json.loads(recorded.stdout)
        self.assertEqual(record_payload["peak_context"], 228_055)
        self.assertEqual(record_payload["verdict"], "under-sliced")

    def test_codex_session_spanning_active_and_archived_roots_uses_every_rollout(self):
        active = self.write_codex_session(
            "codex-mixed", [codex_meta_line("codex-mixed"), codex_token_line(5_000)]
        )
        archived = self.write_codex_session(
            "codex-mixed", [codex_meta_line("codex-mixed"), codex_token_line(228_055)],
            root="archived_sessions",
        )
        self.claim("TICKET-290-MIXED", "codex-mixed", agent="codex")

        scanned = self.ticket("scan", "TICKET-290-MIXED")

        self.assertEqual(scanned.returncode, 0, scanned.stderr)
        scan_payload = json.loads(scanned.stdout)
        self.assertEqual(
            scan_payload["sessions"][0]["transcripts"],
            [str(path) for path in sorted((active, archived))],
        )
        self.assertEqual(scan_payload["peak_context"], 228_055)

        recorded = self.ticket(
            "record", "TICKET-290-MIXED", "--verb", "start",
            "--trait", "shared-contract", "--depth", "full",
        )

        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        record_payload = json.loads(recorded.stdout)
        self.assertEqual(record_payload["peak_context"], 228_055)
        self.assertEqual(record_payload["verdict"], "under-sliced")

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

    def test_a_reviewer_peak_changes_no_verdict(self):
        # Review overhead runs on nearly every ticket and says nothing about
        # how big the work was.
        self.worked("TICKET-27", "proj-a", "flat-1", [assistant_line(90_000)])
        self.worked(
            "TICKET-27", "proj-a", "reviewer-1", [assistant_line(250_000)], role="reviewer"
        )

        flat = self.ticket(
            "record", "TICKET-27", "--verb", "start", "--trait", "any", "--depth", "light"
        )

        self.assertEqual(json.loads(flat.stdout)["verdict"], "ok")
        self.assertEqual(json.loads(flat.stdout)["reviewer_peak"], 250_000)

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


if __name__ == "__main__":
    unittest.main()
