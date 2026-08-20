# Scope: Codebase Memory worktree lifecycle

Issue: ConnorGriffin/skills#66

## Decisions

- Classify the ticket as `code`: it lands as one pull request in this repository.
  Why: the deliverables are public shell interfaces, their tests, and documentation.
  Disposition: inline.
- Keep the order flat rather than chunked.
  Why: one repository and one trust boundary are involved; multiple related artifacts
  fire only one slicing trait, closest to the flat anchor.
  Disposition: inline.
- Preserve default onboarding for maintained checkouts; add a hookless mode for
  ephemeral worktrees.
  Why: PR #12 established the long-lived hook behavior, while the issue-66
  reproduction proved that linked worktrees share the control checkout's hooks.
  Disposition: inline.
- Both lifecycle scripts must reject unknown options and excess positional arguments
  before any repository or graph mutation.
  Why: the current onboarding parser treats a misspelled safety flag as a path and can
  silently fall through to default hook installation.
  Disposition: inline.
- Do not promise a generic secret-exposure control for this change.
  Why: no secret-bearing input is part of the interface; exact-target deletion,
  repository non-mutation, and fail-closed external responses are the concrete risks.
  Disposition: inline.
- Review depth is Full.
  Why: teardown deletes graph state, and selecting the wrong Codebase Memory project
  would cross the ticket's destructive boundary even though the graph is rebuildable.
  Disposition: inline.
- Require Codebase Memory MCP v0.10.8 or newer for the ephemeral lifecycle and
  assign its project name explicitly during onboarding.
  Why: v0.10.8 supports `index_repository.name`; an explicit versioned SHA-256
  identity derived from the canonical physical checkout path lets teardown delete
  directly by name without an unreliable registry lookup or a list/delete race.
  Disposition: inline.
- Keep default maintained-checkout onboarding on its existing derived-name behavior;
  the explicit identity contract belongs to hookless ephemeral onboarding and its
  paired teardown command.
  Why: renaming existing maintained-checkout projects would create duplicate stale
  graphs and is outside issue 66.
  Disposition: inline.
- Reject `CBM_SKIP_INDEX=1` in hookless mode before repository mutation, while
  preserving it for default maintained-checkout onboarding.
  Why: teardown can exist only after hookless onboarding establishes the named graph;
  silently skipping that operation would make the lifecycle contract fictitious.
  Disposition: inline.
- Accept only a stable three-part `codebase-memory-mcp MAJOR.MINOR.PATCH` banner and
  compare its numeric tuple with `(0, 10, 8)`.
  Why: numeric components handle later patches/minors/majors without lexicographic
  errors; rejecting prefixes, suffixes, and prereleases avoids inventing compatibility.
  Disposition: inline.
- Support spaces in canonical checkout paths but reject newline-bearing paths before
  mutation or deletion.
  Why: Git reports the top level through a line-oriented interface whose terminating
  newline is ambiguous with path bytes under POSIX command substitution; fail-closed
  rejection is honest, while pretending to hash the original bytes is not.
  Disposition: inline.

### Risk contract

- **Must prevent:** deleting a project without the deterministic identity used by the
  matching hookless index operation; writing Git hooks in hookless mode; modifying
  repository files or Git hooks during teardown; silent success after malformed or
  failed external tool responses; loss of authoritative repository data.
- **Must recover:** none automatically. External tool failures stop nonzero and leave
  manual retry to the caller.
- **Accepted failure:** hookless onboarding may reconcile the target `.cbmignore`
  before a failed initial index, matching the existing operation order. A race that
  replaces rebuildable graph data under the same already-established project identity
  is recoverable by reindexing and is not promised atomic recovery.
- **Unsupported:** Codebase Memory versions older than v0.10.8, non-Git targets,
  malformed external responses, and teardown of a project whose identity was not
  established by the matching hookless onboarding operation.
- **Evidence owed:** public-interface tests for exact worktree indexing, zero hook
  writes, strict argument rejection before mutation, identity handoff, exact-name
  deletion, idempotent repeat teardown, fail-closed response parsing, repository
  non-mutation, and the repository's validation/CI gates.

Why: the graph is derived and rebuildable, but deletion identity and control-checkout
isolation must be mechanically enforced.

Disposition: inline in the eventual work order after the identity interface settles.

## Open questions

- None.

## Generated facts

- `codebase-memory-mcp --version` → `codebase-memory-mcp 0.8.1`.
- `codebase-memory-mcp cli list_projects '{}'` parsed through Python → 1,009 records,
  1,009 empty `root_path` fields, zero nonempty `root_path` fields.
- `codebase-memory-mcp cli delete_project
  '{"project":"__issue66_preflight_nonexistent__"}'` →
  `{"project":"__issue66_preflight_nonexistent__","status":"not_found"}`.
- GitHub's official latest-release API on 2026-08-20 → `v0.10.8`, published
  2026-08-19. Its upstream tool schema adds an optional explicit `name` to
  `index_repository`; deletion remains name-based.
- The local executable was upgraded to v0.10.8. With stdout/stderr captured
  separately, a disposable explicit-name cycle returned `indexed`/`isError=false`
  at exit 0, then `deleted`/`isError=false` at exit 0; repeat deletion returned
  `not_found`/`isError=true` at exit 1. Graph commands wrote allocator info to stderr.
- Disposable linked-worktree reproduction with current `cbm-onboard.sh
  --this-checkout` → `.cbmignore` created in the linked worktree and all three managed
  hooks installed in the control checkout's shared `.git/hooks`.
- `python3 --version` → `Python 3.9.6`; the repository validator passes, while the
  documented full unittest command fails before issue-66 work because existing tests
  require `TemporaryDirectory(ignore_cleanup_errors=True)`. CI selects Python 3.12.
- `uv python list --only-installed` → managed Python 3.12.13 is available locally;
  `uv run --python 3.12 python ...` ran the validator plus 212 tests successfully
  with 23 expected skips, matching CI's Python version line.
- `.github/workflows/validate.yml` additionally runs `tests.test_ticket`; the work
  order's local gate includes it rather than deferring that coverage to GitHub.

## Review rounds

- Round 1: five blocking authoring defects, zero injected defects.
  - Path-to-project deletion relied on `root_path` values the installed CLI does not
    supply.
  - The deletion response/identity contract was not executable from the draft.
  - The absolute list-then-delete path invariant was non-atomic across the external
    process boundary.
  - Safety-sensitive argument parsing did not require fail-closed rejection.
  - The local green-before-PR verification gate named no runnable Python 3.12+
    environment.
  - A generic secret-exposure promise was also removed as an unearned control; this
    was fixed without expanding the build.
- Round 2: four blocking authoring gaps, zero injected defects.
  - Added exact stdout/stderr/exit evidence for the v0.10.8 lifecycle.
  - Settled `CBM_SKIP_INDEX`: preserved for default mode, rejected pre-mutation for
    hookless mode.
  - Fixed a strict stable-version grammar and numeric comparison cases.
  - Added physical alias and spaces identity evidence, plus pre-mutation rejection for
    newline-bearing paths that cannot cross Git's line-oriented shell interface safely.
- Round 3: countersigned with no remaining blocking objections after attaching the
  exact v0.10.8 command/output/exit-code appendix.

## Spawned tasks

- None. Cold review agents produced read-only findings; no implementation or follow-up
  ticket was delegated.
