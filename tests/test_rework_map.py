"""The rework-map fixture passes the shared checker in both modes, and the checker rejects a status word
outside the map's vocabulary: a relationship's result, a special case's reach, a finding's kind."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/rework-map"
SCRIPT = ROOT / "skills/render_page.py"
_spec = importlib.util.spec_from_file_location("page", SCRIPT)
page = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(page)


def run(note, *flags):
    return subprocess.run([sys.executable, str(SCRIPT), str(note), *flags], capture_output=True, text=True)


class ReworkMapTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "rework-map"
        shutil.copytree(FIXTURE, self.root)
        self.note = self.root / "rework-map.md"
        self.source = self.note.read_text()

    def test_fixture_renders_and_checks_in_both_modes(self):
        text_only = run(self.note, "--check", "--markdown-only", "--sync-labels")
        self.assertEqual(text_only.returncode, 0, text_only.stderr)
        self.assertEqual(self.note.read_text(), self.source, "run --sync-labels on the fixture and commit the key")
        rendered = run(self.note, "--sync-labels")
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        html = self.note.with_suffix(".html").read_text()
        for fragment in ('id="questions-for-the-user"', 'id="stated-design-and-the-code"', 'id="special-cases"', 'id="rework-steps"'):
            self.assertIn(fragment, html, fragment)
        checked = run(self.note, "--check", "--sync-labels")
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_label_key_defines_the_three_map_vocabularies(self):
        self.assertEqual([group for group in page.label_groups(self.source) if group != "diagram-evidence"],
                         ["design-results", "special-case-reach", "structure-findings"])
        for group, values in (("design-results", page.DESIGN_RESULTS), ("special-case-reach", page.REACH_STATUSES),
                              ("structure-findings", page.FINDING_KINDS)):
            self.assertEqual(tuple(page.LABELS[group]["options"]), tuple(values))

    def test_status_cells_start_with_a_known_word(self):
        for old, new, message in (
                ("| `quotes` to `pricing` | not found |", "| `quotes` to `pricing` | missing |", "Stated design and the code: start the Result cell"),
                ("| compatibility path | unknown: no caller", "| compatibility path | probably dead: no caller", "Special cases: start the Reach cell"),
                ("| unjustified special case | [rounding.py:8]", "| dead code | [rounding.py:8]", "Findings: start the Kind cell")):
            with self.subTest(new=new):
                self.assertIn(old, self.source)
                self.note.write_text(self.source.replace(old, new))
                result = run(self.note, "--check", "--markdown-only")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr + result.stdout)

    def test_not_reached_is_not_read_as_reached_and_empty_cells_fail(self):
        page.check_rework_map("| Special case | Kind | Reach | Why it exists | Points to |\n| --- | --- | --- | --- | --- |\n"
                              "| `a.py:3` | default | not reached: callers enumerated, probe failed | none found | nothing found |\n")
        with self.assertRaisesRegex(Exception, "fill every table cell"):
            page.check_rework_map("| Finding | Kind | Where | Cost today | Removed by |\n| --- | --- | --- | --- | --- |\n"
                                  "| Rule in two places | scattered rule | `a.py:3` | TBD | kept |\n")

    def test_template_declares_the_kind_and_the_checked_columns(self):
        template = (ROOT / "skills/untangle/references/map-template.md").read_text()
        self.assertTrue(template.startswith("---\nkind: rework-map\n---\n"))
        for columns in page.MAP_TABLES:
            self.assertIn("| " + " | ".join(columns) + " |", template)
        self.assertIn("rework-map", page.NOTE_KINDS)


if __name__ == "__main__":
    unittest.main()
