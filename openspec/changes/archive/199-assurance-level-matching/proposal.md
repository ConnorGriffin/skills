# Match review assurance to the request

## Why

Review rounds can turn prose agreements into unrequested enforcement machinery,
raising the assurance bar without a user decision.

## What changes

Record assurance-level matching as a standing working preference, bound plan
reviewers to the requested behavior and admitted risk, and make a coordinator
session re-read settled decisions after mid-review compaction.

## Risk contract

- **Must prevent:** a review round silently raising the assurance bar above what the
  admitted work declared, with no user decision.
- **Must recover:** nothing. There is no runtime here.
- **Accepted failure:** an agent misreads the rule and still over-hardens; the user
  says so and the round is redone. Consequence is one wasted round.
- **Unsupported:** enforcement. This is instruction prose read by agents; nothing
  parses, validates, or gates on it at runtime.
- **Evidence owed:** the pinned-prose tests this repo already uses for skill
  contract text (`tests/test_behavior.py` pattern), and nothing more.
- **Why:** the subject is agent-instruction prose with no execution surface, so the
  only real consequence of failure is a wasted review round.
- **Disposition:** admitted at intent level; a mechanism stronger than prose plus a
  string-pinning test is out of scope for this ticket by decision, not by oversight.
