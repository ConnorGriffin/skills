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

Round 2 — same reviewer, re-checking only round 1's deltas as fresh attack surface.

* Blockers: 2, both tagged `injected` — each was introduced by a round-1 fix, not
  present in the original draft.
  * The differential-parity idiom that replaced the golden literals (the reviewer's
    own round-1 recommendation) is satisfied by two silent runs: if the migrated
    guard never fires, both halves produce empty stdout and exit 0, so the test
    passes green while four of the five CLIs are dead. Fixed by asserting the
    real-path run's stdout is non-empty before comparing the pair — which pins that
    the CLI ran, not what it printed, so it still invents no baseline.
  * Folding in the fifth call site would have deleted
    `detect-antipatterns.mjs:49`, the trailing-separator spelling
    (`...endsWith('detect-antipatterns.mjs/')`), with nothing naming the invocation
    shape it exists for. `node <path>/detect-antipatterns.mjs/ --help` works today.
    `realpath` of `file/` resolves on darwin but raises `ENOTDIR` on some platforms,
    where the fallback would compare `file:///…mjs/` against `file:///…mjs` and
    reintroduce this ticket's defect at a new site. Fixed in the helper rather than
    only in a test: strip a trailing separator before comparing. Spiked and executed
    — all four shapes (real path and symlink, each with and without the trailing
    separator) fire, and the fallback compare holds once stripped.
* Notes: 1, `injected`. The `--help` justification cited
  `detector/cli/main.mjs:137`, which only computes the flag; handling is at 164, and
  lines 149 and 155 read from `process.cwd()` first, so the invocation is
  cwd-sensitive and the same-cwd requirement is load-bearing rather than incidental.
  Corrected, with the writes-nothing claim re-grounded (no write call exists
  anywhere in the detector tree).
* One reviewer claim was checked and did not reproduce on first run — that all four
  pinned invocations emit output today. Re-run without the quoting artifact in the
  probe, all four do. Claim upheld, not forwarded on the strength of the first
  reading.
* The fifth call site was attacked on the scope and cost axes as asked and cleared:
  a genuine fifth copy of the same predicate, one constant plus one test pair of
  marginal diff, and `detect.mjs` reaches `detectCli` by dynamic import with
  `argv[1]` pointing at `detect.mjs`, which is false under both the old and new
  predicates.

Injected blockers by round: 0, then 2. The climb is the rewrite-clean signal, and
round 2's fixes are confined to the two steps that produced them.

Round 3 — the cap. Spent on round 2's deltas, because round 2's fixes had changed
the helper's semantics rather than only a test.

* Blockers: 1, `injected`, and it retracted round 2's own second blocker. The
  trailing-separator normalization guards a state that cannot occur: Node resolves
  and normalizes the entry path before the module sees it, so `process.argv[1]`
  never carries a trailing separator. Reproduced independently on this machine's
  Node 26.7.0 — `node probe.mjs`, `node probe.mjs/`, and `node probe.mjs//` all
  report the same normalized path. `detect-antipatterns.mjs:49` is therefore dead
  code, and round 2's fix accommodated a clause that should have been deleted.
* Resolution taken, rather than a fourth round: delete the normalization, and delete
  line 49 as dead code while naming the invariant that makes its state unreachable,
  which is what this repo's charter requires of a guard removal. The trailing-
  separator test pair is kept and reframed — it no longer claims to prove a
  normalization the helper does not perform; it pins the invariant the deletion
  rests on, and fails loudly if a future runtime stops normalizing. The order also
  gained a boundary forbidding the guard from being re-added.
* Supporting evidence gathered here, not from the reviewer: line 49 arrived in a
  bulk categorization commit (`3bc9c25`, #56) with no recorded rationale, and the
  repo's CI pins no Node version.
* Residual, stated rather than hidden: the invariant was measured on Node 26.7.0
  and no Node 20 runtime was available on this machine. The step 5 pair is what
  converts that gap from an assumption into a test.
* Notes: 0 new. Deltas B and D were confirmed clean.
* The reviewer also closed the false-TRUE question I could not settle by
  construction: `argv[1]` is the path Node resolved for the entry it loaded, so a
  realpath match implies the module is the entry at all five call sites.

Injected blockers by round: 0, 2, 1 — and round 3's retracted round 2's. Reviewing
stopped at the cap with the order rewritten to the simpler shape rather than the
accommodating one.
