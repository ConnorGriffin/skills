# Remove the worker-egress consent declaration

## Why

Codex worker sessions read the bounded worker-egress consent framing in the
ticket and orchestrate skills and stopped mid-workflow to re-ask permission for
a review the operator had already ordered. Rewording the declaration did not
stop the balking, because the sessions were reacting to the presence of a
consent-shaped statement, not to its exact phrasing.

## What changes

- Delete the worker-egress consent declaration from `skills/drivers/ticket/`
  and `skills/drivers/orchestrate/`, rather than rewording it: no statement
  that a literal invocation grants bounded transfer to a named model service,
  no "asks once" framing for automatic activation, and no exclusions sentence
  for credentials, secrets, patient data, `.env`, or real database contents.
- Keep the coordinator-owned mandatory-review handoff that consent framing was
  wrapped around: the coordinator's delegation prompt identifies the handoff,
  the worker returns its review-ready result through the coordinator-recorded
  durable result locator, the coordinator dispatches every mandatory reviewer
  and resumes that same worker, and unavailable review evidence blocks
  advancing as reviewed.
- Retire `### Requirement: Bounded worker-egress consent` in
  `ticket-workflow` and `### Requirement: Orchestration authorization and
  isolation` in `planning-and-review`, replacing each with a requirement
  scoped to only the surviving contract: adapter isolation plus the
  coordinator-owned review handoff (`planning-and-review` also keeps its
  adapter-isolation sentence).
- Add no replacement guard against the removed language returning: this is a
  deliberate reversal of ADR 194, recorded as ADR 275, not a rewording.

## Impact

- Affected skills: `skills/drivers/ticket/`, `skills/drivers/orchestrate/`.
- Affected specs: `ticket-workflow`, `planning-and-review`.
- `docs/adr/adr-194-literal-invocation-egress-consent.md` stays byte-identical
  as frozen legacy history; the reversal is recorded in this change's
  `design.md` as `## ADR 275`.
- Ticket 275 stays open after merge as a recurrence tracker.
