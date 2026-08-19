---
name: ui-craft
description: Lifecycle for user-facing surfaces — revise a shipped surface in the running app, lock a greenfield visual spec, build to a lock, critique/audit/polish a UI, or re-settle a locked term. Use for any request to design, review, or verify rendered UI (screens, dashboards, flows, components). Not for backend-only work or module/API design ("interface" in the code sense — use codebase-design for that).
---

# UI craft

One skill for the whole life of a user-facing surface: **revise** a shipped
surface in place, **lock** a greenfield visual spec, **build** to it,
**critique** it, **audit** it, **polish** it, **re-settle** it.
Parts absorbed from `impeccable` (Apache-2.0, by Paul Bakaus — see the repo
NOTICE).

Vocabulary guard: in the engineering charter, *interface* means a module's API.
This skill owns **surfaces** — rendered UI. If the request is about a Python
class, function signature, or module boundary, this is the wrong skill.

## Setup (every invocation)

1. Resolve this skill's installed directory as `UI_CRAFT_SKILL_DIR` (e.g.
   `~/.claude/skills/ui-craft`).
2. Run `node $UI_CRAFT_SKILL_DIR/scripts/context.mjs` once per session
   (`--target <path>` inside a monorepo). It prints PRODUCT.md / DESIGN.md or
   reports `NO_PRODUCT_MD` — in that case follow `reference/init.md` first.
   Ignore any `UPDATE_AVAILABLE` directive; this is a maintained fork.
   If `node` is unavailable or a script here errors, say so, read
   PRODUCT.md / DESIGN.md directly, and continue — the scripts are
   accelerators, not gates.

Before routing any design change:

3. Resolve whether the app already embodies the surface (`shipped` or
   `greenfield`). For a shipped surface, classify local runnability as `runnable`
   or `unavailable`; inspect its `CLAUDE.md` / `AGENTS.md` dev-server declaration
   and classify it as `absent`, `complete`, `incomplete` or `ambiguous`; classify
   its named data source as `manufactured`, `synthetic` or `unknown`.
4. Run `node $UI_CRAFT_SKILL_DIR/scripts/route.mjs --embodiment <state>
   --runnability <state> --declaration <state> --data-source <kind>` and obey its
   mode. A `refuse` result is blocking. `lock-fallback` is the recorded
   predecessor fallback in `reference/revise.md`, not ordinary `lock`
   permission.

For `revise`, `lock`, `build`, and general design invocations only:

5. Read the project's design system: tokens, theme, one representative
   component or page. Use what's there when it works. **The shipped app wins
   over any mock scaffold**: when a repo carries both an app stylesheet and a
   `mockups/` theme, the app is chrome ground truth for every surface that
   has shipped. `revise` operates on that app directly; `lock` mode's step-0
   pre-flight (reference/lock.md) refuses to replace it with a fresh mock.
6. Read the matching register reference: `reference/brand.md` when design IS
   the product (marketing, landing, portfolio), `reference/product.md` when
   design SERVES the product (app UI, dashboards, tools).
7. New project with no committed tokens: run
   `node $UI_CRAFT_SKILL_DIR/scripts/palette.mjs` for a brand seed.

## The contract follows the surface

For a greenfield surface that has been through `lock`, the contract is:

- a `★ LOCKED` header in the mockup HTML, and
- a **lock manifest** — `mockups/<surface>.lock.md` — the checkable inventory
  `build` reads. Format in `reference/lock.md`.

For a surface the app already ships, `revise` bans a from-scratch mock. Its
contract is the frozen **behavior ledger** plus its replay script, exercised
against the built app. The app branch is the visual artifact; screenshots record
the review, but no lock manifest is pinned to an app template.

Rules that bind every mode:

- **No arbitration in private.** If two locked artifacts disagree, a locked
  term collides with the app's shipped design system beyond what the manifest's
  precedence line settles, or a revision drops shipped behavior, stop and ask.
  Implementer judgment never silently overrides a contract.
- **Deviation is recorded.** Any build or refactor that changes a locked term
  goes through `re-settle`; any revision that changes shipped behavior amends
  the frozen behavior ledger. Both paths are dated and sanctioned, never quiet.
- **Evidence over green gates.** A locked surface is done when every manifest
  term has evidence; a revision is done when every behavior story replayed and
  every affected state has before/after evidence. A green suite alone is never
  the finish line.

## Modes

Route on the first word (or obvious intent). Read the mode's reference before
acting — it defines the flow.

| Mode | Job | Reference |
| --- | --- | --- |
| `revise [surface]` | Inventory shipped behavior, then iterate the running app on a branch; never mock the shipped surface from scratch | [reference/revise.md](reference/revise.md) |
| `lock [surface]` | Explore grounded variants for a greenfield surface, converge, lock spec + manifest | [reference/lock.md](reference/lock.md) |
| `behavior-sweep [surface]` | Freeze interactive behavior into a ledger + replay script. `revise` runs it against the built app before design; the lock fallback also diffs a shipped predecessor before locking | [reference/behavior-sweep.md](reference/behavior-sweep.md) |
| `build [surface]` | Implement a locked spec; ship the fidelity ledger | [reference/build.md](reference/build.md) |
| `critique [target]` | Heuristic scoring, slop verdict, persona walkthroughs | [reference/critique.md](reference/critique.md) |
| `audit [target]` | Technical checks (a11y, contrast, responsive, detector) + lock-fidelity audit when a manifest exists | [reference/audit.md](reference/audit.md) |
| `polish [target]` | Pre-ship quality gate; includes the manifest walk | [reference/polish.md](reference/polish.md) |
| `resettle [term]` | Amend a locked term with record-keeping | [reference/resettle.md](reference/resettle.md) |
| `consensus [question]` | Settle a contested design decision via a 3-persona vote-and-negotiate panel (advisory; requires repo personas) | [reference/consensus.md](reference/consensus.md) |
| `init` / `document` | Project context setup / generate DESIGN.md | [reference/init.md](reference/init.md), [reference/document.md](reference/document.md) |

No argument: recommend the 1–3 most useful modes from context (a shipped
surface → `revise`; a greenfield surface or explicitly recorded safe-start
fallback → `lock`; an unlocked fallback mock with no predecessor verdicts →
`behavior-sweep`'s predecessor pass **before** `lock`; frozen manifest for a
greenfield surface with interactive behavior and no behavior ledger →
`behavior-sweep` **before** `build`; open manifest without a fidelity ledger →
`build`; never critiqued → `critique`), then list the table. Never auto-run a
mode.

Three artifacts carry the word *ledger*; always qualify it. The **fidelity
ledger** is one row per manifest term (`build`; `revise` has none). The
**behavior ledger** is
`mockups/<surface>.behavior.md`, one entry per story plus one permanent entry
per sanctioned retirement (`behavior-sweep`). The **surface ledger** is
`mockups/INDEX.md`, one row per surface.

General design invocations with no mode match (e.g. "make this less bland",
"fix the spacing") route by embodiment: shipped surface → `revise`-then-fix;
greenfield surface → `critique`-then-fix. Use
[reference/design-rules.md](reference/design-rules.md) for the craft pass.

## Design rules (all modes)

[reference/design-rules.md](reference/design-rules.md) carries the shared
craft discipline: the design-brief template, token-system-before-components,
typography/color/layout/motion rules, the absolute bans (side-stripes,
gradient text, default glassmorphism, hero-metric template, identical card
grids, eyebrow-on-every-section…), the AI-slop and category-reflex tests, and
the layered critique order. It is required reading for `lock`, `build`, and
any general invocation; the other modes consult it as needed.

## Personas

Persona walkthroughs live in `critique` (five built-in archetypes plus
project-specific ones). **Repo personas win:** if the repo has its own persona
definitions (canonically `.claude/qa/personas/*.md` — written by `init`'s
persona-panel step — or a location named in its CLAUDE.md/AGENTS.md), use
those personas — a diabetic user, a concerned parent — instead of inventing
equivalents, and follow the repo's sweep protocol when one exists. The
`consensus` mode requires these repo personas and refuses to run on generic
archetypes.

**"The repo's sweep protocol" is not `behavior-sweep`.** That phrase means the
repo's persona-driven QA pass — exploratory, judgment-led, run against a live
app to find bugs. `behavior-sweep` is a mode of this skill: mechanical, run
against the **built app** before a revision, or against a locked mock plus its
shipped predecessor on the explicit fallback path. Its output is a contract.
Neither substitutes for the other.

## Grounding rules (inherited from ui-mockups, apply everywhere)

- Ground every artifact in the app's real tokens, shipping UI/chart library
  at its shipping version, and real data shape from a **safe, manufactured
  fixture** — never production, personal, health, credential, or customer
  data. **This is the shared default and it does not bend on convenience.**
- **Real-data inversion — repo-scoped, opt-in.** Some repos invert the rule:
  their build contracts must be grounded in the owner's *own real* data, because
  a fixture cannot reveal what the surface does at real scale. That inversion
  applies **only** where the repo's own `CLAUDE.md`/`AGENTS.md` declares an
  operator-sanctioned real-data protocol (e.g. a read-only snapshot flow), and
  only within that protocol's bounds. Absent that declaration, the manufactured
  default above governs — no exceptions inferred from context or precedent.
  Where the inversion does apply: renders of real personal/health data **never
  commit and never attach to a PR** (a PR is a publish) without the operator's
  exact authorizing sentence quoted in the record; committed and PR-attached
  evidence uses labeled synthetic fixtures, and real-data renders stay local,
  handed to the verifier with the pinned data.
- Vary the concept, not the decoration; three variants that differ only in
  color are one design.
- Inspect rendered output — source review alone never validates a visual
  artifact. Use `drive-local-webapp` for rendering; ask to install it if
  missing.
- **Sibling exactness** ([reference/sibling-fidelity.md](reference/sibling-fidelity.md)):
  any element with a sibling in a shipped surface uses the shipped values
  exactly — geometry, type, alignment spines, chart furniture, and interaction
  idioms alike — and fidelity is proven with a computed-style diff against the
  running app, never by eyeball. Token bridges are verified by computed value
  on the consuming element; mock-global base styles (body font/line-height)
  are banned because they shift extracted chrome off its shipped pixels.
- Keep `mockups/INDEX.md` as the surface ledger (one row per surface:
  Surface / Concept / Status / Issue / File). `locked` rows are binding
  precedent; `shipped` rows defer to the app itself, and are also how the next
  lock finds its predecessor (`behavior-sweep` §2). Every mode that touches
  a lock updates the ledger in the same change — a stale ledger is a defect.
