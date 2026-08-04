# Per-variant prompt

Fill every placeholder. Give one fresh subagent one concept and no sibling
implementation details.

```markdown
Design one UI mockup variant. Commit to the assigned concept; do not blend it
with the sibling directions.

## Assigned concept

<concept name> — <layout, visualization, and interaction bet; explain how it
differs from the named sibling concepts>

## Surface and decision

<screen or component, the one question it must answer, and hard constraints>

## Shared scaffold (mandatory)

`mockups/_theme.css` and `mockups/_shell.js` exist for this surface — read
`mockups/SCAFFOLD.md` and follow it. Link the stylesheet, import the module,
use `loadCapture()`, `renderMockBar()`, and `resolveColors()` from it. Do NOT
re-implement theme tokens, base card styles, mockbar chrome, or fetch glue —
build only the concept-specific markup and chart render logic.

## Grounding kit

- Theme: <tokens copied from the named source files, light and dark>
- UI/chart library: <library, exact version, and existing loading pattern>
- Data: `fetch('./<surface>.capture.json')` using <real field names and shape>
- Render source: <shipping module or component to fork>

Use only the safe development fixture or captured demo payload supplied here.
Do not access production, customer, credential, health, or personal data.

## Required states

<empty, typical, dense, error, mobile, light, dark, or named fixture states>

## Deliverables

- `mockups/<surface>-<concept>.html`
- `mockups/<surface>-<concept>-chart.js` when rendering is non-trivial

Lift the shipping theme and library. Bind the real fields. Mark mock-only
controls with a `not part of the real app` comment. Do not start a server or
take screenshots; the orchestrator handles rendering.

Report the files written and one sentence describing the design bet.
```
