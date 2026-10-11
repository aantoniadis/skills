"""Check the npm payload from both clean and locally prepared package trees."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("npm"), "npm is needed to inspect its package payload")
class PackageTests(unittest.TestCase):
    def test_preparation_does_not_change_payload_and_references_are_shipped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("skills", "opencode"):
                shutil.copytree(ROOT / name, root / name,
                                ignore=shutil.ignore_patterns("node_modules", "__pycache__", "*.pyc"))
            for name in ("package.json", "README.md", "LICENSE", "THIRD-PARTY-NOTICES.md"):
                shutil.copy2(ROOT / name, root / name)

            def payload():
                result = subprocess.run([shutil.which("npm"), "pack", "--dry-run", "--ignore-scripts", "--json"],
                                        cwd=root, capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stderr)
                return {f["path"] for f in json.loads(result.stdout)[0]["files"]}

            clean = payload()
            for name in ("skills/diagram-renderer/node_modules/fixture/package.json",
                         "skills/diagram-renderer/node_modules/fixture/local.js",
                         "skills/__pycache__/render_page.cpython-314.pyc",
                         "skills/find-bugs/scripts/__pycache__/untested_added_lines.cpython-314.pyc"):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("{}\n")
            self.assertEqual(clean, payload(), "local installations and caches must not enter the release")
            self.assertTrue({"skills/render_page.py", "skills/page-template.html", "skills/peek.js",
                             "skills/assets/manrope-latin.woff2", "skills/diagram-renderer/package-lock.json",
                             "skills/diagram-renderer/render.mjs"} <= clean)
            for name in clean:
                if not name.endswith(".md") or not name.startswith("skills/"):
                    continue
                path = root / name
                prose = re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", "", path.read_text())
                for link in re.findall(r"\]\(([^\s)]+)\)", prose):
                    if "://" in link or link.startswith(("#", "/")):
                        continue
                    target = (path.parent / link.split("#", 1)[0]).resolve()
                    self.assertTrue(target.is_relative_to(root), (name, link))
                    self.assertIn(str(target.relative_to(root)), clean, (name, link))


if __name__ == "__main__":
    unittest.main()
