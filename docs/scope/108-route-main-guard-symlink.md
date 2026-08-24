# Scope — 108 route.mjs main-guard under a symlinked skill dir

## Decisions

- Route: interview mode. One bounded fix-shape decision; everything else is
  grounded and reproduced. `inline`
- Bug confirmed live, not from docs: through a symlinked `ui-craft` directory,
  `node .../scripts/route.mjs --embodiment greenfield ...` prints nothing and
  exits 0; the same command on the real path prints
  `{"mode":"lock","reason":"the app has no shipped embodiment"}`. `inline`
- Three working copies of the same predicate already exist in the same scripts
  directory: `critique-storage.mjs` `isMainModule()` (realpath, with a
  `pathToFileURL` fallback and a comment naming the symlink cause),
  `context-signals.mjs` and `context.mjs` `invokedAsScript()` (realpath,
  byte-identical to each other). `route.mjs` is the only raw-string comparison
  left. `inline`
- `skills/drivers/ui-craft/scripts/lib/` is the established home for shared
  helpers in this skill (5 modules today). `inline`
- Existing route.mjs coverage (`tests/test_behavior.py:1163`) invokes the script
  by its real path from repo root, so it passes today and can never catch this;
  new evidence must invoke through a symlink. `inline`
- Profile: none. No `Harden:` line in the repo's `CLAUDE.md` repo facts. `inline`
- Surface lifecycle: none. CLI script; `CLAUDE.md` declares `ui-surfaces: none`. `inline`

- Q1 fix shape settled by the user: **A** — extract one shared predicate into
  `skills/drivers/ui-craft/scripts/lib/main-guard.mjs` and migrate all four call
  sites (`route.mjs`, `critique-storage.mjs`, `context-signals.mjs`,
  `context.mjs`). Why: three copies of one predicate already exist in that
  directory and the fourth has drifted into a broken variant, which is the
  divergence the charter's reuse rule names. `inline`

### Risk contract

- **Must prevent:** a CLI in this pack exiting 0 with no output when it was asked
  to do work — the silent-incorrect-success default, and the exact defect here.
- **Must recover:** nothing automatic. The script is a one-shot read-only router.
- **Accepted failure:** on a platform where `realpathSync` throws, the guard falls
  back to a URL comparison and, failing that, does not run; a clear no-op the
  operator sees, not a wrong route.
- **Unsupported:** invocation shapes other than `node <path> <flags>` — no
  `npx`, no shell wrapper, no Windows guarantee beyond the fallback.
- **Evidence owed:** `route.mjs` invoked through a symlinked skill directory
  prints route JSON and exits 0/2 exactly as the real-path invocation does.
- **Why:** the failure is silent and already cost a live triage run a detour.
- **Disposition:** `inline` — copy into the work order.

## Open questions

- none. Q1 settled (see Decisions).

## Spawned tasks

- none

## Spike — the guard predicate, executed

Run in the session scratchpad (not on the branch: triage writes no shipping code).
A four-case harness over the proposed `isMainModule(moduleUrl)` — realpath compare
with a `pathToFileURL` fallback and an `argv[1]` absent guard:

| Case | Result |
|---|---|
| invoked by its real path | runs |
| invoked through a symlinked skill directory | runs |
| imported by another module, not the entry point | does not run |
| no `process.argv[1]` (`node --input-type=module -e`) | returns false, no throw |

All four passed. The literal the order carries is that predicate, not prose.

## Review rounds

Round 1 — one cold panel (`/plan-review`, ordinary stakes), reviewer had no hand in
the draft.

* Grounding: clean. Every cited line number, path, module list, quoted command, and
  pinned output literal was independently reproduced, including the bug itself.
* Blockers: 1, tagged `authoring`. Step 5 demanded the three migrated CLIs "still
  produce existing output" when no baseline exists for any of them — zero test
  coverage outside `route.mjs` — so the executing agent would have had to invent
  golden literals for three previously untested commands, one of which emits
  absolute paths. Fixed by making step 5 differential: same invocation, real path
  versus symlink, assert equality. No goldens.
* Notes: 2, both `authoring`. The Done-when `import.meta.url` grep was not
  mechanically satisfiable (10 hits before and after the fix, 6 of them legitimate
  directory resolution) — replaced with two greps that genuinely flip. And step 1's
  comment spec dropped the why-not-`endsWith` rationale that step 3 told the agent
  to delete from `context.mjs:945-947`.
* Injected blockers: 0.
* Found by the reviewer, outside the original scope: a fifth copy of the predicate
  at `detector/detect-antipatterns.mjs:48`, using the loose suffix match
  `context.mjs` warns against. Not symlink-broken. Folded into the migration and
  sent back for attack on the scope and cost axes.

Order rewritten clean rather than patched.
