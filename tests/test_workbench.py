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
    def test_rework_map_reads_problem_by_problem(self):
        directory, note, result = render("rework-map", "rework-map.md")
        self.addCleanup(directory.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        page = BeautifulSoup(note.with_suffix(".html").read_text(), "html.parser")
        self.assertIn("report", page.body["class"])
        main = page.main
        articles = main.select("section#problems > article.problem")
        self.assertEqual([a.get("class") for a in articles], [["problem", "structure", "decision-decided"], ["problem", "structure", "decision-open", "brief"],
                                                              ["problem", "bug", "decision-decided"]], "structure first, the possible bug last")
        self.assertEqual(articles[0].select_one(".problem-number").get_text(), "1.")
        self.assertIsNotNone(articles[2].select_one("figure.history-view"), "the change history draws beside its problem")
        self.assertIsNotNone(articles[0].select_one("figure.sv-focus .sv-pane.today svg"))
        self.assertIsNotNone(articles[0].select_one("figure.sv-focus .sv-pane.proposed svg"))
        self.assertEqual(len(articles[2].select(".code-grid > figure.code-card")), 2, "excerpts that follow each other sit side by side")
        self.assertEqual([d.get("class") for d in main.select(".decision")], [["decision", "decided"], ["decision", "open"], ["decision", "decided"]])
        waiting = main.select("section#in-short .waiting li > a")
        self.assertEqual([a["href"] for a in waiting], ["#2-apply_legacy_rounding-has-no-caller"], "only what waits for the reader is gathered")
        spec = main.select("section#what-it-does li.behavior")
        self.assertEqual([li["class"][-1] for li in spec], ["verified-tested", "verified-tested", "verified-locked", "verified-locked",
                                                            "verified-tested", "verified-untested"])
        rows = main.select("section#how-the-code-carries-it figure.behavior-map tbody tr:not(.bm-feature)")
        self.assertEqual(len(rows), 4)
        self.assertIn("bm-spread", rows[0]["class"], "a behavior decided in two files stands out")
        self.assertEqual(rows[0].select_one("a.bm-problem")["href"], "#1-changing-a-loyalty-rate-takes-three-edits")
        renamed = main.select_one('section#the-plan .sv-file[data-change="renamed"] text')
        self.assertEqual((renamed["data-today"], renamed["data-proposed"]), ("…op/pricing/discounts.py", "shop/pricing/loyalty.py"), "long paths are shortened from the left")
        counts = {chip["class"][1]: chip.b.get_text() for chip in main.select(".report-counts .count")}
        self.assertEqual(counts, {"count-problems": "3", "count-bugs": "1", "count-waiting": "1", "count-defaults": "0"})
        self.assertEqual([s.get_text() for s in main.select(".waiting .waiting-state")], ["open"], "an index: state and title")
        self.assertEqual([s.get_text() for s in main.select(".waiting .waiting-when")], ["can wait"], "when the answer is needed")
        self.assertEqual(main.select_one("article.brief .brief-tag").get_text(), "in brief")
        grid = main.select_one("table.scorecard")
        self.assertEqual(grid.caption.get_text(), "The rework restores 9 of 11 principles.")
        self.assertEqual([td.get_text() for td in grid.select("tbody tr")[2].select("td")], ["not applicable", "not applicable"], "Liskov")
        self.assertIsNotNone(main.select_one("details.scorecard-evidence > ul"), "the evidence folds under the grid")
        rail = page.select_one('nav[aria-label="Sections"]')
        self.assertEqual(len(rail.select("ol.nav-problems > li")), 3)
        self.assertEqual(len(rail.select('a[href="#3-a-gold-customer-is-quoted-38-00-and-charged-36-00"]')), 1, "each problem is listed once")
        self.assertIsNotNone(main.select_one("section#how-it-works-today > details.reference"), "the reference folds")
        self.assertIsNotNone(page.select_one("button.theme-toggle"))
        self.assertNotIn("prefers-color-scheme:dark", page.select_one("style.workbench-style").get_text(), "light unless the reader asks")
        checked = subprocess.run([sys.executable, str(SCRIPT), str(note), "--check", "--sync-labels"], capture_output=True, text=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_change_card_has_the_same_shape_and_its_own_view_labels(self):
        directory, note, result = render("change-card", "change-card.md")
        self.addCleanup(directory.cleanup)
        self.assertEqual(result.returncode, 0, result.stderr)
        page = BeautifulSoup(note.with_suffix(".html").read_text(), "html.parser")
        main = page.main
        self.assertEqual([b.get_text() for b in main.select(".sv-switch button")], ["Before", "After the change"])
        self.assertEqual([p.get_text() for p in main.select(".sv-focus .sv-pane-label")], ["Before", "After the change"])
        self.assertEqual(len(main.select("article.problem")), 2)
        self.assertIn("corner", main.select("article.problem")[1]["class"])
        self.assertEqual(len(main.select("section#in-short .waiting li")), 2, "a default applied waits for the reader too")
        self.assertEqual([p.get_text(" ", strip=True).split(":")[0] for p in main.select("section#in-short > p.field")],
                         ["The problem", "What we propose", "What you decide"])
        grid = main.select_one("table.scorecard")
        self.assertIsNotNone(grid, "the card's design principles draw as a scorecard")
        self.assertEqual(grid.caption.get_text(), "3 of 11 principles broken; the proposal restores 3.", "a card says what it found, not a rework")
        self.assertEqual([th.get_text() for th in grid.select("thead th")], ["Principle", "Before", "After the change"], "the columns follow the view's labels")

    def test_committed_card_fixture_carries_a_current_label_key(self):
        source = (ROOT / "tests/fixtures/change-card/change-card.md").read_text()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        copy = Path(directory.name) / "change-card.md"
        copy.write_text(source)
        result = subprocess.run([sys.executable, str(SCRIPT), str(copy), "--check", "--markdown-only", "--sync-labels"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(copy.read_text(), source, "run --sync-labels on the fixture and commit the key")

    def test_a_card_whose_principles_draw_no_scorecard_fails_its_check(self):
        source = (ROOT / "tests/fixtures/change-card/change-card.md").read_text()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        copy = Path(directory.name) / "change-card.md"
        heading = "### Design principles\n\n"
        liskov = next(line for line in source.splitlines() if line.startswith("- **Liskov substitution:**")) + "\n"
        for changed, message in ((source.replace(heading, "**Design principles:**\n\n"), "not from a bold field"),
                                 (source.replace(liskov, ""), "today's result and the proposed one for: Liskov substitution")):
            with self.subTest(message=message):
                copy.write_text(changed)
                result = subprocess.run([sys.executable, str(SCRIPT), str(copy), "--check", "--markdown-only"], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
