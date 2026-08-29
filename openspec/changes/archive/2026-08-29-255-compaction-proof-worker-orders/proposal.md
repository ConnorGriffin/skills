# Keep worker orders available after compaction

## Why

A write-mode worker can lose the constraints in its initial prompt when its context
compacts. The coordinator's session-scratch copy is outside the worker's own cwd, so
the worker cannot reliably recover the order and may continue past its closed
acceptance list.

## What changes

- Put the complete prompt bytes in the write-mode worker's own worktree before
  dispatch and make that file the worker's standing re-read target.
- Stop and resume safely when the order is missing or unreadable, and keep resume
  messages anchored to the durable order.
- Delete the worktree-local scaffold at the existing teardown sites so it cannot
  block worktree removal or cleanliness checks.
- Pin the single normative contract, its pointer-only references, the sub-order
  instruction, and teardown ordering in a behavior test.

No adapter or worker-lifecycle code changes.
