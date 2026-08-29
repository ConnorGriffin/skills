# Tasks

- [x] Remove the unused telemetry path, append helper, and record write-denial path
      while preserving `record` stdout and claim storage.
- [x] Rewrite ticket command tests to assert stdout and remove persistence-only
      setup, helpers, and cases.
- [x] Update finalization guidance and the active ticket-workflow spec delta without
      editing the baseline early or rewriting frozen historical records.
- [x] Run `openspec validate --all --strict`, `python3 scripts/validate.py`,
      `python3 -m unittest tests.test_behavior tests.test_ticket`, and the full
      repository test command from `AGENTS.md`.
