# Model routing table

Benchmarked 2026-08-03 against real replayed tasks from the operator's repos: the
public agentflow fleet daemon plus two private apps (a telemetry/tuning app and a
recipe collection). Ground truth: the actually-merged fixes, a locked mockup spec,
and a planted-defect review fixture. Models: Claude Opus 5, Sonnet 5, Haiku 4.5; GPT-5.6-Sol, -Terra, -Luna,
GPT-5.3-Codex-Spark (full suite); GPT-5.5, GPT-5.4, GPT-5.4-Mini (light pass: plan +
review only). Codex runs at `model_reasoning_effort=medium`. Scores 1–5, judged blind by
the coordinator against ground truth; published-eval data was a secondary signal only.
Re-benchmark when a new model ships — and note Claude routes dispatch via unversioned aliases (`opus`/`sonnet`/`haiku`), so re-verify this stamp when Anthropic rolls a snapshot, not only on a named launch. See `benchmark/README.md`.

Cost tiers as of 2026-08-03 — routes were selected at these prices; re-check on a
price move (per M tokens in/out): Opus $5/$25 · Sonnet $3/$15 · Haiku $1/$5 ·
Sol $5/$30 · Terra $2.50/$15 · Luna $1/$6. Spark, GPT-5.5, GPT-5.4, and
GPT-5.4-Mini are flat-rate under the operator's ChatGPT plan (price them normally if you pay
per token) — under flat rate they sit outside the cheapest-clears-bar rule and are chosen only where a route
below names them explicitly (Spark for latency; GPT-5.4 as a plan alternate).

## Review-consumer classification

Before applying their own named area row, `code-review` and `plan-review` obtain
routine/load-bearing routing stakes and their initial route directly from
[`review-routing.md`](review-routing.md).

Opus in the Plan / spec writing ladder is an availability rung, not a benchmarked
plan-writing win.

## Routes (cheapest that clears the bar) and escalation ladders

Escalate one step at a time along the row's ladder; at the last rung, stop and
surface both failed attempts to the operator.

| Area | Route | Ladder | Why |
|---|---|---|---|
| Exploration / codebase-mapping | **Luna** for bounded lookups; **Sonnet** for full-system maps | Luna → Sonnet → Opus | Sonnet tied Opus at 5/5 with fully verified citations at 60% of the cost; Luna scored 4 at a fraction of both. Haiku fabricated a citation — do not use for exploration you won't verify. |
| Hermetic implementation | **Terra** | Terra → Sonnet → Opus | Terra matched the merged fix exactly (incl. the window-bounds subtlety) at $2.50; Sonnet/Opus scored 5 with richer tests — escalate for correctness-critical or gnarly changes. Luna/Haiku/Spark all missed a subtle placement decision. Field-derived provenance (sources: #144's session-fit comment and epic ledger PR #136): Terra failed canonical byte-for-byte prose-contract work on #151 and #152, required escalation, and informed #144's stamp; this observation changes neither Route nor Ladder. |
| Plan / spec writing | **Terra** | Terra → Sol → Opus | The Codex family owns this area: Terra 5/5 (tightest, correct fail-closed), Sol/Luna/GPT-5.4 ≈4.8. Opus wrote the prettiest spec with a load-bearing polarity error — never route specs to Claude models without a fail-safe review. Field-derived provenance (sources: #144's session-fit comment and epic ledger PR #136): Terra failed canonical byte-for-byte prose-contract work on #151 and #152, required escalation, and informed #144's stamp; this observation changes neither Route nor Ladder. |
| Prototyping (incl. UI mockups) | **Sol** | Sol → Opus → none (top of ladder; Sol first despite Opus's lower sticker price — Sol's per-task token volume ran leaner and its output resolved a spec tension Opus ignored) | Sol, Opus, and Spark all hit 5; Sol resolved a spec tension the others ignored. Spark ties when repo context (an existing lock/design system) exists to reuse — and it's near-instant. Luna is banned here (1/5: no page geometry, invented UI, leaked never-print content). |
| Novel-solution brainstorming | **Terra**; **Opus** when novelty is the deliverable | Terra → Opus → none (top of ladder) | Opus 5/5 with the most novel idea of the whole benchmark; Terra 4.5 at half the price. Haiku and Spark produce generic-ML re-skins — don't route ideation there. |
| Documentation writing | **Haiku** (default; Luna equal-scored alternate) | Haiku → Opus → Sol (Opus first: equal score, lower price) | Both scored 4 at ~$1; Opus and Sol scored 5 — escalate for load-bearing ADRs. Sonnet (3) narrated implementation identifiers; Spark (2) fabricated a cross-reference. |
| Code review | **Luna** for routine PRs; **Opus** for load-bearing/safety review | Luna → Sonnet → Opus; Opus route: none (top of ladder) | Opus was the only model to catch all 3 planted defects (incl. a silently weakened test). Luna caught 2/3 with zero false positives at the lowest cost. GPT-5.5 confidently reported a nonexistent syntax error; GPT-5.4-Mini missed a blatant inverted guard — avoid both for review. Field-derived provenance (source: epic ledger PR #136's 2026-08-25 rounds): Sol produced zero hallucinated findings across approximately 20 Full-depth and cold reviews in one epic session, with every blocking finding reproduced against the tree, grounding the standing Codex-first review practice. |

## Effort notes (coarse, per spec decision 8)
- Every delegation carries an effort dial (per ADR 149,
  `docs/adr/adr-149-pack-owned-model-dispatch.md`), defaulting to medium for
  every model — overridable per delegation, never left implicit. The default
  is uniform because no effort benchmarking exists yet: all scored runs used
  Codex medium effort, and it was sufficient everywhere tested. Changing a
  model's default effort is a benchmark result, not a preference, and gets set
  only when a replay measures one; escalation changes the model tier, not the
  effort dial.
- The two adapters validate different enums, each a literal in its own
  script: `claude-worker.py` accepts `low|medium|high|xhigh|max`;
  `codex-worker.py` accepts `minimal|low|medium|high|xhigh` (unvalidated
  locally by the Codex CLI itself). See
  `docs/scope/149-probes/effort-enums.md`.
- Spark's value is latency: use for tight edit-test loops and mockup iteration, not judgment.
- Opus spends ~4–5× Haiku's tokens on the same exploration prompt; route it only where the depth is the point.

## Light-tier verdicts (plan + review probes only)
- **GPT-5.5**: competent but padded; one confident false positive. No niche the 5.6 family doesn't fill better.
- **GPT-5.4**: genuinely strong spec-writer (4.7, line-level verified citations) — viable Terra alternate for plans.
- **GPT-5.4-Mini**: clean prose, weak review (missed a blatant inversion), invents scope. Avoid.

## Cross-cutting empirical findings
- Self-assessments were directionally honest about weaknesses (every model self-flagged visual prototyping; all were right except Sol/Spark, who beat their own expectations) but inflated on strengths — Sol claimed 5s across the board and scored 3 on brainstorming; Terra's claimed 5s on plan/docs held up, its review 4 didn't (3.5).
- The Claude models' edge is depth-with-verification (review, exploration); the Codex 5.6 family's edge is disciplined, executable specs and cheap accuracy.
- Never delegate to Fable (coordinator tier only — spec decision 4).
