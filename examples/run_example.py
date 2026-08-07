#!/usr/bin/env python3
"""Run one real task under both output styles and save the full replies.

The task is a genuine diagnosis on the fixture repo: the suite is green, the
retry count is wrong. Each run gets a fresh copy of the fixture so nothing
carries between arms.

Usage:
  python3 examples/run_example.py --models claude-opus-5,claude-sonnet-5,claude-fable-5
"""

import argparse
import concurrent.futures
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture"
STYLE = ROOT.parent / "output-styles" / "say-less.md"
TRANSCRIPTS = ROOT / "transcripts"

PROMPT = (
    "Ops says a flaky artifact upload gives up after 3 tries, but the config sets "
    "retries to 3 and the README promises one initial attempt plus 3 retries. The "
    "test suite is green. What is wrong and what should change?"
)

TOOLS = "Read,Glob,Grep,Bash(python3:*)"


def scratch():
    d = pathlib.Path(tempfile.mkdtemp(prefix="say-less-example-"))
    shutil.copytree(FIXTURE, d, dirs_exist_ok=True)
    style_dir = d / ".claude" / "output-styles"
    style_dir.mkdir(parents=True)
    shutil.copy(STYLE, style_dir / "say-less.md")
    (d / ".claude" / "settings.json").write_text("{}\n")
    return d


def run(model, style):
    project = scratch()
    cmd = ["claude", "-p", "--model", model, "--setting-sources", "project",
           "--allowedTools", TOOLS, "--output-format", "json"]
    if style == "say-less":
        cmd += ["--settings", json.dumps({"outputStyle": "say-less"})]
    cmd.append(PROMPT)
    proc = subprocess.run(cmd, cwd=project, capture_output=True, text=True, timeout=1200)
    shutil.rmtree(project, ignore_errors=True)
    if proc.returncode != 0:
        return {"model": model, "style": style, "error": proc.stderr.strip()[:400]}
    payload = json.loads(proc.stdout)
    return {
        "model": model,
        "style": style,
        "text": payload.get("result", ""),
        "output_tokens": payload.get("usage", {}).get("output_tokens"),
        "num_turns": payload.get("num_turns"),
        "duration_ms": payload.get("duration_ms"),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--models", default="claude-opus-5,claude-sonnet-5,claude-fable-5")
    p.add_argument("--jobs", type=int, default=6)
    args = p.parse_args()

    jobs = [(m, s) for m in args.models.split(",") for s in ("default", "say-less")]
    TRANSCRIPTS.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        for row in pool.map(lambda j: run(*j), jobs):
            name = f"{row['model']}.{row['style']}.md"
            body = row.get("text") or f"ERROR: {row.get('error')}"
            (TRANSCRIPTS / name).write_text(
                f"<!-- {row['model']} / {row['style']} / "
                f"{row.get('output_tokens')} output tokens / "
                f"{row.get('num_turns')} turns -->\n\n{body}\n"
            )
            print(name, row.get("output_tokens"), "tokens", file=sys.stderr)


if __name__ == "__main__":
    main()
