# Doctor procedure

Report-only estate audit. Never edits a skill, a `CLAUDE.md`, or an `AGENTS.md` — every
finding is a recommendation for a human to act on.

## 1. Measure the always-loaded surface

Walk every document the agent loads before or during session start, and size each one:

* The global `CLAUDE.md`/`AGENTS.md`, following every `@import` line to its target file,
  recursively.
* The project `CLAUDE.md`/`AGENTS.md` in the current repo.
* Every `SKILL.md` frontmatter `description` under `~/.claude/skills/` (follow symlinks
  to the real file — an installed skill is usually a symlink into a checkout).
* Any other file the import chain names as read at session start (a referenced profile
  file, a shared instructions doc).

For each component, report character count and estimated tokens (`chars / 4`). Sum to a
total. This total is the tax every single turn pays before the user's first word.

## 2. Sweep descriptions

Check every `SKILL.md` description against the "Invocation" and "Writing the
description" sections of this skill's own `SKILL.md` (terms defined in `GLOSSARY.md`):

* **Synonym-stuffed trigger lists** — three phrasings of one branch instead of one
  phrasing each of three branches (**duplication** of a branch).
* **Mechanism or output detail the body already owns** — a description restating *how*
  the skill works instead of *when* to reach for it.
* **User-invoked skills missing the manual-invocation signal** — a skill with
  `disable-model-invocation: true` whose description still reads like an autonomous
  trigger list instead of a human-facing summary.
* **Trigger overlap between skills** — two descriptions matching the same phrase or
  intent, risking the wrong skill firing.

## 3. Sweep the always-loaded chain

Read the full chain from step 1 and check for:

* **Duplicated rules** — the same instruction stated in more than one always-loaded
  file. Quote both locations.
* **Conditional sections that belong behind a pointer** — a paragraph that only matters
  for a rare case, sitting in-file instead of disclosed.
* **Stacked negations** — prohibitions with no paired positive target (see
  `references/upstream-levers.md`'s Negation section).
* **No-op sentences** — instructions the model already follows by default.
* **Sediment** — stale material describing a world that's moved on (a tool no longer
  used, a workflow that's been replaced).

## 4. Evidence rule

A finding without a quoted grep or read result gets dropped before it's reported. Verify
every claim directly against the file; don't report from memory of a prior pass.

## 5. Report

Rank findings worst first. Accuracy risks (duplication that could drift, overlapping
triggers that misfire) outrank pure token cost. For each finding: what it is, where
(file, and quoted evidence), and the estimated recoverable tokens if it's a cost
finding. No fixes — every finding is an operator judgment call, not an auto-apply diff.

## 6. Refresh

Re-fetch the upstream source (`https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/writing-for-agents/SKILL.md` and its `SKILL-MECHANICS.md` sibling). Diff
the substance — new recommendations, retracted ones, reworded ones that change meaning —
against `references/upstream-levers.md`. Flag drift for a human to rewrite by hand;
never auto-update the adapted file. Once a human reconciles it, update the attribution
line's fetch date at the top of `references/upstream-levers.md`.
