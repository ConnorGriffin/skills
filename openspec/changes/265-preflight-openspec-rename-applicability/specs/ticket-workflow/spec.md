## MODIFIED Requirements

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
