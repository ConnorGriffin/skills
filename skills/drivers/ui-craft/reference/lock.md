# Mode: lock

Explore a greenfield surface as several genuinely different,
repository-grounded HTML mockups, converge with the reviewer, and end with a
**lock** that a build agent cannot silently drift from: a ★ LOCKED mockup plus a
lock manifest. A surface the app already ships uses `revise`, except for the
explicit safe-start fallback below.

## Review mode

- **Interactive:** keep the server running, give the user live URLs, wait for
  their choice before locking.
- **Headless (AgentFlow):** never wait for browser review. Render required
  states, inspect screenshots and console output, choose the direction that
  best satisfies the brief, and lock it. Save evidence to the orchestrator's
  artifact directory.

## Workflow

### 0. Pre-flight — chrome ground truth (MANDATORY, before any concept work)

A from-scratch mock of a shipped surface is banned. Before any concept work,
check `mockups/INDEX.md`, the app routes and the shipping render modules. If the
app already embodies this surface or the shell containing it, **refuse `lock`
and name `revise`**. This is a blocking verdict, the same class as a `missed`
predecessor behavior.

There is one exception: `revise` pre-flight may have recorded that the repo has
no dev-server declaration and routed the change here as the accepted fallback.
That record must name the absent declaration and state that mockup plus
predecessor inventory is weaker than app-branch iteration. A declared entrypoint
that omits its data source is unsupported, not fallback. Without the fallback
record, `lock` never proceeds on a shipped embodiment.

The fallback does not authorize starting the app. Any live predecessor or chrome
evidence must come through a separately declared safe harness; otherwise record
the missing evidence and let the predecessor QUESTION gate block rather than
guessing.

On a greenfield surface, or on that recorded fallback, a lock round dies at
review when its chrome doesn't match the app the reviewer uses every day. Run
these checks before the ledger, and do not fan out a single variant until the
fidelity gate passes:

1. **Resolve the material ground truth for chrome.** If any locked surface has
   shipped — check `mockups/INDEX.md` for `shipped` rows and the log for port
   commits — the RUNNING APP's own stylesheet is the material truth for
   tokens, chrome, and component styling. The mock scaffold that *authored*
   the design is a stale ancestor the moment the port lands: same design,
   superseded values. Never source chrome from mockup lineage when a shipped
   embodiment exists. (Lesson: ciq-autotune #660 burned three rounds on a
   shell forked from `_theme.css` after #655 had re-materialized the same
   lock onto the app's `--wk-*` layer — wrong ground, wrong radii, wrong
   fonts, wrong button chrome, every round.)
2. **Extract, never transcribe.** Materialize the app's token layer into
   `mockups/_theme-app.css` by script/verbatim copy from the app's stylesheet
   (both themes, plus the app's exact `body` ground and type rules), with a
   header naming the source file and how to refresh it. Post-ship mocks link
   this sheet; the legacy scaffold `_theme.css` serves only surfaces that
   predate the port. When two token layers coexist, SCAFFOLD.md must name
   which is ground truth — silence here is the defect that lets the next
   round anchor wrong.
3. **Round-zero fidelity gate.** Render the empty shell/chrome (no concept
   content) and put it beside a screenshot of the safely running app, or an
   operator-provided base capture on fallback. Chrome —
   ground color, fonts, control sizes, radii, bar heights — must be
   indistinguishable BEFORE variants are briefed; save the pair as evidence.
   A reviewer should never have to argue the background color mid-round.
4. **Chart medium check.** If the surface charts, the mock renders with the
   app's shipping chart library at its shipping version from step one — a
   hand-rolled SVG facsimile invalidates every judgment made on it.

### 1. Ledger

Read `mockups/INDEX.md` (create if absent; one row per surface, columns
Surface / Concept / Status / Issue / File). `locked` entries are binding
precedent for adjacent surfaces; for `shipped` entries the app is ground
truth, not old mockup markup. On the recorded fallback path, a `shipped` row
covering this surface or the one it replaces also **triggers the predecessor
pass** (§9.3) — note it here, where it is cheap, rather than discovering it at
lock time. Outside that fallback, the row triggers the refusal above.

### 2. Grounding kit

Collect: the screen and its primary user question; visual tokens and their
source files; UI/chart library and version; the shipping render module; real
data shape from a safe fixture; required states (empty, typical, dense,
error, mobile, light, dark). Save runtime captures as
`mockups/<surface>.capture.json`, gitignored unless deliberately manufactured
and free of sensitive data.

### 3. Brief

Write the design brief from `design-rules.md` (job, audience and setting,
direction, signature move, density, constraints, anti-references) plus: one
surface, one decision, hard constraints, states to render, and three or four
named concept directions that differ in layout metaphor, information
hierarchy, or interaction model — not decoration. Use `scope`'s interview mode to
sharpen the brief when installed.

### 4. Prep the shared scaffold

The scaffold is **repo-global, prepped once and extended per surface**: the
first lock round in a repo creates it (extracted from an approved existing
mockup if one exists, else built fresh, by the orchestrator or one cheap prep
agent); every later surface's prep step *extends* the existing files — new
mockbar states, new capture names — and never rewrites or forks them. The
fixed filenames are the point: one theme, one shell, shared by every surface's
variants.

- `mockups/_theme.css` — theme tokens (light+dark), base page/card styles,
  the mock-shell layout (a plain width-constrained column).
- `mockups/_shell.js` — ES module: `loadCapture(name)` fetch glue for the
  capture fixtures, `renderMockBar()` (state + theme toggle groups,
  `?theme=dark` deep-link), `resolveColors()` for theme-aware chart options.
- `mockups/SCAFFOLD.md` — ~30 lines telling variant agents what the scaffold
  provides, how to link it, and what remains theirs (concept-specific markup
  and chart render logic).

`resolveColors()` and the chart-library CDN line exist only when the surface
family actually charts — a chartless repo's scaffold omits them. The CDN
`<script>` tag cannot live in the ES module (load order); it stays a
documented copy-paste line in SCAFFOLD.md.

**Mock chrome is recessive:** width constraint, state/theme toggles, one-line
concept note — no device bezels, frames, or decoration. Chrome that exists to
serve the mockup gets out of the way.

### 5. Fan out

One fresh subagent per concept, using
[variant-agent-prompt.md](variant-agent-prompt.md) filled with the grounding
kit, shared brief, and SCAFFOLD.md. Each writes `mockups/<surface>-<concept>.html` (+
`-chart.js` when render logic is non-trivial). Sequential with isolated
briefs if parallel agents are unavailable.

### 6. Render and inspect

Serve `mockups/` over HTTP; render every required state with
`drive-local-webapp`; inspect the actual images and console errors.
Screenshots go outside the repo.

### 7. Review tersely

One line of design bet + one line of judgment per variant; recommend one.
Incorporate feedback by re-rendering, not arguing from source.

### 8. Persona round and craft gate

Walk the primary task as 2–3 relevant personas (repo personas first — see
SKILL.md); name the first concrete element that stalls each walkthrough and
fix it. Then run the `audit` technical checks (contrast, keyboard focus,
overflow, target sizes) on the finalist.

**On the recorded fallback path, run the predecessor inventory on the finalist
here** ([behavior-sweep.md](behavior-sweep.md) §2) and take its
QUESTION round to the operator with the rest of this gate's findings. This is
the last point at which a dropped interaction is still a design conversation
rather than an amendment to a merged contract. The personas walk the mock and the
audit measures the mock; neither can catch what the mock does not contain,
because neither is looking at anything else.

### 9. Lock

Locking is complete only when ALL of these exist:

1. **★ LOCKED header** in the winning HTML (+ companion JS), dated and
   attributed, carrying the narrative spec as today.
2. **Consistency check across locked artifacts.** Read every artifact the
   lock touches — sibling mockups (desktop/mobile), copy specs, glossaries,
   prior locks being superseded. Any contradiction is resolved *now*, by the
   user (interactive) or explicitly in the header (headless) — never left
   for the implementer to arbitrate.
3. **The predecessor diff on the recorded fallback or a legacy lock.** If a
   `shipped` row in `mockups/INDEX.md` covers this surface or the one it
   replaces, or a prior lock is being superseded, or the running app already
   does this job, then `behavior-sweep`'s **predecessor inventory**
   ([behavior-sweep.md](behavior-sweep.md) §2) has run and every predecessor
   behavior carries a verdict: `kept`, `deferred` to a term this manifest states
   and an omitting build would violate, or `retired` with its sanction line. **A
   `missed` row blocks the lock.** So does an unsanctioned `retired` row, and so
   does one whose only sanction is a term of this very manifest — a lock cannot
   sanction the omissions it is itself freezing. A greenfield surface records the
   one-line skip and moves on.

   **This one pass precedes the lock; the rest of the sweep follows it — and the
   ordering is the whole point.** The rest needs a frozen mock, so it cannot run
   earlier; this pass needs the finalist only as a diff target, so it can. Lock
   first and the record inverts: **the lock is what turns a retirement into
   contract**, so a pass that runs afterwards is not deciding anything, it is
   transcribing a decision the project already made by omission — and every
   later mode reads the lock, so the omission is now the spec. A real Diagnose
   lock froze the retirement of a shipped drag-to-draw selection window its mock
   had simply never implemented. Ten exploration rounds, a persona panel and a
   52-run audit all read the mock, and a mock-side reading cannot see an absence;
   the operator caught it by eye on a screenshot after the lock merged. Nothing
   in that sequence was skipped. The sequence had no step that looked backwards,
   and this is that step.
4. **The lock manifest** — `mockups/<surface>.lock.md` (format below).
5. Losing variants and their screenshots deleted — but never the scaffold
   files (`_theme.css`, `_shell.js`, `SCAFFOLD.md`), which the locked mock
   links and other surfaces share; `mockups/INDEX.md` set to `locked`,
   pointing at mock + manifest; the implementation issue references both.

After implementation ships, set the surface-ledger row to `shipped`, archive the
mockup, and delete that surface's `TARGET=mock` CI leg; the app becomes the
source of truth. **All three land in the port PR itself** — the PR that turns the
app-opener replay leg green — never in a follow-up issue, which is how a surface
stays `locked` long after it merged. The mock, its screenshots, the manifest and
the behavior ledger stay as the design record, and the ledger's stories keep
running against the built app forever; post-ship hotfixes owe no mock pass and no
mock sync, and later design work starts with `revise` from the shipping app
rather than a runnable mock. `resettle` remains only for terms in the archived
lock.

## Lock manifest format

The manifest is the machine-walkable extraction of the header prose. The
header stays the narrative; the manifest is the contract.

```markdown
# Lock manifest — <surface>
Locked: <date> by <who>   Mocks: <files, incl. the scaffold files the mock links (_theme.css, _shell.js)>   Supersedes: <prior lock, the shipped surface it replaces + its source path, or —>

## Precedence
<One sentence: which artifact wins for component-level styling when the mock
and the app's shipped design system disagree. Default: the mock wins for
anything it states explicitly; the app system wins for anything it doesn't.>

## Terms
| # | Term | Kind | Evidence expected |
|---|------|------|-------------------|
| 1 | No page scroll at 1280x800 or 1440x900 | gate | browser-gate assertion |
| 2 | Primary button tinted, never solid; min-height 36px; radius 8px | gate | assertion |
| 3 | Outcome excursion aligns vertically with its setting block | eye | paired render |

## Fixture obligations
<What the fixture must exercise for the locked visuals to be provable —
e.g. "glucose spread wide enough that the p10–90 envelope is visible and the
low-tail fill fires". A fixture that cannot show a term cannot prove it.>

## Verbatim strings
<Legend chips, labels, button text — copied exactly from the mock, so text
drift is a diff, not a judgment call.>
```

**`Supersedes:` is how the predecessor stays findable.** The surface ledger
identifies it by its `shipped` row — and that row flips to `locked` in this same
change, so from then on this line is the only record of what this surface
replaced. Name the shipped surface and where its behavior is registered, not just
a prior lock; a bare `—` on a replacement surface reads as greenfield to the next
round, and a greenfield surface skips the predecessor pass.

Rules for writing terms:

- Every load-bearing sentence in the header becomes a numbered term. If it's
  precise enough to violate, it's precise enough to list.
- `gate` = mechanically assertable (geometry, overflow, colors, counts,
  text). `eye` = needs rendered human/vision judgment. When in doubt, `gate`
  — an assertable term that goes unasserted is how drift ships.
- Terms carried forward from a superseded lock are restated here, not
  referenced — the manifest must stand alone.
- **A surface with more than one view/mode/tab owes two extra terms: which one
  is the default, and what chrome persists across all of them.** Name the
  switcher itself as persistent chrome. Both are the kind of thing a lock is
  silent on because it felt obvious while the mock was open in front of you,
  and silence is what a builder resolves in private.
- **"Mounts <existing surface> unchanged" is not a term — it is a hole.** When
  one view hands off to a sibling or shipped surface, say what the host keeps
  on screen around it. Read literally, "unchanged" licenses dropping the
  navigation that got the reader there, which is exactly how a real Diagnose
  lock shipped a view you could enter and never leave. If a rail's contents
  differ per view, spell out each view's contents rather than describing the
  rail once from whichever view you happened to be designing.
