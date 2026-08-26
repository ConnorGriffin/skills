# skills

Connor Griffin's public, portable skill pack for coding agents. Skills live under
`skills/`, one directory each, consumed by the standard `skills` CLI and read
interactively by Claude Code and Codex.

profile: reviewed
ui-surfaces: none

## Repo facts

- Install: none for the pack itself; Python 3 standard library only. The browser
  driver installs its own deps under `skills/tools/drive-local-webapp` (`npm ci`
  plus `npx playwright install chromium`).
- Test: `python3 scripts/validate.py && python3 -m unittest tests.test_behavior
  tests.test_pr_body tests.test_pr_body_gate tests.test_pr_body_bench
  tests.test_ticket tests.test_codebase_memory_install tests.test_check_dco
  tests.test_ci_changed_paths && python3 -m py_compile
  skills/tools/codebase-memory/scripts/install.py scripts/ci_changed_paths.py
  skills/drivers/orchestrate/scripts/worker_lifecycle.py
  skills/drivers/orchestrate/scripts/codex-worker.py
  skills/drivers/orchestrate/scripts/claude-worker.py`. Requires Python 3.10
  or newer (the worker scripts use `X | None` union syntax).
- Dev: no app to run. To exercise a skill, install the pack into a scratch
  directory with `npx skills add . --skill '<name>' --copy --yes`.
- Source: `skills/<category>/<name>/` (SKILL.md plus its own `references/`,
  `reference/`, and `scripts/`), with `profile/`, `output-styles/`, `hooks/`, and
  `docs/` alongside.
- Tests: `tests/`. `scripts/validate.py` is the structural validator and is part
  of the gate, not a lint.

## Hazards

- Never commit without `Signed-off-by:` — `scripts/check_dco.py` runs on every
  pull request and a missing trailer fails CI, so the commit cannot be fixed
  after the fact without a rewrite.
- Never move, retag, or delete a release tag. Published releases are immutable
  history that installers may pin by any ref.
- Never edit `.agents/skills/` or `.claude/skills/` — those are vendored, pinned
  copies of skills this repo itself authors under `skills/`. Edit the source and
  let the pin be bumped deliberately; editing the copy forks the pack against
  itself.
- Never publish real colleague identities. `persona-review` mines real people's
  GitHub activity into persona profiles; the profiles belong in a private data
  repo, and nothing identifying a real colleague may land in this public repo.
- Never add a third-party dependency to the pack. The pack must install and run
  from a stock Python 3 and Node 20 with no package manager step, which is what
  makes it portable across agents.
- Never run the pack's own scripts against a real project checkout while testing
  them. `skills/tools/cbm-onboard/scripts/cbm-onboard.sh` writes `.cbmignore` and
  installs git hooks, and `skills/tools/spin-worktree/scripts/spin-worktree.py`
  creates worktrees and branches; both mutate whatever repo they are aimed at.
