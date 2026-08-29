## ADDED Requirements

### Requirement: Write-mode workers retain a durable closed order

Before starting a write-mode worker, the coordinator MUST write the same complete
prompt bytes supplied to the adapter to `ORDER.md` at the root of the worker's cwd.
The prompt MUST instruct the worker to re-read that file before each commit and
before declaring the work done, treat the acceptance list as closed, stop and report
when it is met, and propose further improvement instead of editing beyond it. Chunk
sub-order boilerplate MUST carry that instruction; the coordinator MUST author it
for every other write-mode prompt, including a delegated flat work order.

A worker that cannot find or read the file MUST stop and report instead of
continuing from memory. The coordinator MUST rewrite it and resume the same worker.
Every write-mode resume MUST restate the order's constraints or point back to the
file. A coordinator that cannot write the file MUST report the dispatch unavailable
and MUST NOT start the worker. Read-mode workers MUST NOT receive the file.

The order file MUST remain uncommitted worktree-local scaffolding. The step that
removes a worker worktree MUST delete it before worktree removal and before any
cleanliness check. The repository MUST contain a behavior test that pins the
canonical guidance, worker-facing instruction, pointer-only references, and cleanup
ordering.

#### Scenario: A compacted worker re-reads its order

- **WHEN** a write-mode worker's context compacts before its next commit or completion
- **THEN** the worker re-reads the complete prompt bytes from its own cwd and stops
  once the closed acceptance list is met

#### Scenario: The durable order is unreadable

- **WHEN** a write-mode worker cannot find or read its order file
- **THEN** it stops and reports, and the coordinator rewrites the file and resumes
  that same worker

#### Scenario: The coordinator cannot write the order

- **WHEN** the coordinator cannot write the complete prompt bytes into the worker's
  cwd before dispatch
- **THEN** it reports the dispatch unavailable and does not start the worker

#### Scenario: A worker worktree is torn down

- **WHEN** a workflow reaches an existing worktree teardown or stale-worktree
  cleanliness check
- **THEN** it deletes the order file before the operation that the untracked file
  would block

#### Scenario: Durable-order guidance regresses

- **WHEN** the canonical rule, worker-facing instruction, pointer direction, or
  teardown ordering is removed or weakened
- **THEN** the behavior test fails
