---
name: epic
description: Drive a batch of triaged tickets as one integration branch ending in one pull request — the coordinator merges gated sub-PRs into the integration branch, ticket by ticket, and a human merges the final PR. Use when the user invokes /epic with an ordered ticket list, or asks to ship several work-ordered tickets as a single batch/mega PR.
---

# Epic — integration-batch coordinator

Run a batch of already-triaged tickets as **one integration branch, one final
pull request**. This skill composes `/orchestrate` and `/ticket`: invoke
`orchestrate` first — the session is coordinator-only for the life of the epic,
and every routing, verification, and escalation rule there applies unchanged.
Nothing here overrides the routing table; a per-run model restriction is the
operator's instruction for that run, never part of this skill.

The session **is** the epic: it lives until the final PR merges or the operator
kills it. Either way its ledger is the durable state — a killed epic restarts by
reading the ledger (via `/handoff` when one exists), not by re-deriving the
batch from chat.

## Inputs — refuse without them

1. **Ordered ticket list.** Every ticket has a posted, countersigned work order
   (per `/ticket`: the newest comment containing a fenced `WORK ORDER` block).
   The order is the verbatim brief — never re-triage, never improvise scope. A
   ticket without an order stops the batch at its slot: report it, ask the
   operator to run `/ticket triage` or drop it from the list.
2. **Integration branch name.** Created from a **freshly fetched**
   `origin/main`, pushed immediately.
3. **Parked list** (may be empty). Parked tickets are untouchable: never read
   into scope, never "quickly fixed" because the code is nearby.

Open a ledger at `docs/scope/<epic-slug>.md` (scope's convention) before the
first dispatch: the ticket order with per-ticket status, decisions as they
settle, and the parked list.

## The loop — strictly in order

For each ticket:

1. **Rebase** the ticket's branch onto the **current integration tip**. Reuse
   an existing worktree for the ticket when one exists (`spin-worktree`
   convention); never respin over uncommitted work.
2. **`/ticket start <n>`** with the worktree on that rebased branch. Its PR
   targets the **integration branch, never main**. Delegation, review depth,
   and escalation belong to `/ticket` and `/orchestrate`; the epic coordinator
   does not re-review inside the ticket.
3. **Merge** the sub-PR into the integration branch once its review passes and
   its gates are green. The coordinator's merge authority covers the
   integration branch **only** — merging to main is always the human's.
4. **Full repo gate** on the new integration tip: every check the repo's own
   docs name as the merge bar, not just the changed ticket's tests. A red gate
   stops the loop — route the failure back to the ticket's agent before the
   next ticket starts.
5. **Re-measure, never copy.** Any figure a work order states (test counts,
   replay totals, fixture sizes) was measured against an older base. Claims in
   commits, comments, and the final PR body come from commands run on the
   current tip, reading the actual summary line.

Gated orders (one ticket's order requiring another's change on the tip) are
honored by the ordering; if a gate condition fails, stop and surface it rather
than reordering silently.

## Sub-coordinators

Default is the sequential loop above. When the batch contains a **genuinely
independent slice** — tickets sharing no files, fixtures, or ledger sections
with the rest — the epic session may hand that slice to one sub-coordinator: an
`/orchestrate` session with its own ticket order and its own ledger section,
merging into the same integration branch through the same loop. Two levels
maximum, ever: a sub-coordinator never spawns another. When in doubt about
independence, stay sequential — a false-parallel slice pays merge conflicts for
no wall-clock win.

## Finishing

When every ticket is merged and the integration tip is green: write the PR body
with `/pr-body` where available, in product terms, closing every batch ticket,
with per-ticket evidence. Open **one** PR from the integration branch to main
and stop — a human merges it. `/ticket finalize` runs per ticket only after
that merge.

## Operator contract

- Escalate only trust failures (an agent gone untrustworthy per orchestrate's
  verification rules) and design decisions the work orders leave unsettled.
  Everything else is the coordinator's.
- Report every externally visible state change — branch pushed, PR opened,
  sub-PR merged, comment posted — in the first sentence after it happens.
- Repo-specific hazards (ports, publish guards, ledger append rules) come from
  the repo's own agent docs and the work orders; this skill adds none and
  skips none.
