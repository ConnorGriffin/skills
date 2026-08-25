# Benchmark replay procedure

Empirical basis for `../routing-table.md`. Run this when a new model ships or an
existing one is updated; results replace the table's scores **for that model
only**. Exploration/impl/plan/brainstorm/docs scores stay comparable across runs
(same ground truth); **review and prototyping do not** — the defect triad is
re-planted and the lock file moves — so whenever those fixtures are regenerated,
re-run a mid-scoring incumbent as an anchor — Luna for review, Terra for
prototyping (a floor-scoring model can't distinguish fixture difficulty) — and
read new scores relative to it.

## Materialize the environment

The prompts in `prompts/` are parameterized templates. Set up (all throwaway,
outside any repo you care about):

```bash
BENCH_ROOT=$(mktemp -d)/bench && mkdir -p $BENCH_ROOT/{fixtures,runs}
# Pinned pre-fix commits (from the original 2026-08-03 run):
#   impl task : private target app @ e9a9e975114539078a5f2636e13dc5a97883c213^
#   plan task : private target app @ 37606dd7d7d4fbd06681c77157a8b8f91620cfb9^
# (This procedure is a template: a reader outside the operator's machines swaps
#  in their own repos, issues, and fixtures.)
git -C <target-app> worktree add --detach $BENCH_ROOT/wt-target <pre-fix-sha>
git -C <agentflow>    worktree add --detach $BENCH_ROOT/wt-agentflow <sha-under-test>
git -C <recipes>      worktree add --detach $BENCH_ROOT/wt-recipes HEAD
# One EXTRA worktree per model for the impl task — writing agents never share.
# Fixtures (issue bodies and PR diffs live in PRIVATE repos — fetch at replay
# time, keep under $BENCH_ROOT, never commit them to this public pack):
gh issue view <N> -R <owner/private-repo> --json title,body > $BENCH_ROOT/fixtures/issue-<N>.json
gh pr diff <N>  -R <owner/private-repo> > $BENCH_ROOT/fixtures/pr-<N>-truth.diff
```

Substitute `$WT_*`, `$FIXTURES`, and `<ISSUE BODY HERE>` into each prompt before
dispatch.

## Areas, tasks, ground truth (originals, 2026-08-03)

| Area | Task | Ground truth |
|---|---|---|
| Exploration | Map ready-issue→merged-PR pipeline in agentflow | Repo itself; judge spot-checks file:line claims |
| Hermetic impl | Replay a real bug-fix issue at the pre-fix commit | The actually-merged fix, including its placement subtleties |
| Plan/spec | Spec a settled design issue at the pre-impl commit | The actually-merged design decisions |
| Prototyping | A printable-card design question from a private recipe repo | That repo's locked mockup spec |
| Brainstorming | 5–7 distinct directions for an open design question | Judged on divergence, domain grounding, kill-tests |
| Documentation | Write the ADR for a merged agentflow PR (#458) | House ADRs + charter's no-implementation-narration rule |
| Code review | Mutated real PR diff with 3 planted defects | The answer key you record when planting (see below) |

## Review fixture: plant the defects

Have a separate agent mutate the truth diff with exactly three defects of graded
subtlety — (1) a blatant logic bug (inverted condition), (2) a subtle boundary
bug (off-by-one that type-checks), (3) a silently weakened test (drop one
sub-case, keep the test green, fix the hunk header) — and write an answer key
(file, region, why wrong, severity) next to the mutated diff under
`$BENCH_ROOT/fixtures/`. The key is scored mechanically: catches out of 3, minus
confident false positives. Keep both files out of this public pack.

## Judging rubrics (score 1–5 per area)

- **Exploration**: spot-check ≥3 file:line claims per output; any fabricated
  citation caps the score at 3. 5 = complete map, all checks pass.
- **Hermetic impl**: run both suites against a recorded baseline; compare the
  diff to the merged fix — same behavior AND same placement subtleties = 5;
  works-but-deviates = 3–3.5.
- **Plan/spec**: single load-bearing decision correct, all consumer sites named,
  fail-safe semantics right, tests concrete, executable without questions,
  brief. A confidently wrong safety decision demotes below a hedged spec.
- **Prototyping**: correct print geometry, single-page discipline, no external
  assets, spec comment complete, proximity to the locked spec's concerns.
  Inventing UI or printing never-print content caps at 1.
- **Brainstorming**: mechanism-distinct directions, real domain grounding,
  cheap decisive kill-tests, ≥2 genuinely non-obvious. Generic-ML re-skins cap
  at 2.5.
- **Documentation**: house-style fidelity, decision + why in domain terms, no
  implementation narration, no fabricated cross-references.
- **Code review**: catches/3 from the answer key; each confident false positive
  costs as much as a miss.

## Rules learned the hard way

1. **One worktree per writing agent**; shared read-only worktrees get an
   explicit "never modify/patch/stash" line in every prompt. A fixture-prep
   agent once left a patch applied to a shared tree and invalidated 20 runs.
2. Record the baseline suite result before judging impl runs (the original
   target app had 20 pre-existing environment errors).
3. Dispatch: Codex via `codex exec -m <model> -c model_reasoning_effort=medium
   --sandbox read-only|workspace-write --skip-git-repo-check -C <dir>`; Claude
   via the Agent tool with a `model` override. Effort stays medium for scored
   runs so results are comparable. (This records how the 2026-08-03 runs were
   dispatched, not how dispatch works now — see ADR 149 and
   `references/dispatch-claude.md` / `references/dispatch-codex.md` for
   current routing.)
4. Judge against ground truth, not eloquence: grep-verify citations, run the
   tests, apply the review answer key mechanically.
5. Interview the model first (self-assessment across the 7 areas) as a
   hypothesis; the benchmark has final say. Expect overclaiming on strengths
   and rough honesty about weaknesses.
