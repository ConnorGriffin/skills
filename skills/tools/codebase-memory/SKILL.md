---
name: codebase-memory
description: Use the codebase knowledge graph for structural code queries, trace call paths and dependencies, inspect architecture, assess change impact, or activate the bundled Claude Code discovery hooks.
---

# Codebase Memory

Follow [reminder.md](reminder.md) for the standing discovery policy; it is the one
authored policy shared by this skill, the profile pointer, and the installed
SessionStart hook.

## Activate discovery guidance in Claude Code

After the standard skills installer copies this directory, run:

```sh
python3 ~/.claude/skills/codebase-memory/scripts/install.py
```

For a non-default Claude home:

```sh
python3 <installed-skill>/scripts/install.py --claude-home PATH
```

The installer owns three files under the selected Claude home's `hooks/`
directory and merges the skill's registrations into `settings.json`. It preserves
unrelated settings and hook registrations. Malformed settings, conflicting
registrations, symlinks, and unowned managed-path files are no-write failures.
Its scope is the bundled files and registrations.

To merge the registrations into a settings file kept outside the Claude home, for
example one versioned in a dotfiles checkout:

```sh
python3 <installed-skill>/scripts/install.py --claude-home PATH \
  --settings-file PATH/TO/settings.json
```

`--settings-file` moves only the settings file. The three hook files, and the
paths rendered into the registrations, still follow `--claude-home`. The named
target must be a regular non-symlink file, and its parent directory must already
exist, be a directory, and be writable and searchable; a symlinked target or an
unusable parent is a no-write failure. A parent reached through a symlinked
directory is fine, which is how a versioned checkout is usually wired.

For a consumer that manages its own `settings.json` hook registrations, add
`--skip-settings`:

```sh
python3 <installed-skill>/scripts/install.py --claude-home PATH --skip-settings
```

This installs the three managed hook files and stops there: it does not read,
parse, validate, merge, or write `settings.json` at all. The consumer owns
registering the installed hooks in its own settings. All the other guards
still run: source ownership, the hooks-directory symlink check, and the
unowned-managed-file check. `--skip-settings` and `--settings-file` name two
different settings targets, so the installer refuses both together at the
command-line level rather than picking one.

The external tool `codebase-memory-mcp` installs its own hooks at two of the
same names (`cbm-code-discovery-gate`, `cbm-session-reminder`). Activation does
not reclaim a name another tool already owns; it stops and names the likely
owner and the repair (move the foreign files out of `hooks/`, remove that
tool's registrations from `settings.json`, then rerun).

## Graph-query vocabulary

- `list_projects` and `index_status` report indexed-project inventory and health.
- `get_architecture` summarizes repository structure and architectural relationships.
- `search_graph` locates symbols by name, label, or qualified-name pattern.
- `trace_path` follows callers, callees, data flow, and cross-service paths.
- `get_code_snippet` returns exact source for a resolved symbol.
- `query_graph` handles complex multi-hop graph questions.
- `search_code` searches literal source text.
- `detect_changes` maps a Git diff to its structural impact.
- `index_repository` creates or refreshes a repository graph.
