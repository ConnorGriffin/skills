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
