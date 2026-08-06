#!/usr/bin/env python3
"""Validate public skill structure and catch common disclosure mistakes."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
EXPECTED = {
    "drive-local-webapp",
    "say-less",
    "cbm-onboard",
    "ci-design",
    "codebase-design",
    "domain-modeling",
    "spin-worktree",
    "research",
    "implement",
    "tdd",
    "review",
    "prototype",
    "scope",
    "wayfinder",
    "plan-review",
    "persona-review",
    "ui-craft",
    "orchestrate",
    "writing-for-agents",
}
FORBIDDEN = (
    re.compile("/" + "Users/"),
    re.compile("~/" + "Code/" + "ConnorGriffin"),
    re.compile("Connor's " + r"(?:real browser|rule)"),
    re.compile("nt" + "fy", re.IGNORECASE),
    re.compile("t" + "connect", re.IGNORECASE),
    re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
)
PERSONA_REVIEW_ALLOWLIST = {
    "SKILL.md",
    "agents/openai.yaml",
}
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HISTORY_PATTERN = "|".join(
    (
        "/" + "Users/",
        "~/" + "Code/" + "ConnorGriffin",
        "Connor's " + "(real browser|rule)",
        "nt" + "fy",
        "t" + "connect",
        "BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY",
        "gh[pousr]_[A-Za-z0-9_]{20,}",
        "AKIA[0-9A-Z]{16}",
        "sk-[A-Za-z0-9]{20,}",
        "xox[baprs]-[A-Za-z0-9-]{10,}",
    )
)


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
    required = {"name", "description"}
    allowed = required | {"disable-model-invocation"}
    if fields < required or fields - allowed:
        fail(
            errors,
            f"{path.relative_to(ROOT)}: frontmatter must contain name and description, "
            "plus an optional disable-model-invocation",
        )
    if "disable-model-invocation" in fields:
        value_match = re.search(
            r"^disable-model-invocation:\s*(.+)$", match.group(1), re.MULTILINE
        )
        if not value_match or value_match.group(1).strip() != "true":
            fail(
                errors,
                f"{path.relative_to(ROOT)}: disable-model-invocation must be true when present",
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


def validate_persona_review_allowlist(errors: list[str]) -> None:
    skill_dir = SKILLS / "persona-review"
    if not skill_dir.exists():
        return
    for path in skill_dir.rglob("*"):
        if path.is_file():
            relative = path.relative_to(skill_dir).as_posix()
            if relative not in PERSONA_REVIEW_ALLOWLIST:
                fail(
                    errors,
                    f"skills/persona-review: file not on the allowlist: {relative}",
                )


def validate_reachable_history(errors: list[str]) -> None:
    commits = subprocess.run(
        ["git", "rev-list", "--all"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if commits.returncode != 0:
        fail(errors, f"history scan failed: {commits.stderr.strip()}")
        return
    for revision in commits.stdout.splitlines():
        scan = subprocess.run(
            ["git", "grep", "-I", "-q", "-E", HISTORY_PATTERN, revision, "--", "."],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
        if scan.returncode == 0:
            fail(errors, f"reachable history contains a forbidden value at {revision}")
        elif scan.returncode != 1:
            fail(errors, f"history content scan failed at {revision}")

    objects = subprocess.run(
        ["git", "rev-list", "--objects", "--all"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if objects.returncode != 0:
        fail(errors, f"history path scan failed: {objects.stderr.strip()}")
        return
    for line in objects.stdout.splitlines():
        _, separator, object_path = line.partition(" ")
        if not separator:
            continue
        for pattern in FORBIDDEN:
            if pattern.search(object_path):
                fail(errors, f"reachable history contains a forbidden path")


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

    validate_persona_review_allowlist(errors)
    validate_reachable_history(errors)

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"validated {len(EXPECTED)} skills and {len(tracked_candidates)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
