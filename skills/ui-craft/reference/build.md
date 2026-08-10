# Mode: build

Implement a locked visual spec. The finish line is **every manifest term has
evidence** — not "the gates are green". A build that passes every test while
diverging from the lock is a failed build.

Input: the ★ LOCKED mockup(s) and `mockups/<surface>.lock.md`. If the
manifest is missing, stop and create it first (run the manifest-extraction
part of `lock` mode against the existing header — do not build from prose).

Where the surface has interactive behavior, the input is **two** contracts: the
manifest and the `★ FROZEN` behavior ledger from `behavior-sweep`. Building
against an unfrozen (or absent) ledger is a blocking finding — check the header
first. The manifest alone never encodes what the surface *does*.

## Before writing code

1. Read the manifest, the mock headers, and the mock's **component CSS** —
   not just its layout. Diff the mock's component styling (buttons, chips,
   rows) against the app's shipped equivalents; where they differ, the
   manifest's precedence line decides. List the differences you will honor.
2. If any two locked artifacts contradict each other, or a locked term
   collides with the design system beyond what precedence settles: **stop and
   surface it.** Implementer arbitration is how locks die.
3. Read the fixture obligations. Build or extend fixtures until every locked
   visual feature actually renders under them. A tame fixture that leaves a
   ribbon invisible or a threshold untriggered cannot prove anything.
4. **Pin the provenance.** Branch off a **freshly fetched** default branch and
   record the base SHA in the ledger header, along with the paths + SHAs of
   every source artifact (mock HTML, its module files, manifest, behavior
   ledger, fixtures, comparator). A branch cut from a pre-squash tip produces a
   conflicting PR that silently attaches no CI.

## Port, don't reimplement

The mock is code, not a picture. **Its own JS and CSS are ported** — imported
outright, or adapted line-by-line with a **diff-to-mock** attached. Reimplementing
a feature from a lock term's *description* is a blocking finding, however faithful
the result looks: the description was never the artifact.

- **The diff unit is `mock line-range → app file`, verbatim-first.** "Per ported
  file" is undefined when the mock is a thousand inline lines plus a sibling
  module. Every non-verbatim line is listed with why it changed.
- **New code is limited to adapters**: real data → the shape the mock's module
  already consumes, plus mounting and wiring into the app shell. If the mock's
  code cannot run against real app data without redesign, that is a QUESTION back
  to the operator — never a license to reimplement.
- **Keep the mock's selectors.** The behavior replay script runs against mock and
  app alike; a rename that breaks a replay selector is a port defect, not a script
  defect.
- Suspected data bugs surfaced by the sweep are verified against the real payload
  and fixed in the adapter or backend — never papered over in the port.
- If the app has no static asset mount, every new frontend file gets its serving
  route **in the same commit**, and at least one verification pass runs against
  the real app server rather than a disk-serving harness, which is structurally
  blind to a missing route.

## While building

- `design-rules.md` governs craft; the manifest governs content. Where they
  disagree, the manifest wins — improvements to a locked surface go through
  `resettle`, even mid-build, even when the improvement is real.
- Every `gate` term gets an assertion in the rendered browser gate, tagged
  with its manifest number in a comment (`// LOCK:<surface>:<n>`), so
  coverage is greppable.
- **Prove each lock assertion can fail.** Once per assertion: knock the
  feature out, watch the assertion go red for the right reason, restore.
  This is the charter's "failed first" applied to visual gates; it is what
  catches operator-precedence truthiness, wrong-state fixtures, and
  screenshots of nothing.
- **Rewriting a test file transfers its invariants.** Before replacing any
  rendered gate, list the assertions the old file made; every one either
  reappears in the new file or is named as dropped (with why) in the PR.
  Silently dropped assertions are how locked terms become untested.

## The fidelity ledger

The PR ships a ledger — in the PR body or `docs/` — one row per manifest
term:

```markdown
| # | Term | Status | Evidence |
|---|------|--------|----------|
| 1 | No page scroll at 1280x800 | met | LOCK:settings-audit:1 assertion |
| 3 | Excursion aligns with block | met | paired render R3 |
| 7 | Meal blocks colour-washed | re-settle requested | see PR comment |
```

Statuses: `met`, `re-settle requested` (with the resettle recorded), or
`blocked` (with why). There is no "partially" and no silent omission — a term
absent from the ledger is a blocking gap.

**There is no waiver.** A term that will not be built is dropped by one of the
two dated paths in `behavior-sweep.md`: cites a lock term → `resettle` (the
manifest row is the record); no lock term → an operator ruling recorded inline
under a QUESTION entry, his exact sentence quoted. An unverified waiver in a PR
body is how a dropped term recurs.

## Behavior replay

Where a behavior ledger exists, its committed replay script re-exercises **every
STORY against the built app** — not against the mock; a run wired through the
mock opener exercises the mock and proves nothing about the port.

- Each story's ledger `status` moves to `ported` → `replayed-pass` /
  `replayed-fail` / `re-settle requested`. **`replayed-fail` blocks.**
- The script's fail-closed rule holds here: a green step that executed zero
  stories is a failure, so confirm the run **reported its applicable story
  count**, not merely that the step ran.
- Where PHI or other sensitive data splits the runs, the CI gate replays a
  committed labeled-synthetic fixture set and the real-data run stays local; the
  two subsets must **union to the full ledger**, and the ledger records which run
  covers each story.

## Paired renders

For every `eye` term and every state the manifest names: render the **locked
mock** and the **built surface** side by side and attach the pairs to the PR as
the charter's proof-of-match.

- **Same data, not merely the same kind of data.** Both sides render identical
  bytes. Comparing a synthetic build render against a real-capture mock render is
  not a pair; it is two pictures.
- **The pairs cover every state and viewport the lock's own terms enumerate** —
  all of them, in both themes — not one convenient state. This is the only
  accepted fidelity evidence.
- **Any harness, comparator, or screenshot rig loads the app's real CSS.**
  Re-declaring theme tokens from memory is a blocking finding: it puts wrong
  colors into the "proof" and can mask a real token bug in the shipped build.
- Verify each pair actually exercises its term before attaching (fixture
  obligations again).
- Drive the build into each enumerated state deliberately. If the mock is
  state-addressable by URL and the app is not, the port carries an equivalent
  hook (or a `goto<State>(page)` export per state in the replay script) — without
  it the comparator renders two of the matrix's pairs and reports a full sweep.

## Review handoff

- **The verifier is a freshly spawned session** that did not author the port and
  has **no access to the builder's transcript or working notes**. Hand it only
  the contract artifacts — manifest, frozen behavior ledger, replay script, the
  pinned data files, the renders, the diff-to-mock set — and instruct it to
  distrust the port. A verifier sharing the builder's context is a self-graded
  table with extra steps, whatever its model tier.
- **The builder's session may not mark any status beyond `ported`.** Statuses are
  recorded by the verifier from raw script output. A self-graded fidelity table
  is an index into evidence, never evidence.
- **Craft and eye judgment route to the top model tier**, or the coordinator's own
  eyes **when the coordinator did not drive the port** (otherwise the verifier's
  or the operator's). Mid-tier polish grades are not accepted for craft.
- **Every `eye` term gets its own named judgment entry** in the PR evidence,
  written by the eye reviewer. An eye term is *never* satisfied by gate
  assertions passing.
- An eye term defined over a **gesture in progress** is viewed **live in-browser**;
  static pairs cannot evidence it.
- Their checklist is the manifest and the ledger, not the diff. "Does render N
  match mock N on terms X, Y, Z" is an answerable question.
- **Surface the evidence unprompted** — pairs, replay output, judgment entries,
  diffs-to-mock go in the PR. Evidence withheld until demanded is a process
  violation.
