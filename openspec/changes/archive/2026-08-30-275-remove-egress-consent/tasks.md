# Tasks

- [x] Retire `### Requirement: Bounded worker-egress consent` in the
      `ticket-workflow` spec delta and add a requirement scoped to only the
      coordinator-owned review handoff.
- [x] Retire `### Requirement: Orchestration authorization and isolation` in
      the `planning-and-review` spec delta and add a requirement scoped to
      adapter isolation plus the coordinator-owned review handoff.
- [x] Record the reversal of ADR 194 as `## ADR 275` in this change's
      `design.md`.
- [x] Run `python3 scripts/validate.py`.
- [x] Run `python3 -m unittest tests.test_behavior tests.test_pr_body
      tests.test_pr_body_gate tests.test_pr_body_bench tests.test_ticket
      tests.test_reviewer_memory tests.test_codebase_memory_install
      tests.test_check_dco tests.test_ci_changed_paths tests.test_site_build`.
- [x] Run `./docs/scope/275-probes/no_consent_framing.sh`.
- [x] Run `openspec validate --all --strict`.
