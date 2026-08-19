#!/usr/bin/env python3
"""Measure whether the pr-body skill's prose teaches a model to write a passing body,
and whether the deny-and-fix loop (the hook's real workflow) closes the gap.

The first eval measured only a first draft with the whole of SKILL.md in context, and
found nothing (+8% against a +/-17% noise band). This version asks two sharper
questions:

Experiment A: which slice of SKILL.md's ~1600 words teaches. Four arms run the same
diffs through the same model:
  none    - the diff only
  example - only the worked example block (the fenced ```markdown body, plus the
            paragraph that follows it)
  rules   - only "## The shape" and "## Textures to cut"
  full    - all of SKILL.md
Slices are extracted from SKILL.md at runtime by heading (see build_skill_slices());
if a heading has moved, extraction raises rather than shipping an empty slice.

Experiment B: for each arm, after the first draft, score with pr_body_lint.py; on a
fail, send the model its own body plus the findings and ask for a corrected body, to a
maximum of 3 rounds. This is the deny-and-fix loop the hook actually runs.

Experiment C: a --retry-modes flag varies what the retry prompt includes.
  fix-text   - each finding's rule name and its fix text (what the hook sends)
  rule-names - only the rule names that fired, no fix text
If rule-names converges as fast as fix-text, the fix wording is decoration.

Usage:
  python3 bench/pr_body_bench.py slices
  python3 bench/pr_body_bench.py run --models claude-sonnet-5 --repeats 8
  python3 bench/pr_body_bench.py run --retry-modes fix-text,rule-names --repeats 4
  python3 bench/pr_body_bench.py score

Fixtures live in bench/fixtures/pr-body/ and results in bench/results/pr-body/, both
gitignored: the diffs and the bodies written about them come from a private estate.
Point --diffs at your own.

`run` is resumable: it skips (arm, retry_mode, diff, model, repeat) combinations
already present in the target jsonl, and appends new results one at a time so an
interrupted run loses nothing already written.

CAVEAT, load-bearing and not to be missed: a linter pass is a weak proxy for a good
body. On the operator's hand-labeled set of 25 real bodies, the linter caught 4 of the
12 rejected ones. A high loop-pass rate here means the countable defects are gone, not
that the body is good.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import math
import pathlib
import re
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
SKILL_MD = REPO_ROOT / "skills" / "tools" / "pr-body" / "SKILL.md"
LINT_SCRIPT = REPO_ROOT / "skills" / "tools" / "pr-body" / "scripts" / "pr_body_lint.py"

ARMS = ("none", "example", "rules", "full")
RETRY_MODES = ("fix-text", "rule-names")
MAX_ROUNDS = 3

CAVEAT = (
    "CAVEAT: a linter pass is a weak proxy for a good body. On the operator's "
    "hand-labeled set of 25 real bodies, the linter caught 4 of the 12 rejected "
    "ones. A high loop-pass rate means the countable defects are gone, not that "
    "the body is good."
)


def _load_lint():
    spec = importlib.util.spec_from_file_location("pr_body_lint", LINT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LINT = _load_lint()


# --- SKILL.md slice extraction --------------------------------------------------

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*)$", re.MULTILINE)
FENCED_MARKDOWN_RE = re.compile(r"```markdown\n.*?\n```", re.DOTALL)


class SkillExtractionError(RuntimeError):
    """SKILL.md no longer has the structure a slice extractor expects.

    Raised instead of returning an empty slice, so a moved heading fails the
    run loudly rather than silently shipping a blank prompt for that arm.
    """


def _headings(text: str) -> list[tuple[int, int, str]]:
    return [
        (match.start(), match.end(), match.group(2).strip())
        for match in HEADING_RE.finditer(text)
    ]


def _section_body(text: str, heading_title: str) -> str:
    """Text between a heading line (matched by title, case-insensitive) and the
    next heading of any level, or end of document."""
    headings = _headings(text)
    matches = [
        (start, line_end) for start, line_end, title in headings
        if title.lower() == heading_title.lower()
    ]
    if not matches:
        raise SkillExtractionError(
            f"heading {heading_title!r} not found in {SKILL_MD}; extraction target moved"
        )
    start, line_end = matches[0]
    later_starts = [s for s, _, _ in headings if s > start]
    end = later_starts[0] if later_starts else len(text)
    body = text[line_end:end].strip()
    if not body:
        raise SkillExtractionError(
            f"heading {heading_title!r} has no body text in {SKILL_MD}"
        )
    return body


def _example_slice(text: str) -> str:
    """The worked example: the fenced ```markdown block, plus the paragraph that
    immediately follows it (the "No headings. No reason..." sentence group)."""
    match = FENCED_MARKDOWN_RE.search(text)
    if match is None:
        raise SkillExtractionError(
            f"no fenced ```markdown example block found in {SKILL_MD}; extraction target moved"
        )
    fence = match.group(0)
    rest = text[match.end():]
    paragraph_match = re.match(r"[ \t]*\n+([^\n].*?)(?:\n[ \t]*\n|\Z)", rest, re.DOTALL)
    if paragraph_match is None:
        raise SkillExtractionError(
            f"no paragraph follows the fenced example block in {SKILL_MD}; extraction target moved"
        )
    sentence = paragraph_match.group(1).strip()
    return f"{fence}\n\n{sentence}"


def _rules_slice(text: str) -> str:
    """"The shape" numbered list plus the "Textures to cut" list, nothing else."""
    shape = _section_body(text, "The shape")
    cuts = _section_body(text, "Textures to cut")
    return f"{shape}\n\n{cuts}"


def build_skill_slices(skill_text: str | None = None) -> dict[str, str]:
    text = skill_text if skill_text is not None else SKILL_MD.read_text(encoding="utf-8")
    slices = {
        "none": "",
        "example": _example_slice(text),
        "rules": _rules_slice(text),
        "full": text,
    }
    for name in ("example", "rules", "full"):
        assert slices[name].strip(), f"{name!r} slice extracted empty from {SKILL_MD}"
    return slices


# ai-disclosure-missing is the one rule SKILL.md states as an explicit requirement
# (in the intro example's closing line and in the rules table); "rules" never
# mentions it and "none" never mentions it either, so scoring those two arms
# against that rule would manufacture a difference that reflects what the prompt
# withheld, not what the slice teaches. "example" is left in scope because the
# example body it hands the model ends with that exact disclosure sentence.
UNTAUGHT_RULES_BY_ARM = {
    "none": {"ai-disclosure-missing"},
    "example": set(),
    "rules": {"ai-disclosure-missing"},
    "full": set(),
}


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


RETRY_TEMPLATE = """Here is the pull-request body you wrote:

{body}

A linter found these problems with it:

{findings}

Write a corrected version of the body. Reply with the body text only. No
preamble, no explanation, no code fence around the body."""


def build_prompt(diff_text: str, arm: str, skill_slices: dict[str, str]) -> str:
    prompt = PROMPT_TEMPLATE.format(diff=diff_text)
    slice_text = skill_slices[arm]
    if slice_text:
        prompt = f"{slice_text}\n\n---\n\n{prompt}"
    return prompt


def _findings_block(findings: list[dict], retry_mode: str) -> str:
    lines = []
    for finding in findings:
        if retry_mode == "rule-names":
            lines.append(f"- {finding['rule']} ({finding['severity']})")
        else:
            lines.append(f"- {finding['rule']} ({finding['severity']}): {finding['fix']}")
    return "\n".join(lines)


def build_retry_prompt(previous_body: str, findings: list[dict], retry_mode: str) -> str:
    return RETRY_TEMPLATE.format(
        body=previous_body, findings=_findings_block(findings, retry_mode)
    )


def score_body(body: str) -> dict:
    result = LINT.lint(body)
    findings = result["findings"]
    return {
        "chars": len(body),
        "verdict": result["verdict"],
        "findings": findings,
        "rules_fired": sorted({f["rule"] for f in findings}),
        "blocking_rules_fired": sorted(
            {f["rule"] for f in findings if f["severity"] == "block"}
        ),
    }


def call_claude(project: pathlib.Path, model: str, prompt: str) -> dict:
    cmd = [
        "claude", "-p", "--model", model,
        "--setting-sources", "project",
        "--output-format", "json",
    ]
    # Prompt goes on stdin, never argv: SKILL.md's frontmatter starts with `---`,
    # which argv parsing would read as a flag.
    proc = subprocess.run(cmd, cwd=project, input=prompt,
                          capture_output=True, text=True, timeout=900)
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()[:400]}
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        return {"error": f"non-JSON output: {error}"}
    return {
        "body": payload.get("result", ""),
        "output_tokens": payload.get("usage", {}).get("output_tokens") or 0,
    }


def one_run(
    project: pathlib.Path,
    model: str,
    arm: str,
    diff_path: pathlib.Path,
    retry_mode: str,
    skill_slices: dict[str, str],
) -> dict:
    """First draft, then up to MAX_ROUNDS deny-and-fix rounds.

    Each retry_mode regenerates its own first draft rather than sharing one
    across modes, so requesting both fix-text and rule-names in one --retry-modes
    run doubles the round-0 calls. Kept simple deliberately: round 0 is cheap
    relative to the retry rounds, and every row stays self-contained.
    """
    diff_text = diff_path.read_text(encoding="utf-8")
    row = {
        "arm": arm, "retry_mode": retry_mode, "diff": diff_path.name,
        "model": model, "rounds": [],
    }
    prompt = build_prompt(diff_text, arm, skill_slices)
    result = call_claude(project, model, prompt)
    if "error" in result:
        row["error"] = result["error"]
        return row

    body = result["body"]
    total_output_tokens = result["output_tokens"]
    round_index = 0
    rounds_to_pass = None
    while True:
        scored = score_body(body)
        row["rounds"].append({
            "round": round_index,
            "body": body,
            "chars": scored["chars"],
            "verdict": scored["verdict"],
            "rules_fired": scored["rules_fired"],
            "blocking_rules_fired": scored["blocking_rules_fired"],
        })
        if scored["verdict"] == "pass":
            rounds_to_pass = round_index
            break
        if round_index >= MAX_ROUNDS:
            break
        retry_prompt = build_retry_prompt(body, scored["findings"], retry_mode)
        retry_result = call_claude(project, model, retry_prompt)
        if "error" in retry_result:
            row["error"] = retry_result["error"]
            break
        body = retry_result["body"]
        total_output_tokens += retry_result["output_tokens"]
        round_index += 1

    row["rounds_to_pass"] = rounds_to_pass
    row["output_tokens_total"] = total_output_tokens
    return row


def _completed_keys(path: pathlib.Path) -> set[tuple[str, str, str, int, str]]:
    if not path.exists():
        return set()
    keys = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not {"arm", "diff", "model"} <= row.keys():
            continue
        keys.add((
            row["arm"], row["diff"], row["model"],
            row.get("repeat", 0), row.get("retry_mode", "fix-text"),
        ))
    return keys


def cmd_slices(args: argparse.Namespace) -> int:
    slices = build_skill_slices()
    for arm in ARMS:
        print(f"{arm:<8} {len(slices[arm]):>6} chars")
    return 0


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
    retry_modes = args.retry_modes.split(",")
    for retry_mode in retry_modes:
        if retry_mode not in RETRY_MODES:
            print(f"unknown retry mode {retry_mode!r}, must be one of {RETRY_MODES}", file=sys.stderr)
            return 1

    try:
        skill_slices = build_skill_slices()
    except SkillExtractionError as error:
        print(f"SKILL.md slice extraction failed: {error}", file=sys.stderr)
        return 1
    print("slice sizes:", file=sys.stderr)
    for arm in ARMS:
        print(f"  {arm:<8} {len(skill_slices[arm]):>6} chars", file=sys.stderr)

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{args.tag}.jsonl"
    done_keys = _completed_keys(out)

    jobs = [
        (model, arm, diff, repeat, retry_mode)
        for model in models
        for arm in arms
        for diff in diffs
        for repeat in range(args.repeats)
        for retry_mode in retry_modes
        if (arm, diff.name, model, repeat, retry_mode) not in done_keys
    ]
    if not jobs:
        print(f"all {len(done_keys)} runs already recorded in {out}; nothing to do", file=sys.stderr)
        return 0

    project = scratch_project()
    total = len(jobs)
    try:
        with out.open("a") as fh, concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
            futures = {
                pool.submit(one_run, project, model, arm, diff, retry_mode, skill_slices):
                    (model, arm, diff, repeat, retry_mode)
                for model, arm, diff, repeat, retry_mode in jobs
            }
            completed = 0
            for fut in concurrent.futures.as_completed(futures):
                model, arm, diff, repeat, retry_mode = futures[fut]
                try:
                    row = fut.result()
                except Exception as exc:  # noqa: BLE001 - one job's crash must not lose the rest
                    row = {
                        "arm": arm, "diff": diff.name, "model": model,
                        "retry_mode": retry_mode, "rounds": [],
                        "error": repr(exc)[:400],
                    }
                row["repeat"] = repeat
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                completed += 1
                print(
                    f"{completed}/{total} {model} {arm} {retry_mode} {diff.name} rep{repeat}",
                    file=sys.stderr,
                )
    finally:
        shutil.rmtree(project, ignore_errors=True)

    print(out)
    return 0


# --- scoring / aggregation --------------------------------------------------

def _adjusted_blocking(rules_fired: list[str], arm: str) -> list[str]:
    untaught = UNTAUGHT_RULES_BY_ARM.get(arm, set())
    return [rule for rule in rules_fired if rule not in untaught]


# Cross-arm comparison excludes every rule ANY arm fails to teach, not each arm's
# own set. Per-arm exclusion scores the arms against different rulebooks: it
# credits an arm for never being told a rule while charging the arm that was.
# That alone reversed `full`'s ranking on this bench's first run.
COMPARABLE_UNTAUGHT = set().union(*UNTAUGHT_RULES_BY_ARM.values())


def _comparable_blocking(rules_fired: list[str]) -> list[str]:
    return [rule for rule in rules_fired if rule not in COMPARABLE_UNTAUGHT]


def _fully_errored(row: dict) -> bool:
    """The first draft itself never came back; nothing in this row is usable."""
    return not row.get("rounds")


def _partial(row: dict) -> bool:
    """A draft exists but a later retry call errored before a pass or 3 rounds."""
    return bool(row.get("error")) and bool(row.get("rounds"))


def _single_se(p: float, n: int) -> float:
    return math.sqrt(p * (1 - p) / n) if n else 0.0


def _pooled_se(p1: float, n1: int, p2: float, n2: int) -> float:
    return math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)


def _bucket_first_draft(rows: list[dict], arm: str) -> dict:
    bucket = {"n": 0, "raw_pass": 0, "adj_pass": 0, "cmp_pass": 0, "chars": [], "rule_fires": {}}
    for row in rows:
        first = row["rounds"][0]
        bucket["n"] += 1
        bucket["raw_pass"] += 1 if first["verdict"] == "pass" else 0
        adjusted = _adjusted_blocking(first["blocking_rules_fired"], arm)
        bucket["adj_pass"] += 1 if not adjusted else 0
        bucket["cmp_pass"] += 1 if not _comparable_blocking(first["blocking_rules_fired"]) else 0
        bucket["chars"].append(first["chars"])
        for rule in first["rules_fired"]:
            bucket["rule_fires"][rule] = bucket["rule_fires"].get(rule, 0) + 1
    return bucket


def _bucket_loop(rows: list[dict]) -> dict:
    """Rows here have already been filtered to non-partial, non-fully-errored."""
    bucket = {
        "n": 0, "raw_pass": 0, "chars": [], "rounds_to_pass": [], "never_in_3": 0,
        "rule_fires_final": {},
    }
    for row in rows:
        last = row["rounds"][-1]
        bucket["n"] += 1
        bucket["raw_pass"] += 1 if last["verdict"] == "pass" else 0
        bucket["chars"].append(last["chars"])
        rtp = row.get("rounds_to_pass")
        bucket["rounds_to_pass"].append(rtp)
        if rtp is None:
            bucket["never_in_3"] += 1
        for rule in last["rules_fired"]:
            bucket["rule_fires_final"][rule] = bucket["rule_fires_final"].get(rule, 0) + 1
    return bucket


def _report_two_sample(label: str, p1: float, n1: int, p2: float, n2: int) -> None:
    delta = p1 - p2
    se = _pooled_se(p1, n1, p2, n2)
    band = 1.96 * se
    n_total = n1 + n2
    if se == 0:
        if delta == 0:
            verdict = "the effect is not measurable at this sample size (both arms unanimous, SE=0)"
        else:
            verdict = (
                f"full separation at n={n_total} (both arms unanimous, pooled SE=0); "
                "treat as provisional, not settled, until n grows"
            )
    elif abs(delta) < band:
        verdict = "the effect is not measurable at this sample size"
    else:
        verdict = "clears the noise band"
    print(
        f"{label}: delta {delta:+.0%}, n={n_total} "
        f"(pooled SE={se:.0%}, 95% band +/-{band:.0%}) -> {verdict}"
    )


def cmd_score(args: argparse.Namespace) -> int:
    path = RESULTS / f"{args.tag}.jsonl"
    if not path.exists():
        print(f"no results at {path}", file=sys.stderr)
        return 1

    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    fully_errored = [row for row in rows if _fully_errored(row)]
    partial = [row for row in rows if not _fully_errored(row) and _partial(row)]
    usable = [row for row in rows if not _fully_errored(row)]
    completed = [row for row in usable if not _partial(row)]

    print(
        f"{len(rows)} runs total: {len(usable)} produced at least a first draft, "
        f"{len(fully_errored)} errored before any draft (excluded from everything), "
        f"{len(partial)} errored mid-loop after a draft (first draft counted below, "
        "loop-completion metrics excluded)."
    )
    print()
    print(CAVEAT)
    print()

    fix_text_rows = [row for row in completed if row.get("retry_mode", "fix-text") == "fix-text"]
    fix_text_usable = [row for row in usable if row.get("retry_mode", "fix-text") == "fix-text"]

    print("=== Experiment A: first-draft pass rate per arm ===")
    print(
        "Like-for-like: every arm scored on the same rules, excluding any rule some\n"
        "arm was never taught (" + ", ".join(sorted(COMPARABLE_UNTAUGHT)) + "). Scoring each\n"
        "arm against only its own taught rules compares them to different rulebooks."
    )
    print()
    first_draft_buckets = {
        arm: _bucket_first_draft([r for r in usable if r["arm"] == arm], arm) for arm in ARMS
    }
    for arm in ARMS:
        b = first_draft_buckets[arm]
        if b["n"] == 0:
            print(f"{arm}: no runs")
            continue
        rate = b["cmp_pass"] / b["n"]
        band = 1.96 * _single_se(rate, b["n"])
        print(
            f"{arm}: {b['cmp_pass']}/{b['n']} pass ({rate:.0%} +/-{band:.0%}, n={b['n']}), "
            f"median length {statistics.median(b['chars']):.0f} chars"
        )
    print()
    baseline = first_draft_buckets["none"]
    if baseline["n"]:
        p2 = baseline["cmp_pass"] / baseline["n"]
        for arm in ("example", "rules", "full"):
            b = first_draft_buckets[arm]
            if b["n"] == 0:
                continue
            p1 = b["cmp_pass"] / b["n"]
            _report_two_sample(f"{arm} vs none (first draft)", p1, b["n"], p2, baseline["n"])
    else:
        print("delta: not computable, no runs for arm 'none'")

    print()
    print("per-rule fire rate at first draft (raw, unadjusted, pooled across arms):")
    all_first_rules: dict[str, int] = {}
    total_first_n = 0
    for arm in ARMS:
        b = first_draft_buckets[arm]
        total_first_n += b["n"]
        for rule, count in b["rule_fires"].items():
            all_first_rules[rule] = all_first_rules.get(rule, 0) + count
    if not all_first_rules or total_first_n == 0:
        print("  (no rules fired, or no runs)")
    for rule in sorted(all_first_rules):
        rate = all_first_rules[rule] / total_first_n
        print(f"  {rule:<24} {rate:>4.0%}  (n={total_first_n})")

    print()
    print("=== Experiment B: the deny-and-fix loop (retry_mode=fix-text) ===")
    print()
    if not fix_text_rows:
        print("no completed fix-text loop runs to score")
    else:
        loop_buckets = {arm: _bucket_loop([r for r in fix_text_rows if r["arm"] == arm]) for arm in ARMS}
        for arm in ARMS:
            b = loop_buckets[arm]
            if b["n"] == 0:
                print(f"{arm}: no completed loop runs")
                continue
            rate = b["raw_pass"] / b["n"]
            band = 1.96 * _single_se(rate, b["n"])
            never_rate = b["never_in_3"] / b["n"]
            never_band = 1.96 * _single_se(never_rate, b["n"])
            finite = [r for r in b["rounds_to_pass"] if r is not None]
            median_rounds = statistics.median(finite) if finite else "n/a"
            print(
                f"{arm}: final pass {b['raw_pass']}/{b['n']} ({rate:.0%} +/-{band:.0%}, n={b['n']}), "
                f"never-pass-in-3 {b['never_in_3']}/{b['n']} ({never_rate:.0%} +/-{never_band:.0%}), "
                f"median rounds-to-pass (of those that pass) {median_rounds}, "
                f"median final length {statistics.median(b['chars']):.0f} chars"
            )
            counts = {}
            for r in b["rounds_to_pass"]:
                key = "never" if r is None else str(r)
                counts[key] = counts.get(key, 0) + 1
            dist = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
            print(f"  rounds_to_pass distribution: {dist}")

        print()
        print("median body length, first draft vs final (fix-text only):")
        for arm in ARMS:
            b = loop_buckets[arm]
            fb = first_draft_buckets[arm]
            if b["n"] == 0 or fb["n"] == 0:
                continue
            print(
                f"  {arm:<8} first {statistics.median(fb['chars']):>6.0f} chars -> "
                f"final {statistics.median(b['chars']):>6.0f} chars"
            )

        print()
        print("per-rule fire rate, first draft vs final (fix-text, pooled across arms):")
        first_pool: dict[str, int] = {}
        final_pool: dict[str, int] = {}
        n_pool = len(fix_text_rows)
        for row in fix_text_rows:
            for rule in row["rounds"][0]["rules_fired"]:
                first_pool[rule] = first_pool.get(rule, 0) + 1
            for rule in row["rounds"][-1]["rules_fired"]:
                final_pool[rule] = final_pool.get(rule, 0) + 1
        all_rules = sorted(set(first_pool) | set(final_pool))
        if not all_rules:
            print("  (no rules fired)")
        for rule in all_rules:
            first_rate = first_pool.get(rule, 0) / n_pool if n_pool else 0.0
            final_rate = final_pool.get(rule, 0) / n_pool if n_pool else 0.0
            flag = ""
            if final_pool.get(rule, 0) > 0 and final_rate >= 0.20:
                flag = "  <-- SURVIVES THE LOOP: told exactly what is wrong and still fires; likely a defect in this rule or its fix text"
            print(f"  {rule:<24} first {first_rate:>4.0%}  final {final_rate:>4.0%}{flag}")

    print()
    print("=== Experiment C: fix-text vs rule-names on rounds-to-pass ===")
    print()
    rule_names_rows = [row for row in completed if row.get("retry_mode") == "rule-names"]
    if not rule_names_rows:
        print("no rule-names runs recorded; run with --retry-modes fix-text,rule-names to compare")
    else:
        for label, subset in (("fix-text", fix_text_rows), ("rule-names", rule_names_rows)):
            n = len(subset)
            converged = sum(1 for r in subset if r.get("rounds_to_pass") is not None)
            rate = converged / n if n else 0.0
            band = 1.96 * _single_se(rate, n)
            finite = [r["rounds_to_pass"] for r in subset if r.get("rounds_to_pass") is not None]
            median_rounds = statistics.median(finite) if finite else "n/a"
            print(
                f"{label}: converged-in-3 {converged}/{n} ({rate:.0%} +/-{band:.0%}, n={n}), "
                f"median rounds-to-pass (of those that pass) {median_rounds}"
            )
        n1, n2 = len(fix_text_rows), len(rule_names_rows)
        if n1 and n2:
            p1 = sum(1 for r in fix_text_rows if r.get("rounds_to_pass") is not None) / n1
            p2 = sum(1 for r in rule_names_rows if r.get("rounds_to_pass") is not None) / n2
            _report_two_sample("fix-text vs rule-names (converged-in-3)", p1, n1, p2, n2)
            if abs(p1 - p2) < 1.96 * _pooled_se(p1, n1, p2, n2):
                print(
                    "rule-names converges as fast as fix-text within noise: the fix "
                    "text is not shown to be earning its keep at this sample size."
                )

    if not fix_text_usable and not rule_names_rows:
        print()
        print("(nothing scored yet; run 'run' first)")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sl = sub.add_parser("slices", help="print each arm's slice character count and exit")
    sl.set_defaults(func=cmd_slices)

    r = sub.add_parser("run", help="generate PR bodies across arms, then run the deny-and-fix loop")
    r.add_argument("--models", default="claude-sonnet-5")
    r.add_argument("--arms", default=",".join(ARMS))
    r.add_argument("--retry-modes", default="fix-text")
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
