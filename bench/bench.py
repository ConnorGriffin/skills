#!/usr/bin/env python3
"""Run the say-less output style against the default style on a fixed question set.

Both arms run headless with `--setting-sources project` from a scratch project that
holds nothing but the output style, so user settings, hooks and CLAUDE.md memory are
out of the comparison. The style is the only variable.

Usage:
  python3 bench/bench.py run --models claude-opus-5,claude-sonnet-5,claude-fable-5 --repeats 2
  python3 bench/bench.py score

Iterating on the style itself costs half as much with `--styles say-less` (the default
arm is a property of the model, not of the style, so it only needs measuring once), and
`--style-file` points the say-less arm at a candidate file instead of the shipped one.
"""

import argparse
import concurrent.futures
import json
import pathlib
import re
import shutil
import statistics
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
RESULTS = ROOT / "results"
STYLE = ROOT.parent / "output-styles" / "say-less.md"

WORD = re.compile(r"[a-z]+")


def scratch_project(style_file=STYLE, thinking=0):
    """A project dir carrying the style and nothing else."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="say-less-bench-"))
    style_dir = d / ".claude" / "output-styles"
    style_dir.mkdir(parents=True)
    shutil.copy(style_file, style_dir / "say-less.md")
    settings = {"env": {"MAX_THINKING_TOKENS": str(thinking)}} if thinking else {}
    (d / ".claude" / "settings.json").write_text(json.dumps(settings) + "\n")
    return d


def one_run(project, model, style, question):
    cmd = ["claude", "-p", "--model", model, "--setting-sources", "project",
           "--output-format", "json"]
    if style == "say-less":
        cmd += ["--settings", json.dumps({"outputStyle": "say-less"})]
    cmd.append(question["prompt"])
    proc = subprocess.run(cmd, cwd=project, capture_output=True, text=True, timeout=900)
    if proc.returncode != 0:
        return {"id": question["id"], "model": model, "style": style,
                "error": proc.stderr.strip()[:400]}
    payload = json.loads(proc.stdout)
    return {
        "id": question["id"],
        "model": model,
        "style": style,
        "text": payload.get("result", ""),
        "output_tokens": payload.get("usage", {}).get("output_tokens"),
        "duration_ms": payload.get("duration_ms"),
    }


def cmd_run(args):
    questions = json.loads((ROOT / "questions.json").read_text())
    if args.ids:
        wanted = {int(i) for i in args.ids.split(",")}
        questions = [q for q in questions if q["id"] in wanted]
    project = scratch_project(pathlib.Path(args.style_file) if args.style_file else STYLE,
                              args.thinking)
    jobs = [(m, s, q, r)
            for m in args.models.split(",")
            for s in args.styles.split(",")
            for q in questions
            for r in range(args.repeats)]
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"{args.tag}.jsonl"
    done = 0
    with out.open("w") as fh, concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        futures = {pool.submit(one_run, project, m, s, q): (m, s, q, r)
                   for m, s, q, r in jobs}
        for fut in concurrent.futures.as_completed(futures):
            m, s, q, r = futures[fut]
            try:
                row = fut.result()
            except Exception as exc:
                row = {"id": q["id"], "model": m, "style": s, "error": repr(exc)[:400]}
            row["repeat"] = r
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            done += 1
            print(f"{done}/{len(jobs)} {m} {s} q{q['id']}", file=sys.stderr)
    shutil.rmtree(project, ignore_errors=True)
    print(out)


VERDICT = re.compile(r"\b(yes|no)\b")


def first_word(text):
    m = WORD.search(text.lower())
    return m.group(0) if m else ""


def verdict(text):
    """The reply's first yes or no wherever it falls, "" if the reply never signs."""
    m = VERDICT.search(text.lower())
    return m.group(1) if m else ""


RUBRIC = """Score one reply for the outcome it commits to. Nothing else.

Question:
{prompt}

Correct outcome: {answer}. Why: {basis}

Reply:
{text}

Does the reply commit to the same outcome as the correct one? Judge the outcome
only. A reply that never says yes or no still commits to an outcome; read it. A
reply that states one outcome and then corrects itself commits to the corrected
one. Wrong intermediate numbers with the right outcome are a MATCH. Right
numbers with the opposite outcome are a MISMATCH. Ignore wording, length, style,
and whether the reply opens with a verdict word.

Reply with one word: MATCH or MISMATCH."""


def judge(question, entry, text, model):
    """MATCH/MISMATCH from a judge model, "" when the call fails or is unreadable."""
    prompt = RUBRIC.format(prompt=question["prompt"], answer=entry["answer"],
                           basis=entry["basis"], text=text)
    proc = subprocess.run(["claude", "-p", "--model", model, "--setting-sources", "project"],
                          input=prompt, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        return ""
    out = proc.stdout.strip().upper()
    for token in ("MISMATCH", "MATCH"):
        if token in out:
            return token
    return ""


def semantic_scores(rows, key, args):
    """{id(row): MATCH/MISMATCH/""} judged in parallel, keyed by row identity."""
    questions = {q["id"]: q for q in json.loads((ROOT / "questions.json").read_text())}
    scored = {}
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        futures = {}
        for row in rows:
            if "error" in row:
                continue
            futures[pool.submit(judge, questions[row["id"]], key[str(row["id"])],
                                row["text"], args.judge_model)] = id(row)
        for done, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                scored[futures[fut]] = fut.result()
            except Exception:
                scored[futures[fut]] = ""
            print(f"judged {done}/{len(futures)}", file=sys.stderr)
    return scored


def cmd_score(args):
    key = json.loads((ROOT / "answers.json").read_text())
    rows = [json.loads(l) for l in (RESULTS / f"{args.tag}.jsonl").read_text().splitlines()]
    if args.score == "semantic":
        return score_semantic(args, key, rows)
    buckets = {}
    per_q = {}
    wrong = {}
    for row in rows:
        if "error" in row:
            continue
        b = buckets.setdefault((row["model"], row["style"]),
                               {"n": 0, "stated": 0, "correct": 0, "signed": 0,
                                "tokens": []})
        b["n"] += 1
        fw = first_word(row["text"])
        expected = key[str(row["id"])]["answer"]
        hit = fw == expected
        if fw in ("yes", "no"):
            b["stated"] += 1
            if hit:
                b["correct"] += 1
        b["signed"] += verdict(row["text"]) == expected
        b["tokens"].append(row.get("output_tokens") or 0)
        q = per_q.setdefault((row["model"], row["style"]), {})
        n, c = q.get(row["id"], (0, 0))
        q[row["id"]] = (n + 1, c + hit)
        if not hit:
            wrong.setdefault((row["model"], row["style"], row["id"]), []).append(row["text"])
    print(f"{'model':<20} {'style':<10} {'n':>3} {'verdict-first':>14} {'correct':>8} "
          f"{'signed ok':>10} {'median tok':>11} {'mean tok':>9}")
    for (model, style), b in sorted(buckets.items()):
        print(f"{model:<20} {style:<10} {b['n']:>3} {b['stated']:>13}  {b['correct']:>8} "
              f"{b['signed']:>10} "
              f"{statistics.median(b['tokens']):>11.0f} {statistics.mean(b['tokens']):>9.0f}")
    if not args.by_question:
        return
    for (model, style), qs in sorted(per_q.items()):
        print(f"\n{model} {style}")
        for q in sorted(qs):
            n, c = qs[q]
            flag = "" if c == n else "  <-- "
            print(f"  q{q}: {c}/{n}{flag}")
            for text in wrong.get((model, style, q), [])[:2]:
                print(f"      {' '.join(text.split())[:170]}")


def score_semantic(args, key, rows):
    """Outcome-match scoring: what the reply commits to, not what word it opens with."""
    scored = semantic_scores(rows, key, args)
    buckets = {}
    per_q = {}
    wrong = {}
    for row in rows:
        if "error" in row:
            continue
        b = buckets.setdefault((row["model"], row["style"]),
                               {"n": 0, "match": 0, "unjudged": 0, "tokens": []})
        b["n"] += 1
        verdict_ = scored.get(id(row), "")
        b["match"] += verdict_ == "MATCH"
        b["unjudged"] += verdict_ == ""
        b["tokens"].append(row.get("output_tokens") or 0)
        q = per_q.setdefault((row["model"], row["style"]), {})
        n, c = q.get(row["id"], (0, 0))
        q[row["id"]] = (n + 1, c + (verdict_ == "MATCH"))
        if verdict_ != "MATCH":
            wrong.setdefault((row["model"], row["style"], row["id"]), []).append(row["text"])
    print(f"{'model':<20} {'style':<10} {'n':>3} {'outcome ok':>11} {'unjudged':>9} "
          f"{'median tok':>11} {'mean tok':>9}")
    for (model, style), b in sorted(buckets.items()):
        print(f"{model:<20} {style:<10} {b['n']:>3} {b['match']:>11} {b['unjudged']:>9} "
              f"{statistics.median(b['tokens']):>11.0f} {statistics.mean(b['tokens']):>9.0f}")
    if not args.by_question:
        return
    for (model, style), qs in sorted(per_q.items()):
        print(f"\n{model} {style}")
        for q in sorted(qs):
            n, c = qs[q]
            flag = "" if c == n else "  <-- "
            print(f"  q{q}: {c}/{n}{flag}")
            for text in wrong.get((model, style, q), []):
                print(f"      {' '.join(text.split())[:250]}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--models", default="claude-opus-5,claude-sonnet-5,claude-fable-5")
    r.add_argument("--repeats", type=int, default=2)
    r.add_argument("--jobs", type=int, default=6)
    r.add_argument("--tag", default="latest")
    r.add_argument("--ids", help="comma-separated question ids, default all")
    r.add_argument("--styles", default="default,say-less")
    r.add_argument("--style-file", help="candidate style to run the say-less arm against")
    r.add_argument("--thinking", type=int, default=0,
                   help="MAX_THINKING_TOKENS for both arms, 0 leaves the harness default")
    r.set_defaults(func=cmd_run)
    s = sub.add_parser("score")
    s.add_argument("--tag", default="latest")
    s.add_argument("--by-question", action="store_true")
    s.add_argument("--score", choices=("first-word", "semantic"), default="first-word",
                   help="first-word compares the reply's opening word to the key; "
                        "semantic asks a judge model whether the outcome matches")
    s.add_argument("--judge-model", default="haiku", help="judge for --score semantic")
    s.add_argument("--jobs", type=int, default=6, help="parallel judge calls")
    s.set_defaults(func=cmd_score)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
