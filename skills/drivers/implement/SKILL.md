---
name: implement
description: "Implement a piece of work based on a PRD or set of issues."
---

For a tracked ticket, consume its selected caller lifecycle and admitted lock. Do
not re-triage a valid lock, run more than one ticket verb in one session, or create
a competing current-branch path. `triage`, `start`, `revise`, and `finalize` stay
fresh sessions; `start` stops at its open pull request and `finalize` runs only
after human merge. Explicit operator overrides still control their stated scope.

For an untracked PRD, resolve the tracked path explicitly: ask whether the operator
wants a ticket filed, then route a yes through `/ticket triage <id>`. If the
operator explicitly declines, return that there is no tracked implementation path
rather than duplicating ticket's worktree, lock, review, commit, or PR procedure.
