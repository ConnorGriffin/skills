#!/usr/bin/env python3
"""Resolve a review route to its skill, or report why it can't be resolved.

Route rows are data, layered from two files: the shipped ``routes.json`` beside
this script's parent directory, and an operator's ``~/.config/review/routes.json``
(or ``$REVIEW_ROUTES_CONFIG``). An operator row replaces a shipped row with the
same ``route`` value; any other ``route`` value extends the table.

Three outcomes are machine-decidable for a single route: installed (exit 0),
registered but its skill is missing (exit 3), and not a registered route at all
(exit 4). A fourth, malformed config (exit 2), is a trust-boundary failure, not a
normal outcome, and is never returned for the other three.
"""

from __future__ import annotations

import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

SHIPPED_ROUTES = Path(__file__).resolve().parent.parent / "routes.json"
ROUTE_FIELDS = {"route", "skill", "kind", "for"}
VALID_KINDS = {"skill", "agent-builtin"}

# Skill names this pack itself ships a directory for. A row naming one of these
# gets the pack's own install command when missing; any other skill name gets a
# pointer at the row's source file instead, since this pack can't install it.
PACK_SHIPPED_SKILLS = {"code-review", "plan-review", "persona-review"}
INSTALL_COMMAND = "npx skills add ConnorGriffin/skills --skill {skill}"

EXIT_INSTALLED = 0
EXIT_USAGE = 1
EXIT_MALFORMED_CONFIG = 2
EXIT_MISSING = 3
EXIT_NOT_A_ROUTE = 4


class ConfigError(Exception):
    pass


def operator_config_path() -> Path:
    override = os.environ.get("REVIEW_ROUTES_CONFIG")
    if override:
        return Path(override)
    return Path(os.path.expanduser("~/.config/review/routes.json"))


def load_rows(path: Path, *, required: bool) -> list[dict]:
    if not path.exists():
        if required:
            raise ConfigError(f"{path}: missing")
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ConfigError(f"{path}: {error}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path}: invalid JSON: {error.msg}")
    if not isinstance(data, list):
        raise ConfigError(f"{path}: must be a JSON list of route rows")
    rows = []
    for index, row in enumerate(data):
        if not isinstance(row, dict) or set(row) != ROUTE_FIELDS:
            raise ConfigError(
                f"{path}: row {index} must have exactly route, skill, kind, for"
            )
        if not all(isinstance(row[field], str) and row[field] for field in ROUTE_FIELDS):
            raise ConfigError(f"{path}: row {index} fields must be nonempty strings")
        if row["kind"] not in VALID_KINDS:
            raise ConfigError(f"{path}: row {index} has an unknown kind {row['kind']!r}")
        rows.append({**row, "_source": str(path)})
    return rows


def merged_rows() -> "OrderedDict[str, dict]":
    merged: "OrderedDict[str, dict]" = OrderedDict()
    for row in load_rows(SHIPPED_ROUTES, required=True):
        merged[row["route"]] = row
    for row in load_rows(operator_config_path(), required=False):
        merged[row["route"]] = row
    return merged


def skill_roots() -> list[Path]:
    override = os.environ.get("REVIEW_SKILL_ROOTS")
    if override is not None:
        return [Path(part) for part in override.split(os.pathsep) if part]
    roots: list[Path] = []
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        roots.append(Path(project_dir) / ".claude" / "skills")
    roots.append(Path(".claude") / "skills")
    roots.append(Path(os.path.expanduser("~/.claude/skills")))
    roots.append(Path(".agents") / "skills")
    roots.append(Path(os.path.expanduser("~/.agents/skills")))
    return roots


def find_skill(skill: str) -> Path | None:
    for root in skill_roots():
        candidate = root / skill / "SKILL.md"
        if candidate.is_file():
            return candidate
    return None


def cmd_list(rows: "OrderedDict[str, dict]") -> int:
    for row in rows.values():
        print(f"{row['route']}\t{row['skill']}\t{row['kind']}\t{row['for']}")
    return EXIT_INSTALLED


def cmd_resolve(rows: "OrderedDict[str, dict]", route: str) -> int:
    row = rows.get(route)
    if row is None:
        names = ", ".join(rows.keys())
        print(
            f"{route!r} is not a registered review type here. "
            f"Registered routes: {names}"
        )
        return EXIT_NOT_A_ROUTE

    if row["kind"] == "agent-builtin":
        print(
            f"{route} -> {row['skill']} ships with the agent itself; its presence "
            f"was not verified on disk. for: {row['for']}"
        )
        return EXIT_INSTALLED

    path = find_skill(row["skill"])
    if path is not None:
        print(f"{route} -> {row['skill']} at {path}. for: {row['for']}")
        return EXIT_INSTALLED

    if row["skill"] in PACK_SHIPPED_SKILLS:
        print(
            f"{route} -> {row['skill']} is registered but not installed. "
            f"Install it with: {INSTALL_COMMAND.format(skill=row['skill'])}"
        )
    else:
        print(
            f"{route} -> {row['skill']} is registered but not installed, and this "
            f"pack does not ship it. See {row['_source']} for where this row came from."
        )
    return EXIT_MISSING


def main(argv: list[str]) -> int:
    try:
        rows = merged_rows()
    except ConfigError as error:
        print(f"resolve_route: {error}", file=sys.stderr)
        return EXIT_MALFORMED_CONFIG

    if argv == ["--list"]:
        return cmd_list(rows)
    if len(argv) == 1 and argv[0] != "--list":
        return cmd_resolve(rows, argv[0])

    print("usage: resolve_route.py <route> | --list", file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
