# Overlaying machine specifics on this pack

This repo is the portable layer, and it carries everything needed to rebuild the whole
layering from scratch. Assume a machine that has never seen this setup and has no access
to any private dotfiles. What follows is the contract, not a copy of one machine's
scripts.

## The four skill sources

Every skill an agent can see is a symlink at `~/.claude/skills/<name>`. One installer
creates all of them, from four sources. Each source has its own allowlist and a prune
step, so deleting a line removes the link on the next run.

1. This repo: portable and public. Skills under `skills/`, the output style at
   `output-styles/say-less.md`, the shared instruction layer under `profile/`
   (`base.md`, `CHARTER.md`), and the say-less evidence (`bench/`, `examples/`,
   [`before-after.md`](before-after.md)). Reachable from any machine. One machine links
   12 of these by allowlist, not all of them.
2. A private per-machine skills repo: skills that need that machine's employer, hosts,
   trackers or credentials to be useful (19 on one machine). Never portable, never
   public.
3. Third-party packs, read only. One machine links 13 skills from an internal pack
   published by its employer, and 2 from `github.com/mattpocock/skills`. Cloned, pinned
   to `main`, linked by allowlist, never edited in place.
4. The machine's dotfiles: private. The `CLAUDE.md` overlay, `settings.json`, hooks,
   `.mcp.json`, and the allowlists. It holds no skills at all.

### Where a new skill goes

1. Does it need an employer name, an internal host, a tracker or a credential store to
   work? It goes in the private per-machine repo.
2. Does someone else maintain it? It stays in their pack, linked read only.
3. Otherwise it goes here, where every machine can link it.
4. Configuration is not a skill. Hooks, settings and allowlists go in dotfiles.

## Precedence

The overlay file imports the profile first, then adds its own sections:

```
@<path-to-clone>/profile/base.md
@<path-to-clone>/profile/CHARTER.md

## Overlay: <machine name>
```

Later sections win on conflict, so the overlay's rules beat the profile's. Keep
long-form behavior rules in a skill and put an imperative pointer in the overlay, since
subagents receive the overlay file but no hooks:

```
Read ~/.claude/skills/say-less/SKILL.md and follow it for all output.
```

## The installer contract

Write it in any language. The contract is the part that matters.

1. Read the sources. A source is a clone root plus an allowlist file: one skill name per
   line, blank lines and `#` comments ignored. A name is a directory name, never a path.
2. Resolve every name to a source path before touching the filesystem. Here that is
   `<clone>/skills/<name>`; some packs keep skills at the clone root, so each source
   declares its own subdirectory.
3. Build the desired state as one map of link name to target path across all four
   sources, then reconcile in a single pass. Never prune one source before linking the
   next. If source A retires `foo` in the same run that source B adopts it, per-source
   pruning deletes the link just created and leaves `foo` dangling.
4. A name that resolves in two sources is an error. Link neither, leave any existing
   link untouched, print both paths, and exit non-zero. Silent shadowing makes a
   skill's provenance depend on source order. The fix is to drop the name from one
   allowlist.
5. A name that resolves nowhere is an error. Print the name and the path searched, skip
   it, continue with the rest, and exit non-zero at the end. One typo must not stop the
   run.
6. Create each link as a symlink to the source directory, never a copy. An edit in the
   clone then applies at the next prompt, and one `git pull` updates every machine that
   links it.
7. Retarget rather than trust. If `~/.claude/skills/<name>` is on an allowlist but
   points anywhere other than the resolved target (a moved clone, an older path, a
   target that no longer exists), replace the link.
8. Prune only what the installer owns. Remove a symlink when its target resolves inside
   a managed clone root and its name is absent from the desired map. Leave any link
   whose target lies outside every managed root, and report it. Never delete a real
   directory: report the name as unmanaged and leave it alone.
9. Exit non-zero if anything was reported. Make the run idempotent: a second run with no
   allowlist change makes no filesystem change.

## The digest hook

A skill carrying always-on rules ships a `reminder.md` digest next to its `SKILL.md`.
Those rules decay over a long session, so a `UserPromptSubmit` hook re-injects the
digest at prompt time. There is no second copy to drift.

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

Plain stdout from this event is injected as context, with no JSON envelope. Editing
`reminder.md` in the repo changes the next prompt's injection and nothing else. A
missing file is non-blocking.

## Adding a machine

1. Clone this repo, the machine's private skills repo, and each third-party pack.
2. Write `~/.claude/CLAUDE.md`: the two profile imports first, machine sections after,
   an imperative pointer for every skill that carries always-on rules.
3. Write one allowlist per source, then run the installer.
4. Link `output-styles/say-less.md` into `~/.claude/output-styles/` and set
   `"outputStyle": "say-less"` in `~/.claude/settings.json`.
5. Add the digest hook to that same settings file.
6. Re-run the installer after any allowlist edit and after any `git pull`.

## Rules

* No employer specifics in this repo. No employer name, internal hostname, ticket id or
  absolute home path in any tracked file. `scripts/validate.py` fails the run when one
  appears, so run it before every commit.
* A machine's edit to a third-party skill goes in the overlay, as a rule in that
  machine's `CLAUDE.md`, not as a forked copy of the skill. A fork stops receiving
  upstream updates the day it is made.
* Hooks over instructions. An instruction that asks the model to prefer a tool it cannot
  see does nothing. One machine ran a session-start paragraph telling agents to query a
  code graph before searching; across 2101 transcripts it produced zero such calls,
  because those tools arrive deferred behind a tool-search step while Bash is always
  present. What worked was a `PreToolUse` hook that injects the graph's answer alongside
  the search the agent was already running. Put behavior in a hook wherever a hook can
  carry it, and reserve instructions for what only the model can decide.
* Delete what nothing invokes. A skill with no recorded invocation gets deleted, not
  kept in case it is useful later. The local transcripts are the evidence.
* A skill that carries always-on behavior ships a `reminder.md` digest and documents the
  pointer line an overlay should add.
