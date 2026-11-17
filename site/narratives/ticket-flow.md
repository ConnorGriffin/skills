---
title: The ticket flow
description: How one tracked issue becomes merged history, and which skill owns each step.
flow: ticket,code-review
---

## The common path

Tracked work starts at `ticket`; work that needs several pull requests, in one repo or many, stays on one ticket with a locked work order per piece, tracked on a pieces checklist. Each ticket verb produces one artifact and stops at a human gate. Triage resolves the open questions, asking the operator in rounds when only they can decide, and locks a work order for every piece, which the operator approves in one pass. Start builds the next unblocked piece's order, verifies it, passes one `code-review`, and opens a pull request. Revise actions a review round. A human merges, and finalize closes the piece (and the ticket after its last piece), archives its change through a reviewed pull request, and records what the ticket cost.

Agents never merge. At Full review depth, triage also sends the draft order through one cold `plan-review` pass.
