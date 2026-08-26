"""Public-interface tests for the generated documentation site."""

import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate import FORBIDDEN


ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location("site_builder", ROOT / "site/build.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SiteBuildTest(unittest.TestCase):
    def test_builds_real_pack_with_resolved_internal_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            subprocess.run([sys.executable, "site/build.py", "--out", str(output)], cwd=ROOT, check=True)
            stale = output / "skills" / "deleted-skill.html"
            stale.write_text("stale output")
            subprocess.run([sys.executable, "site/build.py", "--out", str(output)], cwd=ROOT, check=True)
            self.assertFalse(stale.exists())
            skills = [path.parent.name for path in ROOT.glob("skills/*/*/SKILL.md")]
            self.assertEqual({path.stem for path in (output / "skills").glob("*.html")}, set(skills))
            anchors = {}
            for page in output.rglob("*.html"):
                text = page.read_text()
                anchors[page.resolve()] = set(re.findall(r' id="([^"]+)"', text))
                self.assertNotIn('href="#"', text)
                self.assertNotRegex(text, r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
                self.assertNotRegex(text, r"<(?:script|img)\b")
                self.assertNotRegex(text, r"<(?:link|script)\b[^>]+https?://")
                self.assertIn('<svg class="diagram"', text)
                self.assertNotRegex(text, r'<div class="prose body">\s*</div>')
                for pattern in FORBIDDEN: self.assertIsNone(pattern.search(text), pattern.pattern)
            stylesheet = (output / "style.css").read_text()
            self.assertNotRegex(stylesheet, r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
            for pattern in FORBIDDEN: self.assertIsNone(pattern.search(stylesheet), pattern.pattern)
            skill_page = (output / "skills" / "ui-craft.html").read_text()
            self.assertEqual(re.findall(r"<dt>([^<]+)</dt>", skill_page), ["Invoke", "Requires", "Bundled", "Source"])
            self.assertEqual(skill_page.count("<h1>"), 1)
            self.assertIn("CLAUDE.md/AGENTS.md estate.", (output / "index.html").read_text())
            self.assertIn("<dt>Invoke</dt><dd>/ui-craft</dd>", skill_page)
            self.assertNotIn(".n-writing-for-agents", (output / "workflows" / "ticket-flow.html").read_text())
            for page in output.rglob("*.html"):
                for href in re.findall(r'(?:href|src)="([^"]+)"', page.read_text()):
                    if re.match(r"(?:https?://|mailto:)", href): continue
                    target, _, fragment = href.partition("#")
                    destination = (page.parent / target).resolve() if target else page.resolve()
                    self.assertTrue(destination.exists(), href)
                    if fragment: self.assertIn(fragment, anchors.get(destination, set()), href)

    def test_duplicate_headings_receive_suffixes(self):
        rendered = load_builder().markdown("## Repeat\n\n## Repeat\n", {"path": ROOT / "site/narratives/ticket-flow.md"}, {})
        self.assertIn('id="repeat"', rendered)
        self.assertIn('id="repeat-1"', rendered)


if __name__ == "__main__":
    unittest.main()
