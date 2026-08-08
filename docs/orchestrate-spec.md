# /orchestrate — locked spec (2026-08-03)

Settled in a scope interview session; this file is the fixed reference the finished
skill is compared against. Changes after this point are deviations and must be
called out, not silently absorbed.

## Purpose

A user-invocable skill that flips a Claude Code session into **coordinator
mode**: the parent agent plans, scopes, reviews, and ships, but does not write
the implementation itself. Real work is delegated to sub-agents, routed by an
empirically built model-capability table.

## Decisions

1. **Parent**: Claude Code only. Codex models are reached via `codex exec`
   (non-interactive), with `codex exec resume` for follow-ups so sub-agent
   context carries over. No symmetric Codex-parent mode.
2. **Home**: `skills/orchestrate/` in the public skills repo.
   - `SKILL.md` — behavior.
   - `references/routing-table.md` — the routing table.
   - `references/benchmark/` — benchmark prompts, rubrics, and a documented
     replay procedure for re-benchmarking when new models ship.
3. **Behavioral core** (embedded verbatim from the operator's ruling):
   - Coordinator plans, scopes, reviews, ships; does not implement.
   - Delegates exploration, implementation, review passes, fixes to sub-agents
     on cheaper tiers.
   - Writes detailed, self-contained specs per sub-agent (files to read, exact
     requirements, test obligations, commit format) and verifies output rather
     than trusting it, including independent review passes on
     correctness-sensitive changes with findings routed back to the
     implementing agent.
   - Continues an existing sub-agent for follow-ups in its area instead of
     spawning fresh.
   - Coordinator keeps: small mechanical glue (git/gh plumbing, toggles, log
     checks, daemon restarts), verification probes, and all
     communication/decisions with the operator.
4. **Routing principle**: cheapest model that clears the bar for the area.
   **Never delegate to Fable** (it is the coordinator tier only).
5. **Escalation rule**: on failed verification, one retry in the *same*
   sub-agent session carrying the coordinator's findings; on second failure, a
   fresh agent one tier up with the original spec plus a note on what failed.
   Never unbounded retries; never tier-skipping straight to the top.
6. **Session scope**: invoking `/orchestrate` applies for the rest of the
   session until the operator says otherwise.
7. **Areas** routed and benchmarked:
   exploration/codebase-mapping · hermetic implementation · plan/spec writing ·
   prototyping (incl. UI mockups) · novel-solution brainstorming ·
   documentation writing · code review.
8. **Effort granularity**: decided from benchmark data. Prior instinct: model +
   coarse effort note per area, not a full model×effort matrix.

## Benchmark plan

- **Rigorous tier** (full suite): Claude Opus, Sonnet, Haiku; Codex
  GPT-5.6-Sol, GPT-5.6-Terra, GPT-5.6-Luna, GPT-5.3-Codex-Spark.
- **Light tier** (self-assessment interview + 2–3 probes): GPT-5.5, GPT-5.4,
  GPT-5.4-Mini.
- **Tasks**: mined from real agentflow issues/PRs/fleet transcripts —
  representative tasks the operator actually delegated.
- **Repos**: agentflow, ciq-autotune, recipes. Runs in throwaway worktrees,
  never committed. Personal repos (personal-context, follow-through, etc.)
  untouched.
- **Budget cap**: ~50–70 sub-agent runs total.
- **Judging**: blind, by the coordinator (Fable), against per-area rubrics;
  real merged PRs serve as ground truth where they exist. Interviews
  (self-assessments) and published/online eval data are secondary signals —
  empirical results have final say.

## Acceptance

- Skill written to spec above.
- Routing table populated from benchmark results with a one-line rationale per
  cell and a "benchmarked on <date>, models <list>" provenance header.
- Cold `/plan-review` run on the finished skill; blocking findings fixed.

## Amendment — issue #24 (2026-08-08)

Decision 1 remains the original locked Claude-parent decision. A Codex UI parent
is now additionally supported through the `dispatch-codex.md` CLI-worker
adapter: it dispatches and resumes only `codex exec` workers with persisted
session identity, model, sandbox, and canonical working directory. Native Codex
sub-agents are not used for delegated work. Its initial admissions are limited
to bounded exploration (Luna), implementation and plan/spec writing (Terra),
prototyping (Sol), default brainstorming (Terra), documentation and routine
review (Luna); the unbenchmarked Codex-only areas are `NO_VALIDATED_ROUTE`.
Codex-only routes do not fall back to Claude and remain single validated rungs:
after one same-session retry, they stop with `NO_VALIDATED_ROUTE`.
