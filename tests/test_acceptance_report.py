"""The acceptance report contract in render_page.py: python3 tests/test_acceptance_report.py."""
import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/acceptance"
spec = importlib.util.spec_from_file_location("acceptance_page", ROOT / "skills/render_page.py")
page = importlib.util.module_from_spec(spec)
spec.loader.exec_module(page)

NOTE = FIXTURES / "report.md"
REPORT = NOTE.read_text()


def line(source, prefix):
    """The whole line (with its newline) that starts with prefix."""
    return next(text for text in source.splitlines(keepends=True) if text.startswith(prefix))


class AcceptanceReportTests(unittest.TestCase):
    def reject(self, source, message):
        with self.assertRaisesRegex(ValueError, message):
            page.check_acceptance(source, NOTE)

    def test_fixture_passes_acceptance_and_page_check(self):
        page.check_acceptance(REPORT, NOTE)
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stderr(io.StringIO()):  # no repository: the fixture's SHAs resolve nowhere, and links are only listed
            html = page.render(REPORT, NOTE.name, repo=Path(directory))
            page.check(REPORT, html, NOTE, repo=Path(directory))
        self.assertEqual(len(page.parse(html).select("table.requirements-table")), 2)

    def test_head_is_required_and_full(self):
        head = line(REPORT, "head:")
        self.reject(REPORT.replace(head, ""), "requires head")
        self.reject(REPORT.replace(head, "head: bbbbbbb\n"), "full commit SHA")

    def test_each_required_section_is_required(self):
        for name in page.ACCEPTANCE_SECTIONS:
            with self.subTest(section=name):
                self.reject(REPORT.replace(f"## {name}\n", f"## Renamed {name}\n"), f"exactly one '## {name}'")

    def test_requirements_need_a_source_heading(self):
        source = REPORT.replace("### Issue 41: CSV export\n", "").replace("### Issue 42: Export permissions\n", "")
        self.reject(source, "### <source title>")

    def test_requirements_text_before_the_first_source_is_prose(self):
        table = "| Requirement and intent | Status | Behavior and evidence | Next action |\n| --- | --- | --- | --- |\n| Export ([issue 41](intent/issue-41.md)) | Met | [run](runs/record.md) | None |\n\n"
        self.reject(REPORT.replace("### Issue 41: CSV export\n", table + "### Issue 41: CSV export\n"), "prose only")

    def test_gaps_pass_the_evidence_floor(self):
        gap = "### Gaps\n\n- Issues can change after collection, and nobody re-read them before delivery.\n"
        source = REPORT.replace("### Gaps\n", gap)
        page.check_claims(source)
        with self.assertRaisesRegex(ValueError, "not inspected"):
            page.check_claims(source.replace("### Gaps\n", "### Coverage gaps\n"))

    def test_requirement_list_line_is_required(self):
        self.reject(REPORT.replace(line(REPORT, "**Requirement list:**"), ""), "Requirement list")
        self.reject(REPORT.replace(line(REPORT, "**Requirement list:**"), "**Requirement list:**\n"), "Requirement list")

    def test_unsupported_status_fails(self):
        self.reject(REPORT.replace("| Met |", "| Done |"), "unsupported status 'Done'")

    def test_evidence_cell_needs_link_or_explicit_gap(self):
        self.reject(REPORT.replace("not verified: the permission path was not run", "looks fine"),
                    "links pinned source, a run record, or a bug card")

    def test_met_row_needs_an_evidence_link(self):
        met = line(REPORT, "| Export the table as CSV")
        self.reject(REPORT.replace(met, "| Export the table as CSV ([issue 41](intent/issue-41.md)) | Met | already held at base: unknown | None |\n"),
                    "Met row links its evidence")

    def test_intent_cell_needs_source_unless_needs_clarification(self):
        self.reject(REPORT.replace("Include a header row ([issue 41](intent/issue-41.md))", "Include a header row"), "link the intent source")

    def test_questions_need_spec_owner_and_author(self):
        self.reject(REPORT.replace("**Author:**\n", ""), r"Spec owner:\*\* and \*\*Author:")
        self.reject(REPORT.replace(line(REPORT, "- Was the missing role check"), ""), "give each list a nonempty entry")

    def test_nobody_asked_for_this_items_carry_the_label(self):
        self.reject(REPORT.replace(" — *nobody asked for this*", ""), "label each item")
        wrapped = REPORT.replace(" — *nobody asked for this*", " — *nobody asked\n  for this*")
        self.assertNotIn("label each item", " ".join(page.acceptance_problems(wrapped, NOTE)))
        start, end = REPORT.index("## Nobody asked for this"), REPORT.index("## Possible bugs")
        scope = "## Nobody asked for this\n\nNone found: inspected these files.\n\n- `src/export.py`\n- `src/permissions.py`\n\n"
        self.assertNotIn("label each item", " ".join(page.acceptance_problems(REPORT[:start] + scope + REPORT[end:], NOTE)))

    def test_nobody_asked_for_this_is_explicit(self):
        start = REPORT.index("## Nobody asked for this")
        end = REPORT.index("## Possible bugs")
        self.reject(REPORT[:start] + "## Nobody asked for this\n\n" + REPORT[end:], "None found:")
        page.check_acceptance(REPORT[:start] + "## Nobody asked for this\n\nNone found: feature scope in Feature scope inspected.\n\n"
                              + REPORT[end:], NOTE)

    def test_feature_scope_record_required(self):
        self.reject(REPORT.replace("### Feature scope", "### Elsewhere"), "Feature scope")

    def test_duplicate_source_titles_fail(self):
        self.reject(REPORT.replace("### Issue 42: Export permissions", "### Issue 41: CSV export"), "distinct name")

    def test_no_base_report(self):
        source = REPORT.replace(line(REPORT, "base:"), "")
        source = source.replace("*pre-existing, made worse*", "*no base pinned*").replace("*from an unrelated commit*", "*no base pinned*")
        source = source.replace("*new in this change*", "*no base pinned*")
        source = source.replace("| refused |", "| no base pinned |").replace("| predicted: no file |", "| no base pinned |")
        source = source.replace(line(source, "**Introduced by:**"), "")
        page.check_acceptance(source, NOTE)
        self.reject(source.replace("repository:", line(REPORT, "base:") + "repository:"), "a base is pinned")
        self.reject(source.replace("*we ran it* · *no base pinned*", "*we ran it* · *new in this change*"), "no base is pinned")

    def test_template_sections_match_the_contract(self):
        template = (ROOT / "skills/check-acceptance/references/report-template.md").read_text()
        front, body = page.split_front_matter(template)
        self.assertEqual(list(front), ["head", "base", "repository"])
        self.assertEqual(tuple(name for name, _ in page.markdown_sections(body, 2)),
                         page.ACCEPTANCE_SECTIONS + ("Status and label key",))

    def test_cli_acceptance_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "acceptance"
            shutil.copytree(FIXTURES, copy)
            command = [sys.executable, str(ROOT / "skills/render_page.py"), str(copy / "report.md"), "--check", "--acceptance"]
            checked = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertIn("Markdown checks passed", checked.stdout)
            both = subprocess.run(command + ["--review"], capture_output=True, text=True)
            self.assertEqual(both.returncode, 2)
            self.assertIn("--acceptance", both.stderr)


if __name__ == "__main__":
    unittest.main()
