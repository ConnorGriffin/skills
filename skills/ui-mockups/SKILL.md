---
name: ui-mockups
description: Explore a UI surface as several radically different, repository-grounded HTML mockups, render them, and converge on a locked visual specification. Use when asked to design, mock up, compare, or redesign a screen, dashboard, flow, or component before implementation.
---

# UI mockups

Produce several genuinely different HTML mockups using the target application's
real visual language, data shape, and rendering stack. Render every variant,
iterate with the reviewer, and preserve one locked mockup as the implementation
specification.

Use `drive-local-webapp` to render and exercise the mockups. If it is not
installed, ask to install it from this repository before the screenshot phase.
Use parallel subagents when the client supports them. Optional interviewing,
module-design, and visual-audit skills may improve the workflow, but their
absence is not a blocker.

## Choose the review mode

- **Interactive mode:** keep the server running, give the user the live URLs,
  and wait for their choice before locking a direction.
- **AgentFlow/headless mode:** never wait for browser review. Render the required
  states, inspect screenshots and console output, choose the direction that best
  satisfies the brief, and lock it. Produce the screenshots in the
  orchestrator's evidence/artifact directory plus
  `mockups/<surface>.locked.md`: a contract of at most 150 words stating the
  chosen concept, primary behavior, required states, details implementation
  must preserve, and evidence paths.

## Ground rules

1. **Ground every variant.**
   - Read `DESIGN.md` and `PRODUCT.md` when present, then verify their claims
     against the shipping frontend.
   - Lift actual light and dark theme tokens, fonts, radii, and shadows.
   - Use the application's shipping UI or chart library at its shipping version.
   - Prefer a deliberately manufactured fixture with the real schema. A
     captured payload must come from a throwaway development/demo environment.
     Never collect production, private, personal, health, credential, or
     customer data for a mockup.
   - Fork relevant render logic so the winner can be lifted into the app.
2. **Vary the concept, not the decoration.** Change the layout metaphor,
   information hierarchy, interaction model, or visualization. Three variants
   that differ only in color are one design.
3. **Mark throwaway chrome.** Label variant switchers, seed controls, and other
   mock-only scaffolding in comments.
4. **Inspect rendered output.** Source review alone does not validate a visual
   artifact.

## Workflow

### 1. Establish the ledger

Read `mockups/INDEX.md`. Create it if absent. Record one row per surface:

```markdown
| Surface | Concept | Status | Issue | File |
| --- | --- | --- | --- | --- |
```

Treat `locked` entries as binding precedent for adjacent surfaces. For
`shipped` entries, use the application itself as ground truth rather than old
mockup markup.

### 2. Build a grounding kit

Collect:

- the relevant screen and its primary user question;
- visual tokens and their source files;
- the UI/chart library and version;
- the shipping render module or component;
- the real data shape from a safe fixture or throwaway demo environment;
- required states such as empty, typical, dense, error, mobile, light, and dark.

Save runtime captures as `mockups/<surface>.capture.json` and add
`*.capture.json` to `.gitignore`. Do not commit captures unless they are
deliberately manufactured fixtures containing no sensitive data.

### 3. Fix the brief

Define one surface, one decision, hard constraints, states to render, and three
or four named concept directions. A short inline interview is enough when no
interviewing skill is installed.

### 4. Fan out

Give one fresh subagent exactly one concept. Fill in
[the variant prompt](references/variant-agent-prompt.md) with the grounding kit
and shared brief. Each agent writes:

- `mockups/<surface>-<concept>.html`;
- `mockups/<surface>-<concept>-chart.js` when rendering logic is non-trivial.

If parallel agents are unavailable, create the variants sequentially while
keeping each concept brief isolated from the others.

### 5. Render and inspect

Serve `mockups/` over HTTP, then use `drive-local-webapp` to render every
required state. Store screenshots in a temporary directory outside the
repository. Inspect the actual images and console errors.

In interactive mode, keep the server alive for review. Open the served URLs
when the environment and user permit browser control; otherwise return the
URLs. In AgentFlow/headless mode, save the rendered evidence and continue
without opening a browser or waiting for a person.

### 6. Review tersely and iterate

For each variant, give one line describing its design bet and one line of
judgment. Recommend one direction. Incorporate review feedback in a new render
round rather than arguing from source.

### 7. Lock the winner

For interaction-heavy finalists, walk the primary task with two or three useful
perspectives: an impatient expert, a confused first-time user, a keyboard-only
user, a stress tester, or a distracted mobile user. Name the first concrete
element that stalls each walkthrough and fix it.

Run an installed visual-audit skill on the finalist when available; otherwise
check contrast, keyboard focus, responsive overflow, and target sizes directly.
Then:

1. Add a `LOCKED` header comment to the winning HTML and companion JavaScript.
2. In AgentFlow/headless mode, write the required 150-word-or-shorter locked
   contract and retain its evidence screenshots.
3. Delete losing variants and their screenshots.
4. Update `mockups/INDEX.md` with status `locked`.
5. Reference the locked file from the implementation issue.

After implementation ships, set the ledger row to `shipped` and archive the
mockup. The application then becomes the source of truth.
