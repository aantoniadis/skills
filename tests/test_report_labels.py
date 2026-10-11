"""Portable, complete definitions for the report vocabularies actually in use."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('page', ROOT / 'skills/render_page.py')
page = importlib.util.module_from_spec(spec)
spec.loader.exec_module(page)

SOURCE = '''# Requirement report

## Requirements

| Requirement and intent | Status | Behavior and evidence | Next action |
| --- | --- | --- | --- |
| Inferred example intent | Met | Source inspected; limited to the example | None within this scope |
'''


class ReportLabelTests(unittest.TestCase):
    def test_catalog_covers_every_supported_value_without_conflating_partial(self):
        for group, values in [('requirements', page.FULFILLMENT),
                              ('verification-results', page.CHECK_RESULTS),
                              ('verification-origins', page.CHECK_ORIGINS),
                              ('decisions', page.DECISION_STATUSES),
                              ('questions', page.QUESTION_STATUSES),
                              ('review-actions', page.ACTION_PHRASES),
                              ('review-evidence', page.EVIDENCE_PHRASES),
                              ('intent-alignment', page.INTENT_PHRASES)]:
            self.assertEqual(tuple(page.LABELS[group]['options']), tuple(values))
        self.assertNotEqual(page.LABELS['requirements']['options']['Partial'],
                            page.LABELS['questions']['options']['Partial'])

    def test_key_includes_unused_values_but_only_relevant_groups(self):
        source = page.with_label_key(SOURCE)
        self.assertEqual(page.label_groups(source), ['requirements'])
        self.assertIn('| Unmet |', source)
        self.assertIn('| Not applicable |', source)
        self.assertNotIn('| Passed |', source)
        self.assertEqual(page.with_label_key(source), source)
        page.check_label_key(source, require=True)

    def test_refresh_preserves_later_sections_and_ignores_fenced_headings(self):
        source = page.with_label_key(SOURCE) + '\n## Later evidence\n\nUnknown boundary.\n'
        refreshed = page.with_label_key(source)
        self.assertIn('## Later evidence\n\nUnknown boundary.', refreshed)
        fenced = SOURCE + '\n```text\n## Status and label key\n```\n'
        self.assertIn('```text\n## Status and label key\n```', page.with_label_key(fenced))
        with self.assertRaisesRegex(ValueError, 'one Status'):
            page.with_label_key(source + '\n## Status and label key\n')

    def test_html_has_nearby_help_and_complete_static_definitions(self):
        html = page.render(SOURCE, 'report.md')
        page.check_label_key(SOURCE, html)
        soup = page.parse(html)
        self.assertEqual(soup.select_one('.label-help a')['href'], '#key-requirement-fulfillment')
        self.assertEqual([node.get_text() for node in soup.select('.label-definitions dt')], list(page.FULFILLMENT))
        self.assertIsNotNone(soup.select_one('#status-and-label-key details summary'))
        soup.select_one('.label-definitions dd').string = 'Everything is safe.'
        with self.assertRaisesRegex(ValueError, 'definitions differ'):
            page.check_label_key(SOURCE, str(soup))

    def test_stale_or_missing_key_is_rejected_and_sync_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            note = Path(directory) / 'report.md'
            note.write_text(SOURCE)
            command = [sys.executable, str(ROOT / 'skills/render_page.py'), str(note), '--check']
            missing = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn('--sync-labels', missing.stderr)
            self.assertEqual(note.read_text(), SOURCE)
            synced = subprocess.run(command + ['--sync-labels'], capture_output=True, text=True)
            self.assertEqual(synced.returncode, 0, synced.stderr)
            self.assertFalse(note.with_suffix('.html').exists())
            page.check_label_key(note.read_text(), require=True)
            note.write_text(note.read_text().replace('Evidence supports the whole stated requirement', 'Everything supports any requirement'))
            stale = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn('stale', stale.stderr)

    def test_custom_html_can_keep_the_key_as_a_table(self):
        html = '<main><section id="status-and-label-key">' + page.MARKDOWN.render(page.label_key_markdown(SOURCE)) + '</section></main>'
        page.check_label_key(SOURCE, html)

    def test_key_labels_reuse_status_badges_and_review_chips(self):
        source = SOURCE + '\n## What to look at\n\n1. **Example** — *you decide* · *read at the line*\n\nIntent: partly matches the stated intent.\n'
        soup = page.parse(page.render(source, 'report.md'))
        body_badge = soup.select_one('.requirements-table .status')
        key_badge = soup.select_one('#key-requirement-fulfillment + dl .status')
        self.assertEqual(key_badge['class'], body_badge['class'])
        for group in ('requirements', 'review-actions', 'review-evidence', 'intent-alignment'):
            heading = 'key-' + page.slug(page.LABELS[group]['title'])
            for term in soup.select(f'#{heading} + dl dt'):
                label = term.get_text()
                classes = (['status', 'status-' + page.slug(label)] if group == 'requirements'
                           else ['chip', 'chip-' + page.code_of(label).replace(' ', '-')])
                self.assertEqual(term.span['class'], classes)
        page.check_label_key(source, str(soup))

    def test_pr_labels_and_diagrams_are_detected_outside_the_key(self):
        source = '# Report\n\n## What to look at\n\nIntent: intent unclear. Resolution: Open.\n\n## Reading plan\n\n```mermaid\nflowchart LR\n```\n'
        groups = page.label_groups(source)
        self.assertEqual(groups, ['review-actions', 'review-evidence', 'intent-alignment',
                                  'finding-resolution', 'reading-depth', 'diagram-evidence'])
        self.assertEqual(page.label_groups(page.with_label_key(source)), groups)


if __name__ == '__main__':
    unittest.main()
