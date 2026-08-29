# Design

## ADR 273 — Review post-merge archives

After an ordinary ticket's implementation pull request is human-merged and green,
finalization creates the OpenSpec archive on a dedicated archive branch in a
sibling checkout. It validates the archive, creates a signed-off commit, opens a
small follow-up pull request, posts an attributed `Archive PR: <url>` comment, and
stops.

A later finalization reads that locator. An open archive pull request remains
pending. A closed-unmerged pull request stops for operator direction. A
human-merged pull request with a green workflow allows completion, actuals, and
cleanup.

The archive checkout is the sole narrow exception to the ticket's normal
one-branch, one-worktree rule. Failures stop visibly and leave recoverable Git
state for the operator. There is no automatic missing-locator recovery, parser,
new state module, API integration, or merge automation.
