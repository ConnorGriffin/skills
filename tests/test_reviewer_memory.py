from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEMORY_SCRIPT = ROOT / "skills" / "tools" / "reviewer-memory" / "scripts" / "memory.py"
REPO = "git@github.com:ConnorGriffin/skills.git"
REPO_KEY = "github.com_ConnorGriffin_skills"


def run(home: Path, *arguments: str, input_text: str = "") -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(MEMORY_SCRIPT), *arguments],
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )


def run_bytes(
    home: str,
    *arguments: str,
    input_bytes: bytes = b"",
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["HOME"] = home
    return subprocess.run(
        [sys.executable, str(MEMORY_SCRIPT), *arguments],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        cwd=cwd,
        check=False,
    )


class ReviewerMemoryTests(unittest.TestCase):
    def test_ensure_creates_the_skeleton_and_pins_the_remote_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            result = run(home, "ensure", REPO)

            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            store = (home / ".config" / "reviewer-memory" / REPO_KEY).absolute()
            self.assertEqual(response["key"], REPO_KEY)
            self.assertEqual(Path(response["raw_path"]), store / "raw.jsonl")
            self.assertEqual(Path(response["index_path"]), store / "okf" / "index.md")
            self.assertFalse(response["has_content"])
            self.assertTrue((store / "raw.jsonl").is_file())
            index = (store / "okf" / "index.md").read_text(encoding="utf-8")
            self.assertTrue(index.startswith("---\n"))
            self.assertIn("\n---\n", index)

    def test_append_round_trips_both_kinds_and_pointer(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            self.assertEqual(run(home, "ensure", REPO).returncode, 0)
            review = {"ticket": "197", "findings": ["tighten failure copy"], "reviewer": "terra"}
            slicing = {"ticket_id": "197", "chunked": True, "chunks": 2, "traits": ["wide"]}

            self.assertEqual(
                run(home, "append-review", REPO, input_text=json.dumps(review, indent=2)).returncode,
                0,
            )
            self.assertEqual(
                run(home, "append-slicing", REPO, input_text=json.dumps(slicing, indent=2)).returncode,
                0,
            )
            pointer = run(home, "pointer", REPO)

            self.assertEqual(pointer.returncode, 0, pointer.stderr)
            records = [
                json.loads(line)
                for line in (home / ".config" / "reviewer-memory" / REPO_KEY / "raw.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual([record["kind"] for record in records], ["review", "slicing"])
            self.assertEqual(records[0]["findings"], review["findings"])
            self.assertEqual(records[1]["chunks"], slicing["chunks"])
            self.assertTrue(all(record["recorded_at"].endswith("Z") for record in records))
            self.assertEqual(pointer.stdout.strip(), str((home / ".config" / "reviewer-memory" / REPO_KEY / "okf" / "index.md").absolute()))

    def test_corrupt_store_stops_with_the_named_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            self.assertEqual(run(home, "ensure", REPO).returncode, 0)
            store = home / ".config" / "reviewer-memory" / REPO_KEY
            raw = store / "raw.jsonl"
            raw.write_text("not json\n", encoding="utf-8")

            append = run(home, "append-review", REPO, input_text="{}")
            self.assertNotEqual(append.returncode, 0)
            self.assertIn(str(raw), append.stderr)

            raw.write_text("", encoding="utf-8")
            index = store / "okf" / "index.md"
            index.write_text("# broken\n", encoding="utf-8")
            pointer = run(home, "pointer", REPO)
            self.assertNotEqual(pointer.returncode, 0)
            self.assertIn(str(index), pointer.stderr)

    def test_invalid_utf8_uses_the_command_error_surface(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            self.assertEqual(run(home, "ensure", REPO).returncode, 0)
            store = home / ".config" / "reviewer-memory" / REPO_KEY
            raw = store / "raw.jsonl"
            index = store / "okf" / "index.md"

            raw.write_bytes(b"\xff\n")
            raw_result = run_bytes(str(home), "pointer", REPO)
            self.assertNotEqual(raw_result.returncode, 0)
            self.assertIn(b"reviewer-memory:", raw_result.stderr)
            self.assertIn(str(raw).encode(), raw_result.stderr)
            self.assertNotIn(b"Traceback", raw_result.stderr)

            raw.write_bytes(b"")
            index.write_bytes(b"\xff\n")
            index_result = run_bytes(str(home), "pointer", REPO)
            self.assertNotEqual(index_result.returncode, 0)
            self.assertIn(b"reviewer-memory:", index_result.stderr)
            self.assertIn(str(index).encode(), index_result.stderr)
            self.assertNotIn(b"Traceback", index_result.stderr)

            index.write_text("---\n---\n", encoding="utf-8")
            self.assertEqual(run(home, "ensure", REPO).returncode, 0)
            stdin_result = run_bytes(str(home), "append-review", REPO, input_bytes=b"\xff")
            self.assertNotEqual(stdin_result.returncode, 0)
            self.assertIn(b"reviewer-memory: stdin", stdin_result.stderr)
            self.assertNotIn(b"Traceback", stdin_result.stderr)

    def test_pointer_is_absolute_when_home_is_relative(self):
        with tempfile.TemporaryDirectory() as temporary:
            cwd = Path(temporary)
            relative_home = "relative-home"
            ensure = run_bytes(relative_home, "ensure", REPO, cwd=cwd)
            pointer = run_bytes(relative_home, "pointer", REPO, cwd=cwd)

            self.assertEqual(ensure.returncode, 0, ensure.stderr.decode())
            self.assertEqual(pointer.returncode, 0, pointer.stderr.decode())
            self.assertTrue(Path(pointer.stdout.decode().strip()).is_absolute())

    def test_symlinked_store_components_cannot_redirect_access(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as external:
            home = Path(temporary)
            outside = Path(external)
            for component in ("raw", "okf", "index", "root"):
                with self.subTest(component=component):
                    case_home = home / component
                    self.assertEqual(run(case_home, "ensure", REPO).returncode, 0)
                    store = case_home / ".config" / "reviewer-memory" / REPO_KEY
                    raw = store / "raw.jsonl"
                    bundle = store / "okf"
                    index = bundle / "index.md"
                    target = outside / component

                    if component == "raw":
                        target.write_text("{}\n", encoding="utf-8")
                        raw.unlink()
                        raw.symlink_to(target)
                        result = run(case_home, "append-review", REPO, input_text="{}")
                        self.assertEqual(target.read_text(encoding="utf-8"), "{}\n")
                        blocked_path = raw
                    elif component == "okf":
                        bundle.rename(target)
                        bundle.symlink_to(target, target_is_directory=True)
                        result = run(case_home, "pointer", REPO)
                        blocked_path = bundle
                    elif component == "index":
                        target.write_text(index.read_text(encoding="utf-8"), encoding="utf-8")
                        index.unlink()
                        index.symlink_to(target)
                        result = run(case_home, "pointer", REPO)
                        blocked_path = index
                    else:
                        store.rename(target)
                        store.symlink_to(target, target_is_directory=True)
                        result = run(case_home, "pointer", REPO)
                        blocked_path = store

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("reviewer-memory:", result.stderr)
                    self.assertIn(str(blocked_path), result.stderr)

    def test_commands_never_write_outside_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            before = {path.relative_to(home) for path in home.rglob("*")}
            self.assertEqual(run(home, "ensure", REPO).returncode, 0)
            self.assertEqual(run(home, "append-review", REPO, input_text="{}").returncode, 0)
            self.assertEqual(run(home, "append-slicing", REPO, input_text="{}").returncode, 0)
            self.assertEqual(run(home, "pointer", REPO).returncode, 0)
            after = {path.relative_to(home) for path in home.rglob("*")}

            self.assertTrue(after - before)
            allowed = {
                Path(".config"),
                Path(".config/reviewer-memory"),
                Path(f".config/reviewer-memory/{REPO_KEY}"),
                Path(f".config/reviewer-memory/{REPO_KEY}/raw.jsonl"),
                Path(f".config/reviewer-memory/{REPO_KEY}/okf"),
                Path(f".config/reviewer-memory/{REPO_KEY}/okf/index.md"),
            }
            self.assertTrue(after - before <= allowed)


if __name__ == "__main__":
    unittest.main()
