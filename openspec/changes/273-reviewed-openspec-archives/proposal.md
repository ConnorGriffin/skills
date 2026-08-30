# Proposal

## Why

This repository currently tells ticket finalization to push a post-merge OpenSpec
archive directly to `main`. OpenSpec recommends the post-merge timing, but does not
require bypassing normal review.

## What changes

- Keep post-merge archiving for ordinary OpenSpec tickets.
- Land the archive through a small reviewed follow-up pull request.
- Record that pull request on the ticket and finish only after a human merges it
  and its workflow succeeds.
- Keep strict validation, signed-off commits, and the rule that agents never merge.

## Impact

Repository archive guidance (`openspec/config.yaml`), the `skills/drivers/ticket/`
source skill's `SKILL.md` and `verbs/finalize.md`, the ticket-workflow delta,
`docs/epic-flow.md`, and their contract tests change together. No runtime module,
parser, external service, or merge automation is added.
