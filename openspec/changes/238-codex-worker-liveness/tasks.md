# Tasks

- [ ] Add live Codex `thread.started` observation through the shared lifecycle's
  existing adapter-supplied parser without changing Claude transport or terminal
  output validation.
- [ ] Persist the exact session ID atomically while lifecycle remains running, with
  schema and CLI-level buffered-worker regression coverage.
- [ ] Replace ambiguous CPU/newest-rollout liveness guidance with exact-session,
  progress-based stop preconditions and pin the prose contract in tests.
- [ ] Run `python3 scripts/validate.py`, the complete named unittest command from
  `AGENTS.md`, and the three named `py_compile` checks for worker scripts.
