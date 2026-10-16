"""The diagnosis fixture passes the shared checker in both modes, and the checker rejects the two
mistakes a fix record is most likely to make: an unrecorded run and a fact without evidence."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/diagnosis"
SCRIPT = ROOT / "skills/render_page.py"
_spec = importlib.util.spec_from_file_location("page", SCRIPT)
page = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(page)


def run(note, *flags):
    return subprocess.run([sys.executable, str(SCRIPT), str(note), *flags], capture_output=True, text=True)


class DiagnosisNoteTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "diagnosis"
        shutil.copytree(FIXTURE, self.root)
        self.note = self.root / "diagnosis.md"
        self.source = self.note.read_text()

    def tearDown(self):
        self.directory.cleanup()

    def test_fixture_renders_and_checks_in_both_modes(self):
        text_only = run(self.note, "--check", "--markdown-only", "--sync-labels")
        self.assertEqual(text_only.returncode, 0, text_only.stderr)
        rendered = run(self.note, "--sync-labels")
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertTrue(self.note.with_suffix(".html").exists())
        page = self.note.with_suffix(".html").read_text()
        for fragment in ("code-card", "verification-table", 'id="cause"', 'id="fix-and-regression-test"'):
            self.assertIn(fragment, page, fragment)
        checked = run(self.note, "--check", "--sync-labels")
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_committed_fixture_carries_a_current_label_key(self):
        synced = run(self.note, "--check", "--markdown-only", "--sync-labels")
        self.assertEqual(synced.returncode, 0, synced.stderr)
        self.assertEqual(self.note.read_text(), self.source, "run --sync-labels on the fixture and commit the key")

    def test_executed_row_without_a_run_record_is_rejected(self):
        broken = self.source.replace("| [Reproduction loop before the fix](runs/bugs/1/run.md) |",
                                     "| Reproduction loop before the fix |", 1)
        self.assertNotEqual(broken, self.source)
        self.note.write_text(broken)
        result = run(self.note, "--check", "--markdown-only", "--sync-labels")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Verification", result.stderr)

    def test_fact_without_evidence_is_rejected(self):
        broken = self.source.replace(
            "**Trigger:** one `StockTimeout` after the stock service has recorded the reservation, so the retry "
            "reserves again; observed with the stub in [repro.py](runs/bugs/1/repro.py#L9).",
            "**Trigger:** one stock timeout after the stock service wrote the reservation row, so the retry "
            "reserves the same order a second time.", 1)
        self.assertNotEqual(broken, self.source)
        self.note.write_text(broken)
        result = run(self.note, "--check", "--markdown-only", "--sync-labels")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("claim block", result.stderr)

    def test_template_is_rejected_until_filled_and_matches_the_fixture_headings(self):
        template = ROOT / "skills/fix-bug/references/diagnosis-template.md"
        copy = self.root / "template.md"
        copy.write_text(template.read_text())
        result = run(copy, "--check", "--markdown-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unfilled template prompts", result.stderr)
        headings = lambda text: [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
        expected = [h for h in headings(self.source) if h != "Status and label key"]
        self.assertEqual(headings(template.read_text()), expected + ["Status and label key"])

    def test_page_guidance_is_short_and_points_at_the_evidence_rule(self):
        guidance = (ROOT / "skills/fix-bug/references/diagnosis-page.md").read_text()
        self.assertLess(guidance.count("\n"), 100)
        self.assertIn("EVIDENCE.md", guidance)
        self.assertIn("diagnosis-template.md", guidance)

    def test_cause_card_and_checked_chips_render_with_their_key(self):
        rendered = run(self.note, "--sync-labels")
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        soup = page.parse(self.note.with_suffix(".html").read_text())
        card = soup.select_one("#cause article.bug-card")
        self.assertIsNotNone(card, "the Cause section renders its ### card as a bug card")
        chips = [c.get_text(strip=True) for c in card.select("p.bug-chips .chip")]
        self.assertEqual(chips, ["we ran it", "regression"])
        checked = next(p for p in soup.main.find_all("p") if p.get_text().startswith("Checked:"))
        self.assertGreaterEqual(len(checked.select(".chip")), 6)
        self.assertIn("chip-supported", " ".join(" ".join(c["class"]) for c in checked.select(".chip")))
        key = soup.select_one("#status-and-label-key").get_text(" ", strip=True)
        for title in ("Bug evidence", "Cause origin", "Diagnosis checks"):
            self.assertIn(title, key)
        self.assertNotIn("Review evidence labels", key)

    def test_pr_cards_keep_rejecting_diagnosis_origin_chips(self):
        report = (ROOT / "tests/fixtures/bug-cards/report.md").read_text()
        broken = report.replace("*new in this change*", "*regression*", 1)
        self.assertNotEqual(broken, report)
        with self.assertRaisesRegex(ValueError, "chip"):
            page.check_bug_cards(broken, ROOT / "tests/fixtures/bug-cards/report.md")

    def test_incomplete_diagnoses_render_truthful_status_chips(self):
        for reproduced, fix in (("reproduced", "no fix proposed"),
                                ("not reproduced", "fix proposed"),
                                ("not reproduced", "fixed")):
            with self.subTest(reproduced=reproduced, fix=fix):
                labels = [reproduced, fix, "test not verified", "origin skipped",
                          "reach skipped", "consequence skipped"]
                self.note.write_text("# Incomplete diagnosis\n\n**Checked:** "
                                     + " · ".join(f"*{label}*" for label in labels)
                                     + ". Inferred example: regression evidence remains incomplete.\n")
                rendered = run(self.note, "--sync-labels")
                self.assertEqual(rendered.returncode, 0, rendered.stderr)
                soup = page.parse(self.note.with_suffix(".html").read_text())
                chips = soup.select(".checked-line .chip")
                self.assertEqual([c.get_text() for c in chips], labels)
                self.assertIn("chip-unresolved", chips[2]["class"])
                key = soup.select_one("#status-and-label-key").get_text(" ", strip=True)
                self.assertIn("test not verified", key)
                self.assertIn("no fix proposed", key)
                checked = run(self.note, "--check", "--sync-labels")
                self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_diagnosis_labels_stay_out_of_other_notes(self):
        explain = ("# How retries work\n\n**Answer:** The retry is *fixed* at three attempts, source at "
                   "[a.py:3](a.py#L3).\n\n## Walkthrough\n\nThe timeout was *reproduced* once, observed in the run.\n")
        self.assertNotIn("diagnosis-checks", page.label_groups(explain))
        review = (ROOT / "tests/fixtures/report-layout/report.md").read_text().replace(
            "## What the change does", "## What the change does\n\nThe crash is *fixed* by the guard, observed in the run.\n", 1)
        self.assertNotIn("diagnosis-checks", page.label_groups(review))
        self.assertIn("diagnosis-checks", page.label_groups(self.source))


if __name__ == "__main__":
    unittest.main()
