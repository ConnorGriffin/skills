from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
TICKET_SCRIPT = ROOT / "skills" / "drivers" / "ticket" / "scripts" / "ticket.py"
TICKET_DIRECTORY = ROOT / "skills" / "drivers" / "ticket"


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


def tool_result_line(text: str, timestamp: str = "2026-01-01T00:00:00Z") -> str:
    return json.dumps(
        {
            "type": "user",
            "timestamp": timestamp,
            "message": {"content": [{"type": "tool_result", "content": text}]},
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

    def ticket(self, *arguments: str, environment: Optional[dict] = None):
        return run(
            ["python3", str(TICKET_SCRIPT), *arguments],
            cwd=ROOT,
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

    def test_a_claim_whose_transcript_is_missing_is_reported_not_dropped(self):
        self.claim("TICKET-6", "session-gone")

        result = self.ticket("scan", "TICKET-6")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["claim_count"], 1)
        self.assertEqual(payload["session_count"], 0)
        self.assertEqual(payload["unreadable"], ["session-gone"])

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


if __name__ == "__main__":
    unittest.main()
