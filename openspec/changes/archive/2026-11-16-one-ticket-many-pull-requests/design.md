# Design

## A ticket stays whole however many pull requests land it

**Context.** Triage's slicing rule filed child issues whenever two slicing traits
fired, and `multiple targets` plus `multiple deliverables` fire on almost any
cross-repo change. UI Craft separately required a build ticket after every lock.
The operator rejected the split each time, and agents worked around it by posting
one lock per pull request on the original ticket.

**Decision.** The workaround becomes the rule. Work that needs more than one pull
request gets a pieces checklist on its ticket and a sequence of locks, one per
piece, each bounded by its own `Expected diff`. The slicing traits still decide
when work needs sequencing and are still recorded for finalize's cost record.
Child issues are filed only on the operator's request.

**Consequences.** `start` and `revise` are unchanged: each still builds one lock to
one pull request. Finalize runs once per piece and closes the ticket only after the
last box is checked. The tracker shows one ticket per unit of work, with its pull
requests listed on it.
