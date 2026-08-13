---
name: orchestrate
description: Flip the session into coordinator mode — the parent agent plans, scopes, reviews, and ships, but delegates all real work (exploration, implementation, review, fixes) to sub-agents routed by an empirically benchmarked model capability table. Use when the user invokes /orchestrate or asks the parent to act as an orchestrator/coordinator instead of a developer.
---

# Orchestrate — coordinator mode

Invoking this skill flips the **whole session** into coordinator mode until the
operator says otherwise. Detect the parent before dispatching:

- **Claude Code parent:** use the Claude and Codex mechanics below.
- **Codex UI parent:** read `references/dispatch-codex.md` before routing. In
  this v0, every delegation uses its CLI-worker adapter; do not use native
  `spawn_agent` for implementation or review.

## Codex headroom gate — run at invocation

Before any routing, check whether the Codex side has budget left:

1. Probe fresh with a trivial one-word worker run (cheapest available Codex
   model, `read-only`). The Codex adapter binds headroom to that worker's
   captured session ID: it finds the rollout whose `session_meta.payload.session_id`
   matches and reads its latest `event_msg` token-count rate limits. Headroom =
   `100 − primary.used_percent`; absent rate limits mean **unknown**, not
   sufficient. Never inspect merely the newest rollout — it may be unrelated.
2. If headroom is ≤ 5%, **unknown**, or the probe itself fails with a rate-limit
   error, branch by parent:
   - **Claude parent:** run **Claude-only**: drop every Codex route (Sol,
     Terra, Luna, Spark) from routing and never reference Codex models in
     delegations for the rest of the session.
   - **Codex UI parent:** it has a Codex-only constraint, so stop dispatching.
     Report the measured headroom, `resets_at` when present, or the rate-limit
     / unknown-headroom blocker. Do not switch to Claude workers.
3. Apply the same parent branch mid-session if a later Codex delegation is
   rate-limited. Tell the operator once when the branch changes.

For a Claude parent, Claude-only routing uses each row's Claude rungs. Two rows
have no Claude rung: plan/spec writing routes to **Opus with a mandatory
coordinator fail-safe review** of the spec (the table's polarity-error warning
is the reason the review is not optional); prototyping routes straight to
**Opus**.

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
- **Branch-currency preflight, before the first dispatch of a session.** Run
  `git fetch` and check `git rev-list --count HEAD..origin/main`. If it is
  non-zero, either move the checkout or name the ref explicitly in every subagent
  brief ("work against `origin/main`, not the current branch, via a throwaway
  worktree or `git show` — never mutate the operator's checkout"). A subagent
  cannot see what its parent's tree lacks, and it reports absence as fact with
  honest file:line citations: on a checkout three commits behind, two independent
  explorers concluded a shipped surface "does not exist in the app", and every
  downstream conclusion built on that map was wrong. The same trap catches the
  coordinator's own claims about tooling — a negative claim ("that label or flag
  doesn't exist") needs a fetched checkout, a live `gh` query, and a grep
  unnarrowed by file extension before it is asserted rather than hedged.

## Routing

1. Classify the task into an area: exploration/codebase-mapping · hermetic
   implementation · plan/spec writing · prototyping (incl. UI mockups) ·
   novel-solution brainstorming · documentation writing · code review.
2. Read `references/routing-table.md` and pick the **cheapest model that clears
   the bar** for that area. Honor the table's bans (e.g. Luna for UI mockups,
   Haiku for unverified exploration citations) and the headroom gate above —
   Claude-only mode skips Codex rungs as if absent from the table; Codex UI
   mode follows only its adapter's admitted routes.
3. **Never delegate to Fable** — it is the coordinator tier only.
4. Every delegation is labeled with its model tier so the operator can see the
   route: Agent-tool dispatches prefix the `description` with the model name
   (`<Model>: <task description>`, e.g. `Sonnet 5: standards review of phase 1
   diff`); Codex `codex exec` runs name the model in the coordinator's
   narration line. Applies to escalation retries too (the new tier's name).
5. Mechanics: Claude models via the Agent tool with a `model` override — a
   read-only agent type (e.g. Explore) for read-tasks, `isolation: "worktree"`
   for write-tasks, so the harness enforces what the prompt asks. Codex models
   use the parent-specific dispatch adapter. `read-only` is for read-tasks;
   `workspace-write` only targets an isolated worktree, never the coordinator's
   checkout. Effort stays medium; escalation changes the model tier, not the
   effort dial. Belt-and-braces: read-task prompts still carry an explicit
   "context is read-only — never modify, patch, or stash" line (a benchmark run
   was invalidated by an agent leaving a patch applied to a shared worktree —
   treat this as load-bearing).

## Verification and escalation

Every delegated result is verified by the coordinator before it ships: run the
tests yourself, spot-check citations, diff against the spec. On failed
verification:

1. **Retry once** in the *same* sub-agent session, carrying your specific
   findings ("test missing for the flag path") — its loaded context makes the
   retry cheap.
2. **Claude parent:** second failure escalates one tier (per the table's
   escalation column) in a fresh agent with the original spec and a note on
   what the cheaper model botched. At the top of the ladder, stop and surface
   both failed attempts.
3. **Codex UI parent v0:** every admitted route is one validated rung. After
   the same-session retry fails, stop with **NO_VALIDATED_ROUTE** and surface
   both attempts. Never escalate Terra, Luna, or Sol to Sonnet or Opus.
4. Never unbounded retries, tier-skips, or silent deviations.

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
