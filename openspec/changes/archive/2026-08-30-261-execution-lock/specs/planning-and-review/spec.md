# Planning and review routing — deltas

## MODIFIED Requirements

### Requirement: Write-mode workers retain a durable closed order

Before starting a write-mode worker, the coordinator MUST write the same complete
prompt bytes supplied to the adapter to `ORDER.md` at the root of the worker's cwd.
On a ticket or chunk dispatch carrying an `EXECUTION LOCK`, those bytes MUST be the
complete lock or stand-alone sub-lock plus dispatch instructions, never a
restatement of the pinned source's own plan prose; `ORDER.md` MUST remain an
uncommitted transport copy of that payload and MUST NOT become a second authority
over the pinned source. The prompt MUST instruct the worker to re-read that file
before each commit and before declaring the work done, treat the acceptance list as
closed, stop and report when it is met, and propose further improvement instead of
editing beyond it. Chunk sub-order boilerplate MUST carry that instruction; the
coordinator MUST author it for every other write-mode prompt, including a delegated
flat work order.

A worker that cannot find or read the file MUST stop and report instead of
continuing from memory. A worker that cannot read the pinned source the file names
MUST stop and report the same way, and the coordinator MUST NOT generate a second
snapshot to make the prompt self-contained in its place. The coordinator MUST
rewrite the order file and resume the same worker. Every write-mode resume MUST
restate the order's constraints or point back to the file. A coordinator that
cannot write the file MUST report the dispatch unavailable and MUST NOT start the
worker. Read-mode workers MUST NOT receive the file.

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

#### Scenario: The pinned source is unreadable

- **WHEN** a write-mode worker's `ORDER.md` names a pinned source that the worker
  cannot read from its own checkout
- **THEN** the worker stops and reports instead of continuing from memory, and the
  coordinator does not generate a second snapshot to make the prompt self-contained

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

## ADDED Requirements

### Requirement: Worker payload boundary

A chunk-worker prompt MUST copy only the complete lock or stand-alone sub-lock, the
worker's exact worktree/branch/graph identity, the verified source pin, its
selected identifiers, the verification command and expectation, the expected-diff
allowlist and ownership boundaries, and ephemeral verified facts. It MUST NOT copy
the OpenSpec artifacts, repository-native plans, UI contracts, or repository rules
that the pinned source or checkout already carries; the worker reads those from its
own checkout instead.

#### Scenario: A chunk prompt is assembled

- **WHEN** the coordinator writes a chunk's dispatch prompt
- **THEN** the prompt carries the sub-lock, worktree/branch/graph identity, verified
  source pin, selected identifiers, verification command and expectation, and
  expected-diff allowlist, and restates no OpenSpec artifact, repository-native
  plan, UI contract, or repository rule already reachable from the pinned checkout

#### Scenario: A worker cannot reach the referenced material

- **WHEN** a dispatched worker cannot read an OpenSpec artifact, plan, or rule its
  prompt references from its own checkout
- **THEN** the worker stops and reports instead of proceeding from memory, and no
  second snapshot is generated to make the prompt self-contained
