# Scope: reviewed OpenSpec archives

## Decision

Keep archiving ordinary OpenSpec changes after the implementation pull request
merges, but land the archive through a small follow-up pull request instead of a
direct push to `main`.

Ticket finalization therefore has two attended stages:

1. Verify the implementation merge and green workflow, create and validate the
   archive on a dedicated branch, open the archive pull request, post its URL on
   the ticket, and stop.
2. On a later `finalize`, read that URL. If the pull request is still open, stop.
   If a human merged it and its workflow is green, post completion, record actuals,
   and clean up.

The archive branch and sibling checkout are a narrow post-merge exception to the
ticket's normal one-branch, one-worktree rule. Agents still never merge pull
requests.

## Risk contract

- **Must prevent:** direct pushes to `main`, agent merges, and ticket completion
  before the archive pull request is human-merged and green.
- **Accepted failure:** if archive creation, validation, pull-request creation, or
  ticket commenting fails, stop visibly and leave the branch/checkouts for the
  operator to recover manually.
- **Unsupported:** automatic recovery when a pull request was created but its URL
  was not recorded on the ticket; automatic replacement of a closed-unmerged
  archive pull request.
- **Evidence owed:** contract tests show the two-stage order and absence of a
  direct push to `main`.

## Shape

Flat, one agent. This is one small documentation-and-contract change with no new
runtime module, parser, service, or integration.

## Open questions

None.

## Review rounds

- The initial draft was rejected as over-engineered. This revision removes the
  head-branch lookup protocol, automatic missing-comment recovery, scratch Git
  spike, and detailed cleanup state machine. Failures remain visible and manually
  recoverable for the single operator.
- One operator-directed Codex Terra cold review returned `COUNTERSIGNED` with no
  build-changing objections. It spot-checked the current direct-push guidance in
  `openspec/config.yaml` and `skills/drivers/ticket/verbs/finalize.md`.
