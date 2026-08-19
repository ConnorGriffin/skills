# Mode: behavior-sweep

Sweep a locked surface's **interactive behavior** into a contract before anyone
builds it. Runs after `lock`, before `build`, for any surface that has
behavior — handlers, gestures, hover states, keyboard paths, resize response.
Its one backward-looking pass, the **predecessor inventory** (§2), runs *before*
the lock closes instead; `lock.md` §9 gates on it and argues the ordering.

The lock manifest describes what the surface *looks like*. It reliably fails to
describe what the surface *does*: a drag that only works from an edge, a
readout that latches on chart hover, an inspector that re-scopes with selection.
Those behaviors are in the mock's code and nowhere in the manifest, so a build
invents them. The behavior ledger closes that gap; the replay script keeps it
closed.

Two root failures this mode exists to make impossible, one per direction:

> Something approximated the locked artifact instead of using it, and a checker
> accepted the approximation.

> Something dropped the predecessor's behavior, and no checker was looking in
> that direction.

Input: the ★ LOCKED mockup(s), `mockups/<surface>.lock.md`, every module the
mock imports, and — where the surface replaces something — the **predecessor's
own source and running build** (§2). `<surface>` is always the **basename of the
lock manifest** — every artifact below inherits that one name. No agent picks a
nickname.

**Proportionality.** Sweep depth scales with the handler inventory: a surface
whose inventory fits on one screen may fold the passes below into a single
sitting. The **ledger**, the **completeness check**, the **predecessor diff**
wherever a predecessor exists, and the **QUESTION round** are never waived, at
any size.

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

**Handlers are not the only source of stories.** The inventory finds everything
the surface *does*; it cannot find what the surface must *keep true* while doing
it. Those invariants own no handler, so a handler-complete ledger can still have
none of them — and they fail silently, because each one is only visible by
comparing two renders nobody compares. Add a story for each:

- **Across views/modes**, chrome the reader keeps seeing does not move. Measure
  every other view against one designated reference view, not against an
  average, so the reference stays authoritative when they drift together.
- **Across interaction**, nothing reflows that the interaction did not name.
  A header that grows when its hover readout fills moves the content under the
  pointer — reserve the space at rest and assert the resting and active
  geometry are equal.
- **Across data shape**, containers sized for live values do not resize per
  value (counts, timestamps, currency).

A real Diagnose surface shipped 6px low in two of its three views, and grew its
chart header on first hover, with a handler-complete ledger where every story
passed. Each story replayed one view, alone, where a uniform offset is invisible.

Static reading produces the inventory. It never produces a story.

## 2. Predecessor inventory (static + live — the diff run backwards)

§1 inventories the mock, and **a mock-side inventory cannot see an absence**. A
behavior the mock never implemented registers no handler, so it produces no row;
a computed-style harness and a chart-option diff have no opinion about an
interaction that is not there either. Every other check in the lifecycle reads
the mock, so all of them are blind in the same direction. This pass is the only
one that reads the other artifact.

A Diagnose workstation was explored as a grounded mock over ten rounds,
critiqued by a persona panel, put through a 52-run technical audit, and locked
as a 60-term contract. The app it replaced let the reader **drag in the plot
body to draw a custom selection window**, resize it from two titled grab
handles, and ran one grammar where an explicit choice — a preset press or a drag
— outranked the default window. The mock drew five inert preset buttons and
nothing else. Nobody noticed at any round, so the lock froze the retirement of a
shipped interaction as contract, and a build agent reading that lock would have
shipped the retirement faithfully. It was caught by eye, on a screenshot, after
the lock merged. Nothing was skipped — the sequence had no step that looked
backwards.

**When it applies.** Whenever the surface has a shipped ancestor: a `shipped`
row in `mockups/INDEX.md` for this surface or the one it replaces, a lock
manifest whose `Supersedes:` line names a prior lock, or a surface being
replaced in the running app. **A greenfield surface with no predecessor skips
this pass**, and says so in one line in the ledger header naming what was looked
for and not found. The skip is recorded so it stays a fact about the surface,
rather than becoming a step everyone learns to wave through.

**What it inventories.** The PREDECESSOR's behavior, by §1's rules exactly —
`addEventListener`, chart/graphics-library instance handlers, observers, inline
`on*=`, and CSS that encodes behavior — read from the shipped code, never from
memory of using the app. **Including handlers registered inside imported modules
the host HTML never shows.** That clause is load-bearing: it is exactly where
the drawn window's grab handles were registered, and a host-HTML-only sweep
misses them a second time. Then **exercise the predecessor live** (§3's rules,
same viewport): a gesture assembled across three handlers reads as one row only
from the running surface, and suppression conditions — a handle that does not
appear in one state — exist nowhere in the source as a row at all.

**The diff.** Every predecessor row gets exactly one verdict against the mock:

- **kept** — the mock implements it. It is already a §1 story or it becomes one;
  the two inventories meet in that single ledger entry.
- **retired** — the mock deliberately does not implement it, and a human ruled
  that it goes. Requires the **sanction line** below.
- **missed** — the mock does not implement it and nobody decided that. **A
  `missed` row fails the sweep.**

`missed` is the default verdict, and a row leaves it only by being built or by
being sanctioned. "It was probably intentional" is `missed`. A retirement
argued by the agent that wrote the mock is `missed`. An inventory that ends with
no `missed` rows because the sweep could not find the predecessor's source is
`missed` for every row it could not read.

**The sanction line.** A `retired` verdict carries, in its ledger entry:

```
sanction: <who ruled it> · <date> · "<why, in their own words>"
```

`<who>` is a person, named. `<date>` is the day they ruled. The reason is
**quoted, not paraphrased** — the same evidence standard the two drop paths in
§5 already hold. **An unsanctioned retirement fails the sweep, and there is no
waiver for it**: not by proportionality, not by an agent's judgment that the
behavior was vestigial, not by the operator's silence when asked. A behavior
that reaches `retired` without a human's name and date on it is the exact defect
this pass exists to prevent, and in the ledger it is indistinguishable from a
`missed` one — which is why it fails as one.

**Ordering.** This pass runs **before the lock closes**, alone among the mode's
passes; `lock.md` §9 makes it a lock precondition and argues why. It needs the
finalist only as a diff target, never a frozen mock. Its verdict table is
carried into the ledger when the sweep proper runs after the lock. A `missed`
verdict discovered *after* a lock has merged is a `resettle` trigger, not a
build decision and not a bug fix — see `resettle.md`.

## 3. Exercise (live — this is the evidence)

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
to ≥1 story, **every §2 predecessor row carries a verdict**, and every story was
observed live. A handler found in code but not reproducible in-browser becomes a
QUESTION entry — never a silent skip. Handler coverage is not ledger
completeness: a surface with more than one view, or with any interaction that
swaps content in place, also owes its invariant stories above. Record them with
no handler named, since none exists.

## 4. The replay script (committed)

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
- **A retired behavior gets a replay function too, and it is never silent.** The
  function asserts the absence — no grab handle in the DOM, the gesture does
  nothing — and **prints its sanction line on every run**, from a
  `// RETIRED:<who>:<date>` tag beside the `LOCK:` tags. An absence asserted
  without the sanction on screen quietly makes the retirement permanent, and
  reads exactly like a feature nobody ever had; the point of running it at all is
  that a reader of the output sees a shipped behavior was deliberately dropped
  and by whom. The script **fails closed on a retired function whose sanction tag
  is missing**, exactly as it does on a missing driver. Reinstating the behavior
  deletes the absence assertion **in the `resettle` change set that moves the
  ledger entry back to STORY**, never on its own.
- **The script fails closed.** Missing browser dependencies (driver module,
  vendored assets, executable) exit nonzero — never `skip`. A skipped run exits 0,
  and a green step that executed zero stories is precisely the silent skip this
  mode exists to prevent.
- Wire the script into CI **explicitly**. Test globs discover `*.test.js`, not a
  `.replay.mjs`; a browser job that hand-lists its files gets a hand-added step in
  the same change.
- **The mock's CI leg is temporary: it runs from lock until the surface ships, and
  then it is deleted.** While the port is being built the mock is the contract
  artifact and the `TARGET=mock` leg is what guards it; once the app-opener leg is
  green the app is the contract artifact and the mock leg guards nothing the app
  leg does not. **Retirement is atomic with the port**: the same PR that turns the
  app leg green deletes that surface's mock leg, flips its row in `mockups/INDEX.md`
  to `shipped`, and archives the mockup (`lock.md`'s archive-after-ship rule). A
  follow-up issue for any of the three is forbidden — that is exactly how surfaces
  end up merged-but-still-`locked`. The anti-drift guarantee is not lost with the
  leg, because it never lived there: it lives in the ledger's stories replayed
  against the built app, which run forever. A permanent mock leg instead means the
  surface's logic exists twice and is hand-synced, and that drifts — one port branch
  carried three divergent wordings of a single copy-pasted note builder.

## 5. The behavior ledger

One entry per story — and one per sanctioned retirement — in
`mockups/<surface>.behavior.md`:

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

A retirement from §2 takes the same shape, keyed `R`:

```
R3 · Dragging in the plot body drew a custom selection window; two handles
     titled "Drag to resize" resized it, growing away from the edge not being
     dragged.
  predecessor: frontend/day-chart.js:812-980 (installBrush), shipped app
  verdict:  retired
  sanction: Connor · 2026-08-18 · "the presets cover every window I use; the
            drawn window goes."
  replay:   fn R3 asserts absence and prints this sanction line
  status:   retired (permanent)
```

Sweep screenshots and clips live in `mockups/sweep/<surface>/`. Register both the
ledger and that directory in `mockups/INDEX.md`, per resettle's
INDEX-moves-with-the-lock rule.

Entry types are exactly three: **STORY** (observed behavior), **QUESTION** (a
behavior or meaning gap the operator must rule on), and **RETIRED** (a
predecessor behavior deliberately dropped, with its sanction). **RETIRED is not
a waiver** — it is the record a waiver would have replaced.

**Retired entries are permanent.** The ledger stops being a record of only what
the surface does and becomes a record of what it does **and what it deliberately
stopped doing**; the retired entries with their sanctions are the audit trail,
and they stay through every later sweep, port and lock of that surface. Deleting
one leaves either an unrecorded reinstatement or a second undocumented
retirement, and no way to tell which — the same illegible state the pass exists
to prevent, arrived at from the other side.

**There is no waiver entry type.** A drop is always a dated, operator-sanctioned
record, by one of exactly two paths:

- a story that **cites a lock term** → `resettle`; the manifest row is the record
  and the operator's exact authorizing sentence is that resettle's evidence;
- a story with **no lock term** (the ledger's whole reason to exist — resettle
  cannot run where there is no manifest row) → dropped only by an operator ruling
  recorded **inline in the ledger** under a QUESTION entry, his exact sentence
  quoted.

Both paths carry the date and the sanction. A drop path that skips the record is
exactly how a dropped term recurs. A §2 retirement lands as a RETIRED entry
either way; where the retired behavior also touches a manifest row, the
`resettle` is what carries the manifest side, and its date and sanction are the
same ones.

## 6. QUESTION round (one numbered round)

Batch every QUESTION to the operator in **one numbered round** at the end of the
sweep — behavior gaps, meaning-lost-at-scale findings, irreproducible handlers,
and any fixture-set authorization the gate will need (shapes and in-band labeling
authorized together; see the data defaults in SKILL.md's grounding rules).
Answers are recorded inline under their QUESTION entries.

**§2's verdicts get their own round, and it happens before the lock**, since
that pass does. Every row still at `missed` or at an unsanctioned `retired` goes
in it, each stating what the predecessor did, where it was registered, and what
the mock offers instead — a retirement is ruled there or it is not ruled at all.
Answers become `kept` (build it, or `resettle` the lock if it has already closed)
or `retired` with the sanction line written down as given.

## 7. Freeze

Operator approval stamps a header line on the ledger:

```
★ FROZEN <date> · base <sha> · generator <sha> · window <start>..<end>
  · fixtures <name: sha256-prefix, …>   (tripwire, not contract)
  · predecessor <ref, or "none — greenfield">   · retired <n>
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
fixture after freeze requires a recorded reason under the header. **A ledger
carrying a `missed` row cannot be frozen** — the freeze is what makes a verdict
table binding, and freezing an undecided drop is how the retirement becomes
contract without anyone choosing it.

**Ledger + lock manifest together are the build contract.** The manifest alone is
insufficient, in three ways: behaviors and meanings its terms never encoded,
terms no assertion ever exercised, and behaviors the predecessor had that neither
artifact mentions because neither was looking backwards. The ledger's stories
close the first; behavior replay in `build` closes the second; §2's verdicts and
their RETIRED entries close the third.
