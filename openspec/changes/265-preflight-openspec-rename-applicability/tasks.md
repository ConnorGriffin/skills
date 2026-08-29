# Tasks

- [ ] Add the non-mutating OpenSpec applicability command to the ticket command
      interface, including JSON-success checks and actionable diagnostics.
- [ ] Gate flat and chunked OpenSpec-backed `start` and `revise` after their final
      change-record edits at the pre-pull-request or pre-push boundary without
      changing finalization's archive ownership.
- [ ] Add public-command tests for changed-active-change discovery, issue 259's
      validate-pass/archive-fail shape, a correct rename, unexpected output shapes,
      and source-tree immutability.
- [ ] Update the ticket-workflow baseline delta and behavior-contract tests.
- [ ] Run `openspec validate --all --strict` and the full repository test command
      from `AGENTS.md`.
