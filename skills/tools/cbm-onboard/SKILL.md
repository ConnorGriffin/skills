---
name: cbm-onboard
description: Register maintained or ephemeral Git checkouts with codebase-memory-mcp, keep long-lived indexes current through non-clobbering Git hooks, and tear down ephemeral indexes by exact deterministic identity. Use when asked to index, onboard, register, remove, or keep a repository current in Codebase Memory.
---

# Onboard a repository to Codebase Memory

Use the bundled scripts for either a long-lived maintained checkout or a
short-lived checkout with an explicit onboard/teardown lifecycle. Never index a
directory containing several repositories.

## Requirements

- Install `codebase-memory-mcp` and make its executable available on `PATH`, or
  set `CODEBASE_MEMORY_BIN` to the executable path.
- Ephemeral onboarding and teardown require Codebase Memory MCP v0.10.8 or
  newer. Maintained-checkout onboarding keeps its existing compatibility.
- Resolve the installed `cbm-onboard` skill directory.

## Workflow

1. Resolve the target Git repository. Default to the current repository.
2. For a long-lived maintained checkout, run:

   ```sh
   <cbm-onboard-skill-directory>/scripts/cbm-onboard.sh <repo-path>
   ```

   The script resolves linked worktrees to the maintained checkout, reconciles
   a marked baseline inside `.cbmignore`, preserves custom exclusions, and adds
   a managed reindex block to Git's configured `post-commit`, `post-merge`, and
   `post-checkout` hooks without deleting an existing shell hook. The
   `post-checkout` block carries a `[ "$3" = "1" ] || exit 0` guard so it only
   fires on branch checkouts, not per-file checkouts. A symlinked hook is
   followed to the file it resolves to, which is what a dotfiles-managed hooks
   directory needs, and the write lands in whatever repo owns that file. A
   symlink with no regular-file target is refused, and a `.cbmignore` symlink
   is refused outright. A non-shell foreign hook is left unchanged with a
   warning because composing it would be unsafe.

   Linked worktrees share the control checkout's Git hooks; they cannot have
   independent hooks. Pass `--this-checkout` only to select the supplied
   checkout's `.cbmignore` and initial index. Hook installation still resolves
   through Git's shared hooks directory.

3. For an ephemeral checkout, run the complete lifecycle:

   ```sh
   <cbm-onboard-skill-directory>/scripts/cbm-onboard.sh \
     --no-hooks --this-checkout <worktree-path>
   # Use the worktree, then:
   <cbm-onboard-skill-directory>/scripts/cbm-teardown.sh <worktree-path>
   ```

   `--no-hooks` reconciles only the selected checkout's `.cbmignore`, performs a
   full index under a deterministic name derived from its canonical physical
   path, and never enters hook resolution or installation. `--this-checkout` is
   load-bearing for a linked worktree: without it, onboarding deliberately
   resolves to the main checkout, matching maintained-checkout behavior.

   Teardown recomputes that exact identity and calls `delete_project` directly;
   it never scans projects, edits repository files or Git configuration, or
   removes hooks or worktrees. Both a successful deletion and an exact
   already-missing response are success, so teardown is safe to repeat.

4. Verify the project through the available Codebase Memory MCP interface with
   `index_status` or `list_projects`.
5. Report node and edge counts when available.
6. Tell the user that `.cbmignore` is tracked and should be committed. The Git
   hooks are clone-local, so rerun onboarding after a fresh clone.

The initial index uses full mode. Maintained-checkout post-commit/post-merge/post-checkout
indexing uses fast mode in a detached process and always exits 0, so a broken
index never fails a commit, merge, or checkout. Re-running onboarding is
idempotent.

Repositories dominated by YAML, prose, or shell may produce a thin graph; say
so rather than refusing to index them.
