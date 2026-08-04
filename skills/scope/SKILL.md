---
name: scope
description: Triage front door for work that isn't ready to build. Classifies the dominant uncertainty and routes to one specialist skill. Use for 'let's scope this', '/scope', 'scope this out', 'not sure how to approach', 'grill me on this', 'stress-test this plan', or any request carrying real ambiguity about what to do next.
---

# Scope

Diagnose why work isn't buildable yet, route to exactly one specialist skill, and open
a ledger the moment routing happens. Never do the specialist's work yourself — a
correct route with no other output is a complete session.

## Routing table

Classify the **dominant** uncertainty — the one that, if resolved, makes the others
tractable — and route to exactly one of:

- **Big and foggy, many interlocking decisions that block each other** → `wayfinder`.
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

If the request already names a specialist by trigger phrase (a `grill`-style trigger
names interview mode; `stress-test this plan` names `plan-review`; a wayfinder map
names `wayfinder`), route there directly without re-diagnosing.

## Ledger — required

At the moment routing happens, open a ledger before invoking the specialist:

- **Path:** `docs/scope/<slug>.md` in the target project's repo when that path is
  writable; otherwise the session scratchpad. `<slug>` is a short kebab-case name for
  the work.
- **Sections:** `Decisions`, `Open questions`, `Spawned tasks`.
- **Decisions** get appended **at the moment each one settles** — never batched at
  session end. Each entry: the decision, a one-line why, and a disposition tag —
  `→ ADR`, `→ issue`, or `inline`.
- The ledger is the durable session state. A fresh agent resumes by reading it, not by
  re-deriving context from chat history.

## Exit protocol

The session is not done until every disposition is discharged:

- Every `→ ADR` decision has a real ADR written.
- Every `→ issue` decision has a filed GitHub issue.
- The ledger's remaining-dispositions list is empty.

Report which dispositions remain open if the session ends early; do not report the
scoping work as finished while any disposition is outstanding.
