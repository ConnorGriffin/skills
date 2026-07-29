#!/usr/bin/env python3
"""Validate public skill structure and catch common disclosure mistakes."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED = {"ui-mockups", "drive-local-webapp", "cbm-onboard", "spin-worktree"}
FORBIDDEN = (
    re.compile("/" + "Users/"),
    re.compile("~/" + "Code/" + "ConnorGriffin"),
    re.compile("Connor's " + r"(?:real browser|rule)"),
    re.compile("t" + "connect", re.IGNORECASE),
    re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
)
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_frontmatter(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        fail(errors, f"{path.relative_to(ROOT)}: missing YAML frontmatter")
        return
    fields = {
        line.split(":", 1)[0].strip()
        for line in match.group(1).splitlines()
        if ":" in line
    }
    if fields != {"name", "description"}:
        fail(
            errors,
            f"{path.relative_to(ROOT)}: frontmatter must contain only name and description",
        )
    name_match = re.search(r"^name:\s*(.+)$", match.group(1), re.MULTILINE)
    if not name_match or name_match.group(1).strip() != path.parent.name:
        fail(errors, f"{path.relative_to(ROOT)}: name must match directory")
    if len(text.splitlines()) > 500:
        fail(errors, f"{path.relative_to(ROOT)}: exceeds 500 lines")


def validate_links(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for target in LINK.findall(text):
        target = target.split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        resolved = (path.parent / target).resolve()
        if ROOT not in resolved.parents and resolved != ROOT:
            fail(errors, f"{path.relative_to(ROOT)}: link escapes repository: {target}")
        elif not resolved.exists():
            fail(errors, f"{path.relative_to(ROOT)}: broken link: {target}")


def main() -> int:
    errors: list[str] = []
    actual = {path.name for path in SKILLS.iterdir() if path.is_dir()}
    if actual != EXPECTED:
        fail(errors, f"skills: expected {sorted(EXPECTED)}, found {sorted(actual)}")

    tracked_candidates = [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts and "node_modules" not in path.parts
    ]
    for path in tracked_candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            fail(errors, f"{path.relative_to(ROOT)}: unexpected binary file")
            continue
        for pattern in FORBIDDEN:
            if pattern.search(text):
                fail(errors, f"{path.relative_to(ROOT)}: forbidden pattern {pattern.pattern!r}")
        if path.suffix == ".md":
            validate_links(path, errors)

    for skill in sorted(EXPECTED):
        skill_file = SKILLS / skill / "SKILL.md"
        if not skill_file.exists():
            fail(errors, f"skills/{skill}: missing SKILL.md")
            continue
        validate_frontmatter(skill_file, errors)
        metadata = SKILLS / skill / "agents" / "openai.yaml"
        if not metadata.exists():
            fail(errors, f"skills/{skill}: missing agents/openai.yaml")

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"validated {len(EXPECTED)} skills and {len(tracked_candidates)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
