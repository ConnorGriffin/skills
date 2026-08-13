# Mode: behavior-sweep

Sweep a locked surface's **interactive behavior** into a contract before anyone
builds it. Runs after `lock`, before `build`, for any surface that has
behavior — handlers, gestures, hover states, keyboard paths, resize response.

The lock manifest describes what the surface *looks like*. It reliably fails to
describe what the surface *does*: a drag that only works from an edge, a
readout that latches on chart hover, an inspector that re-scopes with selection.
Those behaviors are in the mock's code and nowhere in the manifest, so a build
invents them. The behavior ledger closes that gap; the replay script keeps it
closed.

Root failure this mode exists to make impossible:

> Something approximated the locked artifact instead of using it, and a checker
> accepted the approximation.

Input: the ★ LOCKED mockup(s), `mockups/<surface>.lock.md`, and every module the
mock imports. `<surface>` is always the **basename of the lock manifest** —
every artifact below inherits that one name. No agent picks a nickname.

**Proportionality.** Sweep depth scales with the handler inventory: a surface
whose inventory fits on one screen may fold the three passes below into a single
sitting. The **ledger**, the **completeness check**, and the **QUESTION round**
are never waived, at any size.

## 1. Inventory (static — this is not evidence)

Enumerate every behavior the mock registers:

- `addEventListener` calls (click, mousedown/move/up, keydown, resize, …);
- chart/graphics-library instance handlers (e.g. an ECharts `on()` /
  `updateAxisPointer` / `globalout` set, zr events);
- `ResizeObserver` / `IntersectionObserver` / `MutationObserver` registrations;
- inline `on*=` attributes;
- CSS that *encodes behavior* — `:hover`, `:focus`, `:active`, transitions.

**Including handlers registered inside imported modules**, which the host HTML
never shows. A chart module that installs four instance handlers when given an
`onHover` callback is four inventory rows; missing them is how a latched readout
gets reinvented.

**Excluded by name:** mock-harness chrome — the theme toggle, the mock bar, the
variant switcher — is not the surface's behavior and never enters the inventory
or the contract. Name the excluded file(s) explicitly in the ledger header.
Excluded from the inventory is **not** excluded from the page: the harness and
every imported module are still **served**, because an unserved import throws
before any listener registers.

Static reading produces the inventory. It never produces a story.

## 2. Exercise (live — this is the evidence)

Drive the mock in a **real browser engine at the lock's viewport** — viewport set
explicitly, never a driver default. Perform each behavior for real: hover every
hoverable, drag from inside an element *and* from its edges, click every control,
run every keyboard path (Esc, arrows, Tab), resize. Verify in a second engine
when the behavior is rendering-sensitive.

Two further passes, folded in or run separately per proportionality:

- **Data pass.** Load the mock on *each* authorized fixture, including the
  largest realistic shape the surface will actually see. Record what every
  data-dependent visual *encodes* — clustering, scoping on selection, level
  content, count shapes. A visual whose meaning disappears at real scale
  (uniform glyphs, empty scoping) is a QUESTION, not a build call: a design rule
  is missing and that is a lock conversation.
- **Content pass.** For every information surface (detail panels, headers, meta
  rows, tags) capture the mock's **actual rendered markup and text structure**.
  The story links to markup, never to the lock term's prose — this is what makes
  "built from the description" detectable at review time.

**Completeness check (mechanical, not judgment):** every inventoried handler maps
to ≥1 story, and every story was observed live. A handler found in code but not
reproducible in-browser becomes a QUESTION entry — never a silent skip.

## 3. The replay script (committed)

Alongside the ledger, commit a replay script — `frontend/<surface>-behavior.replay.mjs`
or the repo's equivalent path — that re-runs the sweep mechanically. Hand-driving
is fine for discovery; a story enters the ledger only once its replay function
passes against the mock.

Spec:

- **One exported async function per story**, `export const S12 = async (page) => { … }`.
- Each function carries a `// LOCK:<surface>:<n>` tag for every lock term it
  exercises, so manifest coverage stays greppable.
- **Two openers, both in the script**: a *mock opener* (serves the mock root, its
  theme CSS, vendored libraries, and a fixture stub) and an *app opener* (route
  stubs, auth, navigation). Runnable against mock and app alike is the whole
  point — the same function is what makes it evidence on both sides.
- Both openers are **loud on unstubbed or missing requests**. A catch-all
  `200 {}` renders a build that is missing an asset and still passes.
- Both openers **assert the rendered state equals the requested one**, so state
  addressability drift (a `?state=` param the mock silently ignores) is loud
  rather than a quietly identical render.
- **Selector parity is a port obligation, not a script concern.** Replay-against-both
  only holds if the ported markup keeps the mock's selectors; a rename that
  breaks a replay selector is a **port defect**.
- **Drive every story through the affordance a reader would use.** A story about
  reaching, leaving, or returning to a state is only evidence if the replay gets
  there the way a person does — clicking the control, typing in the field. Browser
  history (`goBack`), a direct URL, or calling the surface's own API bypasses the
  affordance, so the story passes on a surface that offers *no route at all*. A
  shipped Diagnose view once lost its entire view switcher while its "returning to
  an event view restores it" story stayed green, because the replay returned with
  `goBack()`. When a story's verb is navigational, assert the control exists and is
  visible, then use it.
- Replay functions inherit `build.md`'s prove-red-once rule — proven against the
  **built app** (knock the feature out) or a **scratch copy** of the mock, never
  the ★ LOCKED mock in place. A transient edit to the contract artifact risks an
  unrestored diff, which is the quiet deviation `resettle` exists to forbid.
- **The script fails closed.** Missing browser dependencies (driver module,
  vendored assets, executable) exit nonzero — never `skip`. A skipped run exits 0,
  and a green step that executed zero stories is precisely the silent skip this
  mode exists to prevent.
- Wire the script into CI **explicitly**. Test globs discover `*.test.js`, not a
  `.replay.mjs`; a browser job that hand-lists its files gets a hand-added step in
  the same change.

## 4. The behavior ledger

One entry per story, in `mockups/<surface>.behavior.md`:

```
S12 · Dragging a window's edge resizes it; edges are full-height ±5px grab
      zones; Esc clears the window.
  element:  .brace .edge / #grip-a / #grip-b
  source:   <mock file>:2446-2600 (installDrag)
  lock:     terms 6, 7, 21
  data:     any
  evidence: replay fn S12 + screenshot ref
  status:   (build phase fills: ported | replayed-pass | replayed-fail |
             re-settle requested)
```

Sweep screenshots and clips live in `mockups/sweep/<surface>/`. Register both the
ledger and that directory in `mockups/INDEX.md`, per resettle's
INDEX-moves-with-the-lock rule.

Entry types are exactly two: **STORY** (observed behavior) and **QUESTION** (a
behavior or meaning gap the operator must rule on).

**There is no waiver entry type.** A drop is always a dated, operator-sanctioned
record, by one of exactly two paths:

- a story that **cites a lock term** → `resettle`; the manifest row is the record
  and the operator's exact authorizing sentence is that resettle's evidence;
- a story with **no lock term** (the ledger's whole reason to exist — resettle
  cannot run where there is no manifest row) → dropped only by an operator ruling
  recorded **inline in the ledger** under a QUESTION entry, his exact sentence
  quoted.

Both paths carry the date and the sanction. A drop path that skips the record is
exactly how a dropped term recurs.

## 5. QUESTION round (one numbered round)

Batch every QUESTION to the operator in **one numbered round** at the end of the
sweep — behavior gaps, meaning-lost-at-scale findings, irreproducible handlers,
and any fixture-set authorization the gate will need (shapes and in-band labeling
authorized together; see the data defaults in SKILL.md's grounding rules).
Answers are recorded inline under their QUESTION entries.

## 6. Freeze

Operator approval stamps a header line on the ledger:

```
★ FROZEN <date> · base <sha> · generator <sha> · window <start>..<end>
  · fixtures <name: sha256-prefix, …>   (tripwire, not contract)
```

- The pinned **inputs** (generator commit, data window) are a **provenance
  record** — where the bytes came from. In a live-data repo they are not
  themselves reproducible.
- The **transported bytes are the contract**: the builder hands the verifier the
  exact fixture files by a retained path recorded in the ledger header. "Same
  data" means the same bytes, not a re-run of the generator.
- Fixture **hashes are a tripwire**, never the contract — they detect unintended
  regeneration. A hash over data that grows daily is unreproducible tomorrow by
  construction.

A `behavior.md` without the `★ FROZEN` header is a sweep in progress, not a
contract; building against it is a blocking finding. Regenerating any pinned
fixture after freeze requires a recorded reason under the header.

**Ledger + lock manifest together are the build contract.** The manifest alone is
insufficient: behaviors and meanings its terms never encoded, plus terms no
assertion ever exercised, are the two gaps. The ledger closes the first; behavior
replay in `build` closes the second.
