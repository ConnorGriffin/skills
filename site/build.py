#!/usr/bin/env python3
"""Build the static skills documentation site using only the standard library."""

from __future__ import annotations

import argparse
import html
import importlib.util
import re
import shutil
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GITHUB = "https://github.com/ConnorGriffin/skills"
BUILD_STAMP = ".site-build-stamp"
CATEGORIES = ("workflows", "drivers", "tools")
BLURBS = {
    "workflows": "Front doors. You name the situation; the workflow classifies it and routes to exactly one specialist skill — it does no work itself.",
    "drivers": "Lifecycles. A driver owns a piece of work from arrival to done, through named verbs and state it records outside the conversation.",
    "tools": "References and single passes. Load one for its vocabulary, its checklist, or one bounded job, then get on with the work.",
}


def slug(text: str, seen: dict[str, int] | None = None) -> str:
    value = re.sub(r"[^a-z0-9 -]", "", text.lower()).replace(" ", "-")
    value = re.sub(r"-+", "-", value).strip("-")
    if seen is None:
        return value
    count = seen[value]
    seen[value] += 1
    return value if count == 0 else f"{value}-{count}"


def first_sentence(text: str) -> str:
    """Keep sentence punctuation in filenames and abbreviations intact."""
    match = re.search(r"\.(?=\s+[A-Z]|$)", text)
    return text[:match.end()] if match else text


def bundled_contents(skill: dict) -> str:
    """Describe the shipped top-level contents of a skill directory."""
    contents = ["SKILL.md"]
    contents.extend(
        entry.name + "/" if entry.is_dir() else entry.name
        for entry in sorted(skill["path"].parent.iterdir())
        if entry.name != "SKILL.md" and not entry.name.startswith(".")
    )
    return " + ".join(contents)


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not match:
        raise ValueError("missing YAML frontmatter")
    fields = dict(re.findall(r"^([^:\n]+):\s*(.*)$", match.group(1), re.M))
    return {key: value[1:-1] if value.startswith('"') and value.endswith('"') else value for key, value in fields.items()}, match.group(2)


def load_relationships():
    spec = importlib.util.spec_from_file_location("relationships", ROOT / "site/relationships.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.RELATIONSHIPS


def load_skills():
    skills = {}
    for path in sorted((ROOT / "skills").glob("*/*/SKILL.md")):
        meta, body = frontmatter(path.read_text())
        category = path.parents[1].name
        skills[meta["name"]] = {"name": meta["name"], "description": meta["description"], "body": body, "path": path, "category": category}
    return skills


def inline(text: str, current: dict, skills: dict, code_spans=None, restore_code=True) -> str:
    if code_spans is None:
        code_spans = []

    def protect_code(match):
        code_spans.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"@@CODE{len(code_spans) - 1}@@"

    def link(match):
        label, href = match.groups()
        base, fragment = (href.split("#", 1) + [""])[:2] if "#" in href else (href, "")
        suffix = "#" + fragment if fragment else ""
        if not base:
            target = href
        elif re.match(r"(?:https?://|mailto:)", base):
            target = href
        else:
            resolved = (current["path"].parent / base).resolve()
            target_skill = next((skill for skill in skills.values() if skill["path"].resolve() == resolved), None)
            target = f"{target_skill['name']}.html{suffix}" if target_skill else f"{GITHUB}/blob/main/{resolved.relative_to(ROOT).as_posix()}{suffix}"
        return f'<a href="{html.escape(target, quote=True)}">{inline(label, current, skills, code_spans, False)}</a>'
    escaped = html.escape(re.sub(r"`([^`]+)`", protect_code, text))
    escaped = re.sub(r"\[([^]]+)\]\(([^)]+)\)", link, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!_)__([^_]+)__(?!_)", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    escaped = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<em>\1</em>", escaped)
    if restore_code:
        return re.sub(r"@@CODE(\d+)@@", lambda match: code_spans[int(match.group(1))], escaped)
    return escaped


def markdown(body: str, current: dict, skills: dict, drop_leading_h1=False) -> str:
    lines, out, seen, i = body.splitlines(), [], defaultdict(int), 0
    if drop_leading_h1:
        heading_index = 0
        while heading_index < len(lines) and not lines[heading_index].strip():
            heading_index += 1
        if heading_index < len(lines) and lines[heading_index].startswith("# "):
            i = heading_index + 1
    def flush_paragraph(parts):
        if parts: out.append("<p>" + inline(" ".join(parts), current, skills) + "</p>")
    paragraph = []
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            flush_paragraph(paragraph); paragraph=[]; language=line[3:]; i+=1; code=[]
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i+=1
            out.append(f'<pre><code class="language-{html.escape(language)}">{html.escape(chr(10).join(code))}</code></pre>')
        elif re.match(r"^(#{1,6}) ", line):
            flush_paragraph(paragraph); paragraph=[]; marks, text = re.match(r"^(#+) (.*)$", line).groups(); level=len(marks); ident=slug(text, seen)
            out.append(f"<h{level} id=\"{ident}\">{inline(text, current, skills)}</h{level}>")
        elif re.match(r"^[-*] ", line) or re.match(r"^\d+\. ", line):
            flush_paragraph(paragraph); paragraph=[]; ordered=bool(re.match(r"^\d+\. ", line)); tag="ol" if ordered else "ul"; items=[]
            while (i < len(lines) and bool(re.match(r"^\d+\. ", lines[i])) == ordered
                   and (re.match(r"^[-*] ", lines[i]) or re.match(r"^\d+\. ", lines[i]))):
                items.append(re.sub(r"^(?:[-*]|\d+\.) ", "", lines[i])); i+=1
            out.append(f'<{tag} class="body-list">' + "".join(f"<li>{inline(x, current, skills)}</li>" for x in items) + f"</{tag}>"); continue
        elif "|" in line and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-+", lines[i + 1]):
            flush_paragraph(paragraph); paragraph=[]; headers=[x.strip() for x in line.strip("|").split("|")]; i+=2; rows=[]
            while i < len(lines) and "|" in lines[i] and lines[i].strip(): rows.append([x.strip() for x in lines[i].strip("|").split("|")]); i+=1
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(x,current,skills)}</th>" for x in headers) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline(x,current,skills)}</td>" for x in row) + "</tr>" for row in rows) + "</tbody></table>"); continue
        elif not line.strip(): flush_paragraph(paragraph); paragraph=[]
        else: paragraph.append(line)
        i += 1
    flush_paragraph(paragraph)
    return "\n".join(out)


def node(skill, x, y, width=152):
    cat = skill["category"]
    return (f'<g class="node cat-{cat} n-{skill["name"]}" tabindex="0"><title>{skill["name"]} ({cat})</title>'
            f'<rect class="box" x="{x}" y="{y}" width="{width}" height="28" fill="var(--cat-bg)" stroke="var(--cat)"/>'
            f'<text class="nlabel" x="{x+9}" y="{y+18}" fill="var(--cat)">{skill["name"]}</text></g>')


def edge_path(x, y, tx, ty):
    """Route an edge through the sides of two fixed-size diagram boxes."""
    if abs(tx - x) >= abs(ty - y):
        start_x, end_x = (x + 152, tx) if tx >= x else (x, tx + 152)
        direction = 36 if tx >= x else -36
        return f"M{start_x},{y+14} C{start_x+direction},{y+14} {end_x-direction},{ty+14} {end_x},{ty+14}"
    start_y, end_y = (y + 28, ty) if ty >= y else (y, ty + 28)
    direction = 36 if ty >= y else -36
    return f"M{x+76},{start_y} C{x+76},{start_y+direction} {tx+76},{end_y-direction} {tx+76},{end_y}"


def diagram(skills, edges, kind="map", focus=None, flow=None):
    labels=""
    if flow:
        # Serpentine: rows alternate direction, so consecutive steps stay
        # adjacent instead of wrapping back across the whole figure (lock term 23).
        listed=[skills[n] for n in flow]; positions=[]
        for i, skill in enumerate(listed):
            row, col = divmod(i, 3)
            if row % 2: col = 2 - col
            positions.append((skill, 24 + col*200, 16 + row*74))
        height=74*((len(listed)-1)//3+1)+34; width=624
    elif focus:
        incoming=[skills[n] for n, data in edges.items() if focus in data["uses"]]; outgoing=[skills[n] for n in edges[focus]["uses"]]
        listed=incoming + [skills[focus]] + outgoing; positions=[]
        for col, group in enumerate((incoming, [skills[focus]], outgoing)):
            for row, skill in enumerate(group): positions.append((skill, 24+col*200, 42+row*42))
        width=624; height=max(150, 72+42*max(len(incoming),len(outgoing),1))
        # Bands say what the columns MEAN; category names here would be wrong,
        # because either band mixes categories (lock term 21).
        labels=('<text class="glabel" x="24" y="28">referenced by</text>'
                '<text class="glabel" x="424" y="28">references</text>')
    else:
        positions=[]; width=900; rows=defaultdict(int)
        # Tools is far longer than the other two; it runs in two sub-columns so
        # the map stays wide rather than tall (lock term 7).
        by_category={c:[s for s in skills.values() if s["category"]==c] for c in CATEGORIES}
        split=(len(by_category["tools"])+1)//2
        columns=[("workflows", by_category["workflows"], 24), ("drivers", by_category["drivers"], 248),
                 ("tools", by_category["tools"][:split], 472), (None, by_category["tools"][split:], 684)]
        for _, members, x in columns:
            for i, skill in enumerate(members): positions.append((skill, x, 54+i*36))
        height=max(210, 64+max(len(m) for _, m, _ in columns)*36)
        labels="".join(f'<text class="glabel" x="{x}" y="28">{c}</text>' for c, _, x in columns if c)
    lookup={s["name"]:(x,y) for s,x,y in positions}; paths=[]
    connections=list(zip(flow, flow[1:])) if flow else [(a,b) for a,d in edges.items() for b in d["uses"] if a in lookup and b in lookup]
    for source,target in connections:
        if source in lookup and target in lookup:
            x, y = lookup[source]
            tx, ty = lookup[target]
            paths.append(f'<path class="edge e-{source} e-{target}" d="{edge_path(x, y, tx, ty)}" marker-end="url(#arw)"/>')
    diagram_class = "diagram" if flow else "diagram isolating"
    return f'<svg class="{diagram_class}" viewBox="0 0 {width} {height}" role="img" aria-label="Relationship diagram for the skills pack."><defs><marker id="arw" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="var(--ink-dim)"/></marker></defs>{labels}<g class="edges">{"".join(paths)}</g>{"".join(node(s,x,y) for s,x,y in positions)}</svg>'


def isolation_style(skills, names):
    return "".join(
        f'.diagram:has(.n-{name}:hover) .e-{name},.diagram:has(.n-{name}:focus-visible) .e-{name}'
        f'{{opacity:.95;stroke:var(--c-{skill["category"].rstrip("s")});stroke-width:1.4}}'
        for name in sorted(names)
        for skill in [skills[name]]
    )


def chrome(title, subtitle, current, prefix="", style="", tag=""):
    nav=[("Overview", f"{prefix}index.html", current=="Overview"), ("Workflows", f"{prefix}index.html#workflows", current=="Workflows"), ("Drivers", f"{prefix}index.html#drivers", current=="Drivers"), ("Tools", f"{prefix}index.html#tools", current=="Tools"), ("The ticket flow", f"{prefix}workflows/ticket-flow.html", current=="The ticket flow"), ("Source on GitHub", GITHUB, False)]
    tagmark=f'<span class="tag">{tag}</span>' if tag else ""
    tagclass=f" cat-{tag}" if tag else ""
    links = "".join(
        f'<a href="{href}">{name}</a>' if not active
        else f'<a href="{href}" aria-current="page">{name}</a>'
        for name, href, active in nav
    )
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    style_tag = f"<style>{style}</style>" if style else ""
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} — skills</title><link rel="stylesheet" href="{prefix}style.css">{style_tag}</head><body><div class="page"><nav class="sitenav">{links}</nav><header class="masthead{tagclass}">{tagmark}<h1>{title}</h1>{subtitle_html}</header>'


def footer(): return f'<footer class="foot">skills — Connor Griffin · MIT · generated from the SKILL.md files, hand-authored narratives, and hand-maintained relationship data in <a href="{GITHUB}">the repository</a></footer></div></body></html>'


def build(out: Path):
    skills, relationships = load_skills(), load_relationships()
    if set(skills) != set(relationships): raise ValueError("relationships.py must have exactly one entry for every skill")
    for name, data in relationships.items():
        if set(data) != {"uses", "requirements"} or any(target not in skills for target in data["uses"]): raise ValueError(f"invalid relationship for {name}")
    if out.exists() and not out.is_dir():
        raise ValueError(f"refusing to replace non-directory output: {out}")
    if out.exists() and any(out.iterdir()) and not (out / BUILD_STAMP).is_file():
        raise ValueError(f"refusing to clear unrecognized output directory: {out}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True); (out / "skills").mkdir(); (out / "workflows").mkdir()
    (out / BUILD_STAMP).write_text("generated by site/build.py\n")
    shutil.copyfile(ROOT / "site/style.css", out / "style.css")
    tables=[]
    for category in CATEGORIES:
        entries=[s for s in skills.values() if s["category"]==category]
        rows="".join(f'<li><a class="name" href="skills/{s["name"]}.html">{s["name"]}</a><span class="desc">{first_sentence(s["description"])}</span></li>' for s in entries)
        tables.append(f'<section class="cat-{category}" id="{category}"><div class="cathead"><h2>{category}</h2><span class="count">{len(entries)}</span></div><p>{BLURBS[category]}</p><ul class="skills">{rows}</ul></section>')
    index_style = isolation_style(skills, skills)
    index=chrome("skills", "", "Overview", style=index_style) + '<p class="prose">A portable skill pack for coding agents. Twenty-seven skills that turn a vague request into tracked work, that work into a reviewed pull request, and that pull request into merged history — with the decisions written down as they are made.</p><figure class="figure"><div class="diagram-scroll">' + diagram(skills,relationships) + '</div><div class="legend"><span class="cat-workflows"><i></i>workflows</span><span class="cat-drivers"><i></i>drivers</span><span class="cat-tools"><i></i>tools</span><span>→ references</span></div><figcaption>Every skill in the pack, and every skill it names. Hover or tab to a box to isolate that skill’s references.</figcaption></figure><div class="catgrid"><div class="catcol">' + tables[0]+tables[1] + '</div><div class="catcol cat-tools">'+tables[2]+'</div></div>'+footer()
    (out / "index.html").write_text(index)
    for skill in skills.values():
        n=skill["name"]; incoming=[x for x,d in relationships.items() if n in d["uses"]]; outgoing=relationships[n]["uses"]
        body=markdown(skill["body"],skill,skills,True)
        skill_style = isolation_style(skills, set(incoming + [n] + outgoing))
        content=chrome(n, skill["description"], skill["category"].title(), "../", skill_style, tag=skill["category"]) + f'<dl class="meta"><dt>Invoke</dt><dd>/{n}</dd><dt>Requires</dt><dd>{inline(relationships[n]["requirements"],skill,skills)}</dd><dt>Bundled</dt><dd>{bundled_contents(skill)}</dd><dt>Source</dt><dd><a href="{GITHUB}/blob/main/{skill["path"].relative_to(ROOT).as_posix()}">SKILL.md</a></dd></dl><figure class="figure"><div class="diagram-scroll">{diagram(skills,relationships,focus=n)}</div><figcaption>{len(incoming)} skills name <code>{n}</code>; it names {len(outgoing)}.</figcaption></figure><h2>SKILL.md</h2><div class="prose body">{body}</div>'+footer()
        (out / "skills" / f"{n}.html").write_text(content)
    for path in sorted((ROOT / "site/narratives").glob("*.md")):
        meta, body=frontmatter(path.read_text()); flow=[x.strip() for x in meta["flow"].split(",")]
        if any(x not in skills for x in flow): raise ValueError(f"unknown flow endpoint in {path}")
        current={"path":path,"name":path.stem}; content=chrome(meta["title"],meta["description"], "The ticket flow" if path.stem=="ticket-flow" else "", "../") + f'<figure class="figure"><div class="diagram-scroll">{diagram(skills,relationships,flow=flow)}</div><figcaption>The common path. Boxes are coloured by the category of the skill that owns the step.</figcaption></figure><div class="prose body">{markdown(body,current,skills)}</div>'+footer()
        (out / "workflows" / f"{path.stem}.html").write_text(content)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--out", required=True, type=Path); args=parser.parse_args(); build(args.out)
