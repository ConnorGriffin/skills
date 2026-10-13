# Tools

How `lock`, `library`, `build`, `revise`, and `review` use the harness's own design and
browser tooling. The skill does not ship its own copies of these jobs. Each
claim below comes from the cited docs or the tool's own description, and
anything not verified there is marked unverified.

Sources:

- Claude Code artifacts: <https://code.claude.com/docs/en/artifacts>
- Claude Design: <https://support.claude.com/en/articles/14604416-get-started-with-claude-design>
- Claude in Chrome: <https://code.claude.com/docs/en/chrome>

## Design system for the canvas

- **Once the project has a component library** (after the library stage, or one
  the repo already has): run `/design-sync` from the repo root. It mirrors a
  compilable component library or Storybook into a design-system project, so
  canvases mount the real components. Import quality follows the source's
  quality. Exact sync mechanics are unverified.
- **Before the library exists, and on the plain-DOM path:** `/design-sync` has
  nothing to mirror, so skip it. Write the palette, type scale, radius, and
  spacing into the lock doc's `Tokens`, copied from the app's stylesheet. If
  canvases should pick them up, also publish a tokens-only **Design System**
  artifact (the Artifact tool's Design System type). That type holds a README,
  tokens across themes, the type scale, and components with live previews, and
  the agents building canvases read it.
- When the account lists a default design system for the Design type, the
  canvas uses it. For a product surface, make sure that default is the
  project's own system.

## Library stack

- **Best supported: React + TypeScript + Storybook.** The tooling works best
  here: the Storybook MCP server lets an agent read stories, `/design-sync`
  mirrors the library, and per-story screenshots come straight from Storybook's
  story iframes. The Storybook MCP's setup details are unverified.
- **No-framework alternative: Web Components with Storybook.** It keeps
  stories and per-story screenshots, but tool support is weaker. Treat
  `/design-sync` coverage as unverified until one component round-trips.
- **A repo with no component library** records the stack choice as an ADR in
  the `library` ticket, the first code ticket, before its first component
  ([library.md](library.md)). The ADR states the stack, why, and what the
  plain-DOM path would have lost.
- **Declining a library** takes the plain-DOM path in [lock.md](lock.md):
  review at screen grain, and no sync.

## Directions on a Design canvas

Make designs with the Artifact tool's **Design** type, a canvas of live
artboards:

1. Run the Artifact `quickstart` with intent `design`.
2. Publish once with the Design type's `type_url` and a title.
3. Fill the canvas through the type's own instructions.

The operator can also start one with `/design <brief>` where their Claude Code
offers it. The skill never depends on that command.

- Each artboard is an HTML file under `project/` on the canvas. Read the
  artboards back and run `precheck.py` on them. The type tells agents never to
  verify unless asked. This skill's prechecks and browser pass are the
  operator's standing request, so they run.
- The type's sizes are 390×844 for a phone screen and a page width of
  1280–1440. Set `Frames:` to match.
- The brief carries the approved structure sections, the frames, the bans, and
  this line: "three directions that differ in concept and layout, not color;
  every frame; manufactured data only".
- Canvases start private, and the operator shares them from the page.

**Fallback when the Design type is unavailable** (not listed, turned off for
the organization, or a session that cannot publish artifacts): write each
direction as one self-contained HTML page and publish each as an ordinary
artifact. Artifacts need a claude.ai login, and API-key sessions cannot publish
them. If artifacts are unavailable too, render the pages locally in the
browser and share screenshots instead.

## Comments

Pointed feedback arrives as artifact comments. The operator selects an element
on the canvas or page and comments, and the publishing session receives the
comment through ArtifactComments. On an ordinary artifact, an editor uses
**Send to Claude** or mentions `@claude`.

**Echo every received comment back to the operator before acting**, as a
numbered list, and ask them to name anything missing. Both paths have
documented delivery failures:

- Design's inline comments sometimes do not appear, or disappear before Claude
  reads them; the fix is pasting them into chat.
- An artifact's comment watch can end after several hours without activity.
- Watching stops when the delivery service is unavailable.
- Auto-replies pause after 60 sent comments in an hour.

## Rendered verification

Use Claude in Chrome or the desktop app's built-in browser. Start a dev server
only through the repo's declared safe entrypoint. **Size the viewport to the
frame first**, for example with the built-in browser's window resize. A hidden
or unsized pane reports a viewport 0 wide, and every page then looks like it
overflows. Render each approved screen and state at every frame, read the
console, and screenshot. Then measure what the static precheck cannot see:

```js
(() => { const w = document.documentElement.clientWidth;
  if (!w) return { error: 'viewport has no width: size the window to the frame first' };
  return { frame: w, overflow: document.documentElement.scrollWidth > w,
    buttonHeights: [...new Set([...document.querySelectorAll('button,[role=button]')]
      .map(b => Math.round(b.getBoundingClientRect().height)))] }; })()
```

The checks:

- `frame` must equal the frame being checked.
- `overflow: true` fails the same way a precheck fails.
- More distinct `buttonHeights` than `Button sizes:` also fails.

To run `precheck.py` on the running build, save the page's
`document.documentElement.outerHTML` to a local file named `-<width>.html`, or
add `data-frame`. Real-data renders stay in the local browser.

## Cold critique and verifier subagents

Dispatch a fresh subagent and name its model on every dispatch (the top tier
for craft judgment). Give it read-only tools with no shell and no edit. It
gets only the lock doc and the render paths or screenshots, never the
transcript or the author's rationale. Its prompt:

```text
You did not make this design. Judge the renders against the lock doc only.
Report each finding as: lock section or rule, screen and frame, what is wrong,
the smallest fix. Then check design-rules.md's bans and slop test, and walk the
primary task as <repo personas, else two built-in archetypes>. Name the first
element that stalls each walk. No praise, no general theory.
```

When a finding comes back unclear, resume the same subagent once. Do not
start a new one.

## Privacy

Canvases and artifacts are pages hosted on claude.ai. Never put real personal,
health, or customer data, credentials, or private hostnames on them. They hold
manufactured fixtures only. Real-data renders under a repo's declared
inversion stay local: they are never published, committed, or attached to a
PR.
