# ADR 59 - Worktree commits file under their own identity

Date: 2026-08-23
Status: accepted
Issue: https://github.com/ConnorGriffin/skills/issues/59

## Context

Maintained repositories install one managed reindex block in their shared Git
hooks. A linked worktree fires those hooks from the worktree that received the
Git operation, but the reindex command historically supplied only that path.
Codebase Memory therefore derived a second, path-named project instead of
refreshing the deterministic project established for the worktree lifecycle.
Teardown knew only the deterministic identity, so the duplicate survived after
the worktree was removed.

The hooks also retained the absolute reindex-command path written at enrollment
time. Older enrollments used an unfenced marker and could point at another copy
of the command. Re-running onboarding recognized only the current fenced block,
so it appended a second block instead of repairing the owned legacy one.

## Decision

The reindex command classifies the checkout that fired the hook by physically
comparing Git's absolute Git directory with its common Git directory. A failed
classification stops before either indexing path. A maintained checkout keeps
the established behavior: detached fast indexing with only its repository path,
allowing Codebase Memory to derive the project name.

A linked worktree instead derives the deterministic
`cbm-onboard-v1-<sha256>` identity through the existing lifecycle command and
requests one detached fast index under that exact name. Classification and
identity derivation ignore hook-provided `GIT_DIR` and `GIT_WORK_TREE` values so
the firing checkout remains authoritative. The hook never falls back to a
path-derived name. If classification fails, the binary or detached launcher is
missing, the binary version cannot support the identity lifecycle, or identity
derivation fails, the hook prints one reason and exits successfully so the Git
operation continues.

Onboarding recognizes both its fenced managed block and the older unfenced
marker. It removes the legacy marker and only an immediately following exact,
no-argument invocation of `cbm-reindex.sh`; malformed invocations and unrelated
hook lines remain untouched. The replacement block points at the installation
that ran onboarding, so re-running onboarding from the installed skill repairs
stale enrollments without a new repair interface or repository registry.

## Consequences

- A linked-worktree commit refreshes the same deterministic project that its
  lifecycle owns, and teardown no longer leaves a hook-created path-named twin.
- Maintained repositories retain their existing derived-name behavior and
  compatibility.
- Re-running onboarding repairs one repository at a time while preserving hook
  content the skill does not own.
- Hook refresh remains detached, quiet after launch, and unable to fail a
  commit, merge, or checkout; only refusal to launch is reported.
- Existing duplicate projects are not renamed, migrated, or deleted by this
  change.
