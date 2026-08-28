---
name: scope
description: Triage front door for work that isn't ready to build. Classifies the dominant uncertainty and routes to one specialist skill. Use for 'let's scope this', '/scope', 'scope this out', 'not sure how to approach', 'grill me on this', 'stress-test this plan', or any request carrying real ambiguity about what to do next.
---

# Scope

Diagnose why work isn't buildable yet, route to exactly one specialist skill, and open
a ledger the moment routing happens. Never do the specialist's work yourself — a
correct route with no other output is a complete session. For an epic child, every
specialist instead uses untracked session scratch outside the child branch, discarded after the final order;
it creates no scope ledger or docs/scope ledger. `/epic` alone owns the parent
proposal, design, and tasks.

## Routing table

Classify the **dominant** uncertainty — the one that, if resolved, makes the others
tractable — and route to exactly one of:

- **Big and foggy, many interlocking decisions that block each other** → `epic`.
  Mechanical bulk without an unsettled decision is not an epic route; hand-split it
  into serial build tickets.
- **A concrete plan or design exists in someone's head, untested** → interview mode
  ([references/interview.md](references/interview.md), in this skill).
- **A written plan, work order, spec, or brief exists and needs stress-testing
  before anything is built** → `plan-review`.
- **Missing facts answerable from docs or sources** → `research`.
- **Only answerable by feeling it out in running code** → `prototype`.
- **The dominant uncertainty is what a user-facing surface should look like** →
  `ui-craft`, lock phase.
- **Mixed or unclear** → ask the user **one** framing question, then route. One
  question at a time, always — never a menu of questions.
- **Nothing genuinely uncertain** — the plan is grounded, the decisions are already
  settled, and any open point has an obvious default → say so in one line, name the
  defaults being assumed, and return control without asking anything. No ledger. Do
  not manufacture questions to justify the invocation; a caller may route here
  unconditionally, and "nothing to scope" is a correct, complete answer.

If the request already names a specialist by trigger phrase (a `grill`-style trigger
names interview mode; `stress-test this plan` names `plan-review`; an epic map
names `epic`), route there directly without re-diagnosing.

## Ledger — required

Outside an epic child, at the moment routing happens, open a ledger before invoking
the specialist:

- **Path:** `docs/scope/<slug>.md` in the target project's repo when that path is
  writable; otherwise the session scratchpad. `<slug>` is a short kebab-case name for
  the work.
- **Sections:** `Decisions`, `Open questions`, `Spawned tasks`.
- **Decisions** get appended **at the moment each one settles** — never batched at
  session end. Each entry: the decision, a one-line why, and a disposition tag —
  `→ ADR`, `→ issue`, or `inline`.
- The ledger is the durable session state. A fresh agent resumes by reading it, not by
  re-deriving context from chat history.

For an epic child, the remaining ledger, risk-contract, evidence, and exit rules are
applied only through the stamped work order and parent epic authority; session scratch
is never made durable.

## Risk contract

For interview-mode work, and for any other bounded plan being declared ready to
build, settle a risk contract before admission. An epic map whose work is not yet
bounded does not need one.

Keep one `### Risk contract` block under the ledger's `Decisions` section:

- **Must prevent:** harmful outcomes the work may never produce.
- **Must recover:** concrete failures that require automatic recovery.
- **Accepted failure:** a concrete failure and the exact consequence the user accepts,
  such as a clear stop with manual recovery, skipped best-effort work, or degraded
  non-authoritative output.
- **Unsupported:** inputs or operating conditions the work does not promise to handle.
- **Evidence owed:** public-interface behaviors and named invariants that require tests
  or another explicit check.

Give the block one-line `Why:` and `Disposition:` fields rather than tagging every
line separately. Default `Must prevent` to secret exposure, irreversible loss of
authoritative data, and silent incorrect success; changing one of those defaults
requires an explicit user decision. Default rare, recoverable failures to an
`Accepted failure` with a clear stop and manual recovery, not automatic recovery.

Price the contract from concrete consequences, exposure, and recoverability. Audience
size is evidence, not an assurance tier: one person's financial tool can be
high-stakes, while a public toy can be disposable. Do not use a target test count.
Evidence is owed only by supported behavior, a must-prevent outcome, an enforced
invariant, or an observed regression.

At admission, copy the risk contract unchanged into the authoritative issue, plan, or
brief that the implementation and reviews will use. The ledger remains the session
record; the admitted artifact becomes the downstream authority. Do not declare bounded
work ready while the contract is missing or still only in the ledger.

## Exit protocol

The session is not done until every disposition is discharged:

- Every `→ ADR` decision has a real ADR written.
- Every `→ issue` decision has a filed GitHub issue.
- The ledger's remaining-dispositions list is empty.

Report which dispositions remain open if the session ends early; do not report the
scoping work as finished while any disposition is outstanding.
