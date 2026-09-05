# Generated facts

Captured command output, unedited. The source inventory search includes history; inventory.md classifies its scope.

## git rev-parse origin/main

```text
697b44ab8369b3a4cfae2c0595ad7ef98ae61ec9
```

Exit: 0

## /opt/homebrew/bin/python3 --version

```text
Python 3.14.7
```

Exit: 0

## openspec --version

```text
1.11.0
```

Exit: 0

## rg --sort path -l 'When the reader agrees|complete session|stop-at-pull-request|AskUserQuestion|Session fit|unavailable|thirty to sixty|real devices|disable-model-invocation|git checkout|resume the original|outside the repo' skills profile output-styles docs README.md -g '*.md' -g '*.yaml' -g '*.py'

```text
skills/drivers/orchestrate/SKILL.md
skills/drivers/orchestrate/agents/openai.yaml
skills/drivers/orchestrate/references/review-routing.md
skills/drivers/ticket/SKILL.md
skills/drivers/ticket/agents/openai.yaml
skills/drivers/ticket/references/coordinator-mode.md
skills/drivers/ticket/templates/work-order.md
skills/drivers/ticket/verbs/start.md
skills/drivers/ticket/verbs/triage.md
skills/drivers/ui-craft/SKILL.md
skills/drivers/ui-craft/reference/critique.md
skills/drivers/ui-craft/reference/document.md
skills/drivers/ui-craft/reference/init.md
skills/drivers/ui-craft/reference/lock.md
skills/drivers/ui-craft/reference/polish.md
skills/tools/cbm-onboard/SKILL.md
skills/tools/cbm-onboard/scripts/cbm-lifecycle.py
skills/tools/clean/SKILL.md
skills/tools/code-review/SKILL.md
skills/tools/codebase-design/references/DESIGN-IT-TWICE.md
skills/tools/codebase-memory/reminder.md
skills/tools/preflight/SKILL.md
skills/tools/say-less/SKILL.md
skills/tools/writing-for-agents/SKILL.md
skills/tools/writing-for-agents/references/doctor.md
skills/workflows/scope/SKILL.md
skills/workflows/scope/references/interview.md
profile/base.md
docs/epic-flow.md
docs/research/openspec-cli.md
docs/research/openspec-work-order-authority.md
docs/scope/255-compaction-proof-worker-orders.md
docs/scope/293-astra-workflow-conflicts.md
docs/scope/78-claims-sandbox-docs.md
docs/scope/cbm-hook-name-takeover.md
docs/scope/nested-adapter-dispatch.md
```

Exit: 0

## rg -n 'def unavailable|def envelope_or_unavailable|stderr=subprocess.DEVNULL' skills/tools/cbm-onboard/scripts/cbm-lifecycle.py

```text
37:        stderr=subprocess.DEVNULL,
110:def unavailable() -> "NoReturn":
118:def envelope_or_unavailable(code: int, raw: str) -> tuple[dict, object]:
142:        stderr=subprocess.DEVNULL,
155:        stderr=subprocess.DEVNULL,
```

Exit: 0

## rg -n 'Test:|python3 scripts/validate|tests.test_|skills/drivers/orchestrate/scripts' AGENTS.md

```text
15:- Test: `python3 scripts/validate.py && python3 -m unittest tests.test_behavior
16:  tests.test_pr_body tests.test_pr_body_gate tests.test_pr_body_bench
17:  tests.test_ticket tests.test_reviewer_memory tests.test_codebase_memory_install tests.test_check_dco
18:  tests.test_ci_changed_paths tests.test_site_build && python3 -m py_compile
20:  skills/drivers/orchestrate/scripts/worker_lifecycle.py
21:  skills/drivers/orchestrate/scripts/codex-worker.py
22:  skills/drivers/orchestrate/scripts/claude-worker.py`. Requires Python 3.10
```

Exit: 0

## Disposable clean probe

The triage probe initialized a disposable Git repository, committed baseline content, added an operator unstaged edit, added a cleaner edit, and compared bytes after whole-file checkout versus restoring captured pre-clean content. The temporary repository was removed.

```text
whole-file checkout preserves pre-clean bytes: False
restore captured pre-clean bytes preserves operator edit: True
```

This probes the proposed preservation mechanism, not the yet-unwritten skill revision. Implementation still owes the staged-and-unstaged failure replay.

## Current-session metadata probe

An executed local read verified that CODEX_THREAD_ID matches this task, its matching rollout session_meta carries the same identity, and the latest turn_context reports model gpt-6-astra and effort medium. Only these non-sensitive fields were inspected for admission; no private transcript is attached. This is current-session evidence, not a promise that future hosts expose the same metadata. The design names the missing-source fallback explicitly.

The worker adapter probe returned a known session-bound headroom and a successful one-word response under read-only dispatch. That establishes this host's existing dispatch capability, not Astra's reviewer eligibility.
