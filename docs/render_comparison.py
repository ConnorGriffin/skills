#!/usr/bin/env python3
"""Render captured replies as SVG cards for docs/before-after.md.

Every card is drawn from a real captured reply on disk, never from prose typed
into this file, so a re-measured run changes the pictures by re-running this.
Both arms of a comparison get identical width, identical fonts and the same
inline-code colouring, and neither is truncated: the height difference is the
finding.

Usage:
  python3 docs/render_comparison.py
"""

import json
import pathlib
import re
import textwrap

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img"
TRANSCRIPTS = ROOT / "examples" / "transcripts"
RESULTS = ROOT / "bench" / "results"

COLS = 58
ADVANCE = 8.06
LINE = 20
FONT = 13
PAD = 14
GUTTER = 18
HEADER = 46

BG = "#0d1117"
EDGE = "#30363d"
TEXT = "#c9d1d9"
STRONG = "#e6edf3"
MUTED = "#8b949e"
CODE = "#79c0ff"
FENCE_BG = "#161b22"
FENCE_TEXT = "#a5d6ff"
QUOTE_EDGE = "#3d444d"
PROMPT_BG = "#161b22"

RETRY_PROMPT = (
    "Ops says a flaky artifact upload gives up after 3 tries, but the config sets "
    "retries to 3 and the README promises one initial attempt plus 3 retries. The "
    "test suite is green. What is wrong and what should change?"
)
INTERVIEW_PROMPT = (
    "I want uploads that exhaust every retry to go somewhere instead of vanishing "
    "into a raised exception. Ask me whatever you need before writing any code."
)


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def transcript(name):
    raw = (TRANSCRIPTS / name).read_text()
    header = re.match(r"<!--(.*?)-->", raw, re.DOTALL)
    tokens = re.search(r"(\d+) output tokens", header.group(1)) if header else None
    body = raw[header.end():].strip() if header else raw.strip()
    return body, int(tokens.group(1)) if tokens else None


def bench_reply(filename, question_id, model, style):
    for line in (RESULTS / filename).open():
        row = json.loads(line)
        if row["id"] == question_id and row["model"] == model and row["style"] == style:
            return row["text"].strip(), row["output_tokens"]
    raise LookupError(f"{filename}: no q{question_id} {model} {style}")


def layout(body, cols=COLS):
    """Wrap markdown-ish text into styled lines: (kind, text)."""
    lines = []
    fenced = False
    for raw in body.splitlines():
        if raw.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            for piece in textwrap.wrap(
                raw.rstrip(), width=cols, subsequent_indent="  ",
                break_long_words=True, break_on_hyphens=False,
            ) or [""]:
                lines.append(("fence", piece))
            continue
        if not raw.strip():
            lines.append(("blank", ""))
            continue
        kind = "text"
        stripped = raw
        if raw.lstrip().startswith(">"):
            kind = "quote"
            stripped = raw.lstrip()[1:].strip()
        indent = ""
        bullet = re.match(r"^(\s*)([-*]|\d+\.)\s+", stripped)
        if bullet:
            indent = " " * (len(bullet.group(0)))
        width = cols - (2 if kind == "quote" else 0)
        wrapped = textwrap.wrap(
            stripped, width=width, subsequent_indent=indent,
            break_long_words=False, break_on_hyphens=False,
        ) or [""]
        for piece in wrapped:
            lines.append((kind, piece))
    while lines and lines[-1][0] == "blank":
        lines.pop()
    return lines


def runs(text, in_code=False, in_strong=False, in_italic=False):
    """Split a line into (style, chunk) runs, carrying spans across wraps.

    Wrapping happens before styling, so a code, bold or italic span can open on one
    line and close on the next. Returning the end states keeps the styling
    continuous instead of leaving stray markers mid-paragraph.
    """
    out = []
    code_segments = text.split("`")
    for code_index, segment in enumerate(code_segments):
        if in_code:
            if segment:
                out.append(("code", segment))
        else:
            strong_segments = segment.split("**")
            for strong_index, strong_segment in enumerate(strong_segments):
                italic_segments = strong_segment.split("*")
                for italic_index, chunk in enumerate(italic_segments):
                    if chunk:
                        style = "strong" if in_strong else "plain"
                        if in_italic:
                            style = f"{style}-italic" if in_strong else "italic"
                        out.append((style, chunk))
                    if italic_index < len(italic_segments) - 1:
                        in_italic = not in_italic
                if strong_index < len(strong_segments) - 1:
                    in_strong = not in_strong
        # A marker separates segments, so the last segment closes no span.
        if code_index < len(code_segments) - 1:
            in_code = not in_code
    return (out or [("plain", "")]), in_code, in_strong, in_italic


def draw_lines(lines, x, y, width):
    svg = []
    in_code = in_strong = in_italic = False
    for kind, text in lines:
        if kind == "blank":
            y += LINE // 2
            in_code = in_strong = in_italic = False
            continue
        if kind == "fence":
            svg.append(
                f'<rect x="{x - 6}" y="{y - 14}" width="{width + 12}" height="{LINE}" '
                f'fill="{FENCE_BG}"/>'
            )
        text_x = x
        if kind == "quote":
            svg.append(
                f'<rect x="{x}" y="{y - 14}" width="2" height="{LINE}" fill="{QUOTE_EDGE}"/>'
            )
            text_x = x + 12
        spans = []
        if kind == "fence":
            line_runs = [("fence", text)]
        else:
            line_runs, in_code, in_strong, in_italic = runs(
                text, in_code, in_strong, in_italic)
        for style, chunk in line_runs:
            attrs = ""
            if kind == "fence":
                attrs = f' fill="{FENCE_TEXT}"'
            elif style == "code":
                attrs = f' fill="{CODE}"'
            else:
                if "strong" in style:
                    attrs += f' fill="{STRONG}" font-weight="600"'
                if "italic" in style:
                    attrs += ' font-style="italic"'
                    if "strong" not in style:
                        attrs += f' fill="{MUTED}"'
            spans.append(f'<tspan{attrs}>{esc(chunk)}</tspan>' if attrs else esc(chunk))
        svg.append(
            f'<text x="{text_x}" y="{y}" xml:space="preserve">{"".join(spans)}</text>'
        )
        y += LINE
    return svg, y


def card(x, y, width, label, meta, lines):
    body, end = draw_lines(lines, x + PAD, y + HEADER, width - 2 * PAD)
    height = end - y + PAD - LINE + 8
    svg = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" '
        f'fill="{BG}" stroke="{EDGE}"/>',
        f'<text x="{x + PAD}" y="{y + 24}" fill="{STRONG}" font-weight="600">{esc(label)}</text>',
        f'<text x="{x + width - PAD}" y="{y + 24}" fill="{MUTED}" text-anchor="end">{esc(meta)}</text>',
        f'<line x1="{x}" y1="{y + 34}" x2="{x + width}" y2="{y + 34}" stroke="{EDGE}"/>',
        *body,
    ]
    return svg, height


def prompt_card(x, y, width, prompt, cols):
    lines = layout(prompt, cols)
    body, end = draw_lines(lines, x + PAD, y + 42, width - 2 * PAD)
    height = end - y + PAD - LINE + 6
    svg = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" '
        f'fill="{PROMPT_BG}" stroke="{EDGE}"/>',
        f'<text x="{x + PAD}" y="{y + 20}" fill="{MUTED}" font-weight="600">asked</text>',
        *body,
    ]
    return svg, height


def document(width, height, parts):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace" font-size="{FONT}" fill="{TEXT}">',
        f'<rect width="{width}" height="{height}" fill="none"/>',
        *parts,
        "</svg>",
        "",
    ])


def words(text):
    return len(re.sub(r"[`*>]", "", text).split())


def comparison(name, prompt, left, right):
    col = int(COLS * ADVANCE) + 2 * PAD
    width = col * 2 + GUTTER
    parts, y = [], 0
    if prompt:
        block, height = prompt_card(0, 0, width, prompt, int(width / ADVANCE) - 6)
        parts += block
        y = height + GUTTER
    heights = []
    for index, (label, text, tokens) in enumerate((left, right)):
        meta = f"{words(text)} words, {tokens} output tokens"
        block, height = card(index * (col + GUTTER), y, col, label, meta, layout(text))
        parts += block
        heights.append(height)
    (IMG / name).write_text(document(width, y + max(heights), parts))
    return name, width, y + max(heights)


def single(name, prompt, label, text, tokens):
    cols = 76
    width = int(cols * ADVANCE) + 2 * PAD
    parts, y = [], 0
    block, height = prompt_card(0, 0, width, prompt, cols)
    parts += block
    y = height + GUTTER
    meta = f"{words(text)} words, {tokens} output tokens"
    block, height = card(0, y, width, label, meta, layout(text, cols))
    parts += block
    (IMG / name).write_text(document(width, y + height, parts))
    return name, width, y + height


def main():
    IMG.mkdir(parents=True, exist_ok=True)

    default_body, default_tokens = transcript("claude-opus-5.default.md")
    say_less_body, say_less_tokens = transcript("claude-opus-5.say-less.md")
    print(*comparison(
        "retry-diagnosis.svg", RETRY_PROMPT,
        ("default style", default_body, default_tokens),
        ("say-less", say_less_body, say_less_tokens),
    ))

    question = next(
        q for q in json.loads((ROOT / "bench" / "questions.json").read_text())
        if q["id"] == 10
    )
    trap_default, trap_default_tokens = bench_reply(
        "shipped.jsonl", 10, "claude-opus-5", "default")
    trap_say_less, trap_say_less_tokens = bench_reply(
        "val-p-opus.jsonl", 10, "claude-opus-5", "say-less")
    print(*comparison(
        "trap-question.svg", question["prompt"],
        ("default style", trap_default, trap_default_tokens),
        ("say-less", trap_say_less, trap_say_less_tokens),
    ))

    interview_body, interview_tokens = transcript("interview-round.md")
    print(*single(
        "interview-round.svg", INTERVIEW_PROMPT,
        "say-less", interview_body, interview_tokens,
    ))


if __name__ == "__main__":
    main()
