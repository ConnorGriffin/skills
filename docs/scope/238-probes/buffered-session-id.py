#!/usr/bin/env python3
"""Reproduce issue 238 against the Codex adapter's public CLI."""

from __future__ import annotations

import json
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[3]
ADAPTER = ROOT / "skills/drivers/orchestrate/scripts/codex-worker.py"


def wait_for_running(state_path: Path) -> dict[str, object]:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.02)
            continue
        if state.get("lifecycle") == "running":
            return state
        time.sleep(0.02)
    raise RuntimeError("adapter never reached running state")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect", choices=("empty", "live", "none"), default="none")
    args = parser.parse_args()
    if sys.platform != "darwin":
        print("SKIP: durable process-family lifecycle is macOS-only")
        return 0

    with tempfile.TemporaryDirectory(prefix="ticket-238-") as raw:
        scratch = Path(raw)
        fake = scratch / "fake-codex"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import json, time\n"
            "print(json.dumps({'type': 'thread.started', "
            "'thread_id': 'buffered-worker'}), flush=True)\n"
            "time.sleep(30)\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        state_path = scratch / "state.json"
        process = subprocess.Popen(
            [
                sys.executable,
                str(ADAPTER),
                "start",
                "--codex",
                str(fake),
                "--state",
                str(state_path),
                "--model",
                "Terra",
                "--sandbox",
                "read-only",
                "--cwd",
                str(scratch),
                "hold after session start",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            state = wait_for_running(state_path)
            time.sleep(0.25)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            observed = {
                "lifecycle": state.get("lifecycle"),
                "session_id": state.get("session_id"),
                "fixture_event": "buffered-worker",
                "adapter_still_running": process.poll() is None,
            }
            print(json.dumps(observed, sort_keys=True))
            expected_id = "" if args.expect == "empty" else "buffered-worker"
            if args.expect != "none" and observed != {
                "adapter_still_running": True,
                "fixture_event": "buffered-worker",
                "lifecycle": "running",
                "session_id": expected_id,
            }:
                raise RuntimeError(f"{args.expect} expectation failed: {observed!r}")
        finally:
            subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER),
                    "stop",
                    "--state",
                    str(state_path),
                    "--cwd",
                    str(scratch),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
