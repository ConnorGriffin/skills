# Ticket workflow

## Purpose

Define how one tracked ticket moves from grounded scope through isolated execution,
human review, merge reconciliation, cleanup, and measured workflow calibration.

## Requirements

### Requirement: Four-verb lifecycle

The ticket workflow MUST expose one verb at a time: `triage` grounds the ticket and
posts a locked work order after unconditional `/scope`; `start` executes the newest
order in an isolated ticket worktree and, for an ordinary OpenSpec-backed ticket,
proves in both flat and chunked execution that its one active change can apply to a
freshly fetched current baseline without mutating either authoritative tree, then
opens a pull request; `revise` actions one review round and, for an ordinary
OpenSpec-backed ticket, completes its active-change edits and repeats that
applicability proof before pushing; and `finalize`
reconciles a merged or explicitly abandoned pull request with the tracker and local
worktree state. Agents MUST stop at the pull request boundary and MUST NOT merge.

#### Scenario: A ticket reaches implementation

- **WHEN** `start` finds a sufficient newest work order and a compatible session for
  an ordinary OpenSpec-backed ticket
- **THEN** it reuses the ticket's branch and worktree, implements and verifies the
  order, proves its changed active OpenSpec delta applies in a disposable copy,
  opens one pull request, and stops for human review

#### Scenario: A chunked ticket reaches pull-request creation

- **WHEN** coordinator mode has merged and reviewed all chunks for an ordinary
  OpenSpec-backed ticket and recorded its active change
- **THEN** it proves its one changed active OpenSpec delta applies before rejoining
  pull-request creation

#### Scenario: The default branch advanced after ticket branch cut

- **WHEN** flat or chunked `start` reaches applicability preflight
- **THEN** it fetches the remote immediately before exporting the current default-
  branch OpenSpec tree, and a fetch or base-ref failure stops pull-request creation

#### Scenario: A base ref resembles a Git option

- **WHEN** the public applicability command receives a base-ref value that could be
  parsed as a Git option rather than a local revision
- **THEN** it resolves the value with Git's end-of-options form to a verified local
  commit before merge-base or export, and an unresolved value stops locally without
  invoking a remote

#### Scenario: The baseline advances after the gate

- **WHEN** the freshly fetched baseline passes applicability preflight and then
  advances again before the later human merge
- **THEN** the workflow makes no merge-time guarantee or enforcement claim, and a
  resulting post-merge archive mismatch stops finalization for manual correction

#### Scenario: A structurally valid delta cannot apply

- **WHEN** strict validation passes but a disposable archive reports an unmatched
  modified requirement and no archive result
- **THEN** the workflow stops before the pull request and emits exactly two ordered
  `ticket:` stderr lines: the unmatched requirement first, then direction to add
  the missing rename mapping or correct the modified header; it leaves the active
  change and baseline unchanged

#### Scenario: Applicability infrastructure fails

- **WHEN** executable launch, base export, active-change overlay, or archive CLI
  execution fails during the disposable applicability proof
- **THEN** the public command exits nonzero with one `ticket:` stderr diagnostic,
  removes its temporary directory, and leaves the ticket worktree and base-ref
  OpenSpec trees unchanged

#### Scenario: A correctly renamed requirement is preflighted

- **WHEN** a change contains a valid mapping from the current baseline requirement
  header to its modified header
- **THEN** the disposable archive succeeds and the existing pre-merge and
  post-merge lifecycle continues without altering the authoritative tree early

#### Scenario: Review changes an active delta

- **WHEN** `revise` changes an ordinary ticket's checklist or decision record
- **THEN** it completes those active-change edits, fetches the remote immediately
  before proving the resulting bytes against refreshed `origin/<baseRefName>`, and
  only then pushes the branch

#### Scenario: An ordinary ticket changes several active changes

- **WHEN** base-diff discovery finds more than one active OpenSpec change still
  present in the ticket tree
- **THEN** preflight stops visibly because ordinary-ticket finalization owns one
  archive unit instead of independently approving interacting deltas

#### Scenario: A ticket uses another change-record convention

- **WHEN** flat start, chunked coordinator mode, or revise operates a repository
  whose ordinary ticket is not backed by an OpenSpec active change
- **THEN** it preserves that repository's existing verification and pull-request or
  push path without invoking the OpenSpec applicability command

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
work order or task prompt plus only the repository code, documentation, and UI
fidelity evidence rendered from manufactured or synthetic fixtures needed for
every mandatory dispatch that verb routes, including review and orchestration.
Evidence rendered from real user, production, or patient data MUST remain outside
the grant, whether or not a capture is tracked in the repository. Every
coordinator reviewer-dispatch step MUST restate that granted payload where the
dispatch decision is made, so the coordinator does not re-ask for consent the
invocation already gave. Automatic activation outside an invoked parent MUST ask
once on the same terms, while `finalize` MUST grant no worker-egress consent. This
declaration MUST NOT override platform approval policy, adapter isolation, or
prompt handling. When a coordinator delegates ticket work, its prompt MUST
identify the mandatory-review handoff. The worker MUST return or write its
review-ready result through the coordinator-recorded durable result locator at
that boundary. The coordinator MUST collect that result, dispatch every mandatory
reviewer, and resume that same worker with either verified findings for correction
or a verified clean verdict to finish. Unavailable review evidence MUST block the
workflow from advancing as reviewed. The worker MUST NOT launch a nested reviewer.

#### Scenario: Start reaches mandatory independent review

- **WHEN** a user literally invokes `/ticket start` and the order reaches its
  required review step
- **THEN** the workflow may dispatch the bounded review through the pack adapter
  without asking again solely for worker-egress consent

#### Scenario: Fidelity screenshots accompany a reviewer dispatch

- **WHEN** a coordinator holds UI fidelity screenshots rendered from manufactured
  or synthetic fixtures and reaches a mandatory reviewer dispatch
- **THEN** it sends them under the invocation's existing grant instead of halting
  to re-ask, and the exclusions stay in force

#### Scenario: Evidence comes from real data

- **WHEN** the evidence a dispatch would carry was rendered from real user,
  production, or patient data
- **THEN** the grant does not cover it and the transfer is not authorized by the
  invocation alone

#### Scenario: Delegated start reaches mandatory independent review

- **WHEN** a delegated `/ticket start` worker returns implementation ready for its required review
- **THEN** its coordinator dispatches the bounded review through the pack adapter and resumes the same worker with actionable findings or a verified clean verdict

#### Scenario: Delegated review evidence is unavailable

- **WHEN** a delegated ticket review has a failed launch, nonzero exit, missing result artifact, or missing verdict
- **THEN** the coordinator reports the review as unavailable and does not advance the workflow as reviewed

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
  overhead separately

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

Finalization MUST report the misprediction for `under-sliced`, `still-degraded`,
or `over-sliced` verdicts, naming which rubric call was wrong and by how much. It
MUST NOT draft a slicing-rubric amendment, MUST NOT prompt the operator on that
path, and MUST NOT edit the rubric. The slicing record already appended to the
target repository's reviewer-memory store is the calibration sink for those
lessons. Finalization MUST NOT report a misprediction for `no-data`,
`unmeasurable`, `coordinator-only`, or `coordination-degraded`. A change to the
slicing thresholds themselves MUST be operator-initiated and MUST update the
rubric prose and the helper constant together.

#### Scenario: Measured chunks were too large

- **WHEN** role-aware measurement returns `still-degraded`
- **THEN** finalization reports the misprediction against the stamped shape, names
  the per-repo slicing record as the calibration, and neither drafts a rubric diff
  nor asks the operator anything

#### Scenario: A verdict is not a misprediction

- **WHEN** role-aware measurement returns `no-data`, `unmeasurable`,
  `coordinator-only`, or `coordination-degraded`
- **THEN** finalization reports that verdict's own meaning and reports no slicing
  misprediction

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

### Requirement: Epic child triage carries required parent-plan amendments

An epic child's ticket triage MUST treat the issue body's epic-authored order as a
draft, ground and independently review it through the ordinary triage procedure,
fetch the named parent-plan branch as `origin/<branch name>`, and require that branch to resolve to the
full commit pinned in the draft before cutting the child worktree from that branch.
It MUST post the resulting fenced work order as the only execution lock. When the draft
requires an amendment to the parent epic's active OpenSpec change, triage MUST commit
that amendment in the child's ticket worktree and continue; it MUST NOT open or
require a separate planning-only pull request.

#### Scenario: A child draft requires a parent design clarification

- **WHEN** ticket triage verifies that the child cannot execute until the parent design is amended
- **THEN** it commits the amendment in the child worktree, includes it in the independently reviewed lock, and leaves it for the child's implementation pull request

#### Scenario: An epic-authored child draft is ready for locking

- **WHEN** the operator invokes ticket triage on an epic child whose issue contains a draft order and a parent-plan branch/commit pin
- **THEN** triage resolves the unprefixed branch name as `origin/<branch name>`, verifies it resolves to the pinned commit, passes the same unprefixed name to `--base`, and grounds and reviews the draft before posting the only fenced executable work order

#### Scenario: The pinned parent-plan branch advanced

- **WHEN** the fetched remote parent-plan branch no longer resolves to the commit pinned in the child draft
- **THEN** triage posts nothing and returns the stale draft to the attended epic session for refresh

### Requirement: Epic child implementation preserves the parent archive owner

An epic child MAY carry updates to its parent's active OpenSpec change when those
updates are required by that child's implementation. It MUST NOT create a per-child
change record or archive the parent change; the parent epic remains the single change
authority and archive owner.

#### Scenario: A child pull request carries its parent-plan amendment

- **WHEN** the child's implementation is ready after triage amended the parent plan
- **THEN** the pull request includes that parent-plan amendment with the implementation and leaves the active change unarchived

#### Scenario: Another child is ready while the prior child is unmerged

- **WHEN** a prior child implementation pull request is not yet human-merged
- **THEN** the epic refuses the later child handoff regardless of whether the prior child amended the parent plan

### Requirement: Triage mutation authority

Ticket triage MUST confine writes by ownership and purpose. It MAY initialize,
update, and read operator-local state that the installed workflow requires to
execute the selected ticket lifecycle. Repository and tracker writes MUST remain in
the selected ticket's worktree and branch, an ordinary ticket's active change, and
the selected ticket's comment and status, except for the defined Epic-child
parent-plan amendment carried by that child's implementation pull request.

Creating or mutating state for a distinct concern outside that selected lifecycle
MUST require explicit operator authorization to the previously disclosed external
target and exact mutation. Reading a parent, linked ticket, live service, or
repository record for grounding MUST NOT grant authority to create or change a
separate branch, commit, push, pull request, tracker item, or repository artifact
for that external concern. A newly added operator-local workflow mechanism MUST NOT
be misclassified as ancillary solely because an older order did not enumerate it.

The selected-ticket active change allowance MUST apply directly only to an ordinary
ticket. An Epic child MUST create no per-child change record and MUST NOT claim its
parent's active change as its own. A parent-plan amendment required by the selected
child's implementation MAY be committed in that child's worktree and travel with its
implementation pull request under parent ownership; this MUST count as selected-ticket
lifecycle work rather than ancillary work.

An external amendment MUST be treated as a prerequisite only when omitting it would
make the current order contradict a recorded destination, constraint, acceptance
criterion, risk, or sequence in the selected ticket or its governing parent. Triage
MUST cite that clause, name the exact ancillary target and mutation, stop before the
mutation, and accept authorization only from an operator response that explicitly
authorizes the previously disclosed target and exact mutation. Acknowledgment alone
and the original triage invocation MUST NOT count as that authorization.
When no such contradiction exists, triage MUST continue and carry the implementation
decision in the selected ticket's work order.

#### Scenario: A compatible parent clarification appears during triage

- **WHEN** grounding finds a parent-planning clarification that the selected
  ticket's work order can carry without contradicting a recorded destination,
  constraint, acceptance criterion, risk, or sequence
- **THEN** triage records the decision in that order and does not create or require
  a separate branch, commit, push, pull request, or tracker item

#### Scenario: An external amendment is a true prerequisite

- **WHEN** a safe work order depends on changing a parent or other external
  authority first because the order would otherwise contradict one of its recorded
  destination, constraint, acceptance, risk, or sequencing clauses
- **THEN** triage cites the clause, names the exact target and mutation, stops before
  external mutation, and waits for an operator response that explicitly authorizes
  that previously disclosed target and exact mutation

#### Scenario: Required operator-local workflow state is written

- **WHEN** the installed triage workflow requires a claim, exact-worktree Codebase
  Memory state, reviewer-memory state, or local ref refresh to execute the selected
  lifecycle
- **THEN** that operator-local workflow state proceeds without ancillary-work
  approval and does not authorize a distinct repository or tracker concern

#### Scenario: An Epic child carries a required parent-plan amendment

- **WHEN** the selected ticket is a confirmed Epic child and its implementation
  requires an amendment to the pinned parent plan
- **THEN** triage may commit that amendment in the child worktree for the child's
  implementation pull request, creates no per-child change record, and leaves
  ownership and archive responsibility with the parent

### Requirement: Slicing traits are optional record evidence

Finalization MUST be able to record a ticket whose work order fired no slicing
traits without inventing a sentinel trait. The public `record` command MUST emit
an empty `traits` array when no `--trait` flag is supplied. When one or more
`--trait` flags are supplied, it MUST preserve their values and order. Trait
presence MUST NOT alter verdict calculation, session attribution, or
reviewer-memory persistence.

#### Scenario: A flat order fired no slicing traits

- **WHEN** finalization invokes `record` without a `--trait` flag
- **THEN** the command succeeds and emits `"traits": []`

#### Scenario: An order fired multiple slicing traits

- **WHEN** finalization invokes `record` with multiple `--trait` flags
- **THEN** the command emits every supplied trait in the same order
