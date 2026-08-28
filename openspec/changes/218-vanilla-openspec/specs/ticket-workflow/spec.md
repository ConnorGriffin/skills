# Ticket workflow — deltas

## MODIFIED Requirements

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

## ADDED Requirements

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
