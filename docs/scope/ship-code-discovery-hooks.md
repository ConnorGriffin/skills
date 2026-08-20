# Ship code-discovery hooks

## Decisions

- Classify issue #65 as code work delivered through pull requests. The portable pack and its private dotfiles consumer both require tracked changes. `inline`
- Treat the public pack as the canonical source for the code-discovery skill, hook executables, settings fragment, and standing instruction. A clean consumer cannot depend on private dotfiles. `→ ADR` discharged by [`docs/adr/adr-65-code-discovery-bundle.md`](../adr/adr-65-code-discovery-bundle.md).
- Preserve existing hook registrations while installing the discovery hooks. The issue explicitly forbids clobbering consumer configuration. `inline`
- Limit issue #65 to the canonical public-pack change and file a linked `dotfiles` migration issue. Each repository keeps one ticket, branch, worktree, and pull request while the dependency remains explicit. `→ issue` discharged by [ConnorGriffin/dotfiles#73](https://github.com/ConnorGriffin/dotfiles/issues/73).
- Expose code-discovery activation as one installer command bundled inside the `codebase-memory` skill. The interface hides hook placement and settings merging so every consumer uses one implementation. `→ ADR` discharged by [`docs/adr/adr-65-code-discovery-bundle.md`](../adr/adr-65-code-discovery-bundle.md).
- Fail before writing anything when settings are malformed or an existing discovery registration conflicts with the canonical registration. Report the exact conflict and leave manual recovery to the operator. `inline`
- Treat concurrent mutation of the selected Claude home while installation runs as unsupported. The installer validates the state it observes, but does not add descriptor-anchored race machinery for another process replacing paths mid-run. `inline`

### Risk contract

- **Must prevent:** from the filesystem state observed during pre-write validation, clobbering unrelated hook registrations or nodes; exposing secrets or private machine paths; reporting success after partial, conflicting, or non-executable activation; corrupting an existing settings file or following an already-present managed-path symlink into an external target.
- **Must recover:** every managed-file and settings update is atomic; an interrupted installation must leave each destination at its complete old or new bytes, ignore unfinished temporary files, keep the original settings valid, and converge on rerun without duplicate registrations.
- **Accepted failure:** malformed settings; a symlink or other non-regular settings node; a conflicting discovery registration; a hooks path that exists but is not a real, non-symlink directory; or an existing unowned/non-regular node at a managed hook-directory path stops before any write, exits non-zero with the exact conflict, and requires the operator to repair the input before retrying.
- **Unsupported:** concurrent mutation of the selected Claude home while installation runs; configuration formats other than Claude Code's JSON settings schema; installing or configuring the `codebase-memory-mcp` server itself; migrating a consumer's private configuration within issue #65.
- **Evidence owed:** public-interface tests prove clean installation; preservation of unrelated existing hooks; idempotent reruns; exact registration deduplication; atomic managed-file and settings replacement; convergence from complete managed files with settings absent and with unfinished temporary files present; no-write malformed-settings, non-regular-settings-node, registration-conflict, symlinked-hooks-directory, unmarked-file, leaf-symlink, broken-symlink, directory, and FIFO failures with external targets unchanged; shell-safe executable registrations for caller-supplied Claude-home paths including whitespace; executable hook installation; and discovery instructions available from the public pack.

Why: the installer writes user configuration at a trust boundary, but failures are locally visible and manually recoverable when the original file is preserved.

Disposition: copy unchanged into the issue #65 work order.

## Open questions

- None.

## Spawned tasks

- [ConnorGriffin/dotfiles#73](https://github.com/ConnorGriffin/dotfiles/issues/73) migrates the private consumer after issue #65 lands.

## Review rounds

- Panel 1: five unique blocking defects, all `authoring` — unnamed migrated behavior/canonical artifacts, contradictory duplicated discovery policy, stale private tool facts, and incomplete managed-node safety. The first fix verification found one remaining `authoring` path-quoting defect and one `injected` risk-ledger drift defect.
- Panel 1 verification after the clean rewrite: zero blockers; the injected count returned to zero, so the rewrite-clean signal did not fire.
- Panel 2 fresh pass: two `authoring` blockers — managed files were not atomically recoverable, and a symlinked hooks directory could redirect writes. Same-panel verification after the fix: zero blockers.
- Panel 3 fresh pass: one `authoring` blocker — preventing a concurrent hooks-directory replacement required descriptor-anchored race machinery. Scope reopened; the user classified concurrent Claude-home mutation during installation as unsupported. Same-panel verification: zero blockers and countersigned.
