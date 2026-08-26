# Mock scaffold — skills pack

Repo-global. Prepped once (issue #198), extended per surface — never forked.

## Ground truth

**There is no app.** This repo ships a skill pack, not a running product: no
stylesheet, no routes, no render modules. So there is no `_theme-app.css` to
extract, and `_theme.css` here is the *only* token layer. It is authored, not
transcribed — and at build time it becomes the docs site's single hand-written
stylesheet, near enough verbatim.

That makes the usual precedence question moot: when the docs site ships, its
own stylesheet becomes ground truth and this file becomes the stale ancestor.
Until then, `_theme.css` is it.

## What the scaffold provides

- **`_theme.css`** — light + dark tokens, base page/type rules, the mock shell
  (a width-constrained column), category colour tokens, the skill list, the
  diagram styles including edge isolation, and the responsive rules.

## What it deliberately does not provide

- **No `_shell.js`.** The surface is locked at zero JavaScript, so the usual
  ES-module shell (capture loading, mock-bar state toggles, theme deep-link)
  would be scaffolding the mock could use but the build could not. Theme
  follows `prefers-color-scheme` only; there is no in-page toggle to mock.
  Recorded as a deviation in `docs-site.lock.md`.
- **No chart glue.** Nothing on this surface family charts. Diagrams are
  build-time inline SVG, generated from the skill graph — not a library.

## Linking it

```html
<link rel="stylesheet" href="_theme.css">
```

Category colour is applied by putting `cat-workflows` / `cat-drivers` /
`cat-tools` on a container; everything inside reads `--cat` and `--cat-bg`.

## What stays yours

Concept-specific markup, page structure, and the SVG the generator emits.
Per-skill edge-isolation rules are *generated* into each page's inline
`<style>` — they are not part of the hand-written stylesheet, and the count
scales with the number of skills.

## Mock chrome

The `.mockbar` strip at the top of each mock is recessive and does not ship.
Nothing else in these files is mock-only.
