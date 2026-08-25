---
name: orchestrate
description: Flip the session into coordinator mode — the parent agent plans, scopes, reviews, and ships, but delegates all real work (exploration, implementation, review, fixes) to sub-agents routed by an empirically benchmarked model capability table. Use when the user invokes /orchestrate or asks the parent to act as an orchestrator/coordinator instead of a developer.
---

# Orchestrate — coordinator mode

Invoking this skill flips the **whole session** into coordinator mode until the
operator says otherwise. Detect the parent before dispatching:

- **Claude Code parent:** use the Claude and Codex mechanics below — both
  dispatch through their CLI-worker adapters (`claude-worker.py` /
  `codex-worker.py`), never through the Agent tool, the Workflow tool, or a
  background agent.
- **Codex UI parent:** read `references/dispatch-codex.md` before routing. In
  this v0, every delegation uses its CLI-worker adapter; do not use native
  `spawn_agent` for implementation or review. Whether a Codex UI parent also
  dispatches Claude workers through `claude-worker.py` is explicitly deferred
  — `references/dispatch-codex.md`'s admission table is Codex-only until that
  is decided.

## Codex headroom gate — run at invocation

Before any routing, check whether the Codex side has budget left:

0. **Claude parent, presence check first:** run `command -v codex` before
   spending anything on a probe. If the Codex CLI is absent from PATH, skip
   step 1 entirely and go straight to the same **Claude-only** branch as
   headroom ≤ 5% / unknown below; tell the operator once. A Codex UI parent
   cannot land on this branch — the CLI exists there by construction — so the
   check only applies to a Claude parent. Also run `command -v claude` — a
   Claude-only branch dispatches through `claude-worker.py`, which needs the
   `claude` binary. If **neither** `codex` nor `claude` is present on PATH,
   the coordinator cannot dispatch at all: report the blocker to the operator
   and stop — there is no third route.
1. Probe fresh with a trivial one-word worker run (Luna, `gpt-5.6-luna`,
   `read-only`) — Luna is the probe model because it is the cheapest route the
   table already uses, so it is always available; do not pick a cheaper-looking
   mini model, which is not enabled on the operator's plan and fails the probe. The Codex adapter binds headroom to that worker's
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
- Continue an existing worker (`claude-worker.py resume` for Claude;
  `codex-worker.py resume` for Codex) for follow-ups in its area instead of
  spawning a fresh one, so its context carries over.
- The coordinator keeps for itself: small mechanical glue (git/gh plumbing,
  toggles, log checks, daemon restarts), verification probes, and all
  communication/decisions with the operator.
- The coordinator that launched an interrupted worker owns its exact recovery:
  run the adapter's scoped `stop --state ... --cwd ...`, then scoped `verify`
  before a successor receives the worktree. Successors never discover or clean
  unknown processes; names, descendants, sessions, and global test/provider
  searches are not ownership.
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
   route: name the model in the coordinator's narration line for the
   `claude-worker.py` / `codex-worker.py` run (`<Model>: <task description>`,
   e.g. `Sonnet 5: standards review of phase 1 diff`) — the adapters carry no
   `description` field of their own, so the narration line is what carries the
   model label, not the dispatch command. Applies to escalation retries too
   (the new tier's name).
5. Mechanics: every delegation — Claude or Codex — dispatches through its CLI
   worker adapter (`skills/drivers/orchestrate/scripts/claude-worker.py` or
   `codex-worker.py`), never through the Agent tool, the Workflow tool, or a
   background agent. See `references/dispatch-claude.md` for the Claude
   adapter's command surface, sandbox shapes, prompt-on-stdin fact, and
   liveness contract; `references/dispatch-codex.md` for Codex's. `read-only`
   is for read-tasks; `workspace-write` only targets an isolated worktree
   (`--cwd`, with `--control-checkout` set to the coordinator's checkout),
   never the coordinator's checkout directly — both adapters refuse a
   `workspace-write` `--cwd` inside `--control-checkout`. Every delegation
   carries `--effort`, defaulting to medium (see Effort notes below);
   escalation changes the model tier, not the effort dial. Belt-and-braces:
   read-task prompts still carry an explicit "context is read-only — never
   modify, patch, or stash" line (a benchmark run was invalidated by an agent
   leaving a patch applied to a shared worktree — treat this as load-bearing).

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

## Evidence v2

For a durable, revisioned task authority, use [the shared envelope
reference](../../../docs/evidence/envelope-v2.md) to emit a delegation that `delegates`
an admissible claim, criterion, decision, or delegation; a bounded slice that
`derives_from` that delegation; and a settlement that `settles` an admissible
verification. A decline or collapse may separately `derives_from` the slice. The
authority revision and normalized lineage are sufficient. Do not retain worker final
messages, prompts, transcripts, candidates, proposals, or policy state. This
preserves the existing routing and bounded retry protocol.

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
- **Shipped-surface revision**: the hermetic-implementation route. The revision
  agent uses the repo-declared safe fixture, replays the frozen behavior ledger
  against the base before changing it, and iterates the shipped app in place; it
  never creates a replacement mock or lock manifest.
- **Revision evidence**: the revision agent produces same-fixture base-versus-
  revision before/after renders and raw replay output. The coordinator verifies the
  behavior-ledger amendment and replay result; there is no fidelity ledger.

Untested seams (benchmark was single-shot mockup generation only): frontend
build-to-lock with rendered gate assertions, and multi-round mockup iteration.
Treat those routes as provisional until benchmarked.

## Pack-wide reach

Per ADR 149 (`docs/adr/adr-149-pack-owned-model-dispatch.md`): all model
dispatch defined by this pack goes through this pack's own adapters
(`claude-worker.py` / `codex-worker.py`), not the built-in Agent tool, the
Workflow tool, or background agents. That ruling covers every skill that
dispatches a model, not only `orchestrate`. The other skills convert one at a
time behind their own issues and keep their current dispatch mechanism until
converted:

- **code-review** (issue #151)
- **plan-review** (issue #152)
- **persona-review** (issue #153)
- **ticket**'s chunk agents (issue #154)
- **epic** (issue #155)
- **research** (issue #156) — `skills/tools/research/SKILL.md:8` spawns a
  background agent today
- **codebase-design** (issue #157) — `references/DESIGN-IT-TWICE.md:37`
  spawns sub-agents via the Agent tool today

Do not convert any of the above in this ticket; the ban binds each one only
once its own issue lands.

## Maintenance

The table is provenance-stamped. When a new model ships, replay the benchmark
per `references/benchmark/README.md` (~1 area-task per area; note the review and
prototyping fixtures regenerate and need an incumbent anchor run) and update the
table in the same commit.
