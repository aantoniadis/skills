"""The rework-map fixture passes the shared checker in both modes, and the checker rejects a status word
outside the map's vocabulary: a relationship's result, a special case's reach, and a problem's kind, how
sure, and decision; and a problem that lacks one of its fields."""
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
        for fragment in ('id="in-short"', 'id="problems"', 'id="the-plan"', 'id="what-is-sound"',
                         'id="stated-design-and-the-code"', 'id="special-cases"', 'id="steps"', 'class="history-view"', 'class="sv-focus"'):
            self.assertIn(fragment, html, fragment)
        checked = run(self.note, "--check", "--sync-labels")
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_label_key_defines_the_map_vocabularies(self):
        self.assertEqual([group for group in page.label_groups(self.source) if group != "diagram-evidence"],
                         ["design-results", "rule-results", "special-case-reach", "structure-findings", "problem-evidence", "decision-status",
                          "behavior-verification"])
        for group, values in (("design-results", page.DESIGN_RESULTS), ("rule-results", page.RULE_RESULTS),
                              ("special-case-reach", page.REACH_STATUSES), ("structure-findings", page.PROBLEM_KINDS),
                              ("problem-evidence", page.HOW_SURE)):
            self.assertEqual(tuple(page.LABELS[group]["options"]), tuple(values))
        self.assertEqual(set(page.LABELS["decision-status"]["options"]), set(page.DECISIONS))
        self.assertEqual(tuple(page.LABELS["behavior-verification"]["options"]), page.VERIFIED)

    def test_status_cells_start_with_a_known_word(self):
        for old, new, message in (
                ("| `quotes` to `pricing` | not found |", "| `quotes` to `pricing` | missing |", "Stated design and the code: start the Result cell"),
                ("| holds | search for `quantize`", "| fine | search for `quantize`", "Stated rules: start the Result cell"),
                ("| compatibility path | unknown: no caller", "| compatibility path | probably dead: no caller", "Special cases: start the Reach cell"),
                ("**Kind:** unjustified special case ·", "**Kind:** dead code ·", "start **Kind:** with one of"),
                ("**How sure:** observed, removal probe", "**How sure:** fairly sure, removal probe", "start **How sure:** with one of"),
                ("**Decision:** open. Recommended: delete it.", "**Decision:** pending. Recommended: delete it.", "start **Decision:** with one of"),
                ("**Proposed fix:** Delete it once you confirm", "**Fix later:** Delete it once you confirm", "needs **Proposed fix:**"),
                ("**What is wrong:** [rounding.py:8]", "**The issue:** [rounding.py:8]", "add **What is wrong:**"),
                ("*Verified by:* tested, `test_guest_pays_full_price`", "*Verified by:* probably, `test_guest_pays_full_price`", "start *Verified by:* with one of"),
                ("- **Rename** `shop/pricing/discounts.py`", "- **Rework** `shop/pricing/discounts.py`", "Module changes: start each item with one of"),
                ("- **YAGNI:** today", "- **Lean:** today", "Design principles: start each item with one of"),
                ("- **Liskov substitution:** not applicable", "- **Open–closed:** also not applicable", "under ### Design principles today's result and the proposed one for: Liskov substitution")):
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
            page.check_rework_map("| Special case | Kind | Reach | Why it exists | Points to |\n| --- | --- | --- | --- | --- |\n"
                                  "| `a.py:3` | default | reached | TBD | nothing found |\n")

    def test_the_format_guide_worked_problem_passes_the_checks(self):
        guide = (ROOT / "skills/untangle/references/map-format.md").read_text()
        example = guide[guide.index("````markdown\n") + len("````markdown\n"):guide.index("\n````\n")].replace("<sha>", "d" * 40)
        start, end = self.source.index("### 2. "), self.source.index("### 3. ")
        self.note.write_text(self.source[:start] + example + "\n\n" + self.source[end:])
        rendered = run(self.note, "--sync-labels")
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        checked = run(self.note, "--check", "--sync-labels")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        html = self.note.with_suffix(".html").read_text()
        self.assertEqual(html.count('class="history-view"'), 2, "the example's change history draws")

    def test_template_declares_the_kind_and_the_checked_columns(self):
        template = (ROOT / "skills/untangle/references/map-template.md").read_text()
        self.assertTrue(template.startswith("---\nkind: rework-map\n---\n"))
        card = (ROOT / "skills/fit-change/references/card-template.md").read_text()
        for columns in page.MAP_TABLES:
            self.assertIn("| " + " | ".join(columns) + " |", template)
        for text in (template, card):
            for heading in ("## In short", "## Problems", "## The plan"):
                self.assertIn(heading, text)
            for label in page.PROBLEM_FIELDS:
                self.assertIn(f"**{label}:**", text)
        self.assertIn("rework-map", page.NOTE_KINDS)


if __name__ == "__main__":
    unittest.main()
