# Human-operated epics

## Why

The epic coordinator can currently dispatch ticket workers, run research workers,
and coordinate execution waves. In practice that nested an epic coordinator over
ticket coordination, opened an unrequested planning-only pull request during
triage, and split a small set of overlapping documentation changes into eight
children and two planning pull requests.

## What changes

- Keep the epic coordinator at planning altitude: it maintains the OpenSpec change,
  records decisions, files bounded child issues, and writes a draft order into each
  child issue, but never dispatches workers, runs a ticket, or opens a pull request.
- The operator invokes ticket triage to ground, independently review, and post that
  draft as the only executable work-order lock. A required parent-plan amendment
  stays on the child branch and ships with its implementation.
- Require the operator to invoke each child ticket's execution explicitly.
- Default to no more than three child tickets. Four or more children require a
  written justification in the epic change's `design.md` explaining why fewer,
  larger independently shippable builds do not fit.
- Ban pull requests that contain only epic planning artifacts. Planning records
  travel with the implementation pull request that realizes them.

## Risk contract

- **Must prevent:** an epic coordinator dispatching or terminating worker sessions,
  executing child tickets, posting an executable work-order lock, opening pull
  requests, silently creating four or more child tickets without a recorded
  justification, or routing planning artifacts into a planning-only pull request.
- **Must recover:** none; the workflow stops for the operator before execution or
  pull-request creation.
- **Accepted failure:** an attended epic may pause while it waits for the operator
  to run a child ticket or merge an implementation pull request.
- **Unsupported:** automatic epic execution, background waves, and planning-only
  pull requests. Mandatory independent review inside an explicitly invoked ticket
  remains governed by the ticket workflow and is not epic dispatch.
- **Evidence owed:** contract tests prove the epic and ticket skills contain the
  human-dispatch, draft-to-lock handoff, parent-plan carrier, slicing-cap, and
  planning-PR rules and contain no epic-owned adapter, delegated execution, wave,
  or worker-lifecycle path; public docs and agent metadata are covered too; the
  repository's structural and unit gates pass.
