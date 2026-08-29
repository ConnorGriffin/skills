# Tasks

- [x] Replace epic-owned delegated execution, research-worker dispatch, wave, and
  adapter lifecycle prose with a human-dispatch boundary and attended child flow.
- [x] Define the child issue's draft order → operator-invoked ticket triage → fenced
  executable lock handoff without adding a second execution entry.
- [x] Pin each child draft to a pushed remote epic-plan branch/commit and make
  ticket triage fail closed when that branch no longer resolves to the pinned commit.
- [x] Permit only one in-flight epic child; require human merge and planning-branch
  advancement from the updated default branch before handing off the next child.
- [x] Add the three-child default and require a `design.md` justification before
  filing a fourth or later child.
- [x] State that epic planning artifacts ship with implementation and that the
  coordinator never opens a planning-only pull request.
- [x] Replace ticket's docs-only epic-amendment prerequisite with a parent-change
  amendment committed in the child worktree and carried by implementation.
- [x] Align the operator guide, README summary, and Epic agent metadata with the
  new boundary.
- [x] Replace dispatch-presence tests with regression tests for the new rules and
  removal of epic-owned dispatch paths across skill, guide, README, and metadata.
- [x] Run `python3 scripts/validate.py && python3 -m unittest tests.test_behavior tests.test_pr_body tests.test_pr_body_gate tests.test_pr_body_bench tests.test_ticket tests.test_codebase_memory_install tests.test_check_dco tests.test_ci_changed_paths tests.test_site_build && python3 -m py_compile skills/tools/codebase-memory/scripts/install.py scripts/ci_changed_paths.py skills/drivers/orchestrate/scripts/worker_lifecycle.py skills/drivers/orchestrate/scripts/codex-worker.py skills/drivers/orchestrate/scripts/claude-worker.py`.
