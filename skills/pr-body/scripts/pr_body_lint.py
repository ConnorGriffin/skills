#!/usr/bin/env python3
"""Lint a PR body against the pr-body skill's rubric."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


THRESHOLDS = {
    # Robustness cap only, not a judgment about the body: hand-labeled data
    # showed body length does not separate pass from fail (a 2242-char body
    # passed, a 1703-char body failed), so length is not a scored rule here.
    # Past this, the input is refused outright rather than run through every
    # regex below.
    "max_input_chars": 20_000,
    # Below this many prose chars, a body is too short for the density rules
    # (em-dash, emoji, paths, narration, verdicts, reviewer asks,
    # bullet-per-file, symbol-in-prose) to have signal.
    "density_floor_chars": 40,
    "bullet_per_file_min_bullets": 3,
    "bullet_per_file_ratio": 0.6,
    "excerpt_max_chars": 120,
    "vacuous_opener_max_chars": 200,
}


CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
LINK_TARGET_RE = re.compile(r"(?<=\])\([^)]*\)")
BARE_URL_RE = re.compile(r"https?://\S+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")

EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U00002B00-\U00002BFF"
    "]"
)

VACUOUS_OPENER_PATTERNS = [
    re.compile(r"^fix(es|ed)?\.?$", re.I),
    re.compile(r"^fix(es|ed)?\s+(the\s+)?(bug|build|issue|error)s?\.?$", re.I),
    re.compile(r"^add(s|ed)?\s+(a\s+)?patch(es)?\.?$", re.I),
    re.compile(r"^add(s|ed)?\s+convenience\s+functions?\.?$", re.I),
    re.compile(r"^mov(e|ing)\s+code\s+from\s+.+\s+to\s+.+\.?$", re.I),
    re.compile(r"^phase\s*\d+\.?$", re.I),
    re.compile(r"^(wip|work[\s-]in[\s-]progress)\.?$", re.I),
    re.compile(
        r"^(minor|small|misc(ellaneous)?)\s+(fix(es)?|change(s)?|update(s)?)\.?$",
        re.I,
    ),
    re.compile(r"^update(s|d)?\.?$", re.I),
    re.compile(r"^clean\s*up\.?$", re.I),
    re.compile(r"^kill\s+weird\s+urls\.?$", re.I),
]

METHOD_NARRATION_PATTERNS = [
    re.compile(r"\bverified\s+with\b", re.I),
    re.compile(r"\btested\s+by\s+running\b", re.I),
    re.compile(r"\bi\s+ran\b", re.I),
    re.compile(r"\bran\s+the\b", re.I),
]

VERDICT_CLAUSE_PATTERNS = [
    re.compile(r"\bthis\s+is\s+a\s+(low[\s-]risk|simple|straightforward|minor|trivial)\s+change\b", re.I),
    re.compile(r"\bno\s+downtime\s+is\s+expected\b", re.I),
    re.compile(r"\bshould\s+have\s+(no|little|minimal)\s+impact\b", re.I),
    re.compile(r"\bimproves?\s+maintainability\b", re.I),
    re.compile(r"\bmakes?\s+the\s+code\s+(cleaner|more\s+readable)\b", re.I),
    re.compile(r"\bstraightforward\b", re.I),
    re.compile(r"\bshould\s+be\s+safe\b", re.I),
]

REVIEWER_INSTRUCTION_PATTERNS = [
    re.compile(r"\bplease\s+review\b", re.I),
    re.compile(r"\bworth\s+checking\b", re.I),
    re.compile(r"\breviewers?\s+should\b", re.I),
    re.compile(r"\btake\s+a\s+look\s+at\b", re.I),
    re.compile(r"\blet\s+me\s+know\s+if\b", re.I),
]

# Identifier-shaped tokens: snake_case, camelCase, or a bare function call.
SYMBOL_PATTERNS = [
    re.compile(r"\b[a-z][a-z0-9]*_[a-z0-9_]+\b"),
    re.compile(r"\b[a-z]+[A-Z][a-zA-Z0-9]*\b"),
    re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\(\)"),
]

FILENAME_RE = re.compile(r"^[\w.-]+\.[A-Za-z0-9]{1,8}$")

# Flexible AI-disclosure match: an AI-related term and a preparation/assist
# verb on the same line, so any wording of the Kubernetes-style disclosure
# sentence is accepted rather than one fixed string.
AI_TERM_RE = re.compile(
    r"\b(ai|artificial intelligence|generative ai|genai|an? assistant|"
    r"copilot|claude(?:\s+code)?|chatgpt|gpt-?\d*|llm)\b",
    re.I,
)
ASSIST_VERB_RE = re.compile(
    r"\b(assist(ed|ance)?|help(ed)?|prepar(ed|ing)?|wrote|written|writing|"
    r"generat(ed|ing)?|draft(ed|ing)?)\b",
    re.I,
)

FIXES = {
    "empty-body": "State what changed and why; an empty body tells the reviewer nothing.",
    "ai-disclosure-missing": (
        "Add a disclosure line: 'This PR was written in part with the "
        "assistance of generative AI.'"
    ),
    "empty-template-section": "Fill in the {heading!r} section, or delete it if it does not apply.",
    "vacuous-opener": "Open with the behavior that changed, not a generic label like this line.",
    "oversized-input": "Pass the body as a file with --body-file instead of inline; this input is too large to lint directly.",
    "em-dash": "Rewrite without an em dash; use a period or parentheses instead.",
    "emoji": "Remove the emoji; state the fact in words.",
    "path-in-prose": "Name the behavior, not the file; the diff already lists files.",
    "method-narration": "State the result of verification, not how you performed it.",
    "verdict-clause": "Replace the rating with the concrete fact that supports it.",
    "reviewer-instruction": "Delete the instruction to the reviewer; let the diff and description stand on their own.",
    "bullet-per-file": "Describe the behavior the files implement together, not a bullet per file.",
    "symbol-in-prose": "Wrap the identifier in backticks, or name the behavior instead of the symbol.",
}

SEVERITY = {
    "empty-body": "block",
    "ai-disclosure-missing": "block",
    "empty-template-section": "block",
    "vacuous-opener": "block",
    "oversized-input": "block",
    "em-dash": "block",
    "emoji": "block",
    "path-in-prose": "block",
    "method-narration": "block",
    "verdict-clause": "block",
    "reviewer-instruction": "block",
    "bullet-per-file": "block",
    "symbol-in-prose": "warn",
}


class LintError(RuntimeError):
    """An internal failure that should surface as a JSON error object."""


def _excerpt(text: str) -> str:
    limit = THRESHOLDS["excerpt_max_chars"]
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _blank_spans(pattern: re.Pattern, text: str) -> str:
    """Replace every match with just its own newlines, preserving line numbers."""
    return pattern.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def _prose_only(text: str) -> str:
    text = _blank_spans(CODE_FENCE_RE, text)
    text = _blank_spans(INLINE_CODE_RE, text)
    text = _blank_spans(LINK_TARGET_RE, text)
    text = _blank_spans(BARE_URL_RE, text)
    return text


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def _load_template_lines(repo: Optional[Path]) -> set[str]:
    if repo is None:
        return set()
    template = repo / ".github" / "pull_request_template.md"
    if not template.is_file():
        return set()
    try:
        raw = template.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    return {
        _normalize_line(line)
        for line in raw.splitlines()
        if _normalize_line(line)
    }


def _scaffolding_mask(lines: list[str], template_lines: set[str]) -> list[bool]:
    # A disclosure line (the Claude Code footer, e.g.) is tool-appended
    # boilerplate, not authored prose, so it is exempt the same way a
    # template heading is.
    return [
        (bool(template_lines) and _normalize_line(line) in template_lines)
        or (AI_TERM_RE.search(line) is not None and ASSIST_VERB_RE.search(line) is not None)
        for line in lines
    ]


def _first_prose_line(
    lines: list[str], scaffolding: list[bool]
) -> Optional[tuple[int, str]]:
    for index, raw in enumerate(lines):
        if scaffolding[index]:
            continue
        text = raw.strip()
        if not text or HEADING_RE.match(text):
            continue
        bullet_match = BULLET_RE.match(raw)
        content = bullet_match.group(1).strip() if bullet_match else text
        if content:
            return index, content
    return None


def _check_vacuous_opener(
    lines: list[str], scaffolding: list[bool]
) -> list[dict]:
    found = _first_prose_line(lines, scaffolding)
    if found is None:
        return []
    line_index, content = found
    if len(content) > THRESHOLDS["vacuous_opener_max_chars"]:
        return []
    stripped = content.strip().rstrip(".")
    for pattern in VACUOUS_OPENER_PATTERNS:
        if pattern.match(stripped) or pattern.match(content):
            return [
                {
                    "rule": "vacuous-opener",
                    "line": line_index + 1,
                    "excerpt": _excerpt(content),
                }
            ]
    return []


def _check_empty_template_sections(lines: list[str]) -> list[dict]:
    # A heading with nothing under it is the underfill failure mode whether
    # or not the heading happens to also live in a repo's PR template.
    headings: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line.strip())
        if match:
            headings.append((index, match.group(2).strip()))
    findings = []
    for position, (index, heading_text) in enumerate(headings):
        # A blank final section is almost always optional trailing metadata
        # (a ticket link, a screenshot placeholder); only a blank section
        # with more document after it is the abandoned-template failure.
        # A single lone heading has nowhere else to carry content, so it
        # stays in scope even though it is technically "last".
        if position == len(headings) - 1 and len(headings) > 1:
            continue
        is_last = position + 1 >= len(headings)
        end = len(lines) if is_last else headings[position + 1][0]
        section = lines[index + 1 : end]
        if not any(line.strip() for line in section):
            findings.append(
                {
                    "rule": "empty-template-section",
                    "line": index + 1,
                    "excerpt": _excerpt(heading_text or lines[index].strip()),
                    "heading": heading_text or lines[index].strip(),
                }
            )
    return findings


def _check_pattern_rule(
    rule: str,
    patterns: list[re.Pattern],
    lines: list[str],
    scaffolding: list[bool],
) -> list[dict]:
    for index, line in enumerate(lines):
        if scaffolding[index]:
            continue
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                return [
                    {
                        "rule": rule,
                        "line": index + 1,
                        "excerpt": _excerpt(line),
                    }
                ]
    return []


def _check_em_dash(lines: list[str], scaffolding: list[bool]) -> list[dict]:
    for index, line in enumerate(lines):
        if scaffolding[index]:
            continue
        if "—" in line:
            return [
                {
                    "rule": "em-dash",
                    "line": index + 1,
                    "excerpt": _excerpt(line),
                }
            ]
    return []


def _check_emoji(lines: list[str], scaffolding: list[bool]) -> list[dict]:
    for index, line in enumerate(lines):
        if scaffolding[index]:
            continue
        if EMOJI_RE.search(line):
            return [
                {
                    "rule": "emoji",
                    "line": index + 1,
                    "excerpt": _excerpt(line),
                }
            ]
    return []


def _looks_like_path(token: str) -> bool:
    candidate = token.strip(".,;:()[]{}\"'")
    if not candidate or "/" not in candidate:
        return False
    if candidate.startswith(("http://", "https://")):
        return False
    tail = candidate.rsplit("/", 1)[-1]
    if "." not in tail:
        return False
    ext = tail.rsplit(".", 1)[-1]
    return 1 <= len(ext) <= 8 and ext.isalnum()


def _check_path_in_prose(
    prose_lines: list[str], scaffolding: list[bool]
) -> list[dict]:
    for index, line in enumerate(prose_lines):
        if scaffolding[index]:
            continue
        for token in line.split():
            if _looks_like_path(token):
                return [
                    {
                        "rule": "path-in-prose",
                        "line": index + 1,
                        "excerpt": _excerpt(token),
                    }
                ]
    return []


def _check_symbol_in_prose(
    prose_lines: list[str], scaffolding: list[bool]
) -> list[dict]:
    for index, line in enumerate(prose_lines):
        if scaffolding[index]:
            continue
        for pattern in SYMBOL_PATTERNS:
            match = pattern.search(line)
            if match:
                return [
                    {
                        "rule": "symbol-in-prose",
                        "line": index + 1,
                        "excerpt": _excerpt(line),
                    }
                ]
    return []


def _leads_with_file(bullet_text: str) -> bool:
    stripped = bullet_text.strip().lstrip("`*_\"'")
    if not stripped:
        return False
    first_token = stripped.split()[0].rstrip(":,.")
    if "/" in first_token:
        return _looks_like_path(first_token)
    return bool(FILENAME_RE.match(first_token))


def _check_bullet_per_file(
    lines: list[str], scaffolding: list[bool]
) -> list[dict]:
    bullets = []
    for index, line in enumerate(lines):
        if scaffolding[index]:
            continue
        match = BULLET_RE.match(line)
        if match:
            bullets.append((index, match.group(1)))
    if len(bullets) < THRESHOLDS["bullet_per_file_min_bullets"]:
        return []
    file_led = [item for item in bullets if _leads_with_file(item[1])]
    ratio = len(file_led) / len(bullets)
    if ratio >= THRESHOLDS["bullet_per_file_ratio"]:
        first_index, first_text = file_led[0]
        return [
            {
                "rule": "bullet-per-file",
                "line": first_index + 1,
                "excerpt": _excerpt(first_text),
            }
        ]
    return []


def _check_ai_disclosure(body: str) -> list[dict]:
    for line in body.splitlines():
        if AI_TERM_RE.search(line) and ASSIST_VERB_RE.search(line):
            return []
    return [{"rule": "ai-disclosure-missing", "line": 1, "excerpt": ""}]


def _finding(raw: dict) -> dict:
    rule = raw["rule"]
    fix = FIXES[rule]
    if "{heading!r}" in fix:
        fix = fix.format(heading=raw.get("heading", raw["excerpt"]))
    return {
        "rule": rule,
        "severity": SEVERITY[rule],
        "line": raw["line"],
        "excerpt": raw["excerpt"],
        "fix": fix,
    }


def lint(body: str, *, repo: Optional[Path] = None) -> dict:
    chars = len(body)

    if chars > THRESHOLDS["max_input_chars"]:
        finding = _finding(
            {
                "rule": "oversized-input",
                "line": 1,
                "excerpt": _excerpt(body[: THRESHOLDS["excerpt_max_chars"]]),
            }
        )
        return {"verdict": "fail", "chars": chars, "findings": [finding]}

    if not body.strip():
        findings = [
            _finding({"rule": "empty-body", "line": 1, "excerpt": ""}),
            _finding({"rule": "ai-disclosure-missing", "line": 1, "excerpt": ""}),
        ]
        return {"verdict": "fail", "chars": chars, "findings": findings}

    template_lines = _load_template_lines(repo)
    lines = body.splitlines()
    scaffolding = _scaffolding_mask(lines, template_lines)

    raw_findings: list[dict] = []
    raw_findings.extend(_check_empty_template_sections(lines))
    raw_findings.extend(_check_vacuous_opener(lines, scaffolding))
    raw_findings.extend(_check_ai_disclosure(body))

    prose_text = _prose_only(body)
    prose_lines = prose_text.splitlines()
    prose_chars = len(prose_text)

    if prose_chars >= THRESHOLDS["density_floor_chars"]:
        raw_findings.extend(_check_em_dash(prose_lines, scaffolding))
        raw_findings.extend(_check_emoji(prose_lines, scaffolding))
        raw_findings.extend(_check_path_in_prose(prose_lines, scaffolding))
        raw_findings.extend(
            _check_pattern_rule(
                "method-narration", METHOD_NARRATION_PATTERNS, prose_lines, scaffolding
            )
        )
        raw_findings.extend(
            _check_pattern_rule(
                "verdict-clause", VERDICT_CLAUSE_PATTERNS, prose_lines, scaffolding
            )
        )
        raw_findings.extend(
            _check_pattern_rule(
                "reviewer-instruction",
                REVIEWER_INSTRUCTION_PATTERNS,
                prose_lines,
                scaffolding,
            )
        )
        raw_findings.extend(_check_bullet_per_file(lines, scaffolding))
        raw_findings.extend(_check_symbol_in_prose(prose_lines, scaffolding))

    findings = [_finding(item) for item in raw_findings]
    verdict = "fail" if any(f["severity"] == "block" for f in findings) else "pass"
    return {"verdict": verdict, "chars": chars, "findings": findings}


def _extract_body(arguments: argparse.Namespace) -> str:
    if arguments.body_file:
        path = Path(arguments.body_file)
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            raise LintError(f"cannot read --body-file: {error}") from error
    return sys.stdin.read()


def _render_human(result: dict) -> str:
    lines = [f"verdict: {result['verdict']} ({result['chars']} chars)"]
    for finding in result["findings"]:
        lines.append(
            f"[{finding['severity']}] {finding['rule']} (line {finding['line']}): "
            f"{finding['excerpt']!r}"
        )
        lines.append(f"  fix: {finding['fix']}")
    return "\n".join(lines)


def parse_arguments(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-file", help="path to the PR body; defaults to stdin")
    parser.add_argument("--repo", help="repo root, used to find the PR template")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    try:
        arguments = parse_arguments(argv)
        body = _extract_body(arguments)
        repo = Path(arguments.repo).expanduser() if arguments.repo else None
        result = lint(body, repo=repo)
    except LintError as error:
        print(json.dumps({"verdict": "error", "error": str(error)}))
        return 2
    except Exception as error:  # noqa: BLE001 - must never crash the caller
        print(json.dumps({"verdict": "error", "error": f"internal error: {error}"}))
        return 2

    if arguments.json:
        print(json.dumps(result))
    else:
        print(_render_human(result))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
