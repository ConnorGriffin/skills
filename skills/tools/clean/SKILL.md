---
name: clean
description: Clean the current branch's diff without changing behavior — naming, dead code, duplication, and the charter's deep-module rules — in one pass, then stop. Use when the user says "clean this diff", "/clean", "cleanup pass", or wants the branch tidied before review or hardening.
---

# Clean

One cleanup pass over the code a branch changed. It keeps behavior and the test
suite exactly as they were, and it ends with a ledger instead of a verdict.

This skill **changes code**. It is not a reviewer: it never scores, never grades,
and never emits findings for a human to action inside the diff. Anything it
notices outside the diff becomes a follow-up line, never an edit.

One pass. When the ledger is written, stop — no second sweep.

## Fixed point

The pass is scoped to a diff, so it starts by pinning where that diff begins.

Accept an optional ref argument (`/clean <ref>`). With none, the fixed point is
the merge-base with the default branch. Resolve it by the rules in
[`code-review`'s "Pin the fixed point"](../code-review/SKILL.md#1-pin-the-fixed-point) —
the same SHA, branch, tag, PR, and stale-base handling, cited rather than
restated. Confirm the diff is non-empty before touching anything.

The **scope** is the files changed since that point. Unchanged files are read
freely for context — that is how you learn the module that already covers a
behavior — but they are not edited.

## Preconditions

Discover the repo's test command the way `/ticket` does: read `AGENTS.md` or
`CLAUDE.md` for a test line first, then the CI workflows, then package scripts.
An argument naming the command overrides discovery.

Run it before any edit.

* **Green:** proceed, and record the command and result for the ledger.
* **Red:** stop. Report the failing output and make no edits. A branch that is
  already broken has no baseline to preserve, and a cleaner cannot tell its own
  damage from damage that was already there.
* **No runnable suite:** proceed, say so in the ledger, and limit the pass to
  changes a compiler, type checker, or linter can verify. Behavior preservation
  is being asserted rather than demonstrated, and the ledger has to say which.

Generated and vendored code is skipped and named in the ledger.

## Checklist

Load [`codebase-design`](../codebase-design/SKILL.md) for the vocabulary before
starting — module, interface, depth, seam, adapter, deletion test — and use those
words exactly. Load [`domain-modeling`](../domain-modeling/SKILL.md) when the repo
has a `CONTEXT.md`, so renames land on the domain's own terms.

Apply the list once per changed module, in this order. Each item names the
[charter](../../../profile/CHARTER.md) rule that grounds it; a change with no rule
behind it is taste, and taste is not in scope.

1. **Naming and locality.** Names say what the thing is in the repo's own idiom;
   related code sits together. *Rule: match the surrounding code.*
2. **Dead code.** Unreferenced functions, unreachable branches, commented-out
   blocks, and leftover scaffolding introduced by the diff go. *Rule: no dead
   code, no speculative abstraction.*
3. **Duplication.** Behavior the diff re-implements, where an existing module
   already reaches it through its public interface at that call site, collapses
   to the existing module. *Rule: reuse the module that already covers the
   behavior.*
4. **Shallow modules.** A module the diff introduced whose interface is about as
   complex as its implementation is deepened or inlined. Apply the deletion test:
   if removing it only moves complexity around, it should not exist. *Rule: deep
   modules; the deletion test.*
5. **Unearned guards.** A guard for a state that cannot occur is complexity, not
   safety. Remove one **only** when the ledger names the enforced invariant that
   makes the state unreachable — code that rejects it, or a pinned test.
   Otherwise keep it. Guards at a trust boundary, and guards grounded by
   acceptance criteria, security, or observed behavior, always stay. *Rule: earn
   every guard.*
6. **Speculative seams.** A seam with one caller is a hypothetical seam; collapse
   it and build it again when the second caller is real. *Rule: one adapter is a
   hypothetical seam, two is a real one.*

## Invariants

These bound every edit. A cleanup that cannot be made without breaking one of
them is not made — it becomes a follow-up line.

* **No behavior change.** Logic branches, error modes, and outputs are what they
  were. Renaming a variable is in scope; changing what a condition decides is not.
* **Nothing outside the diff.** Public interfaces of modules the diff did not
  touch stay untouched, however tempting.
* **No new dependencies**, and no scope expansion.
* **Tests are not rewritten to pass.** A test that fails after a cleanup is the
  cleanup being wrong. Revert the cleanup, keep the test.

## Post-check

Re-run the same test command.

* **Green:** the pass holds; write the ledger.
* **Red:** revert the cleaner's own edits — `git checkout` the files this pass
  touched, never a reset of the branch, which would destroy the work the diff
  came to clean — and report which change broke it, with the failing output.
  Then stop.

## Ledger

The ledger is the final message. Nothing is written to the repo except the
cleaned code itself: no plan file, no scratch directory, no report committed to
the branch.

It carries three things:

* **Changes made** — per change: the file, what moved, and the charter rule that
  grounded it. A guard removal names its enforced invariant here or it is not a
  legitimate removal.
* **Follow-ups** — what was noticed outside the diff, or inside it but blocked by
  an invariant, listed for a human to route. Not fixed.
* **Verification** — the test command, its result before, and its result after.
  A reduced pass (no runnable suite, skipped generated code) says so here.

## Not this skill

* **Review verdicts** — [`review`](../../workflows/review/SKILL.md) routes those.
  This skill edits; it does not grade.
* **Writing tests** — [`tdd`](../tdd/SKILL.md).
* **Mutation testing, coverage gates, and other deterministic hardening** — the
  hardening step that runs after this one.
