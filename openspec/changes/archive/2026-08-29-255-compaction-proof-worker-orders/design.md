# Design

## ADR 255 — The durable order lives in the worker's own worktree

Write the complete prompt bytes to `ORDER.md` at the root of each write-mode
worker's cwd before dispatch. A compacted worker can rediscover a fixed name in its
own working directory; a coordinator-side path would itself be context that the
worker could forget and may be unreadable from the worker's sandbox.

The order file is the original prompt in a second location, not new mid-session
input. The original-prompt-only worker-input rule therefore remains unchanged: the
coordinator still supplies the same bytes at dispatch, and later resumes only
restate the existing constraints or point the worker back to them.

Cleanup belongs to the step that tears the worktree down. An abandoned or crashed
dispatch can bypass a happy-path cleanup, while the teardown step necessarily runs
before the operation that an untracked order file would block. The three existing
teardown sites delete the file immediately before worktree removal or the
cleanliness check.

No mechanical never-committed enforcement is added. A shared Git exclusion would
also hide the file from the coordinator's pre-merge diff, and a committed ignore,
hook, or new gate would exceed the accepted risk contract. The worker instruction
and the coordinator's existing diff read are the whole enforcement.
