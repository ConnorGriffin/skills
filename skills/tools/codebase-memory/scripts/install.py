#!/usr/bin/env python3
"""Activate the codebase-memory skill's Claude Code discovery hooks."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import stat
import tempfile
from pathlib import Path


SKILL_DIRECTORY = Path(__file__).resolve().parents[1]
OWNERSHIP = "Managed by codebase-memory skill installer."
MANAGED_FILES = {
    "cbm-code-discovery-gate": (SKILL_DIRECTORY / "hooks" / "cbm-code-discovery-gate", 0o755),
    "cbm-session-reminder": (SKILL_DIRECTORY / "hooks" / "cbm-session-reminder", 0o755),
    "cbm-code-discovery-reminder.md": (SKILL_DIRECTORY / "reminder.md", 0o644),
}


def lstat_or_none(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Activate codebase-memory discovery hooks in Claude Code."
    )
    parser.add_argument(
        "--claude-home",
        type=Path,
        default=Path.home() / ".claude",
        help="Claude Code home directory (default: $HOME/.claude)",
    )
    return parser.parse_args()


def atomic_write(path: Path, content: bytes, mode: int) -> None:
    if path.exists() and path.read_bytes() == content and stat.S_IMODE(path.stat().st_mode) == mode:
        return
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".codebase-memory-install-", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def command_target(command: object) -> str | None:
    if not isinstance(command, str):
        return None
    try:
        words = shlex.split(command)
    except ValueError:
        return None
    if len(words) != 1:
        return None
    return os.path.abspath(os.path.expanduser(words[0]))


def merge_settings(existing: dict, canonical: dict) -> dict:
    if not isinstance(existing, dict):
        raise ValueError("settings root must be an object")
    hooks = existing.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings hooks must be an object")

    expected_by_target: dict[str, list[tuple[str, dict]]] = {}
    for event, entries in canonical["hooks"].items():
        for entry in entries:
            for hook in entry["hooks"]:
                target = command_target(hook["command"])
                if target is None:
                    raise ValueError("canonical managed hook command is not executable")
                expected_by_target.setdefault(target, []).append((event, entry))

    for event, entries in hooks.items():
        if not isinstance(entries, list):
            raise ValueError(f"settings hooks.{event} must be an array")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"settings hooks.{event} entries must be objects")
            entry_hooks = entry.get("hooks", [])
            if not isinstance(entry_hooks, list):
                raise ValueError(f"settings hooks.{event} entry hooks must be an array")
            managed_targets = {
                command_target(hook.get("command"))
                for hook in entry_hooks
                if isinstance(hook, dict)
                and command_target(hook.get("command")) in expected_by_target
            }
            for target in managed_targets:
                if not any(
                    event == expected_event and entry == expected_entry
                    for expected_event, expected_entry in expected_by_target[target]
                ):
                    raise ValueError(
                        f"conflicting managed hook registration for {target}"
                    )

    for event, required_entries in canonical["hooks"].items():
        current_entries = hooks.setdefault(event, [])
        for required in required_entries:
            matches = [index for index, entry in enumerate(current_entries) if entry == required]
            if not matches:
                current_entries.append(required)
                continue
            for index in reversed(matches[1:]):
                del current_entries[index]
    return existing


def main() -> int:
    claude_home = arguments().claude_home.expanduser().absolute()
    hooks_directory = claude_home / "hooks"
    settings_path = claude_home / "settings.json"
    settings_stat = lstat_or_none(settings_path)
    if settings_stat is not None and not stat.S_ISREG(settings_stat.st_mode):
        raise SystemExit("settings.json must be a regular non-symlink file")
    hooks_stat = lstat_or_none(hooks_directory)
    if hooks_stat is not None and not stat.S_ISDIR(hooks_stat.st_mode):
        raise SystemExit("hooks must be a real non-symlink directory")
    planned_files = {}
    for name, (source, mode) in MANAGED_FILES.items():
        content = source.read_bytes()
        if OWNERSHIP.encode() not in content:
            raise SystemExit(f"source is missing ownership text: {source}")
        planned_files[name] = (content, mode)

    if hooks_stat is not None:
        for name in MANAGED_FILES:
            destination = hooks_directory / name
            destination_stat = lstat_or_none(destination)
            if destination_stat is None:
                continue
            if not stat.S_ISREG(destination_stat.st_mode):
                raise SystemExit(
                    f"managed target must be a regular non-symlink file: {destination}"
                )
            if OWNERSHIP.encode() not in destination.read_bytes():
                raise SystemExit(f"managed target is not owned: {destination}")

    template = json.loads(
        (SKILL_DIRECTORY / "config" / "claude-settings.json").read_text(
            encoding="utf-8"
        )
    )
    quoted_home = shlex.quote(str(claude_home))
    for entries in template["hooks"].values():
        for entry in entries:
            for hook in entry["hooks"]:
                hook["command"] = hook["command"].replace(
                    "<CLAUDE_HOME>", quoted_home
                )
    canonical = template
    if settings_stat is not None:
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SystemExit(
                f"settings.json is not valid JSON: {error.msg}"
            ) from error
        settings_mode = stat.S_IMODE(settings_stat.st_mode)
    else:
        settings = {}
        settings_mode = 0o600
    try:
        merged = merge_settings(settings, canonical)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    content = (json.dumps(merged, indent=2) + "\n").encode()

    claude_home.mkdir(parents=True, exist_ok=True)
    hooks_directory.mkdir(exist_ok=True)
    for name, (planned_content, mode) in planned_files.items():
        atomic_write(hooks_directory / name, planned_content, mode)
    atomic_write(settings_path, content, settings_mode)
    print(f"Activated codebase-memory discovery hooks in {claude_home}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
