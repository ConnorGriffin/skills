# Scope ledger — issue 43

Coordinate click for the bundled browser driver, plus truthing the README's
optional-skills section.

Route: interview mode (one concrete either/or about how far the README fix reaches).

## Decisions

- Flat order, not chunked. One slicing trait fires (live run inside the ticket:
  the self-check needs real Chromium). Lockstep copies does not fire: the command
  list has exactly two encodings, `driver.mjs`'s header comment and `SKILL.md`'s
  `## Commands` block. `inline`
- Review depth: targeted. New opt-in command in a shared, pinned tool; no existing
  command's behavior changes and nothing in the sensitivity floor is touched. `inline`
- Profile: none. No `Harden:` line in `AGENTS.md` or `CLAUDE.md` repo facts. `inline`
- Surface lifecycle: none. No rendered surface changes. `inline`
- Refuted from the prior contested round: the acceptance criterion claiming a
  command list in `self-check.mjs`. Reproduced against the file: it invokes six
  commands and enumerates none. The order names two encodings, not three. `inline`
- Corrected against CI: `npm run self-check` is a real gate, run by
  `.github/workflows/validate.yml` after `npm ci` and `npx playwright install
  chromium`. It is outside the Python gate, not outside CI. `inline`

- Q1 settled (operator, option A): the README's optional list becomes one list of
  four true entries under a renamed header that no longer says "upstream"; the three
  bundled entries are marked as shipping in this pack; the
  `npx skills add mattpocock/skills --skill codebase-design --skill domain-modeling`
  command is deleted, because after the fix it names nothing external. Why: four of
  the five entries ship here, so "upstream" is the false word.
  `CONTRIBUTING.md:16` still holds, since Codebase Memory remains documented there.
  `inline`
- Spike, executed rather than prosed. Two scratch scripts were run during triage and
  are not committed: this repo's `docs/scope` ledgers are markdown only, and the
  charter forbids dead code, so the executed results are recorded here instead.
  - Coordinate parse, 15 table cases, all passing. It caught a real trap that prose
    would have shipped: `Number("")` is `0`, so `"640,"` and `",360"` parse as
    `640,0` and `0,360` unless each side is rejected when empty *before* `Number()`.
    Accepted: `640,360`, `  640 , 360 `, `0,0`, `12.5,20.5`, `1e2,1e2`.
    Rejected: `640`, empty, `640,`, `,360`, `a,360`, `-1,10`, `10,-1`, `1,2,3`,
    `Infinity,10`, `NaN,10`.
  - Real Chromium against pinned `playwright` 1.61.1: `page.mouse.click` is a
    function, a click at `(120, 80)` lands at exactly that viewport CSS point, the
    default viewport is 1280x720, and the landing point is readable back through the
    driver's existing `eval` command. `inline`

## Open questions

(none)

## Spawned tasks

- none
