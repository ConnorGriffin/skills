# Design

## ADR 276 — Slicing calibration is per-repository

### Context

The slicing rubric decides whether a work order is flat or chunked, and how big
each chunk is. It carries two different kinds of content. One is mechanism: the
trait table, the 180k target, the 120k floor, chunk shape, orchestrator tier.
The other is measurement: an anchor table of real tickets with their measured
peaks, which grew a row at a time as tickets finished.

Only the mechanism is portable. The anchors were measured on one operator's
sessions, on one machine, and increasingly against named repositories —
`259 (skills)`, `253 (harmonic)`. A Harmonic ticket's cost is evidence about
Harmonic's grounding cost, not about what any installation's chunks should weigh.

Ticket #197 already built the right home for those numbers: a per-repository
reviewer-memory store that `finalize` appends a slicing record to and `triage`
reads, with "cross-repo learning: unsupported; per-repo default" as its recorded
risk contract. Both channels then ran at once. `finalize` appended the record
*and*, on a misprediction verdict, drafted a rubric diff for the operator to land
as a skills-repo pull request.

### Decision

Calibration accrues per repository. Three consequences:

1. **The rubric is frozen to mechanism.** `references/slicing.md` keeps the trait
   table, the sizing rules, chunk shape, and orchestrator tier. It carries no
   measured anchors of its own, and stops growing a row per finished ticket.

2. **Lessons accrue in reviewer memory.** The per-repo store is the anchor
   source. `triage` reads it for the shapes and peaks its traits are calibrated
   against here; `finalize` keeps appending to it exactly as it does today.

3. **The misprediction path is report-only.** On `under-sliced`,
   `still-degraded`, or `over-sliced`, `finalize` reports which call was wrong and
   by how much, and stops. It drafts nothing, offers no pull request, and asks the
   operator nothing.

### The threshold escape hatch

A per-repo record cannot move a constant. The 180k target and the 120k floor are
paired with constants in `skills/drivers/ticket/scripts/ticket.py`, so a genuine
move has to change the rubric prose and those constants together. That stays
operator-initiated skills-repo work. The rubric says so; `finalize` never
proposes it.

### Consequences

* A fresh repository starts with the bare thresholds and no anchors, and gains
  them over a handful of finished tickets. That is the intended trade: no anchors
  beats another repository's anchors.
* Anchor rows with a resolvable repository move to that repository's store. Rows
  with no resolvable identity (the lettered rows, `53`, `10`, unlabeled `90`, and
  `62 (external)`) are dropped rather than assigned to a guess; the thresholds
  they informed already carry their lesson.
* Coordinator-cost anchors keep their caveat when migrated: a coordinator peak
  tunes no threshold in either direction.
* The operator loses the automatic rubric-diff offer. That is the point of the
  change, not a cost of it.

### Alternatives considered

* **Keep both channels.** Rejected: it is what produced repository-specific rows
  in a shared rubric, and it puts a prompt and a pull request on every
  misprediction.
* **Have `finalize` edit the rubric itself.** Rejected for the reason the original
  rule gave, which still holds: a skill that amends its own rubric from one
  repository's measurement is exactly the coupling this decision removes.
* **Implement reviewer-memory's `distill` and have triage read raw records
  directly.** Out of scope. `distill` is documented in the reviewer-memory skill
  but absent from `memory.py`; triage reads the curated digest that already
  exists. Worth its own issue.
