"""Render the explanation and planning examples and check their evidence-bearing fields."""
import importlib.util
from pathlib import Path
import unittest
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("page", ROOT / "skills/render_page.py")
page = importlib.util.module_from_spec(spec)
spec.loader.exec_module(page)


class LearningPlanPageTests(unittest.TestCase):
    def test_verification_origins_apply_to_explanations_and_plans_in_both_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / 'note.md'
            (note.parent / 'run.md').write_text('Synthetic run record.\n')
            source = ('# Plan\n\n**Outcome:** Proposed counter change. **Readiness:** Open.\n\n## Verification\n\n'
                      '| Check or scenario | Result | Evidence origin | Revision and configuration | Scope and limits |\n'
                      '| --- | --- | --- | --- | --- |\n'
                      '| [Counter](run.md) | RESULT | ORIGIN | fixture | Explicit fixture limits |\n')
            cases = [('Not run', 'Source inspected', True), ('Blocked', 'Proposed', True),
                     ('Passed', 'Recorded run', True), ('Failed', 'Executed here', True),
                     ('Passed', 'Source inspected', False), ('Failed', 'Proposed', False),
                     ('Not run', 'Executed here', False), ('Passed', 'Invented', False), ('Maybe', 'Recorded run', False)]
            for result, origin, valid in cases:
                text = source.replace('RESULT', result).replace('ORIGIN', origin)
                note.write_text(text)
                with self.subTest(result=result, origin=origin):
                    command = [sys.executable, str(ROOT / 'skills/render_page.py'), str(note),
                               '--check', '--markdown-only', '--sync-labels']
                    checked = subprocess.run(command, capture_output=True, text=True)
                    self.assertEqual(checked.returncode == 0, valid, checked.stderr)
                    html = page.render(text, note.name)
                    if valid:
                        page.check(text, html, note)
                    else:
                        with self.assertRaisesRegex(ValueError, 'Verification'):
                            page.check(text, html, note)
            for text in (source.replace('RESULT', 'Passed').replace('ORIGIN', 'Recorded run').replace('[Counter](run.md)', 'Counter'),
                         source.replace('RESULT', 'Not run').replace('ORIGIN', 'Source inspected').replace('| fixture |', '|  |')):
                with self.assertRaisesRegex(ValueError, 'Verification'):
                    page.check(text, page.render(text, note.name), note)

    def test_proposed_and_mixed_diagrams_keep_distinct_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / 'plan.md'
            (note.parent / 'source.py').write_text('enqueue()\n')
            source = ('# Durable delivery\n\n**Outcome:** Proposed durable delivery.\n\n## Flow\n\n'
                      'Proposed: a queue feeds a worker.\n\n```mermaid\nflowchart LR\n Q[Queue] --> W[Worker]\n```\n\n'
                      'Source map:\n- Q — proposed: [queue decision](#candidate).\n'
                      '- W — proposed: [worker decision](#candidate).\n'
                      '- Q to W — proposed: [delivery decision](#candidate).\n\n'
                      '## Candidate\n\nProposed: add a durable queue and worker.\n')
            mixed = source.replace('Q — proposed: [queue decision](#candidate)', 'Q — [existing queue](source.py#L1)')
            for text in (source, mixed):
                note.write_text(text)
                checked = subprocess.run([sys.executable, str(ROOT / 'skills/render_page.py'), str(note), '--check',
                                          '--markdown-only', '--sync-labels'], capture_output=True, text=True)
                self.assertEqual(checked.returncode, 0, checked.stderr)
            for text, error in ((source.replace('W — proposed:', 'W —'), 'pinned line'),
                                (source.replace('(#candidate)', '(#missing)'), 'Missing fragment'),
                                (mixed.replace('source.py#L1', 'missing.py#L1'), 'missing local file'),
                                (source.replace('[worker decision](#candidate)', 'worker decision'), 'linked proposal')):
                with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                    page.check_diagrams(text, note)

    def test_generated_definitions_cover_blocked_preparation_and_reading_by_consequence(self):
        source = ('# Review\n\n## Reading plan\n\nRead the changed configuration.\n\n## Verification\n\n'
                  '| Check or scenario | Result | Evidence origin | Revision and configuration | Scope and limits |\n'
                  '| --- | --- | --- | --- | --- |\n'
                  '| Dependency probe | Blocked | Proposed | fixture | Installation unavailable |\n')
        key = page.label_key_markdown(source)
        self.assertIn('Not run or Blocked', key)
        self.assertNotIn('Read tests, documentation, configuration', key)
        self.assertNotIn('identifies generated files, lockfiles', key)

    def test_cli_rejects_unfilled_prose_but_preserves_literal_code(self):
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / 'note.md'
            command = [sys.executable, str(ROOT / 'skills/render_page.py'), str(note), '--sync-labels']
            for options in (['--check'], []):
                with self.subTest(options=options):
                    source = '# Explanation\n\n**Answer:** {{central_answer}}\n'
                    note.write_text(source)
                    result = subprocess.run(command + options, capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('unfilled template prompts', result.stderr)
                    self.assertEqual(note.read_text(), source)
                    self.assertFalse(note.with_suffix('.html').exists())
            note.write_text('# Template syntax\n\n**Answer:** Use `{{value}}` as the placeholder.\n\n```text\n{{example}}\n```\n')
            for options in (['--check'], [], ['--check']):
                result = subprocess.run(command + options, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_markdown_cli_checks_local_links_and_fence_citations(self):
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / 'note.md'
            command = [sys.executable, str(ROOT / 'skills/render_page.py'), str(note), '--check', '--sync-labels']
            for content, error in (
                ('[source](missing.py#L1)', 'Missing local file'),
                ('```python url="missing.py#L1"\nvalue = 2\n```', 'Missing local file'),
                ('[details](#missing)', 'Missing fragment'),
            ):
                with self.subTest(content=content):
                    note.write_text('# Explanation\n\n' + content + '\n')
                    result = subprocess.run(command, capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(error, result.stderr)
            (Path(directory) / 'saved source.py').write_text('value = 2\n')
            note.write_text('# Explanation\n\n[details](#details)\n\n## Details\n\nSource: [snapshot](saved%20source.py#L1).\n\n```python url="saved%20source.py#L1"\nvalue = 2\n```\n')
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([part for part in command if part != '--check'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            # The snapshot beside the note opens in the code peek, and the fence that cites it numbers its rows from line 1.
            soup = page.parse(note.with_suffix('.html').read_text())
            payload = page.source_peek.decode(soup.find(id='peek-data').string)
            self.assertEqual(list(payload['files']), ['local:saved source.py'])
            self.assertEqual(payload['links']['saved%20source.py#L1']['start'], 1)
            self.assertEqual({a['href'] for a in soup.main.select('a[data-peek]')}, {'saved%20source.py#L1'})
            self.assertEqual(soup.select_one('figure.code-card')['data-first'], '1')
            result = subprocess.run(command, capture_output=True, text=True)  # the embedded copy is checked against the file
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_cross_file_fragments_use_markdown_headings_and_html_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = root / 'note.md'
            note.write_text('# Notes\n')
            (root / 'source.md').write_text('---\ntitle: Source\n---\n# Release **all** reservations\n')
            (root / 'source.html').write_text('<h1 id="release">Release reservations</h1>')
            (root / 'source.py').write_text('release()\n')
            for href in ('source.md#release-all-reservations', 'source.md#L1',
                         'source.html#release', 'source.py#L1', '#notes',
                         'https://example.invalid/not-fetched#missing'):
                with self.subTest(href=href):
                    page.check_links([href], note, {'notes'})
            for href in ('source.md#missing', 'source.html#missing', '#missing'):
                with self.subTest(href=href):
                    with self.assertRaisesRegex(ValueError, 'Missing fragment'):
                        page.check_links([href], note, {'notes'})
            # HTML companions may cite Markdown source lines too.
            page.check_links(['source.md#L1'], note.with_suffix('.html'), set())

    def test_markdown_only_checks_current_note_without_touching_stale_html(self):
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / 'note.md'
            note.write_text('# Explanation\n\n**Answer:** Illustrative value.\n\n```python\nvalue = 1\n```\n')
            command = [sys.executable, str(ROOT / 'skills/render_page.py'), str(note), '--sync-labels']
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            html = note.with_suffix('.html').read_bytes()
            note.write_text(note.read_text().replace('value = 1', 'value = 2'))
            result = subprocess.run(command + ['--check'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Displayed code differs', result.stderr)
            result = subprocess.run(command + ['--check', '--markdown-only'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('HTML was not checked', result.stdout)
            self.assertEqual(note.with_suffix('.html').read_bytes(), html)
            result = subprocess.run(command + ['--markdown-only'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('requires --check', result.stderr)
            self.assertEqual(note.with_suffix('.html').read_bytes(), html)

    def test_question_coverage_requires_status_answer_link_and_next_check(self):
        source = """# Explanation

## Questions answered

| Question | Status | Answer and evidence | Follow-up |
| --- | --- | --- | --- |
| Can it retry? | Partial | Unknown recovery; [gap](#recovery) | Inspect the failure handler |

## Recovery

Unknown: recovery is not inspected.
"""
        page.check_learning_plan(source)
        for old, new in [('Partial', 'Probably'), ('Unknown recovery; [gap](#recovery)', ''),
                         ('#recovery)', '#absent)'), ('Inspect the failure handler', '')]:
            with self.subTest(old=old):
                with self.assertRaises(ValueError):
                    page.check_learning_plan(source.replace(old, new))
        page.check_learning_plan('# Narrow explanation\n\n**Answer:** Unknown recovery.\n')

    def test_agreed_decision_requires_acceptance_authority_and_real_slice(self):
        source = (ROOT / 'tests/fixtures/reading-pages/plan.md').read_text()
        page.check_learning_plan(source)
        for old, new in [('**Acceptance:**', '**Expected:**'), ('**Authority:**', '**Who:**'),
                         ('**Delivery:**', '**Implementation:**'),
                         ('](#explore-the-sequential-contract)', '](#open-questions)')]:
            with self.subTest(old=old):
                with self.assertRaises(ValueError):
                    page.check_learning_plan(source.replace(old, new))

    def test_blockers_require_resolution_and_affected_slice(self):
        source = """# Plan

## Open questions

| Blocker | What would settle it | Affected work |
| --- | --- | --- |
| Unknown recovery | Inspect publication failures | [Production](#production) |

## Delivery slices

### Production

Unknown: blocked by recovery.
"""
        page.check_learning_plan(source)
        for old, new in [('Inspect publication failures', ''), ('#production)', '#open-questions)'),
                         ('[Production](#production)', 'Production')]:
            with self.subTest(old=old):
                with self.assertRaises(ValueError):
                    page.check_learning_plan(source.replace(old, new))

    def test_markdown_only_cli_checks_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / 'note.md'
            note.write_text('# Note\n\n## Questions answered\n\n| Question | Status | Answer and evidence | Follow-up |\n| --- | --- | --- | --- |\n| Retry? | Partial | Unknown | |\n')
            result = subprocess.run([sys.executable, str(ROOT / 'skills/render_page.py'), str(note), '--check'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Questions answered', result.stderr)

    def render_sample(self, name):
        note = ROOT / "tests/fixtures/reading-pages" / f"{name}.md"
        source = note.read_text()
        with patch.object(page, "mermaid_svg", return_value=None):
            html = page.render(source, note.name)
        page.check(source, html, note)
        return note, source, page.parse(html)

    def test_explanation_exposes_answer_steps_and_condition_outcome(self):
        _, _, soup = self.render_sample("understanding")
        self.assertEqual(soup.select_one(".brand").get_text(), "Code walkthrough")
        self.assertTrue(soup.select_one(".page-summary").get_text().startswith("Answer:"))
        self.assertIsNone(soup.select_one("#walkthrough > details"))
        self.assertIsNone(soup.select_one("#limits-and-next-questions > details"))
        self.assertIsNotNone(soup.select_one("#evidence-and-record > details"))
        self.assertEqual(len(soup.select("#walkthrough .behavior-fact")), 6)
        self.assertEqual(len(soup.select("article.scenario")), 3)
        self.assertEqual(soup.select_one(".scenario-title").name, "h3")
        self.assertEqual(soup.select_one(".scenario-label").name, "h4")
        self.assertEqual([x.get_text() for x in soup.select('.questions-table .status')], ['Answered', 'Partial', 'Unresolved'])
        self.assertEqual(tuple(x["data-column"] for x in soup.select_one("article.scenario").select("[data-column]")), page.EXPLANATION_COLUMNS)

    def test_plan_keeps_decision_status_separate_from_execution(self):
        _, _, soup = self.render_sample("plan")
        self.assertEqual(soup.select_one(".brand").get_text(), "Change plan")
        self.assertIn("blocked for production handoff", soup.select_one(".readiness").get_text())
        self.assertIsNone(soup.select_one("#decisions > details"))
        self.assertEqual([x.get_text() for x in soup.select(".decisions-table .status")], ["Agreed", "Agreed", "Open", "Proposed"])
        self.assertEqual([x.get_text() for x in soup.select(".verification-table .status")], ["Not run"] * 3)
        self.assertEqual(tuple(x["data-column"] for x in soup.select_one("article.scenario").select("[data-column]")), page.PLAN_COLUMNS)
        self.assertTrue(all(x.get("data-label") for x in soup.select(".decisions-table td")))

    def test_changed_status_outcome_or_owning_section_is_rejected(self):
        for name, selector in (("understanding", '[data-column="Outcome"]'), ("plan", '.decisions-table .status'), ("plan", '[data-column="Planned"]'),
                               ('understanding', '.questions-table .status'), ('plan', '.blockers-table td')):
            with self.subTest(name=name, selector=selector):
                note, source, soup = self.render_sample(name)
                soup.select_one(selector).string = "Incorrect replacement"
                with self.assertRaisesRegex(ValueError, "table content differs"):
                    page.check(source, str(soup), note)
        note, source, soup = self.render_sample("plan")
        soup.select_one("#open-questions").append(soup.select_one("article.scenario").extract())
        with self.assertRaisesRegex(ValueError, "table content differs"):
            page.check(source, str(soup), note)

    def test_long_comparison_retains_markup_and_uncertainty(self):
        note = ROOT / "tests/fixtures/reading-pages/understanding.md"
        source = note.read_text().replace("Recovery and the caller's eventual result are unknown", "Unknown: " + "The consumer boundary needs more context. " * 12 + "`retry` remains [unverified](sample-record.md#L15)")
        with patch.object(page, "mermaid_svg", return_value=None):
            html = page.render(source, note.name)
        page.check(source, html, note)
        field = page.parse(html).select('[data-column="Outcome"]')[-1]
        self.assertEqual(field.get_text().count("The consumer boundary needs more context."), 12)
        self.assertEqual(field.code.get_text(), "retry")
        self.assertEqual(field.a["href"], "sample-record.md#L15")


if __name__ == "__main__":
    unittest.main()
