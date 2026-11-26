"""The workbench layout of the structure skills' pages: a rework map and a change card render around the
structure view, with panels copied from their own tables, and still pass every page check."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/render_page.py"


def render(fixture, name):
    directory = tempfile.TemporaryDirectory()
    root = Path(directory.name) / fixture
    shutil.copytree(ROOT / "tests/fixtures" / fixture, root)
    note = root / name
    result = subprocess.run([sys.executable, str(SCRIPT), str(note), "--sync-labels"], capture_output=True, text=True)
    return directory, note, result


class WorkbenchTests(unittest.TestCase):
    def test_rework_map_page_puts_the_view_first_and_copies_the_tables_into_panels(self):
        directory, note, result = render("rework-map", "rework-map.md")
        self.addCleanup(directory.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        page = BeautifulSoup(note.with_suffix(".html").read_text(), "html.parser")
        self.assertIn("workbench", page.body["class"])
        main = page.main
        order = [child.get("class", [None])[0] for child in main.find_all(recursive=False) if child.name != "footer"]
        self.assertEqual(order, ["wb-top", "wb-summary", "wb-hero", "wb-panels", "wb-data", "wb-full"])
        self.assertIsNotNone(main.select_one(".wb-hero figure.structure-view"))
        chips = {chip["class"][1]: chip.b.get_text() for chip in main.select(".wb-chip")}
        self.assertEqual(chips, {"decide": "1", "open": "1", "finding": "2", "lock": "2"})
        panels = {box["aria-label"]: len(box.select(".wb-card")) for box in main.select(".wb-panel")}
        self.assertEqual(panels, {"Decide": 3, "Findings": 2, "Rework": 5})
        self.assertIsNotNone(main.select_one(".wb-target"), "the recommendation heads the rework panel")
        self.assertEqual(len(main.select("section#findings")), 1, "the full text keeps each section once")
        self.assertFalse(any(tag.get("id") for tag in main.select(".wb-panels [id]")), "panel copies carry no ids")
        self.assertIn('data-path="shop/api/serializers.py"', str(main))
        checked = subprocess.run([sys.executable, str(SCRIPT), str(note), "--check", "--sync-labels"], capture_output=True, text=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_change_card_has_its_own_panels_and_view_labels(self):
        directory, note, result = render("change-card", "change-card.md")
        self.addCleanup(directory.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        page = BeautifulSoup(note.with_suffix(".html").read_text(), "html.parser")
        main = page.main
        self.assertEqual([b.get_text() for b in main.select(".sv-switch button")], ["Before", "After the change"])
        self.assertEqual([box["aria-label"] for box in main.select(".wb-panel")], ["Decide", "Findings", "Reshape first"])
        self.assertEqual(len(main.select('.wb-panel[aria-label="Reshape first"] .wb-card')), 3)
        self.assertEqual([label.get_text() for label in main.select(".wb-summary-label")], ["The change", "Fit", "Choice"])
        self.assertIn("dependencies drawn in this view", str(main))

    def test_committed_card_fixture_carries_a_current_label_key(self):
        source = (ROOT / "tests/fixtures/change-card/change-card.md").read_text()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        copy = Path(directory.name) / "change-card.md"
        copy.write_text(source)
        result = subprocess.run([sys.executable, str(SCRIPT), str(copy), "--check", "--markdown-only", "--sync-labels"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(copy.read_text(), source, "run --sync-labels on the fixture and commit the key")


if __name__ == "__main__":
    unittest.main()
