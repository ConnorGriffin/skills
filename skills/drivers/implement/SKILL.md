---
name: implement
description: "Implement a piece of work based on a PRD or set of issues."
---

For a tracked ticket, enter through `/ticket triage <id>` and continue through
`start`, `revise`, and `finalize`; that lifecycle owns the worktree, lock, review,
commit, and pull-request boundary. Do not create a competing current-branch path.

For an untracked PRD, first ask the operator whether to file a ticket. If they
explicitly keep it untracked, use an isolated worktree, agree the interface and
tests, work test-first where meaningful, run the repository's verification, then
invoke `/review` before returning the commit and evidence. Do not open or merge a
pull request unless the operator separately asks.
