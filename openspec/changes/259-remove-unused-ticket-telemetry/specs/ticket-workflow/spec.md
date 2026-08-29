## MODIFIED Requirements

### Requirement: Role-aware measurement and review depth

Each participating session MUST be claimable with both its responsibility
(`coordinator`, `worker`, or `reviewer`) and the ticket lifecycle verb that
produced the claim. Finalization MUST compute responsibility-tagged and
verb-tagged costs separately, print the resulting record as JSON, and append that
same record to the target repository's reviewer-memory store. It MUST NOT create
or append a second ticket-wide telemetry store. Worker peaks alone MUST calibrate
chunk sizing; measurable non-reviewer `start` claims alone MUST calibrate a flat
order; triage, revise, finalize, and reviewer peaks MUST remain independent
overhead. Claims without a lifecycle verb MUST remain readable as legacy data and
MUST NOT be guessed into a verb. A session MUST NOT be reused under a different
lifecycle verb; same-verb resumes remain valid, while a later verb requires a
fresh session. Review depth MUST be stamped from change scope and sensitivity
rather than inferred from recorded slicing outcomes.

#### Scenario: A measurable ticket is finalized

- **WHEN** finalization computes a slicing record from attributable claims
- **THEN** `record` prints the complete JSON record and finalization appends those
  bytes to reviewer memory without creating a parallel ticket telemetry file

#### Scenario: A flat ticket has expensive lifecycle overhead

- **WHEN** triage, revise, or finalize peaks above the slicing band while the
  measurable non-reviewer `start` claim remains below it
- **THEN** the flat verdict is based on the `start` peak and reports lifecycle
  overhead separately without proposing a slicing-rubric amendment

#### Scenario: A claimed flat ticket has no attributable execution

- **WHEN** at least one attributable claim exists but no measurable non-reviewer
  `start` claim exists, including when every readable claim predates
  lifecycle-verb attribution
- **THEN** finalization returns `unmeasurable` and makes no slicing judgment

#### Scenario: A flat ticket has no attributable claims

- **WHEN** no attributable in-repository claim exists
- **THEN** finalization preserves the existing `no-data` outcome

#### Scenario: A later lifecycle verb follows execution

- **WHEN** revise or finalize follows the session that executed `start`
- **THEN** the later verb runs in a fresh session so its context cannot inflate the
  start-attributed execution peak

#### Scenario: A session is re-claimed under another verb

- **WHEN** `claim` receives a ticket/session pair already persisted under a
  different lifecycle verb
- **THEN** it preserves and prints the persisted claim, reports one visible
  non-blocking conflict naming both verbs, and does not claim that the submitted
  verb was stored

#### Scenario: A chunked ticket has an expensive review

- **WHEN** finalization records a reviewer peak above the slicing band while the
  implementation workers remain within it
- **THEN** the reviewer cost is reported separately and does not make the chunks
  appear under-sliced or change their stamped review depth

### Requirement: Slicing amendment verdicts

Finalization MUST draft, but MUST NOT apply, a concrete slicing-rubric amendment
for `under-sliced`, `still-degraded`, or `over-sliced` verdicts. It MUST NOT draft
such an amendment for `no-data`, `unmeasurable`, `coordinator-only`, or
`coordination-degraded`, and a threshold proposal MUST update both the rubric prose
and helper constant together.

#### Scenario: Measured chunks were too large

- **WHEN** role-aware measurement returns `still-degraded`
- **THEN** finalization reports the misprediction and shows the user a concrete
  rubric diff without editing the rubric in the ticket branch
