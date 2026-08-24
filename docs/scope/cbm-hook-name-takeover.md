# Codebase Memory hook-name takeover

Issue [#110](https://github.com/ConnorGriffin/skills/issues/110).

## Decisions

- Classify issue #110 as code work delivered through a pull request. The fix changes
  `skills/tools/codebase-memory/scripts/install.py` and its tests. `inline`
- Treat the ticket's "any future install or upgrade silently rewrites the hook names"
  premise as refuted for `codebase-memory-mcp` 0.10.8. Its own installer refuses to
  rewrite hook files it does not own and says so. `inline`
- Keep both existing guards intact. ADR 65 settled that a conflicting registration
  stops before any write and leaves manual recovery to the operator; the fix may not
  convert either guard into an automatic repair without superseding that decision.
  `inline`
- Exclude installing, upgrading, or configuring `codebase-memory-mcp` from this work.
  ADR 65's scope doc already lists that as unsupported. `inline`

## Grounding evidence (verified live this session, 2026-08-23)

- External tool version on this machine: `codebase-memory-mcp 0.10.8`, at
  `$HOME/.local/bin/codebase-memory-mcp`. It ships `install`, `update`, and
  `uninstall` subcommands, so its config pass reruns on upgrade.
- `codebase-memory-mcp install --dry-run -n` against the real Claude home reports both
  managed names "would be skipped — the file there is not ours (modified, or written by
  another install), so the rewrite is refused and existing hook entries are left
  untouched". The takeover is not silent at this version.
- A clean external install into a scratch HOME writes three hook files:
  `cbm-code-discovery-gate`, `cbm-session-reminder`, and `cbm-subagent-reminder`. The
  first two collide with the pack's managed names; the third does not.
- The external hook files carry no pack ownership text. Their own headers read
  `# codebase-memory-mcp search augmenter (Claude Code PreToolUse).` and
  `# SessionStart context adapter installed by codebase-memory-mcp.`
- The external tool registers its hooks as `"$HOME/.claude/hooks/<name>"` — a literal
  shell variable inside double quotes — across `PreToolUse` (Grep|Glob),
  `PostToolUse` (Read), `SessionStart` (startup/resume/clear/compact), and
  `SubagentStart`. The ticket recorded a `~/.claude/hooks/...` form, so both forms
  exist across versions.
- Reproduced, external-first ordering, pack installer second: it stops at the first
  guard with `managed target is not owned: <path>/hooks/cbm-code-discovery-gate`,
  exit 1, nothing written.
- Reproduced, foreign hook files moved aside, foreign registrations left in place: the
  pack installer **exits 0 and prints success**, leaving the foreign
  `"$HOME/..."` entries beside its own absolute-path entries. Result: the Grep|Glob
  gate and all four SessionStart reminders are registered twice, plus an orphaned
  `PostToolUse` Read entry and a `SubagentStart` entry the pack neither owns nor
  reports. The registration-conflict guard never fires, because `command_target()`
  expands `~` but not `$HOME`, so the foreign command resolves to a path under the
  process working directory instead of the managed target.
- That silent success contradicts ADR 65's own risk contract, which lists "reporting
  success after partial, conflicting, or non-executable activation" under
  **Must prevent**.
- Real machine state right now: `~/.claude/settings.json` carries pack-only cbm
  registrations and both installed hook files carry the pack ownership marker. The
  manual repair held; the defect is latent here, not active.
- Baseline verification on the ticket branch is green: `python3 scripts/validate.py`
  exits 0, `tests.test_codebase_memory_install` runs 15 tests OK.
- `.agents/` and `.claude/` are gitignored; CI regenerates the vendored copy with the
  skills CLI before its `cmp` gate, so no vendored copy is edited by this work.
- The repo has no `Harden:` line in `CLAUDE.md` repo facts, so the hardening profile
  is unavailable for this ticket.

- Ship an installer option that skips the `settings.json` merge and still installs the
  three managed hook files. A consumer that owns its own settings needs the pack's
  hooks without the pack's registrations; skipping both would leave the installer
  nothing to do. User decision. `inline`
- Correct the collision source: the tilde registrations came from the private
  `dotfiles` repo's `claude/settings.json`, added in `ea8f2f4`, not from the external
  tool. `inline`
- Change `dotfiles` to drop its own Codebase Memory registrations and call the pack
  installer instead, which also means it stops symlinking `claude/settings.json` (the
  installer refuses a symlinked settings file). User decision.
  `→ issue`
- Fix the registration matcher to resolve `$HOME` and `${HOME}`, so a foreign
  registration in that form is visible to the conflict guard instead of silently
  passing. Not a mechanism choice: silent success is on ADR 65's must-prevent list.
  `inline`
- Name `codebase-memory-mcp` and the repair in the not-owned error, rather than
  printing only the path. That is the ticket's actual ask. `inline`
- Keep the fix inside the existing installer interface. No new command, no reclaim
  path, no rename of the managed hook names. `inline`

### Risk contract

- **Must prevent:** reporting success after a partial or conflicting activation;
  clobbering hook registrations the pack does not own; following a symlink at a
  managed path into an external target.
- **Must recover:** every managed-file and settings write stays atomic and converges
  on rerun without duplicate registrations.
- **Accepted failure:** a foreign owner at a managed hook path, or a conflicting
  registration, stops before any write, exits non-zero naming the exact path and the
  likely owner, and leaves repair to the operator.
- **Unsupported:** installing, upgrading, or configuring `codebase-memory-mcp`;
  reclaiming or rewriting another tool's hook files or registrations; concurrent
  mutation of the selected Claude home while the installer runs.
- **Evidence owed:** the skip-settings option installs the managed files and leaves
  `settings.json` byte-identical; a `"$HOME/..."` registration at a managed target is
  detected as a conflict and stops before any write; the not-owned failure names the
  likely owner; existing clean-install, idempotence, and no-write failure behavior is
  unchanged.

Why: the installer writes user configuration at a trust boundary, and the pack is
consumed by machines the author does not control.

Disposition: copy unchanged into the issue #110 work order.

## Spike

Ran against the real registration forms with `HOME` set to the operator's home, comparing today's
`command_target` to the candidate that adds `os.path.expandvars`:

| Registration form | Today | With `expandvars` |
|---|---|---|
| `$HOME_ABS/.claude/hooks/cbm-code-discovery-gate` (an absolute path) | match | match |
| `~/.claude/hooks/cbm-code-discovery-gate` | match | match |
| `"$HOME/.claude/hooks/cbm-code-discovery-gate"` | **no match** | match |
| `${HOME}/.claude/hooks/cbm-code-discovery-gate` | **no match** | match |
| `"$UNSET_VAR/.claude/hooks/cbm-code-discovery-gate"` | no match | no match |

Today's unresolved results are also unstable: `abspath` resolves them against the
process working directory, so the same settings file compares differently depending
on where the installer was invoked from.

## Open questions

- None.

## Spawned tasks

- A `dotfiles` issue to drop its Codebase Memory registrations and call the pack
  installer. Pending.

## Review rounds

- Panel 1 was not cold: agent spawning is disabled in this session, so the order's
  author reviewed it and the pass is recorded as non-independent. Three blockers, all
  `authoring`: the admitted risk contract was never copied into the order; the order
  justified keeping the not-owned message's first line on an assertion that does not
  exist (`test_every_non_regular_or_unowned_managed_node_is_a_no_write_failure` checks
  only the exit status and an unchanged external target); and the list of guards
  surviving `--skip-settings` omitted the hooks-directory symlink check that
  `test_symlinked_hooks_directory_fails_without_writing_through_it` pins. Delta
  re-check caught one fix that silently failed to apply and reapplied it. Injected
  blockers: zero.
- Noted, not blocking: `--skip-settings` ships without a first caller, since `dotfiles`
  will call the installer rather than use the flag. The charter's rule against building
  a seam before the second caller exists would forbid it; the user asked for it on the
  public pack's behalf, so it is a recorded decision rather than an objection.
