# Closed source inventory

Only paths listed for a chunk are editable by that chunk. Inclusion permits only the changes specified by tasks.md and dispositions.md; it is not permission for general cleanup. Existing archived changes, legacy ADRs, transcript examples and generated/vendored copies are historical evidence, not live consumers to rewrite.

## Chunk 1

- `profile/base.md`
- `output-styles/say-less.md`
- `skills/tools/say-less/SKILL.md`
- `skills/tools/say-less/reminder.md`
- `skills/workflows/scope/SKILL.md`
- `skills/workflows/scope/references/interview.md`
- `skills/workflows/scope/references/interview-format.lock.md`
- `skills/workflows/review/SKILL.md`
- `skills/tools/clean/SKILL.md`
- `skills/tools/tdd/SKILL.md`
- `skills/tools/preflight/SKILL.md`
- `skills/tools/plan-review/SKILL.md`
- `skills/tools/code-review/SKILL.md`
- `skills/tools/persona-review/SKILL.md`
- `skills/tools/reviewer-memory/SKILL.md`
- `skills/tools/cbm-onboard/SKILL.md`
- `skills/tools/cbm-onboard/scripts/cbm-lifecycle.py`
- `skills/tools/codebase-memory/SKILL.md`
- `skills/tools/codebase-memory/reminder.md`
- `skills/tools/writing-for-agents/SKILL.md`
- `skills/tools/writing-for-agents/agents/openai.yaml`
- `tests/test_behavior.py`

- `skills/tools/writing-for-agents/references/doctor.md`

## Chunk 2

- `profile/CHARTER.md`
- `README.md`
- `skills/drivers/ticket/SKILL.md`
- `skills/drivers/ticket/verbs/triage.md`
- `skills/drivers/ticket/verbs/start.md`
- `skills/drivers/ticket/verbs/revise.md`
- `skills/drivers/ticket/templates/work-order.md`
- `skills/drivers/ticket/references/coordinator-mode.md`
- `skills/drivers/ticket/references/review-depth.md`
- `skills/drivers/orchestrate/SKILL.md`
- `skills/drivers/orchestrate/references/routing-table.md`
- `skills/drivers/orchestrate/references/review-routing.md`
- `skills/drivers/orchestrate/references/dispatch-codex.md`
- `skills/drivers/epic/SKILL.md`
- `skills/drivers/implement/SKILL.md`
- `skills/drivers/ui-craft/SKILL.md`
- `skills/drivers/ui-craft/reference/revise.md`
- `skills/drivers/ui-craft/reference/behavior-sweep.md`
- `skills/drivers/ui-craft/reference/init.md`
- `skills/drivers/ui-craft/reference/document.md`
- `skills/drivers/ui-craft/reference/polish.md`
- `skills/tools/domain-modeling/SKILL.md`
- `skills/tools/domain-modeling/references/ADR-FORMAT.md`
- `skills/tools/pr-body/SKILL.md`
- `skills/tools/pr-body/references/rubric.md`
- `docs/overlay.md`
- `docs/orchestrate-spec.md`
- `tests/test_ticket.py`

- `docs/epic-flow.md`
- `skills/drivers/ticket/agents/openai.yaml`
- `skills/drivers/orchestrate/agents/openai.yaml`

## Coordinator only

- `openspec/changes/293-workflow-continuation/tasks.md` (verified checkbox bookkeeping only after lock)
- `openspec/changes/293-workflow-continuation/replay-results.md` (new aggregate evidence record)

## Inventory evidence

`generated-facts.md` contains the repository-wide term search. Matches outside the allowlist are reviewed as historical/source evidence or unchanged contracts; any newly discovered live consumer requiring a semantic edit requires a new lock rather than an escape clause.
