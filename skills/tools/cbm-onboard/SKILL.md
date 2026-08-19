---
name: cbm-onboard
description: Register a Git repository with codebase-memory-mcp, create a managed .cbmignore baseline, install non-clobbering post-commit/post-merge/post-checkout reindex hooks, and run the initial index. Use when asked to index, onboard, register, or keep a repository current in Codebase Memory.
---

# Onboard a repository to Codebase Memory

Use the bundled script to make one maintained checkout one Codebase Memory
project. Never index a directory containing several repositories.

## Requirements

- Install `codebase-memory-mcp` and make its executable available on `PATH`, or
  set `CODEBASE_MEMORY_BIN` to the executable path.
- Resolve the installed `cbm-onboard` skill directory.

## Workflow

1. Resolve the target Git repository. Default to the current repository.
2. Run:

   ```sh
   <cbm-onboard-skill-directory>/scripts/cbm-onboard.sh <repo-path>
   ```

   The script resolves linked worktrees to the maintained checkout, reconciles
   a marked baseline inside `.cbmignore`, preserves custom exclusions, and adds
   a managed reindex block to Git's configured `post-commit`, `post-merge`, and
   `post-checkout` hooks without deleting an existing shell hook. The
   `post-checkout` block carries a `[ "$3" = "1" ] || exit 0` guard so it only
   fires on branch checkouts, not per-file checkouts. It refuses symlink
   targets. A non-shell foreign hook is left unchanged with a warning because
   composing it would be unsafe.

   Pass `--this-checkout` to onboard the current checkout as-is instead of
   resolving to the main worktree — use this for a linked worktree that wants
   its own `.cbmignore` and hooks rather than sharing the control checkout's.

3. Verify the project through the available Codebase Memory MCP interface with
   `index_status` or `list_projects`.
4. Report node and edge counts when available.
5. Tell the user that `.cbmignore` is tracked and should be committed. The Git
   hooks are clone-local, so rerun onboarding after a fresh clone.

The initial index uses full mode. post-commit/post-merge/post-checkout
indexing uses fast mode in a detached process and always exits 0, so a broken
index never fails a commit, merge, or checkout. Re-running onboarding is
idempotent.

Repositories dominated by YAML, prose, or shell may produce a thin graph; say
so rather than refusing to index them.
