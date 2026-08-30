# Tasks

- [x] Define the `EXECUTION LOCK v2` envelope in
      `skills/drivers/ticket/templates/work-order.md`: flat and chunked
      sub-lock shapes, the three source modes, and `inline` retaining today's
      Context/Do/Done-when payload.
- [x] Extend the locate operation in
      `skills/drivers/ticket/references/tracker-contract.md` and the
      github-issues binding so the newest recognized lock wins across both
      protocols, with no field merging.
- [x] Rewrite `skills/drivers/ticket/verbs/triage.md` to author, validate,
      commit, and pin the change before posting a lock, with the
      `repository-native` and `inline` paths stated for other repositories.
- [x] Align `references/drafting-conventions.md` and `references/slicing.md`
      with the lock's fields and with sub-locks selecting disjoint task
      subsets.
- [x] Rewrite `verbs/start.md` and `verbs/revise.md` to resolve and validate
      the pinned source per the fail-closed matrix before any implementation
      or dispatch, each refusal named in prose.
- [x] Update `skills/drivers/ticket/SKILL.md` so the lock-entry rule and the
      fresh-session contract define self-sufficiency as deterministic
      acquisition of the authorized source, naming both protocols.
- [x] Update `skills/drivers/orchestrate/SKILL.md` and
      `references/coordinator-mode.md` so `ORDER.md` and chunk prompts carry
      the lock as transport, never a second authority.
- [x] Update `skills/drivers/epic/SKILL.md` and `docs/epic-flow.md`
      terminology for the lock protocol.
- [x] Write the `ticket-workflow` and `planning-and-review` spec deltas in
      this change's `specs/` subtree.
- [x] Add fail-first tests in `tests/test_ticket.py` covering one row per
      refusal, legacy-order location and execution, and newest-wins across
      mixed legacy and v2 comments; repair `tests/test_behavior.py` pins.
- [x] Run `scripts/validate.py`, the repository test command from `CLAUDE.md`,
      and `openspec validate 261-execution-lock --strict`.
- [ ] Open the pull request linking #261.
