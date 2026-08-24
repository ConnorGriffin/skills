# Scope ledger — ticket 78: claim telemetry vs Codex workspace sandbox

## Decisions

- Q1 → escalated run: docs and the denial message name one remedy — rerun the
  claim command outside the sandbox. No `TICKET_CLAIMS` redirect documented, no
  standing config. Why: user rejects standing config as over-engineering; runs
  interactively and guides the agent. Disposition: inline (lands in the work
  order).
- Q2 → yes: `record`'s identical denial (`TICKET_TELEMETRY` path) gets the same
  one-line escalated-rerun remedy. Why: same defect class, marginal cost one
  sentence. Disposition: inline (lands in the work order).

### Risk contract

- Must prevent: secret exposure; silent incorrect success (a denial that looks
  like a recorded claim); turning the claim into a gate that blocks a verb.
- Must recover: none — claiming is telemetry, not workflow state.
- Accepted failure: a session that neither escalates nor is guided loses its
  claim; finalize reports it under existing `no-data`/partial semantics.
- Unsupported: sandboxes where escalation is unavailable and the operator is
  absent.
- Evidence owed: denied claim write exits 0, prints one line naming the denial
  and the escalated rerun; existing claim/record behavior unchanged (tests).
- Why: telemetry-only surface; worst case is an unmeasured session.
- Disposition: inline (copied into the work order).

## Open questions

(none — Q1, Q2 settled)

## Review rounds

- Round 1 (cold panel): 3 blocking + 2 notes, all tagged `authoring`
  (verification command missing test_check_dco; no-Markdown claim contradicted
  by this ledger; stdout fate unspecified; finalize.md anchor missing; wrong
  file named in doc sentence). All reproduced, all fixed.
- Round 2 (same reviewer, delta check): 1 blocking, tagged `injected` by the
  round-1 stdout fix (already_claimed would report true on a denied write).
  Fixed by requiring already_claimed: false on denial.

## Spawned tasks

(none)
