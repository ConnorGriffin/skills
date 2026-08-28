# Ticket workflow

## Purpose

Define how one tracked ticket moves from grounded scope through isolated execution,
human review, merge reconciliation, cleanup, and measured workflow calibration.

## Requirements

### Requirement: Four-verb lifecycle

The ticket workflow MUST expose one verb at a time: `triage` grounds the ticket and
posts a locked work order after unconditional `/scope`; `start` executes the newest
order in an isolated ticket worktree and opens a pull request; `revise` actions one
review round; and `finalize` reconciles a merged or explicitly abandoned pull
request with the tracker and local worktree state. Agents MUST stop at the pull
request boundary and MUST NOT merge.

#### Scenario: A ticket reaches implementation

- **WHEN** `start` finds a sufficient newest work order and a compatible session
- **THEN** it reuses the ticket's branch and worktree, implements and verifies the
  order, opens one pull request, and stops for human review

### Requirement: Work-order lock and model fit

`start` and `revise` MUST refuse execution when no work-order comment exists, MUST
use the newest work order when several exist, and MUST NOT execute an order or
sub-order above the coordinator session's admitted model rung.

#### Scenario: No work order exists

- **WHEN** `start` scans the ticket comments and finds no fenced block beginning
  `WORK ORDER`
- **THEN** it refuses implementation and routes the ticket back to triage instead
  of inventing scope

### Requirement: Bounded worker-egress consent

A literal invocation of ticket `triage`, `start`, or `revise` MUST authorize the
work order or task prompt plus only the repository code and documentation needed
for every mandatory dispatch that verb routes, including nested review and
orchestration. Automatic activation outside an invoked parent MUST ask once on the
same terms, while `finalize` MUST grant no worker-egress consent. This declaration
MUST NOT override platform approval policy, adapter isolation, or prompt handling.

#### Scenario: Start reaches mandatory independent review

- **WHEN** a user literally invokes `/ticket start` and the order reaches its
  required review step
- **THEN** the workflow may dispatch the bounded review through the pack adapter
  without asking again solely for worker-egress consent

### Requirement: Slicing and chunk coordination

Triage MUST slice an order when at least two calibrated context-load traits apply,
target each worker chunk below the 180k-token peak band, fold a projected sub-120k
chunk into a neighbor, and treat four chunks as the practical ceiling. A chunked
`start` MUST use one independently executable sub-order per chunk under coordinator
mode while retaining one ticket branch and one pull request.

#### Scenario: A work order has two slicing traits

- **WHEN** grounding finds two or more traits from the slicing rubric
- **THEN** triage posts independently executable sub-orders with explicit file,
  capability, contract, ordering, model, and review-depth ownership

### Requirement: Epic promotion distinguishes uncertainty from bulk

Triage MUST promote work to `/epic` only when the projected shape exceeds four
chunks and at least one decision remains unsettled. It MUST hand-split a purely
mechanical oversized effort into serial `build` tickets instead of using Epic
machinery for bulk alone.

#### Scenario: More than four chunks still contain fog

- **WHEN** a projected order needs more than four chunks and an unresolved
  decision can still invalidate the work
- **THEN** triage routes the effort to `/epic`

#### Scenario: More than four chunks are mechanical

- **WHEN** a projected order is oversized but carries no unsettled decision
- **THEN** triage splits it into serial build tickets rather than promoting it to
  an Epic

### Requirement: Independent type and status labels

The GitHub binding MUST keep the Epic protocol type labels (`epic`, `spike`,
`build`, and `deferred`) independent from the `ticket:*` status labels. A code
ticket's triage transition MUST ensure `build` before applying `ticket:triaged`,
and later ticket verbs MUST move only the status axis they own.

#### Scenario: A code ticket becomes in progress

- **WHEN** `start` reuses or cuts the ticket worktree
- **THEN** the binding adds `ticket:in-progress` and removes `ticket:triaged`
  without removing the ticket's `build` type

### Requirement: Role-aware telemetry and review depth

Each participating session MUST be claimable as coordinator, worker, or reviewer,
and finalization MUST record those role-tagged costs separately. Worker peaks alone
MUST calibrate chunk sizing; coordinator and reviewer peaks MUST remain independent
overhead. Review depth MUST be stamped from change scope and sensitivity rather
than inferred from slicing telemetry.

#### Scenario: A chunked ticket has an expensive review

- **WHEN** finalization records a reviewer peak above the slicing band while the
  implementation workers remain within it
- **THEN** the reviewer cost is reported separately and does not make the chunks
  appear under-sliced or change their stamped review depth

### Requirement: Finalization and abandonment

Merged finalization MUST verify the pull-request merge and successful
post-merge workflow, then, for an ordinary OpenSpec-backed ticket, complete the
repository's `operations.archive.guidance` procedure — archive the change,
revalidate strictly, land the signed-off archive commit, and verify the
post-push workflow — before posting the completion comment or moving the
ticket to done; an archive, validation, commit, push, or post-push failure MUST
stop finalization visibly. Actuals MUST be recorded before the ticket worktree
is torn down. An epic child MUST leave archive ownership with its parent epic.
A closed-unmerged or cancelled ticket MUST NOT be torn down or assigned a
terminal state until the user explicitly confirms the abandoned path and
chooses the ticket state.

#### Scenario: An ordinary OpenSpec ticket is finalized after merge

- **WHEN** `finalize` verifies the human merge and green post-merge workflow on
  a repository with `operations.archive.guidance`
- **THEN** it completes the configured archive, strict validation, signed-off
  commit, direct push, and post-push verification before commenting completion
  and moving the ticket to done

#### Scenario: A pull request was abandoned

- **WHEN** `finalize` finds the pull request closed without merge or the work
  was cancelled
- **THEN** it comments the reason and waits for explicit user confirmation
  before teardown or any user-selected terminal transition

### Requirement: Slicing amendment verdicts

Finalization MUST draft, but MUST NOT apply, a concrete slicing-rubric amendment
for `under-sliced`, `still-degraded`, or `over-sliced` verdicts. It MUST NOT draft
such an amendment for `no-data`, `unmeasurable`, `coordinator-only`, or
`coordination-degraded`, and a threshold proposal MUST update both the rubric prose
and helper constant together.

#### Scenario: Measured chunks were too large

- **WHEN** role-aware telemetry returns `still-degraded`
- **THEN** finalization reports the misprediction and shows the user a concrete
  rubric diff without editing the rubric in the ticket branch

### Requirement: Active change reviewable through merge

`start` and `revise` MUST keep an OpenSpec-backed ticket's active change and
its deltas reviewable in the ticket pull request and MUST NOT fold the change
into the baseline or archive it before the merge. Archive timing MUST come from
the repository's `operations.archive.guidance` rather than a competing rule
stated in a pack skill.

#### Scenario: A ticket pull request is opened with an active change

- **WHEN** `start` opens the ticket pull request for OpenSpec-backed work
- **THEN** the active change and its deltas ride the pull request for review
  and remain active until post-merge finalization archives them per repository
  guidance
