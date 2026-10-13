#!/usr/bin/env python3
"""Mechanical prechecks for a rendered UI against its one-page lock.

Usage: precheck.py <render.html | directory> <lock.md>

Reads the static HTML of each render. It sees markup, text, classes and inline or
<style> declarations. It does not lay anything out, so it cannot see computed sizes,
real overflow, contrast, or text painted into a canvas; the rendered browser pass
owns those. Exit 0 when every check passes, 1 when any fails, 2 on bad input.

Render conventions it relies on:
  data-screen="<name>"  root of each screen (default: one screen per file)
  data-label            text naming served data; must be in the served vocabulary
  data-value            a served value (number, name, time); skipped by text checks
  data-primary          a primary action (so is a class token ending in "primary")
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

BLOCK = {
    "a", "article", "aside", "button", "caption", "dd", "div", "dt", "figcaption",
    "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "label", "legend", "li",
    "main", "nav", "option", "p", "section", "summary", "td", "th",
}
SKIP = {"script", "style", "template", "noscript", "head", "title"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr"}
ACTION = {"button", "a", "input"}
SIZE_WORD = re.compile(r"(?:^|[-_])(?:xs|sm|small|md|medium|lg|large|xl|compact|mini|tiny|big)$")
SIZE_UTILITY = re.compile(r"^(?:h|min-h|px|py|p|text)-(?:\d|xs|sm|base|lg|xl)")
SIZE_PROP = re.compile(r"\b(height|min-height|padding|font-size)\s*:\s*([^;]+)")
WIDE = re.compile(r"\b(?:width|min-width|flex-basis)\s*:\s*(\d+(?:\.\d+)?)px")
RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")


def read_lock(path: Path) -> dict:
    """Bullets under each `## Heading`, keyed by lowercased heading, plus Key: lines."""
    sections, keys, current = {}, {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).lower()
            sections.setdefault(current, [])
            continue
        bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
        if bullet and current:
            item = re.split(r"\s+[—–]\s+|\s+-\s+", bullet.group(1), maxsplit=1)[0]
            sections[current].append(item.strip().strip("`\"'").lower())
            continue
        key = re.match(r"^([A-Za-z ]+):\s*(.+)$", line)
        if key:
            keys[key.group(1).strip().lower()] = key.group(2).strip()
    frames = [int(w) for w, _ in re.findall(r"(\d+)\s*[x×]\s*(\d+)", keys.get("frames", ""))]
    return {
        "glossary": set(sections.get("glossary", [])),
        "served": set(sections.get("served vocabulary", [])),
        "allowed": set(sections.get("allowed strings", [])),
        "narrowest": min(frames) if frames else None,
        "button_sizes": int(keys.get("button sizes", "1")),
    }


class Render(HTMLParser):
    def __init__(self, default_screen: str):
        super().__init__(convert_charrefs=True)
        self.stack = []  # (tag, attrs, parent screen, text buffer or None, kind)
        self.skip = 0
        self.screen = default_screen
        self.texts = []  # (text, screen, kind) kind: plain | label | value
        self.primaries = {}
        self.buttons = []  # (classes, inline style)
        self.styles = []
        self.css = ""

    def handle_starttag(self, tag, attrs):
        attrs = {k: v or "" for k, v in attrs}
        if tag in SKIP:
            self.skip += 1
            self.stack.append((tag, attrs, self.screen, None, None))
            return
        screen = attrs.get("data-screen") or self.screen
        classes = attrs.get("class", "").split()
        actionable = tag in ACTION or attrs.get("role") == "button"
        if actionable and ("data-primary" in attrs or any(
            re.search(r"(?:^|[-_])primary$", c) and not c.startswith(("text-", "border-"))
            for c in classes
        )):
            self.primaries[screen] = self.primaries.get(screen, 0) + 1
        if tag == "button" or attrs.get("role") == "button" or (
            tag in ACTION and any("btn" in c or "button" in c for c in classes)
        ):
            self.buttons.append((classes, attrs.get("style", "")))
        if attrs.get("placeholder"):
            self.texts.append((attrs["placeholder"], screen, "plain"))
        for match in WIDE.finditer(attrs.get("style", "")):
            self.styles.append(float(match.group(1)))
        if tag in VOID:
            return
        kind = "value" if "data-value" in attrs else "label" if "data-label" in attrs else None
        buffer = [] if (tag in BLOCK or kind or "data-screen" in attrs) else None
        self.stack.append((tag, attrs, self.screen, buffer, kind))
        self.screen = screen

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                break
        else:
            return
        while len(self.stack) > index:
            entry = self.stack.pop()
            if entry[0] in SKIP:
                self.skip -= 1
                self.screen = entry[2]
                continue
            _, _, parent_screen, buffer, kind = entry
            if buffer is not None:
                text = " ".join("".join(buffer).split())
                if text:
                    self.texts.append((text, self.screen, kind or "plain"))
            self.screen = parent_screen

    def handle_data(self, data):
        if self.skip:
            if self.stack and self.stack[-1][0] == "style":
                self.styles_css(data)
            return
        for entry in reversed(self.stack):
            if entry[3] is not None:
                entry[3].append(data)
                return

    def styles_css(self, css):
        self.css += css
        for match in WIDE.finditer(css):
            self.styles.append(float(match.group(1)))


def button_signatures(render: Render) -> set:
    css_sizes = {}
    for selector, body in RULE.findall(render.css):
        sizes = tuple(sorted(SIZE_PROP.findall(body)))
        if sizes:
            for token in re.findall(r"\.([A-Za-z0-9_-]+)", selector):
                css_sizes[token] = css_sizes.get(token, ()) + sizes
    signatures = set()
    for classes, style in render.buttons:
        parts = [c for c in classes if SIZE_WORD.search(c) or SIZE_UTILITY.match(c)]
        parts += [f"{k}:{v.strip()}" for c in classes for k, v in css_sizes.get(c, ())]
        parts += [f"{k}:{v.strip()}" for k, v in sorted(SIZE_PROP.findall(style))]
        signatures.add(tuple(sorted(set(parts))) or ("default",))
    return signatures


def is_sentence(text: str) -> bool:
    words = WORD.findall(text)
    if text.rstrip().endswith("?"):
        return True
    if len(words) >= 8:
        return True
    return len(words) >= 4 and bool(re.search(r"[.!](?:\s|$)", text))


def check(files: list, lock: dict) -> dict:
    known = lock["glossary"] | lock["served"] | lock["allowed"]
    results = {name: [] for name in (
        "microcopy", "provenance", "primary actions", "frame fit", "button sizes", "glossary",
    )}
    signatures = set()
    for path in files:
        render = Render(path.stem)
        render.feed(path.read_text(encoding="utf-8"))
        render.close()
        where = path.name
        for text, screen, kind in render.texts:
            lowered = text.lower()
            if kind == "value" or lowered in lock["allowed"]:
                continue
            if kind == "label":
                if lowered not in lock["served"]:
                    results["provenance"].append(f"{where} [{screen}]: {text!r}")
                continue
            if is_sentence(text):
                results["microcopy"].append(f"{where} [{screen}]: {text!r}")
            elif WORD.search(text) and not re.search(r"\d", text) and lowered not in known:
                results["glossary"].append(f"{where} [{screen}]: {text!r}")
        for screen, count in sorted(render.primaries.items()):
            if count > 1:
                results["primary actions"].append(f"{where} [{screen}]: {count} primary actions")
        if lock["narrowest"]:
            for width in render.styles:
                if width > lock["narrowest"]:
                    results["frame fit"].append(
                        f"{where}: fixed width {width:g}px exceeds the {lock['narrowest']}px frame"
                    )
        signatures |= button_signatures(render)
    if len(signatures) > lock["button_sizes"]:
        results["button sizes"].append(
            f"{len(signatures)} button sizes, lock allows {lock['button_sizes']}: "
            + "; ".join(" ".join(s) for s in sorted(signatures))
        )
    return results


def main(argv: list) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    target, lock_path = Path(argv[1]), Path(argv[2])
    files = sorted(target.rglob("*.html")) if target.is_dir() else [target]
    if not files or not all(f.is_file() for f in files) or not lock_path.is_file():
        print("precheck: no render or no lock doc at the given paths", file=sys.stderr)
        return 2
    results = check(files, read_lock(lock_path))
    failed = False
    for name, findings in results.items():
        failed |= bool(findings)
        print(f"{'FAIL' if findings else 'pass'}  {name}: {len(findings)}")
        for finding in findings:
            print(f"      {finding}")
    print(f"{len(files)} render(s) checked; static markup only, run the browser pass for layout")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
