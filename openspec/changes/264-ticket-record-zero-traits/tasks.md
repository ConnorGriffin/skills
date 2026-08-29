# Tasks

- [ ] Make `record --trait` optional with an empty-list default while preserving
      repeatable explicit values and every non-trait command behavior.
- [ ] Add public-command tests for zero traits and multiple ordered traits.
- [ ] Clarify the finalization command contract for orders with no fired traits.
- [ ] Run `openspec validate 264-ticket-record-zero-traits --strict`,
      `python3 -m unittest tests.test_behavior tests.test_ticket`, and the full
      repository verification command from `AGENTS.md`.
