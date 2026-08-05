# Overlaying machine specifics on this pack

This repo is the machine-agnostic layer: skills under `skills/`, shared instructions
under `profile/` (`base.md` and `CHARTER.md`). Every machine layers its own overlay
on top. This runbook is the pattern; each machine's dotfiles implement it.

## The layers

1. `profile/base.md` and `profile/CHARTER.md`: canonical bytes, imported everywhere,
   read by every agent tool (Claude, Codex). Never carry machine or employer
   specifics.
2. The machine overlay: the local `~/.claude/CLAUDE.md` (or `AGENTS.md`). Imports
   the profile files by path, then adds sections for that machine only (hostnames,
   employer conventions, tool bans, credential patterns).
3. Skills: linked into `~/.claude/skills/` from local clones. Machine-specific
   skills live in a separate private repo; shared skills come from this one.

Where layers conflict, the overlay wins.

## Wiring the overlay

1. The overlay file starts with imports:

   ```
   @<path-to-clone>/profile/base.md
   @<path-to-clone>/profile/CHARTER.md
   ```

2. Shared skills are linked by a manifest, not by hand. Dotfiles keep a
   `github-skills.txt` (one skill name per line); the dotfiles install script links
   each listed `skills/<name>` from this repo's clone into `~/.claude/skills/<name>`
   and prunes links no longer listed. Adding a skill to a machine is one manifest
   line plus a re-run of the install.

3. Long-form behavior rules live in a skill, not in the overlay. The overlay keeps
   an imperative pointer so sessions that never invoke the skill (and subagents,
   which receive the overlay file but no hooks) still reach the rules:

   ```
   Read ~/.claude/skills/say-less/SKILL.md and follow it for all output.
   ```

4. Rules that decay over a long session re-inject via a user-prompt-submit hook
   that reads the skill's digest at prompt time, so there is no second copy to
   drift:

   ```json
   {
     "hooks": {
       "UserPromptSubmit": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "cat ~/.claude/skills/say-less/reminder.md"
             }
           ]
         }
       ]
     }
   }
   ```

   Plain stdout from this hook event is injected as context; no JSON envelope
   needed. Editing `reminder.md` in the repo changes the next prompt's injection
   with no other step. A missing file is non-blocking.

## Adding a machine

1. Clone this repo and the machine's private skills repo.
2. Write the overlay `~/.claude/CLAUDE.md`: profile imports first, machine sections
   after, imperative pointers for any skill that carries always-on rules.
3. Copy the manifest pattern into the machine's dotfiles and list the shared skills
   it needs.
4. Add the digest hook to `~/.claude/settings.json`.

## Rules for future skills

* A skill that carries always-on behavior ships a `reminder.md` digest next to its
  `SKILL.md` and documents the pointer line an overlay should add.
* Machine assumptions (employer hosts, credential vaults, internal tools) never go
  in this repo's skills; they go in the machine's private repo and its overlay.
