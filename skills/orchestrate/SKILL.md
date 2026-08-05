---
name: orchestrate
description: Flip the session into coordinator mode — the parent agent plans, scopes, reviews, and ships, but delegates all real work (exploration, implementation, review, fixes) to sub-agents routed by an empirically benchmarked model capability table. Use when the user invokes /orchestrate or asks the parent to act as an orchestrator/coordinator instead of a developer.
---

# Orchestrate — coordinator mode

Invoking this skill flips the **whole session** into coordinator mode until the
operator says otherwise. **Claude Code is the only supported parent** — if you
are not Claude Code (e.g. this was invoked from the Codex harness), stop and
tell the operator this skill has no Codex-parent mode; the dispatch mechanics
below are Claude Code machinery. Codex models are reached via `codex exec`
(continue an existing Codex session with `codex exec resume`).

## Codex headroom gate — run at invocation

Before any routing, check whether the Codex side has budget left:

1. Probe fresh: run a trivial one-word `codex exec` (cheapest Codex model,
   `--sandbox read-only`), then parse the `rate_limits` event from the newest
   rollout under `~/.codex/sessions/**/*.jsonl`. Headroom =
   `100 − primary.used_percent`. Never trust a snapshot from an old session —
   it may be days stale.
2. If headroom ≤ 5%, or the probe itself fails with a rate-limit error, the
   session runs **Claude-only**: drop every Codex route (Sol, Terra, Luna,
   Spark) from routing and never reference Codex models in delegations for the
   rest of the session. Tell the operator once, with the measured headroom and
   `resets_at`.
3. Same rule mid-session: if any later Codex delegation fails with a rate-limit
   error, flip to Claude-only from that point on.

Claude-only routing uses each row's Claude rungs. Two rows have no Claude rung:
plan/spec writing routes to **Opus with a mandatory coordinator fail-safe
review** of the spec (the table's polarity-error warning is the reason the
review is not optional); prototyping routes straight to **Opus**.

## The coordinator ruling (behavioral core)

- The main session acts as coordinator, not developer: it plans, scopes, reviews,
  and ships, but does not write the implementation itself.
- Real work (exploration, implementation, review passes, fixes) is delegated to
  sub-agents running a cheaper model tier — routed per
  `references/routing-table.md`.
- The coordinator writes detailed, self-contained specs for each sub-agent (files
  to read, exact requirements, test obligations, commit format) and verifies their
  output rather than trusting it — including independent review passes on
  correctness-sensitive changes, with findings routed back to the implementing
  agent to fix.
- Continue an existing sub-agent (SendMessage for Claude; `codex exec resume` for
  Codex) for follow-ups in its area instead of spawning a fresh one, so its
  context carries over.
- The coordinator keeps for itself: small mechanical glue (git/gh plumbing,
  toggles, log checks, daemon restarts), verification probes, and all
  communication/decisions with the operator.
- Worktree creation is not raw git plumbing: when preparing a worktree for a
  sub-agent (or any task work), invoke the `spin-worktree` skill so worktrees
  land under its `~/worktrees/<repository>/<task>` convention, not ad-hoc
  paths next to the checkout.

## Routing

1. Classify the task into an area: exploration/codebase-mapping · hermetic
   implementation · plan/spec writing · prototyping (incl. UI mockups) ·
   novel-solution brainstorming · documentation writing · code review.
2. Read `references/routing-table.md` and pick the **cheapest model that clears
   the bar** for that area. Honor the table's bans (e.g. Luna for UI mockups,
   Haiku for unverified exploration citations) and the headroom gate above —
   in Claude-only mode, Codex rungs are skipped as if absent from the table.
3. **Never delegate to Fable** — it is the coordinator tier only.
4. Mechanics: Claude models via the Agent tool with a `model` override — a
   read-only agent type (e.g. Explore) for read-tasks, `isolation: "worktree"`
   for write-tasks, so the harness enforces what the prompt asks. Codex models
   via `codex exec -m <model> -c model_reasoning_effort=medium --sandbox
   read-only|workspace-write --skip-git-repo-check -C <dir>` — `read-only` for
   read-tasks; `workspace-write` only into an isolated worktree, never the
   coordinator's own checkout. Effort stays medium; escalation changes the
   model tier, not the effort dial. Belt-and-braces: read-task prompts still
   carry an explicit "context is read-only — never modify, patch, or stash"
   line (a benchmark run was invalidated by an agent leaving a patch applied
   to a shared worktree — treat this as load-bearing).

## Verification and escalation

Every delegated result is verified by the coordinator before it ships: run the
tests yourself, spot-check citations, diff against the spec. On failed
verification:

1. **Retry once** in the *same* sub-agent session, carrying your specific
   findings ("test missing for the flag path") — its loaded context makes the
   retry cheap.
2. **Second failure → escalate one tier** (per the table's escalation column):
   fresh agent, original spec, plus a note on what the cheaper model botched.
3. If the failing route is already the top of its ladder (the table's
   escalation column names no higher tier), stop: surface both failed attempts
   to the operator instead of improvising a further escalation.
4. Never unbounded retries; never tier-skip straight to the top; never silently
   absorb a deviation — surface it to the operator.

Watch-items the benchmark confirmed per model family: Claude models may report
success from reasoning rather than a green run (demand command output) and can
embed one confident wrong decision in an otherwise excellent spec; Codex models
are terser and may under-test; small/fast tiers fabricate citations under
exploration pressure.

## Composing with /ui-craft

When coordinator mode runs a ui-craft lifecycle, the delegation split is:

- **Mockup drafts (lock phase)**: Sol; Spark when a design system or existing
  lock is there to reuse (and for fast iteration rounds); Opus escalation.
  **Fan out one sub-agent per concept direction, in parallel** — each agent
  gets the brief plus exactly one named direction and never sees the others'
  output. Never ask a single agent for N variants: one context produces N
  shades of one idea, and the divergence the lock phase exists to compare is
  lost. Iteration rounds on an already-chosen direction may stay single-agent.
- **Visual judgment** — critiquing renders, deciding what locks: stays with the
  coordinator (verification + operator-facing decisions). Persona-critique
  reading passes may go to Terra/Opus, but the lock call is surfaced to the
  operator.
- **Build-to-lock**: the hermetic-implementation route (Terra → Sonnet → Opus) —
  building to a lock manifest is contract-following, not taste.
- **Fidelity evidence**: the build agent produces the mock-vs-build screenshots;
  the coordinator walks the ledger as verification.

Untested seams (benchmark was single-shot mockup generation only): frontend
build-to-lock with rendered gate assertions, and multi-round mockup iteration.
Treat those routes as provisional until benchmarked.

## Maintenance

The table is provenance-stamped. When a new model ships, replay the benchmark
per `references/benchmark/README.md` (~1 area-task per area; note the review and
prototyping fixtures regenerate and need an incumbent anchor run) and update the
table in the same commit.
