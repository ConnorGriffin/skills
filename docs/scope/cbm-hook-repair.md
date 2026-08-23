# Scope: cbm-onboard reindex hooks

Issue: ConnorGriffin/skills#59

## Decisions

- Classify the ticket as `code`: it lands as one pull request in this repository.
  Why: the deliverable is the pack's hook installer, its reindex command, their tests,
  and the skill page.
  Disposition: inline.
- Route scope to interview mode.
  Why: grounding settled the facts; what remains is three choices about behavior that
  only the operator can make.
  Disposition: inline.

- A commit inside a linked worktree refreshes that worktree's own graph under the
  identity the ticket bound it to, never a path-derived one.
  Why: agents read the worktree they are working in, and PR #12's rule that the firing
  checkout is the one that matters still holds; only the name it is filed under was wrong.
  Disposition: inline.
- Onboarding gains a repair that rewrites the managed block of hooks it already installed.
  Why: a hook pointing at a script that no longer exists fails silently, so nothing
  reports which repositories stopped refreshing.
  Disposition: inline.
- The dotfiles fork of this tooling is retired rather than kept in parallel.
  Why: one behavior with two implementations diverges, and the machines actually run the
  dotfiles copy, so the pack fix is inert until the fork goes.
  Disposition: issue (ConnorGriffin/dotfiles).
- dotfiles issue 73 does not already cover the retirement.
  Why: it moves the `codebase-memory` skill bundle to the public pack and is blocked by
  skills#65; the private `scripts/cbm-onboard.sh`, `scripts/cbm-reindex.sh`, and
  `tests/cbm-onboard.test.sh` are outside it.
  Disposition: inline.

- Skipping the refresh prints one line saying why; it never blocks the commit.
  Why: silent skipping is the failure that hid dead hooks in the first place, and a line
  of output costs a commit nothing.
  Disposition: inline.
- Repair is not a new mode. Re-running onboarding already rewrites its managed block, so
  the work is teaching it to recognize the legacy unfenced marker as its own.
  Why: the live hooks carry `# codebase-memory-mcp: reindex on commit (managed by
  cbm-onboard - cbm-reindex)` rather than the pack's fence, so re-running today stacks a
  second block instead of replacing it. No registry of enrolled repositories is invented.
  Disposition: inline.
- Repair takes over any block this tooling owns, legacy marker included, one repository
  per run.
  Why: it is what retires the fork on the machines, and it needs no new interface.
  Disposition: inline.

### Risk contract

- **Must prevent:** deleting or truncating a hook the tooling does not own; leaving a
  repository with two reindex blocks; filing a checkout's graph under any name other
  than its deterministic identity; silent success after a failed or malformed index call.
- **Must recover:** none automatically.
- **Accepted failure:** an unresolvable identity, a missing binary, or a too-old binary
  skips the refresh with one line on stderr and exits 0, so the commit still lands.
- **Unsupported:** non-Git targets, foreign non-shell hooks, and Codebase Memory older
  than the version the ephemeral lifecycle already requires.
- **Evidence owed:** a commit in a linked worktree files under the deterministic name and
  creates no path-derived project; a commit in a maintained checkout keeps its existing
  derived name; re-running onboarding over a legacy-marker hook leaves exactly one block
  and repoints it; a skipped refresh says so and still exits 0; a foreign hook is still
  left unchanged.

Why: the tooling writes into other repositories' hooks and into shared graph state, and
both wrong-name filing and hook clobbering are silent until something else breaks.

Disposition: inline in the work order.

## Grounded facts

- The pack's `skills/tools/cbm-onboard/scripts/cbm-reindex.sh` has no worktree guard at
  all: it resolves `$PWD`'s toplevel and calls `index_repository` with `repo_path` only,
  so Codebase Memory derives a path-named project.
- Hooks install into `git-common-dir/hooks` (or `core.hooksPath`), which linked
  worktrees share, so a commit inside a worktree fires them with the worktree as `$PWD`.
- Every enrolled repository checked on this machine (`skills`, `dotfiles`, `brewgen`)
  calls `<dotfiles>/scripts/cbm-reindex.sh`, not the
  pack's copy. The two have forked; only the dotfiles copy has a guard, and it matches
  `*/.claude/worktrees/*` and `*-wt`, never a worktree root outside those two shapes.
- `the installed skill directory` is a symlink to the pack's source directory, so hooks
  written against the installed path survive a move inside the source repository.
- PR #12 (5a8ff31) deliberately made the hook reindex the checkout that fired it rather
  than the main root.
- `docs/scope/cbm-worktree-lifecycle.md` (issue 66) settled that maintained-checkout
  onboarding keeps derived names and that the deterministic identity belongs to the
  hookless ephemeral lifecycle.
- A sweep on 2026-08-23 deleted 34 projects, 30 of them orphans whose checkout was gone.
- The repository declares no `Harden:` line, so the ticket runs the default workflow.

## Open questions

- None. The frontier is empty.

## Spawned tasks

- Retire the dotfiles fork of cbm-onboard/cbm-reindex and repoint enrolled hooks at the
  pack: filed as ConnorGriffin/dotfiles#76, blocked by this ticket. Disposition discharged.

## Generated facts

- `git --version` here is 2.50.1 (Apple Git-155).
- Linked-checkout detection, run against a disposable repository plus one added
  worktree, classified `main`, `main/sub`, `wt`, and `wt/sub` as
  maintained/maintained/linked/linked:

  ```sh
  gd="$(git rev-parse --absolute-git-dir)"
  cd_="$(git rev-parse --git-common-dir)"
  case "$cd_" in /*) : ;; *) cd_="$(cd "$cd_" && pwd -P)" ;; esac
  [ "$gd" = "$cd_" ] && echo maintained || echo linked
  ```

  Resolving a relative `--git-common-dir` against the toplevel instead of `$PWD`
  misclassified `main/sub` as linked, so the relative case is resolved against `$PWD`.
  Full implementation review also reproduced a maintained checkout reached through a
  logical symlink whose absolute Git directory used the physical spelling; `pwd -P`
  keeps both sides of the classification in the same physical namespace.
- Legacy-block recognition, run against a hook holding a user line, the dotfiles
  marker comment, its invocation, and a trailing user line, left both user lines and
  removed exactly the two managed lines:

  ```sh
  awk '
    /^# codebase-memory-mcp: reindex on .* \(managed by cbm-onboard/ { skip=1; next }
    skip == 1 { skip=0; if ($0 ~ /cbm-reindex\.sh/) next }
    { print }
  '
  ```

  An earlier unbounded form of this fragment, which cleared the skip only on the next
  line matching the invocation, was refuted in review and must not be used. Against a
  hook whose legacy invocation carried an extra argument, it kept that stale invocation
  and deleted an unrelated `exec` line four lines further down, which is both a line the
  tooling does not own and a second reindex block left behind. The bounded form above
  was run against that same hook and against the plain legacy hook, and left every
  unowned line intact in both.

- The live hook this matches, in three enrolled repositories checked, is exactly:

  ```sh
  #!/bin/sh
  # codebase-memory-mcp: reindex on commit (managed by cbm-onboard — cbm-reindex)
  "<dotfiles>/scripts/cbm-reindex.sh"
  ```
