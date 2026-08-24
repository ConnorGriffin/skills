# Scope — explicit settings target for Codebase Memory activation

Ticket: [#76](https://github.com/ConnorGriffin/skills/issues/76)
Route: interview mode (a concrete plan exists, untested).

## Decisions

- Flag name is `--settings-file`, taking a path. Why: mirrors `--claude-home`'s
  noun-for-what-it-names style and reads as the file it writes. `inline`
- Hook files and rendered hook commands stay rooted in `--claude-home` regardless of
  `--settings-file`. Why: the ticket's consumer versions settings only; hooks must
  still execute from the live Claude home. `inline`
- Symlink refusal applies to whichever settings path is selected, default or
  explicit, and the default path keeps its current message text. Why: the existing
  test pins that message, and weakening symlink protection is the one thing the
  ticket forbids. `inline`
- A missing parent directory of an explicit `--settings-file` is a no-write refusal
  naming the missing directory, not a created tree. Why: the caller already owns the
  versioned checkout, and creating directories outside the Claude home is the one way
  this option could write somewhere unintended. `inline`
- An explicit target's parent must exist, be a directory, and pass
  `os.access(parent, W_OK | X_OK)`; symlinks are resolved when judging the parent,
  and only the final settings node must be a regular non-symlink file. Why: review
  reproduced that a 0o600 directory passes `is_dir` and `W_OK` yet raises
  PermissionError on both lstat and mkstemp after the hook files are already written,
  and a settings file reached through a symlinked checkout is the ticket's main
  audience. `inline`
- Verification compares validate.py's `ERROR:` lines against a captured origin/main
  baseline, not exit codes. Why: this clone is known-red from a sibling branch's
  commits, and validate.py accumulates all errors behind one exit 1, so a new error
  would hide. `inline`
- Change record: `docs/adr` tree exists but this is an additive option under the
  interface ADR 65 already settled; no new ADR. Why: nothing hard-to-reverse is
  being decided beyond the flag itself. `inline`

### Risk contract

- **Must prevent:** writing through a symlink at either settings target; clobbering
  unrelated settings or unrelated hook registrations; changing behavior of the
  existing no-option command.
- **Must recover:** nothing automatically; the installer is a one-shot command.
- **Accepted failure:** any refusal (symlink, malformed JSON, conflicting managed
  registration, unwritable target) is a clear stop with no partial write, recovered
  by the operator fixing the target and rerunning.
- **Unsupported:** creating a settings file's parent directory tree, non-regular
  settings targets, and settings files the installer does not own the hooks block of.
- **Evidence owed:** through the copy-runnable installer interface — an explicit
  target outside the Claude home, preservation of unrelated settings at that target,
  idempotent rerun byte-stability, unchanged default-path behavior, and symlink
  refusal at the explicit target.

Why: the installer edits live agent configuration on a real machine; a bad write is
recoverable by hand but a followed symlink is not contained.
Disposition: copy into the work order at admission.

## Open questions

- none open. Q1 (parent-directory behavior) settled as a refusal, above.

## Review

- Two cold panels against the draft order; three blockers in round one (baseline-red
  verification gate, unwritable-parent partial install, no-referent change record),
  three in round two (search-bit-less parent, unspecified symlinked-parent branch,
  failure-level rather than line-level baseline comparison). All six reproduced
  independently before acting; all `authoring`, none `injected`. Order rewritten clean
  after round one, patched after round two.

## Spawned tasks

- none
