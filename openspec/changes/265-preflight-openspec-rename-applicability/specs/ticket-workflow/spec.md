## MODIFIED Requirements

### Requirement: Four-verb lifecycle

The ticket workflow MUST expose one verb at a time: `triage` grounds the ticket and
posts a locked work order after unconditional `/scope`; `start` executes the newest
order in an isolated ticket worktree, proves in both flat and chunked execution
that the one active OpenSpec change modified by the ordinary ticket branch can apply
to the current baseline without mutating either authoritative tree, and opens a
pull request; `revise` actions one review round, completes its active-change edits,
and repeats that applicability proof before pushing; and `finalize`
reconciles a merged or explicitly abandoned pull request with the tracker and local
worktree state. Agents MUST stop at the pull request boundary and MUST NOT merge.

#### Scenario: A ticket reaches implementation

- **WHEN** `start` finds a sufficient newest work order and a compatible session
- **THEN** it reuses the ticket's branch and worktree, implements and verifies the
  order, proves its changed active OpenSpec delta applies in a disposable copy,
  opens one pull request, and stops for human review

#### Scenario: A chunked ticket reaches pull-request creation

- **WHEN** coordinator mode has merged and reviewed all chunks and recorded the
  ordinary ticket's active change
- **THEN** it proves every changed active OpenSpec delta applies before rejoining
  pull-request creation

#### Scenario: A structurally valid delta cannot apply

- **WHEN** strict validation passes but a disposable archive reports an unmatched
  modified requirement and no archive result
- **THEN** the workflow stops before the pull request, names the unmatched
  requirement, directs the author to add the missing rename mapping or correct the
  modified header, and leaves the active change and baseline unchanged

#### Scenario: A correctly renamed requirement is preflighted

- **WHEN** a change contains a valid mapping from the current baseline requirement
  header to its modified header
- **THEN** the disposable archive succeeds and the existing pre-merge and
  post-merge lifecycle continues without altering the authoritative tree early

#### Scenario: Review changes an active delta

- **WHEN** `revise` changes an ordinary ticket's checklist or decision record
- **THEN** it completes those active-change edits, proves the resulting bytes apply,
  and only then pushes the branch

#### Scenario: An ordinary ticket changes several active changes

- **WHEN** base-diff discovery finds more than one active OpenSpec change still
  present in the ticket tree
- **THEN** preflight stops visibly because ordinary-ticket finalization owns one
  archive unit instead of independently approving interacting deltas
