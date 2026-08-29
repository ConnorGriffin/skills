# Ticket workflow — deltas

## MODIFIED Requirements

### Requirement: Role-aware telemetry and review depth

Each participating session MUST be claimable with both its responsibility
(`coordinator`, `worker`, or `reviewer`) and the ticket lifecycle verb that
produced the claim. Finalization MUST record responsibility-tagged and
verb-tagged costs separately. Worker peaks alone MUST calibrate chunk sizing;
measurable non-reviewer `start` claims alone MUST calibrate a flat order;
triage, revise, finalize, and reviewer peaks MUST remain independent overhead.
Claims without a lifecycle verb MUST remain readable as legacy data and MUST NOT
be guessed into a verb. Review depth MUST be stamped from change scope and
sensitivity rather than inferred from slicing telemetry.

#### Scenario: A flat ticket has expensive lifecycle overhead

- **WHEN** triage, revise, or finalize peaks above the slicing band while the
  measurable non-reviewer `start` claim remains below it
- **THEN** the flat verdict is based on the `start` peak and reports lifecycle
  overhead separately without proposing a slicing-rubric amendment

#### Scenario: A flat ticket has no attributable execution

- **WHEN** no measurable non-reviewer `start` claim exists, including when every
  readable claim predates lifecycle-verb attribution
- **THEN** finalization returns `unmeasurable` and makes no slicing judgment

#### Scenario: A chunked ticket has an expensive review

- **WHEN** finalization records a reviewer peak above the slicing band while the
  implementation workers remain within it
- **THEN** the reviewer cost is reported separately and does not make the chunks
  appear under-sliced or change their stamped review depth

