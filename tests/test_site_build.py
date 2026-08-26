"""Public-interface tests for the generated documentation site."""

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.validate import FORBIDDEN


ROOT = Path(__file__).resolve().parents[1]


class SiteBuildTest(unittest.TestCase):
    def test_builds_real_pack_with_resolved_internal_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            subprocess.run(["/opt/homebrew/bin/python3", "site/build.py", "--out", str(output)], cwd=ROOT, check=True)
            skills = [path.parent.name for path in ROOT.glob("skills/*/*/SKILL.md")]
            self.assertEqual({path.stem for path in (output / "skills").glob("*.html")}, set(skills))
            anchors = {}
            for page in output.rglob("*.html"):
                text = page.read_text()
                anchors[page.resolve()] = set(re.findall(r' id="([^"]+)"', text))
                self.assertNotIn('href="#"', text)
                self.assertNotRegex(text, r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
                self.assertNotRegex(text, r"<(?:script|img)\b")
                self.assertIn('<svg class="diagram"', text)
                for pattern in FORBIDDEN: self.assertIsNone(pattern.search(text), pattern.pattern)
            skill_page = (output / "skills" / "ui-craft.html").read_text()
            self.assertEqual(re.findall(r"<dt>([^<]+)</dt>", skill_page), ["Invoke", "Requires", "Bundled", "Source"])
            self.assertEqual(skill_page.count("<h1>"), 1)
            for page in output.rglob("*.html"):
                for href in re.findall(r'(?:href|src)="([^"]+)"', page.read_text()):
                    if re.match(r"(?:https?://|mailto:)", href): continue
                    target, _, fragment = href.partition("#")
                    destination = (page.parent / target).resolve() if target else page.resolve()
                    self.assertTrue(destination.exists(), href)
                    if fragment: self.assertIn(fragment, anchors.get(destination, set()), href)


if __name__ == "__main__":
    unittest.main()
