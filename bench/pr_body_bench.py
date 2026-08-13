#!/usr/bin/env python3
"""Measure whether the pr-body skill's prose teaches a model to write a passing body.

Two arms run the same 8 real diffs through the same model: `with-skill` puts
`skills/pr-body/SKILL.md` in the prompt, `without-skill` gets only the diff.
Each resulting body is scored by `pr_body_lint.py` itself (the judge; no LLM
rubric), so this measures whether the prose teaches, as distinct from the
pr-body-gate hook that enforces compliance after the fact.

Usage:
  python3 bench/pr_body_bench.py run --models claude-sonnet-5 --repeats 2
  python3 bench/pr_body_bench.py score

Fixtures live in bench/fixtures/pr-body/ and results in bench/results/pr-body/,
both gitignored: the diffs and the bodies written about them come from a private
estate. Point --diffs at your own. Aggregate numbers from the run behind this
skill are in docs/pr-body-measurement.md.

`run` is resumable: it skips (arm, diff, model, repeat) combinations already
present in the target jsonl, and appends new results one at a time so an
interrupted run loses nothing already written.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import math
import pathlib
import shutil
import statistics
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
# Own subdirectory: bench/results/ is shared with bench.py, whose tag names
# (v1, v2, shipped) would otherwise collide with these.
RESULTS = ROOT / "results" / "pr-body"
FIXTURES = ROOT / "fixtures" / "pr-body"
SKILL_MD = REPO_ROOT / "skills" / "pr-body" / "SKILL.md"
LINT_SCRIPT = REPO_ROOT / "skills" / "pr-body" / "scripts" / "pr_body_lint.py"

ARMS = ("with-skill", "without-skill")

# ai-disclosure-missing is the one rule SKILL.md teaches that the raw diff
# does not mention at all. Excluded from the without-skill arm's pass/fail
# rate: that arm was never told the requirement exists, so counting it there
# would manufacture a difference that reflects what the prompt withheld, not
# what the skill's prose teaches.
UNTAUGHT_RULES_BY_ARM = {
    "without-skill": {"ai-disclosure-missing"},
    "with-skill": set(),
}


def _load_lint():
    spec = importlib.util.spec_from_file_location("pr_body_lint", LINT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LINT = _load_lint()


def scratch_project() -> pathlib.Path:
    """A project dir with no CLAUDE.md, hooks, or output style to bias the model."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="pr-body-bench-"))
    (d / ".claude").mkdir()
    (d / ".claude" / "settings.json").write_text("{}\n")
    return d


PROMPT_TEMPLATE = """Here is a diff for a pull request.

```diff
{diff}
```

Write the PR body text for this change: the text that would be passed to
`gh pr create --body-file`. Reply with the body text only. No preamble, no
explanation of what you are about to do, no code fence around the body."""


def build_prompt(diff_text: str, arm: str) -> str:
    prompt = PROMPT_TEMPLATE.format(diff=diff_text)
    if arm == "with-skill":
        skill_text = SKILL_MD.read_text(encoding="utf-8")
        prompt = f"{skill_text}\n\n---\n\n{prompt}"
    return prompt


def score_body(body: str) -> dict:
    result = LINT.lint(body)
    findings = result["findings"]
    return {
        "chars": len(body),
        "verdict": result["verdict"],
        "rules_fired": sorted({f["rule"] for f in findings}),
        "blocking_rules_fired": sorted(
            {f["rule"] for f in findings if f["severity"] == "block"}
        ),
    }


def one_run(project: pathlib.Path, model: str, arm: str, diff_path: pathlib.Path) -> dict:
    diff_text = diff_path.read_text(encoding="utf-8")
    prompt = build_prompt(diff_text, arm)
    row = {"arm": arm, "diff": diff_path.name, "model": model}
    cmd = [
        "claude", "-p", "--model", model,
        "--setting-sources", "project",
        "--output-format", "json",
    ]
    # Prompt goes on stdin, never argv: the with-skill arm starts with SKILL.md's
    # `---` frontmatter, which argv parsing reads as a flag.
    proc = subprocess.run(cmd, cwd=project, input=prompt,
                          capture_output=True, text=True, timeout=900)
    if proc.returncode != 0:
        row["error"] = proc.stderr.strip()[:400]
        return row
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        row["error"] = f"non-JSON output: {error}"
        return row
    body = payload.get("result", "")
    row["body"] = body
    row["output_tokens"] = payload.get("usage", {}).get("output_tokens")
    row.update(score_body(body))
    return row


def _completed_keys(path: pathlib.Path) -> set[tuple[str, str, str, int]]:
    if not path.exists():
        return set()
    keys = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not {"arm", "diff", "model"} <= row.keys():
            continue
        keys.add((row["arm"], row["diff"], row["model"], row.get("repeat", 0)))
    return keys


def cmd_run(args: argparse.Namespace) -> int:
    diffs = sorted(FIXTURES.glob("*.diff"))
    if args.diffs:
        wanted = set(args.diffs.split(","))
        diffs = [d for d in diffs if d.name in wanted]
    if not diffs:
        print(f"no fixtures found under {FIXTURES}", file=sys.stderr)
        return 1

    models = args.models.split(",")
    arms = args.arms.split(",")
    for arm in arms:
        if arm not in ARMS:
            print(f"unknown arm {arm!r}, must be one of {ARMS}", file=sys.stderr)
            return 1

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{args.tag}.jsonl"
    done_keys = _completed_keys(out)

    jobs = [
        (model, arm, diff, repeat)
        for model in models
        for arm in arms
        for diff in diffs
        for repeat in range(args.repeats)
        if (arm, diff.name, model, repeat) not in done_keys
    ]
    if not jobs:
        print(f"all {len(done_keys)} runs already recorded in {out}; nothing to do", file=sys.stderr)
        return 0

    project = scratch_project()
    total = len(jobs)
    try:
        with out.open("a") as fh, concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
            futures = {
                pool.submit(one_run, project, model, arm, diff): (model, arm, diff, repeat)
                for model, arm, diff, repeat in jobs
            }
            completed = 0
            for fut in concurrent.futures.as_completed(futures):
                model, arm, diff, repeat = futures[fut]
                try:
                    row = fut.result()
                except Exception as exc:  # noqa: BLE001 - one job's crash must not lose the rest
                    row = {"arm": arm, "diff": diff.name, "model": model, "error": repr(exc)[:400]}
                row["repeat"] = repeat
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                completed += 1
                print(f"{completed}/{total} {model} {arm} {diff.name} rep{repeat}", file=sys.stderr)
    finally:
        shutil.rmtree(project, ignore_errors=True)

    print(out)
    return 0


def _adjusted_blocking(row: dict) -> list[str]:
    untaught = UNTAUGHT_RULES_BY_ARM.get(row["arm"], set())
    return [rule for rule in row["blocking_rules_fired"] if rule not in untaught]


def _pooled_se(p1: float, n1: int, p2: float, n2: int) -> float:
    return math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)


def _bucket(rows: list[dict]) -> dict:
    bucket = {"n": 0, "raw_pass": 0, "adj_pass": 0, "chars": [], "rule_fires": {}}
    for row in rows:
        bucket["n"] += 1
        bucket["raw_pass"] += 1 if row["verdict"] == "pass" else 0
        bucket["adj_pass"] += 1 if not _adjusted_blocking(row) else 0
        bucket["chars"].append(row["chars"])
        for rule in row["rules_fired"]:
            bucket["rule_fires"][rule] = bucket["rule_fires"].get(rule, 0) + 1
    return bucket


def cmd_score(args: argparse.Namespace) -> int:
    path = RESULTS / f"{args.tag}.jsonl"
    if not path.exists():
        print(f"no results at {path}", file=sys.stderr)
        return 1

    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    errored = [row for row in rows if "error" in row]
    scored = [row for row in rows if "error" not in row]

    buckets = {arm: _bucket([row for row in scored if row["arm"] == arm]) for arm in ARMS}

    print(f"scored {len(scored)} runs, {len(errored)} errored (excluded from all rates below)")
    print()
    print(
        "ai-disclosure-missing is excluded from the without-skill arm's pass/fail "
        "rate below: that arm was never told the disclosure requirement exists, "
        "so scoring it against that rule would manufacture a difference that "
        "reflects what the prompt withheld, not what the skill's prose teaches. "
        "It IS counted for with-skill, since SKILL.md states the requirement."
    )
    print()

    for arm in ARMS:
        b = buckets[arm]
        if b["n"] == 0:
            print(f"{arm}: no runs")
            continue
        rate = b["adj_pass"] / b["n"]
        print(
            f"{arm}: {b['adj_pass']}/{b['n']} pass ({rate:.0%}), "
            f"median body length {statistics.median(b['chars']):.0f} chars"
        )

    without = buckets["without-skill"]
    if without["n"]:
        raw_denied = without["n"] - without["raw_pass"]
        print()
        print(
            f"gate counterfactual: {raw_denied}/{without['n']} without-skill bodies "
            "would have been denied outright by the pr-body-gate hook (raw scorer "
            "verdict, ai-disclosure-missing included, since the hook does not know "
            "or care what the author was told). This is what the gate buys on its "
            "own, independent of whether the skill's prose teaches anything."
        )

    with_skill = buckets["with-skill"]
    print()
    if with_skill["n"] and without["n"]:
        p1 = with_skill["adj_pass"] / with_skill["n"]
        p2 = without["adj_pass"] / without["n"]
        delta = p1 - p2
        se = _pooled_se(p1, with_skill["n"], p2, without["n"])
        n_total = with_skill["n"] + without["n"]
        print(
            f"delta (with-skill minus without-skill): {delta:+.0%}, "
            f"n_with-skill={with_skill['n']} n_without-skill={without['n']}"
        )
        if se == 0:
            if delta == 0:
                print("The skill shows no measurable effect at this sample size.")
            else:
                print(
                    f"Full separation at n_with-skill={with_skill['n']} "
                    f"n_without-skill={without['n']} (both arms are unanimous, so "
                    "the pooled standard error is 0). Treat as provisional evidence, "
                    "not a settled result, until the sample size grows."
                )
        elif abs(delta) < 1.96 * se:
            print(
                f"That delta is within noise for n={n_total} (pooled SE={se:.0%}, "
                f"95% band is +/-{1.96 * se:.0%}). The skill shows no measurable "
                "effect at this sample size."
            )
        else:
            print(
                f"That delta clears the noise band for n={n_total} "
                f"(pooled SE={se:.0%}, 95% band is +/-{1.96 * se:.0%})."
            )
    else:
        print("delta: not computable, one or both arms have zero runs")

    print()
    print("per-rule fire rate (raw, unadjusted):")
    all_rules = sorted(set(with_skill["rule_fires"]) | set(without["rule_fires"]))
    if not all_rules:
        print("  (no rules fired in either arm)")
    for rule in all_rules:
        w = with_skill["rule_fires"].get(rule, 0) / with_skill["n"] if with_skill["n"] else 0.0
        wo = without["rule_fires"].get(rule, 0) / without["n"] if without["n"] else 0.0
        print(f"  {rule:<24} with-skill {w:>4.0%}   without-skill {wo:>4.0%}")

    if errored:
        print()
        print(f"{len(errored)} runs errored and were excluded:")
        for row in errored[:10]:
            print(f"  {row.get('arm')} {row.get('diff')} {row.get('model')}: {row.get('error')}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="generate PR bodies with and without SKILL.md in context")
    r.add_argument("--models", default="claude-sonnet-5")
    r.add_argument("--arms", default=",".join(ARMS))
    r.add_argument(
        "--diffs",
        help="comma-separated fixture filenames, default all under bench/fixtures/pr-body",
    )
    r.add_argument("--repeats", type=int, default=1)
    r.add_argument("--jobs", type=int, default=4)
    r.add_argument("--tag", default="pr-body-latest")
    r.set_defaults(func=cmd_run)

    s = sub.add_parser("score", help="score a run's jsonl with pr_body_lint.py")
    s.add_argument("--tag", default="pr-body-latest")
    s.set_defaults(func=cmd_score)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
