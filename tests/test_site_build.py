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
            self.assertTrue((output / ".site-build-stamp").is_file())
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
                self.assertIn('<svg class="diagram', text)
                self.assertNotRegex(text, r'<div class="prose body">\s*</div>')
                for pattern in FORBIDDEN: self.assertIsNone(pattern.search(text), pattern.pattern)
            stylesheet = (output / "style.css").read_text()
            self.assertNotRegex(stylesheet, r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
            for pattern in FORBIDDEN: self.assertIsNone(pattern.search(stylesheet), pattern.pattern)
            skill_page = (output / "skills" / "ui-craft.html").read_text()
            for page in [output / "index.html", *list((output / "skills").glob("*.html"))]:
                styles = re.findall(r"<style>(.*?)</style>", page.read_text())
                self.assertLessEqual(len(styles), 1)
                for style in styles: self.assertIn(".diagram:has(", style)
            for page in (output / "workflows").glob("*.html"):
                self.assertNotIn("<style>", page.read_text())
                self.assertNotIn('class="diagram isolating"', page.read_text())
            self.assertIn('class="diagram isolating"', (output / "index.html").read_text())
            self.assertIn(".diagram.isolating:has(.node:hover) .edge", stylesheet)
            self.assertEqual(re.findall(r"<dt>([^<]+)</dt>", skill_page), ["Invoke", "Requires", "Bundled", "Source"])
            skill_pages = list((output / "skills").glob("*.html"))
            duplicate_h1_pages = [page.name for page in skill_pages if len(re.findall(r"<h1\b", page.read_text())) != 1]
            empty_body_pages = [page.name for page in skill_pages if re.search(r'<div class="prose body">\s*</div>', page.read_text())]
            self.assertEqual(duplicate_h1_pages, [])
            self.assertEqual(empty_body_pages, [])
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

    def test_underscore_emphasis_and_directional_edge_anchors(self):
        builder = load_builder()
        self.assertEqual(builder.inline("_process_ and __important__ and `fix_introduced_defect`", {"path": ROOT / "site/narratives/ticket-flow.md"}, {}), "<em>process</em> and <strong>important</strong> and <code>fix_introduced_defect</code>")
        fenced = builder.markdown("```\nfix_introduced_defect\n```", {"path": ROOT / "site/narratives/ticket-flow.md"}, {})
        self.assertIn("fix_introduced_defect", fenced)
        self.assertNotIn("<em>introduced</em>", fenced)
        self.assertTrue(builder.edge_path(200, 0, 0, 0).startswith("M200,14"))
        self.assertTrue(builder.edge_path(0, 28, 0, 0).startswith("M76,28"))

    def test_leading_blank_h1_is_dropped_without_dropping_a_body_without_one(self):
        builder = load_builder()
        heading_body = builder.markdown("\n# Title\n\nText.\n", {"path": ROOT / "site/narratives/ticket-flow.md"}, {}, True)
        no_heading_body = builder.markdown("\nText.\n", {"path": ROOT / "site/narratives/ticket-flow.md"}, {}, True)
        self.assertNotIn("<h1", heading_body)
        self.assertIn("Text.", heading_body)
        self.assertIn("Text.", no_heading_body)

    def test_refuses_to_clear_foreign_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "foreign-output"
            output.mkdir()
            foreign = output / "keep-me.txt"
            foreign.write_text("foreign")
            result = subprocess.run([sys.executable, "site/build.py", "--out", str(output)], cwd=ROOT, check=False, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(foreign.read_text(), "foreign")


if __name__ == "__main__":
    unittest.main()
