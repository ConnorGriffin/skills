---
name: cbm-onboard
description: Register maintained or ephemeral Git checkouts with codebase-memory-mcp, keep long-lived indexes current through non-clobbering Git hooks, and tear down ephemeral indexes by exact deterministic identity. Use when asked to index, onboard, register, remove, or keep a repository current in Codebase Memory, or to resolve which Codebase Memory project belongs to a checkout and make it ready.
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
   through Git's shared hooks directory. When one of those shared hooks fires
   from a linked worktree, it refreshes that worktree in fast mode under the
   same deterministic identity used by the ephemeral lifecycle. It never falls
   back to a path-derived project. Failed checkout classification, a missing
   binary or detached launcher, an unsupported version, or an identity that
   cannot be derived prints one reason and lets the Git operation continue.

   Re-run onboarding from the installed skill directory to repair an enrollment
   whose managed hook points at a stale or foreign installation. Onboarding
   replaces both its current fenced block and the older unfenced
   `codebase-memory-mcp: reindex` marker, preserves every line it does not own,
   and writes one managed block pointing at the installation that invoked it.

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

4. For an automated workflow that must bind one checkout to its exact project
   without touching that checkout, run:

   ```sh
   python3 <cbm-onboard-skill-directory>/scripts/cbm-lifecycle.py ensure <checkout-path>
   ```

   `ensure` is the machine interface: it resolves the supplied checkout as given,
   canonicalizes it physically, derives the same deterministic name the rest of the
   lifecycle uses, and makes exactly that project ready. It asks `index_status` for
   the computed name only, indexes solely on the exact not-found response, and
   re-asks `index_status` afterwards because `index_repository` does not echo the
   root it indexed. It never chooses among `list_projects`, and it writes nothing to
   the repository, its `.cbmignore`, its Git configuration, or its hooks.

   It prints one object on success, `{"root_path", "project", "status"}`, where
   status is `ready` for a project that was already indexed and `indexed` for one it
   just built. A missing, unsupported, or unable-to-respond CLI prints
   `{"status": "unavailable"}` and exits 2, with a bounded actionable reason on
   stderr; it never exposes raw CLI output, environment values, or private source.
   Missing and unsupported binaries remain distinguishable. An active-generation
   conflict says to wait and retry the same checkout, not that a sandbox denied it,
   and never authorizes closing unrelated sessions. Every malformed response or wrong
   identity remains fail-closed with exit 1 and nothing on stdout.

   In a workspace-write sandbox, try `ensure` normally first. If it exits 2 with
   `{"status": "unavailable"}`, confirm that `codebase-memory-mcp` is present and
   reports a supported version. A usable binary can still be unavailable only
   inside the sandbox because its local CLI must secure and write
   `~/.cache/codebase-memory-mcp` and coordinate through a Unix socket under
   `/private/tmp`. Retry the same `ensure` command with escalated permissions and
   make those local-only destinations explicit in the approval rationale; state
   that no repository data is sent to a network destination. Do not request a
   generic permission to “index a private repository,” which hides the actual
   boundary and can be correctly rejected when the destination is unspecified. If
   the diagnostic names an active-generation conflict, wait for it and retry; do not
   frame it as a sandbox denial or close another session.

5. Verify the project through the available Codebase Memory MCP interface with
   `index_status` or `list_projects`.
6. Report node and edge counts when available.
7. Tell the user that `.cbmignore` is tracked and should be committed. The Git
   hooks are clone-local, so rerun onboarding after a fresh clone.

The initial index uses full mode. Post-commit/post-merge/post-checkout indexing
uses fast mode in a detached process and always exits 0, so a broken index never
fails a commit, merge, or checkout. Maintained checkouts keep their derived
project name; linked worktrees use their deterministic lifecycle identity.
Re-running onboarding is idempotent.

Repositories dominated by YAML, prose, or shell may produce a thin graph; say
so rather than refusing to index them.
