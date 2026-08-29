## MODIFIED Requirements

### Requirement: Four-verb lifecycle

The ticket workflow MUST expose one verb at a time: `triage` grounds the ticket and
posts a locked work order after unconditional `/scope`; `start` executes the newest
order in an isolated ticket worktree, proves that any ordinary active OpenSpec
change can apply to the current baseline without mutating either authoritative
tree, and opens a pull request; `revise` actions one review round and repeats that
applicability proof before pushing a changed OpenSpec delta; and `finalize`
reconciles a merged or explicitly abandoned pull request with the tracker and local
worktree state. Agents MUST stop at the pull request boundary and MUST NOT merge.

#### Scenario: A ticket reaches implementation

- **WHEN** `start` finds a sufficient newest work order and a compatible session
- **THEN** it reuses the ticket's branch and worktree, implements and verifies the
  order, proves any active OpenSpec delta applies in a disposable copy, opens one
  pull request, and stops for human review

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
