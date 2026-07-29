---
name: cbm-onboard
description: Register a Git repository with codebase-memory-mcp, create a managed .cbmignore baseline, install a non-clobbering post-commit reindex hook, and run the initial index. Use when asked to index, onboard, register, or keep a repository current in Codebase Memory.
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
   a managed reindex block to Git's configured `post-commit` hook without
   deleting an existing shell hook. It refuses symlink targets. A non-shell
   foreign hook is left unchanged with a warning because composing it would be
   unsafe.

3. Verify the project through the available Codebase Memory MCP interface with
   `index_status` or `list_projects`.
4. Report node and edge counts when available.
5. Tell the user that `.cbmignore` is tracked and should be committed. The Git
   hook is clone-local, so rerun onboarding after a fresh clone.

The initial index uses full mode. Post-commit indexing uses fast mode in a
detached process. Re-running onboarding is idempotent.

Repositories dominated by YAML, prose, or shell may produce a thin graph; say
so rather than refusing to index them.
