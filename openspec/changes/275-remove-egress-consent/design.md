# Design

## ADR 275 — Reverse literal-invocation worker-egress consent

**Context.** ADR 194 decided that literal invocation of `/ticket triage`,
`/ticket start`, `/ticket revise`, or `/orchestrate` requested bounded
repository egress on the worker's behalf: the task prompt or work order plus
only the repository code and documentation a delegated task needed, sent to
the model service admitted for the parent, with credentials, secrets, patient
data, `.env`, and real database contents excluded. Automatic activation
outside an invoked parent workflow was declared to ask once on the same
terms, and `/ticket finalize` was declared to grant no worker-egress consent.

Codex worker sessions reading that declaration stopped mid-workflow to
re-ask permission for a review the operator had already ordered by invoking
the workflow. The stall recurred after the wording was tightened, which
showed the sessions were reacting to the presence of a consent-shaped
declaration in the surface they read, not to a specific phrasing of it:
rewording did not stop it.

**Decision.** Delete the consent declaration outright rather than reword it
again. The pack now carries no worker-egress consent declaration anywhere in
`skills/drivers/ticket/` or `skills/drivers/orchestrate/`. No exclusions
sentence for credentials, secrets, patient data, `.env`, or real database
contents remains in these surfaces. No guard, lint, or test defends against
the removed language reappearing — a future reintroduction is a fresh
decision, not a regression this change tries to prevent. No runtime
enforcement (parser, provenance artifact, approval state machine, or byte
filter) replaces the prose declaration; ADR 194 already noted the
declaration itself added none of those.

The coordinator-owned mandatory-review handoff that the declaration had been
wrapped around is unaffected: a coordinator's delegation prompt identifies
the mandatory-review handoff, the worker returns or writes its review-ready
result through the coordinator-recorded durable result locator, the
coordinator collects that result, dispatches every mandatory reviewer, and
resumes that same worker with verified findings or a verified clean verdict;
unavailable review evidence blocks advancing as reviewed; the worker never
launches a nested reviewer. Adapter isolation under ADR 149 — every dispatch
continues to use pack-owned isolated adapters, and direct adapter dispatch
from inside a sandboxed worker remains unsupported — is likewise untouched
by this reversal.

**Consequences.** A model dispatch no longer carries any stated egress
consent; the workflows rely on the operator's invocation of the workflow
itself as authorization for the dispatches that invocation orders, with no
separate declaration for a worker to read and react to.
`docs/adr/adr-194-literal-invocation-egress-consent.md` remains
byte-identical as frozen legacy history; this record is the reversal, not an
edit to that file.
