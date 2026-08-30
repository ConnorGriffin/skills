# ticket-workflow Delta

## MODIFIED Requirements

### Requirement: Finalization and abandonment

Merged finalization MUST verify the implementation pull-request merge and
successful post-merge workflow. For an ordinary OpenSpec-backed ticket, it MUST
archive and strictly validate the change on a dedicated branch, create a signed-off
commit, and open a reviewed follow-up pull request instead of pushing the archive
commit directly to the default branch. An agent MUST NOT merge either pull request.

Finalization MUST post an attributed `Archive PR: <url>` ticket comment and stop.
A later finalization MUST read that locator. An open archive pull request MUST
remain pending. A closed-unmerged archive pull request MUST stop for operator
direction. Only a human-merged archive pull request with a successful post-merge
workflow permits completion, actuals recording, and cleanup.

The archive branch and checkout MAY be a narrow post-merge exception to the normal
one-branch, one-worktree ticket lifecycle. A failure MUST stop visibly and preserve
recoverable Git state. Actuals MUST be recorded before the ticket worktree is torn
down. An epic child MUST leave archive ownership with its parent. A closed-unmerged
or cancelled ticket MUST NOT be torn down or assigned a terminal state until the user
explicitly confirms the abandoned path and chooses the ticket state.

#### Scenario: An ordinary OpenSpec ticket is finalized after merge

- **WHEN** the implementation pull request is human-merged and green
- **THEN** finalization archives and validates the change, creates a signed-off
  commit, opens but does not merge a follow-up pull request, posts its attributed
  URL on the ticket, and stops

#### Scenario: The archive pull request is still open

- **WHEN** a later finalization reads an archive pull request that remains open
- **THEN** it reports pending human review and does not complete the ticket

#### Scenario: A human merges the archive pull request

- **WHEN** a later finalization verifies that the archive pull request was
  human-merged and its post-merge workflow succeeded
- **THEN** it posts completion, records actuals, cleans up, and moves the ticket to
  done

#### Scenario: The archive pull request closes without merge

- **WHEN** finalization finds the archive pull request closed without merge
- **THEN** it stops for operator direction without completing the ticket

#### Scenario: A pull request was abandoned

- **WHEN** the implementation pull request closes without merge or the work is
  cancelled
- **THEN** finalization comments the reason and waits for explicit user confirmation
  before teardown or any user-selected terminal transition
