# Design

## ADR 235 — Unchanged wait state is silence, not a status update

The global profile owns the general communication rule so it reaches orchestrate
and every other wait loop. Ticket coordinator mode repeats only the
dispatch-specific application needed by an executor who reads that reference in
isolation. Both distinguish state transitions and predeclared operator-relevant
external-state or decision/action milestones from unchanged observations; elapsed
time alone never promotes an unchanged poll into news or a milestone. For wait
loops this rule takes precedence over the profile's general instruction to say
once after three no-news batches; that fallback remains available outside waits.

The contract remains prose plus normalized string pins. It does not add a poll
parser, a state machine, a timer, or runtime enforcement. Existing instructions to
collect child results from durable locators and to report coordinator-authored
external state changes remain authoritative and unchanged.
