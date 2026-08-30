# Tasks

- [x] Add the non-mutating OpenSpec applicability command to the ticket command
      interface, including JSON-success checks and actionable diagnostics.
- [x] Gate flat and chunked OpenSpec-backed `start` and `revise` after their final
      change-record edits at the pre-pull-request or pre-push boundary without
      changing finalization's archive ownership or non-OpenSpec/epic-child paths.
- [x] Add public-command tests for base-ref, deleted/renamed path, and zero/one/
      unsupported-multiple active-change discovery; issue 259's
      validate-pass/archive-fail shape, a correct rename, unexpected output shapes,
      a base advance after branch cut, executable-launch/export/overlay failures,
      option-shaped base-ref rejection without remote access, temporary-directory
      cleanup, and separate ticket/base-tree immutability.
- [x] Update the ticket-workflow baseline delta and behavior-contract tests.
- [x] Run `openspec validate --all --strict` and the full repository test command
      from `AGENTS.md`.
