# Mode: lock

Explore a surface as several genuinely different, repository-grounded HTML
mockups, converge with the reviewer, and end with a **lock** that a build
agent cannot silently drift from: a ★ LOCKED mockup plus a lock manifest.

## Review mode

- **Interactive:** keep the server running, give the user live URLs, wait for
  their choice before locking.
- **Headless (AgentFlow):** never wait for browser review. Render required
  states, inspect screenshots and console output, choose the direction that
  best satisfies the brief, and lock it. Save evidence to the orchestrator's
  artifact directory.

## Workflow

### 1. Ledger

Read `mockups/INDEX.md` (create if absent; one row per surface, columns
Surface / Concept / Status / Issue / File). `locked` entries are binding
precedent for adjacent surfaces; for `shipped` entries the app is ground
truth, not old mockup markup.

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

### 4. Fan out

One fresh subagent per concept, using
[variant-agent-prompt.md](variant-agent-prompt.md) filled with the grounding
kit and shared brief. Each writes `mockups/<surface>-<concept>.html` (+
`-chart.js` when render logic is non-trivial). Sequential with isolated
briefs if parallel agents are unavailable.

### 5. Render and inspect

Serve `mockups/` over HTTP; render every required state with
`drive-local-webapp`; inspect the actual images and console errors.
Screenshots go outside the repo.

### 6. Review tersely

One line of design bet + one line of judgment per variant; recommend one.
Incorporate feedback by re-rendering, not arguing from source.

### 7. Persona round and craft gate

Walk the primary task as 2–3 relevant personas (repo personas first — see
SKILL.md); name the first concrete element that stalls each walkthrough and
fix it. Then run the `audit` technical checks (contrast, keyboard focus,
overflow, target sizes) on the finalist.

### 8. Lock

Locking is complete only when ALL of these exist:

1. **★ LOCKED header** in the winning HTML (+ companion JS), dated and
   attributed, carrying the narrative spec as today.
2. **Consistency check across locked artifacts.** Read every artifact the
   lock touches — sibling mockups (desktop/mobile), copy specs, glossaries,
   prior locks being superseded. Any contradiction is resolved *now*, by the
   user (interactive) or explicitly in the header (headless) — never left
   for the implementer to arbitrate.
3. **The lock manifest** — `mockups/<surface>.lock.md` (format below).
4. Losing variants and their screenshots deleted; `mockups/INDEX.md` set to
   `locked`, pointing at mock + manifest; the implementation issue references
   both.

After implementation ships, set the ledger row to `shipped` and archive the
mockup; the app becomes the source of truth.

## Lock manifest format

The manifest is the machine-walkable extraction of the header prose. The
header stays the narrative; the manifest is the contract.

```markdown
# Lock manifest — <surface>
Locked: <date> by <who>   Mocks: <files>   Supersedes: <prior lock or —>

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

Rules for writing terms:

- Every load-bearing sentence in the header becomes a numbered term. If it's
  precise enough to violate, it's precise enough to list.
- `gate` = mechanically assertable (geometry, overflow, colors, counts,
  text). `eye` = needs rendered human/vision judgment. When in doubt, `gate`
  — an assertable term that goes unasserted is how drift ships.
- Terms carried forward from a superseded lock are restated here, not
  referenced — the manifest must stand alone.
