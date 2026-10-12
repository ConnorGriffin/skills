---
title: The ticket flow
description: How one tracked issue becomes merged history, and which skill owns each step.
flow: ticket,code-review
---

## The common path

Tracked work starts at `ticket`; triage splits work too big for one session into child issues on a parent checklist. Each ticket verb produces one artifact and stops at a human gate. Triage resolves the open questions, asking the operator in rounds when only they can decide, and locks a work order the operator approves. Start builds to that order, verifies it, passes one `code-review`, and opens a pull request. Revise actions a review round. A human merges, and finalize closes the ticket, archives its change through a reviewed pull request, and records what the ticket cost.

Agents never merge. At Full review depth, triage also sends the draft order through one cold `plan-review` pass.
