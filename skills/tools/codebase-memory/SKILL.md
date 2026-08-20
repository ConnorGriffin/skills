---
name: codebase-memory
description: Use the codebase knowledge graph for structural code queries, trace call paths and dependencies, inspect architecture, assess change impact, or activate the bundled Claude Code discovery hooks.
---

# Codebase Memory

Use the graph for structural code discovery when the exact repository is indexed.
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
Activation does not install `codebase-memory-mcp` or index a repository.

## Structural discovery workflow

1. Call `list_projects` and `index_status` before structural queries.
2. Use `get_architecture` for high-level orientation.
3. Use `search_graph` to locate symbols by name, label, or qualified-name pattern.
4. Use `trace_path` for callers, callees, data flow, and cross-service paths.
5. Use `get_code_snippet` after resolving an exact qualified name.
6. Use `query_graph` for complex multi-hop graph questions.
7. Use `detect_changes` to map a Git diff to its structural impact.

Use `search_code` or ordinary repository search for literal text. Use
`index_repository` only when indexing is explicitly requested or the target
repository requires it.
