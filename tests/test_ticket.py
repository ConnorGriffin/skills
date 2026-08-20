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
        self.telemetry = self.scratch / "config" / "ticket" / "telemetry.jsonl"
        self.environment = os.environ.copy()
        self.environment["CLAUDE_PROJECTS_DIR"] = str(self.projects)
        self.environment["TICKET_TELEMETRY"] = str(self.telemetry)

    def tearDown(self):
        self.temporary.cleanup()

    def ticket(self, *arguments: str):
        return run(
            ["python3", str(TICKET_SCRIPT), *arguments],
            cwd=ROOT,
            env=self.environment,
        )

    def write_session(self, project: str, session_id: str, lines: list[str]) -> Path:
        directory = self.projects / project
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{session_id}.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def telemetry_records(self) -> list[dict]:
        if not self.telemetry.exists():
            return []
        return [
            json.loads(line)
            for line in self.telemetry.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_scan_counts_a_session_the_operator_typed_the_id_into(self):
        self.write_session(
            "proj-a",
            "session-1",
            [
                user_line("please pick up TICKET-1 today"),
                assistant_line(125_000),
            ],
        )

        result = self.ticket("scan", "TICKET-1")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_count"], 1)
        self.assertEqual(payload["sessions"][0]["peak_context"], 125_000)

    def test_scan_excludes_a_tool_result_only_mention(self):
        self.write_session(
            "proj-a",
            "session-1",
            [
                tool_result_line("issue TICKET-2 was returned by the tracker search"),
                assistant_line(200_000),
            ],
        )

        result = self.ticket("scan", "TICKET-2")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_count"], 0)
        self.assertEqual(payload["sessions"], [])

    def test_record_flat_order_above_degradation_band_is_under_sliced(self):
        self.write_session(
            "proj-a",
            "session-1",
            [
                user_line("start TICKET-3"),
                assistant_line(200_000),
            ],
        )

        result = self.ticket(
            "record", "TICKET-3", "--verb", "start", "--trait", "large-diff", "--depth", "deep"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "under-sliced")

        records = self.telemetry_records()
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["ticket_id"], "TICKET-3")
        self.assertEqual(record["verbs"], ["start"])
        self.assertEqual(record["traits"], ["large-diff"])
        self.assertEqual(record["depth"], "deep")
        self.assertEqual(record["chunked"], False)
        self.assertEqual(record["chunks"], 1)
        self.assertEqual(record["peak_context"], 200_000)
        self.assertEqual(record["verdict"], "under-sliced")
        self.assertIn("recorded_at", record)

    def test_record_flat_order_below_band_is_ok(self):
        self.write_session(
            "proj-a",
            "session-1",
            [
                user_line("start TICKET-4"),
                assistant_line(50_000),
            ],
        )

        result = self.ticket(
            "record", "TICKET-4", "--verb", "start", "--trait", "small-diff", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "ok")
        self.assertEqual(self.telemetry_records()[0]["verdict"], "ok")

    def test_record_chunked_order_still_degraded_when_a_chunk_peaks_high(self):
        self.write_session(
            "proj-a",
            "session-1",
            [
                user_line("start TICKET-5"),
                assistant_line(30_000),
                assistant_line(190_000, subagent=True),
            ],
        )

        result = self.ticket(
            "record",
            "TICKET-5",
            "--verb",
            "start",
            "--trait",
            "wide-scope",
            "--depth",
            "deep",
            "--chunked",
            "--chunks",
            "3",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "still-degraded")

    def test_record_chunked_order_over_sliced_when_every_chunk_is_small(self):
        self.write_session(
            "proj-a",
            "session-1",
            [
                user_line("start TICKET-6"),
                assistant_line(40_000),
                assistant_line(50_000, subagent=True),
            ],
        )

        result = self.ticket(
            "record",
            "TICKET-6",
            "--verb",
            "start",
            "--trait",
            "narrow-scope",
            "--depth",
            "light",
            "--chunked",
            "--chunks",
            "3",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "over-sliced")

    def test_record_with_no_matching_transcript_is_no_data_and_writes_nothing(self):
        result = self.ticket(
            "record", "TICKET-7", "--verb", "start", "--trait", "any", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["verdict"], "no-data")
        self.assertEqual(self.telemetry_records(), [])
        self.assertFalse(self.telemetry.exists())

    def test_subagent_peak_is_counted_separately_from_the_main_session_peak(self):
        self.write_session(
            "proj-a",
            "session-1",
            [
                user_line("start TICKET-8"),
                assistant_line(60_000),
                assistant_line(140_000, subagent=True),
            ],
        )

        result = self.ticket("scan", "TICKET-8")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["sessions"][0]["peak_context"], 60_000)
        self.assertEqual(payload["sessions"][0]["subagent_peak"], 140_000)

    def test_project_narrowing_excludes_an_unrelated_project_directory(self):
        self.write_session(
            "included-project",
            "session-1",
            [user_line("start TICKET-9"), assistant_line(10_000)],
        )
        self.write_session(
            "other-project",
            "session-2",
            [user_line("start TICKET-9"), assistant_line(10_000)],
        )

        result = self.ticket("scan", "TICKET-9", "--project", "included")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_count"], 1)
        self.assertEqual(payload["sessions"][0]["project"], "included-project")

    def test_malformed_line_is_skipped_and_the_rest_of_the_session_still_scans(self):
        # A malformed line is external input (a local file this process did not
        # write): the scan skips it and keeps reading the rest of the file
        # rather than failing the whole session.
        self.write_session(
            "proj-a",
            "session-1",
            [
                user_line("start TICKET-10"),
                "not valid json",
                assistant_line(70_000),
            ],
        )

        result = self.ticket("scan", "TICKET-10")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["session_count"], 1)
        self.assertEqual(payload["sessions"][0]["peak_context"], 70_000)

    def test_empty_and_whitespace_ids_are_rejected_and_write_nothing(self):
        for bad_id in ("", "TICKET 11", " "):
            with self.subTest(bad_id=bad_id):
                result = self.ticket(
                    "record", bad_id, "--verb", "start", "--trait", "any", "--depth", "light"
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("ticket:", result.stderr)
                self.assertEqual(self.telemetry_records(), [])

    def test_telemetry_parent_directory_is_created_when_absent(self):
        self.assertFalse(self.telemetry.parent.exists())
        self.write_session(
            "proj-a",
            "session-1",
            [user_line("start TICKET-12"), assistant_line(10_000)],
        )

        result = self.ticket(
            "record", "TICKET-12", "--verb", "start", "--trait", "any", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.telemetry.parent.exists())
        self.assertEqual(len(self.telemetry_records()), 1)

    def test_appended_record_carries_no_prose_from_the_session(self):
        secret_prose = "quietly worried this deadline is unrealistic and stressful"
        self.write_session(
            "proj-a",
            "session-1",
            [
                user_line(f"start TICKET-13, {secret_prose}"),
                assistant_line(10_000),
            ],
        )

        result = self.ticket(
            "record", "TICKET-13", "--verb", "start", "--trait", "any", "--depth", "light"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        record = self.telemetry_records()[0]
        serialized = json.dumps(record)
        self.assertNotIn(secret_prose, serialized)
        self.assertEqual(
            set(record),
            {
                "ticket_id",
                "verbs",
                "traits",
                "depth",
                "chunked",
                "chunks",
                "session_count",
                "peak_context",
                "subagent_peak",
                "session_peaks",
                "verdict",
                "reason",
                "recorded_at",
            },
        )


if __name__ == "__main__":
    unittest.main()
