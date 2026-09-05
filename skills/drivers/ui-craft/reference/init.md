# Init Flow

The setup command for a project. One codebase crawl feeds everything it writes:

- **PRODUCT.md** (strategic): root project file for register, target users, product purpose, brand personality, anti-references, strategic design principles. Answers "who/what/why".
- **DESIGN.md** (visual): root project file for visual theme, color palette, typography, components, layout. Follows the [DESIGN.md format spec](https://raw.githubusercontent.com/google-labs-code/design.md/main/docs/spec.md). Answers "how it looks".
- **`.claude/qa/personas/`** (reviewer personas): 3 distinct user-situation personas with lens, job, and concrete rules, plus a RANKING.md for tie-breaks. Fed to `/ui-craft critique` and required by `/ui-craft consensus`.
- **`.impeccable/live/config.json`** (live mode): pre-configured so `/ui-craft live` boots straight into variant mode with no first-time detour.

It closes by pointing the user at the best command to run next. Every other impeccable command reads PRODUCT.md and DESIGN.md before doing any work.

## Step 1: Load current state

Check what already exists. PRODUCT.md and DESIGN.md live at the project root, or under `.agents/context/` or `docs/` (case-insensitive). Read whichever are present with your native file tool. Also note whether `.impeccable/live/config.json` already exists (Step 7 leaves it untouched if so).

Decision tree:
- **Neither file exists (empty project or no context yet)**: do Steps 2-4 (write PRODUCT.md), then decide on DESIGN.md based on whether there's code to analyze.
- **PRODUCT.md exists, DESIGN.md missing**: skip to Step 6 and offer to run `/ui-craft document` for DESIGN.md.
- **PRODUCT.md exists but has no `## Register` section (legacy)**: add it. Infer a hypothesis from the codebase (see Step 2), confirm with the user, write the field.
- **Both exist**: ask which file to refresh and skip the one the user does not want changed. Use the host's supported choice interface when permitted; otherwise present the substantive alternatives and costs in prose with a stable question identifier, then wait for the answer.
- **Just DESIGN.md exists (unusual)**: do Steps 2-4 to produce PRODUCT.md.

Never silently overwrite an existing file. Always confirm first.

If init was invoked as a setup blocker by another command, such as `/ui-craft craft landing page`, pause that command here. Complete init, then resume the original command. Your own writes are the freshest source; no reload needed. For craft, resume into shape next; init creates project context, but it is not a substitute for the task-specific shape interview and confirmed design brief.

## Step 2: Explore the codebase

Before asking questions, thoroughly scan the project to discover what you can. This single crawl feeds PRODUCT.md, DESIGN.md, **and** the live-mode framework detection in Step 7, so be thorough once rather than re-scanning later:

- **README and docs**: Project purpose, target audience, any stated goals
- **Package.json / config files**: Tech stack, dependencies, existing design libraries, **and the framework** (Vite/SPA, Next.js, Nuxt, SvelteKit, Astro, multi-page static) plus the HTML entry the browser actually loads
- **Existing components**: Current design patterns, spacing, typography in use
- **Brand assets**: Logos, favicons, color values already defined
- **Design tokens / CSS variables**: Existing color palettes, font stacks, spacing scales
- **Any style guides or brand documentation**

Also form a **register hypothesis** from what you find:

- Brand signals: `/`, `/about`, `/pricing`, `/blog/*`, `/docs/*`, hero sections, big typography, scroll-driven sections, landing-page-shaped content.
- Product signals: `/app/*`, `/dashboard`, `/settings`, `/(auth)`, forms, data tables, side/top nav, app-shell components.

Register is a hypothesis at this point, not a decision; Step 3 confirms it.

Note what you've learned and what remains unclear. Also note any rough edges worth a follow-up command (thin hierarchy, flat or gray palette, missing error/empty states, dull copy); Step 8 turns these into concrete recommendations without re-analyzing.

## Step 3: Ask strategic questions (for PRODUCT.md)

Ask only about what you could not infer from the codebase. Use the host's supported
choice interface when permitted; otherwise present substantive alternatives and
costs in prose with a stable question identifier, then wait for the answer.

### Interview mode, not confirmation mode

If the repo is empty or the user's brief is sparse, run a short interview before proposing PRODUCT.md. Do **not** turn a one-sentence request into a complete inferred PRODUCT.md and ask for blanket confirmation.

- Use the harness's structured question tool when one exists. Otherwise, ask directly in chat and stop.
- Ask **2-3 questions per round**, then wait for answers.
- Use inferred answers as hypotheses or options, not as finished facts.
- Complete at least one real user-answer round before drafting PRODUCT.md, unless every required answer is directly discoverable from repo docs.
- Round 1 should establish register, users/purpose, and desired outcome.
- Round 2 should establish brand personality or references, anti-references, and accessibility needs.

### Minimum viable interview

Ask enough to complete PRODUCT.md. At minimum, cover register confirmation, users and purpose, brand personality, anti-references, and accessibility needs unless each answer is directly discoverable from repo context. After at least one interview round, you may propose inferred answers, but the user must confirm them before you write PRODUCT.md. Never synthesize PRODUCT.md from the original task prompt alone.

### Register (ask first; it shapes everything below)

Every design task is either **brand** (marketing, landing, campaign, long-form content, portfolio: design IS the product) or **product** (app UI, admin, dashboards, tools: design SERVES the product).

If Step 2 produced a clear hypothesis, lead with it: *"From the codebase, this looks like a [brand / product] surface. Does that match your intent, or should we treat it differently?"*

If the signal is genuinely split (e.g. a product with a big marketing landing), ask which register describes the **primary** surface. The register can be overridden per task later, but PRODUCT.md carries one default.

### Users & Purpose
- Who uses this? What's their context when using it?
- What job are they trying to get done?
- For brand: what emotions should the interface evoke? (confidence, delight, calm, urgency)
- For product: what workflow are they in? What's the primary task on any given screen?

### Brand & Personality
- How would you describe the brand personality in 3 words?
- Reference sites or apps that capture the right feel? What specifically about them?
  - Push for specific named references with the *specific* thing about them that fits this brand, not generic "modern" adjectives or category-bucket lanes.
- What should this explicitly NOT look like? Any anti-references?

### Accessibility & Inclusion
- Specific accessibility requirements? (WCAG level, known user needs)
- Considerations for reduced motion, color blindness, or other accommodations?

Skip questions where the answer is already clear. **Do NOT ask about colors, fonts, radii, or visual styling here.** Those belong in DESIGN.md, not PRODUCT.md.

## Step 4: Write PRODUCT.md

Write PRODUCT.md only after the user has confirmed the strategic answers from Step 3. If an inferred answer is uncertain or unconfirmed, ask before writing.

Synthesize into a strategic document:

```markdown
# Product

## Register

product

## Users
[Who they are, their context, the job to be done]

## Product Purpose
[What this product does, why it exists, what success looks like]

## Brand Personality
[Voice, tone, 3-word personality, emotional goals]

## Anti-references
[What this should NOT look like. Specific bad-example sites or patterns to avoid.]

## Design Principles
[3-5 strategic principles derived from the conversation. Principles like "practice what you preach", "show, don't tell", "expert confidence". NOT visual rules like "use OKLCH" or "magenta accent".]

## Accessibility & Inclusion
[WCAG level, known user needs, considerations]
```

Register is either `brand` or `product` as a bare value. No prose, no commentary.

Write to `PROJECT_ROOT/PRODUCT.md`. If `.impeccable.md` existed, the loader already renamed it; merge into that content rather than starting from scratch.

## Step 5: Derive the persona panel

Personas feed directly into `/ui-craft critique` (walkthrough scoring) and are **required** by `/ui-craft consensus` (group review). Build them now.

From the freshly written PRODUCT.md, extract exactly 3 reviewer personas — distinct real user **situations**, not demographic sketches. A situation is the concrete context when someone uses this product: *e.g. printed recipe cards → mid-cook glancer, first-time cook, shopper*. If the product has only two genuine situations, split the heavier one into two lenses (first-time vs repeat, or different stages of the job).

**Draft** each persona as `.claude/qa/personas/<name>.md` with:
- **Lens**: the single question they judge everything by (*e.g. "does this stay readable mid-hands-full?"*)
- **Job**: what they concretely do when reviewing a rendered surface (*e.g. "glance mid-cooking, spot what changed, move on"*)
- **Rules/red flags**: what they must flag, in specifics—not vague ("is clear") but concrete (*e.g. "text smaller than 14px", "requires two-step navigation", "lacks progress indicator"*)

Model the format on a stress-tester: lens + job + concrete rules, no fluff.

Also draft `.claude/qa/personas/RANKING.md` with: the tie-break order derived from the product's PRIMARY use per PRODUCT.md (e.g. *"cards are used while cooking → glancer outranks shopper on ties"*), one sentence of justification. If primacy is genuinely unclear, ask the user one question and record the answer.

**Confirm the drafted personas with the user** before writing files (same etiquette as Step 4). If `.claude/qa/personas/` already exists, offer a refresh per file rather than silently overwriting.

## Step 6: Decide on DESIGN.md

Offer `/ui-craft document` either way. Two paths:

- **Code exists** (CSS tokens, components, a running site): "I can generate a DESIGN.md that captures your visual system (colors, typography, components) so variants stay on-brand. Want to do that now?"
- **Pre-implementation** (empty project): "I can seed a starter DESIGN.md from five quick questions about color strategy, type direction, motion energy, and references. You can re-run once there's code, to capture the real tokens. Want to do that now?"

If the user agrees, delegate to `/ui-craft document` (it auto-detects scan vs seed). Load its reference and follow that flow.

If the user prefers to skip, mention they can run `/ui-craft document` any time later.

## Step 7: Configure live mode (when code exists)

Live mode is not part of this fork (it stayed with the upstream impeccable skill); skip live-mode pre-configuration entirely.

## Step 8: Recommend starting points, then wrap up

Summarize tersely:
- Register captured (brand / product)
- What was written (PRODUCT.md, DESIGN.md, live config, or a subset)
- The 3-5 strategic principles from PRODUCT.md that will guide future work
- If DESIGN.md or live config is pending, one line on how to set it up later

Then recommend the **best commands to run next**, drawn from what your Step 2 crawl already surfaced. Do not run a fresh analysis here; surface observations you already have. Tailor to register and to what you saw, offer the 2-4 most relevant (not a menu dump), and give the exact command to type. Group by intent:

- **Build something new**: `/ui-craft craft <feature>` (shape, then build end-to-end) or `/ui-craft shape <feature>` (plan first). Lead with this for empty or early-stage projects.
- **Improve what's there**: name the specific surface. `/ui-craft critique <page>` for a scored UX review; `/ui-craft audit <area>` for a11y / perf / responsive checks; `/ui-craft polish <component>` for a pre-ship pass. When the crawl flagged a specific weakness, point the matching command at it: thin hierarchy or spacing → `layout`, flat or gray palette → `colorize`, missing error / empty states → `harden` or `onboard`, dull or unclear copy → `clarify`.
- **Iterate visually**: `/ui-craft live` (configured in Step 6) to pick elements in the browser and generate variants in place.

The full command menu is one bare `/impeccable` away; keep this list short and pointed.

If init was invoked as a blocker by another impeccable command (e.g. the user ran `/ui-craft polish` with no PRODUCT.md), resume that original task now. Your own writes are the freshest source; no reload needed.

Optionally ask whether they want a brief PRODUCT.md summary appended to CLAUDE.md. Do not write it unless they explicitly agree; then append a short **Design Context** pointer section.
