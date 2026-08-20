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

### Risk contract

- **Must prevent:** deleting a project without an identity established by the matching
  successful index operation; writing Git hooks in hookless mode; modifying repository
  files or Git hooks during teardown; silent success after malformed or failed external
  tool responses; loss of authoritative repository data.
- **Must recover:** none automatically. External tool failures stop nonzero and leave
  manual retry to the caller.
- **Accepted failure:** hookless onboarding may reconcile the target `.cbmignore`
  before a failed initial index, matching the existing operation order. A race that
  replaces rebuildable graph data under the same already-established project identity
  is recoverable by reindexing and is not promised atomic recovery.
- **Unsupported:** non-Git targets, malformed external responses, and teardown of a
  project whose identity was not established by the matching onboarding operation.
- **Evidence owed:** public-interface tests for exact worktree indexing, zero hook
  writes, strict argument rejection before mutation, identity handoff, exact-name
  deletion, idempotent repeat teardown, fail-closed response parsing, repository
  non-mutation, and the repository's validation/CI gates.

Why: the graph is derived and rebuildable, but deletion identity and control-checkout
isolation must be mechanically enforced.

Disposition: inline in the eventual work order after the identity interface settles.

## Open questions

- How does onboarding hand the exact Codebase Memory project identity to teardown?
  The installed v0.8.1 CLI cannot safely rediscover it from a path: its
  `list_projects` response currently contains 1,009 records and every `root_path` is
  empty. The upstream v0.10.8 interface can accept an explicit project name at index
  time, but relying on it establishes a new minimum-version contract. Candidate
  interfaces are: require v0.10.8+ and assign a stable name; persist the successful
  index response's name in worktree-private Git metadata; or make the harness pass the
  returned name explicitly to teardown.

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
- Disposable linked-worktree reproduction with current `cbm-onboard.sh
  --this-checkout` → `.cbmignore` created in the linked worktree and all three managed
  hooks installed in the control checkout's shared `.git/hooks`.
- `python3 --version` → `Python 3.9.6`; the repository validator passes, while the
  documented full unittest command fails before issue-66 work because existing tests
  require `TemporaryDirectory(ignore_cleanup_errors=True)`. CI selects Python 3.12.

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

## Spawned tasks

- None. Cold review agents produced read-only findings; no implementation or follow-up
  ticket was delegated.
