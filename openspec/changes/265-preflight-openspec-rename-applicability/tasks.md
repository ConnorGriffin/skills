# Tasks

- [ ] Add the non-mutating OpenSpec applicability command to the ticket command
      interface, including JSON-success checks and actionable diagnostics.
- [ ] Gate OpenSpec-backed `start` and `revise` at their last pre-pull-request or
      pre-push boundary without changing finalization's archive ownership.
- [ ] Add public-command tests for issue 259's validate-pass/archive-fail shape,
      a correct rename, unexpected output, and source-tree immutability.
- [ ] Update the ticket-workflow baseline delta and behavior-contract tests.
- [ ] Run `openspec validate --all --strict` and the full repository test command
      from `AGENTS.md`.
