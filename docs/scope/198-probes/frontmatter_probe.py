"""Probe: every skills/*/*/SKILL.md has YAML frontmatter with name and description,
parseable with stdlib only (no yaml module)."""
import pathlib, re

def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return None
    fields = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^(\w[\w-]*):\s*(.*)$", line)
        if km:
            fields[km.group(1)] = km.group(2)
    return fields

bad = []
count = 0
for p in sorted(pathlib.Path("skills").glob("*/*/SKILL.md")):
    count += 1
    f = parse_frontmatter(p.read_text())
    if not f or "name" not in f or "description" not in f:
        bad.append(str(p))
print(f"skill files: {count}; missing/name-less frontmatter: {bad}")
