"""Review contract and rendering checks: python3 tests/test_review_report.py."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import json

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reading_page", ROOT / "skills/render_page.py")
page = importlib.util.module_from_spec(spec)
spec.loader.exec_module(page)

REPORT = '''# Count distinct entries

**Bottom line:** the fixture contradicts the stated intent; ask whether deduplication is wanted.

**Reviewed:** head abc against base def; merge base def. **Coverage:** fixture source only; no tests run.

## What the change does

The proposed implementation counts distinct entries ([source.py:2](source.py#L2)).

## Requirements

| Requirement and intent | Status | Behavior and evidence | Next action |
| --- | --- | --- | --- |
| "Count every entry" ([intent.md:1](intent.md#L1)) | Unmet | [Duplicate entries](#duplicate-entries): source contradicts the requirement | Ask whether deduplication is wanted |

## What to look at

1. **Duplicates no longer count** — *you decide* · *read at the line*
   Source uses a set ([source.py:2](source.py#L2)).
   Look at: [Duplicate entries](#duplicate-entries).
   Settle: was deduplication intended?

## Possible bugs

The search for bugs has not run: this fixture checks the report shape only.

## Questions for the author

Does the author intend distinct counting? See [Duplicate entries](#duplicate-entries).

## Behavior changes

### Duplicate entries

**Purpose and tradeoff:** inferred distinct counting trades duplicate preservation for uniqueness ([source.py:2](source.py#L2)).

**Conditions:** repeated values reach the counter ([source.py:2](source.py#L2)).

| Scenario | Before | After | Consumer consequence | Evidence |
| --- | --- | --- | --- | --- |
| Two equal entries | Not inspected | Source predicts one | Caller gets fewer entries; expectation unknown | [source.py:2](source.py#L2) |

**Consumers:** caller expectation is unknown; inspect the real caller next.

**Preserved:** signature accepts one argument ([source.py:1](source.py#L1)).

**Open question:** does the author intend distinct counting?

## Verification

Tests inspected: none. Recorded runs: none. Executed: none.

| Check or scenario | Result | Evidence origin | Revision and configuration | Scope and limits |
| --- | --- | --- | --- | --- |
| [Duplicate entries](#duplicate-entries) | Not run | Source inspected | abc; source only | Prediction only; caller not inspected |
| [Bug probes](#possible-bugs) | Not run | Proposed | abc; no probe ran | No path was probed |

## Evidence and record

### Gaps

Caller expectations remain unknown.

### Changed files

[source.py](source.py): counter inspected; caller not inspected.

### Provenance

Synthetic test fixture, not an actual review or execution result.
'''


class ReviewReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.note = Path(self.tmp.name) / "report.md"
        self.note.write_text(REPORT)
        (self.note.parent / "source.py").write_text("def count(entries):\n    return len(set(entries))\n")
        (self.note.parent / "intent.md").write_text("Count every entry\n")

    def reject(self, source, message):
        with self.assertRaisesRegex(ValueError, message):
            page.check_review(source, self.note)

    def test_complete_source_only_review_passes(self):
        page.check_review(REPORT, self.note)
        page.check(REPORT, page.render(REPORT, self.note.name), self.note)

    def test_source_only_search_and_recorded_probe_results(self):
        source = REPORT.replace('The search for bugs has not run: this fixture checks the report shape only.',
                                'No bugs found: source inspected, e.g. the counter; callers remain uninspected.')
        page.check_review(source.replace('| Not run | Proposed |', '| Not run | Source inspected |'), self.note)
        for origin in ('Recorded run', 'Executed here'):
            for result in ('Passed', 'Mixed', 'Failed', 'Blocked'):
                checked = source.replace('| Not run | Proposed |', f'| {result} | {origin} |')
                self.reject(checked, 'run record')
                (self.note.parent / 'run.md').write_text('Synthetic run record; not a real execution.\n')
                checked = checked.replace('[Bug probes](#possible-bugs)', '[Bug probes](#possible-bugs) ([run](run.md))')
                page.check_review(checked, self.note)

    def test_stale_html_prose_and_metadata_fail(self):
        html = page.render(REPORT, self.note.name)
        changed = REPORT.replace('the fixture contradicts', 'it is false that the fixture contradicts')
        with self.assertRaisesRegex(ValueError, 'source fingerprint'):
            page.check(changed, html, self.note)
        soup = page.parse(html)
        marker = soup.find('meta', attrs={'name': 'source-fingerprint'})
        marker.extract()
        with self.assertRaisesRegex(ValueError, 'source fingerprint'):
            page.check(REPORT, str(soup), self.note)
        with self.assertRaisesRegex(ValueError, 'source fingerprint'):
            page.check('---\nhead: ' + 'a' * 40 + '\n---\n' + REPORT, html, self.note)

    def test_snapshot_syntax_and_required_record_sections(self):
        for meta in ('head: nonsense', 'base: main', 'repository: not-a-repository'):
            self.reject('---\n' + meta + '\n---\n' + REPORT, 'Front matter')
            self.note.write_text('---\n' + meta + '\n---\n' + REPORT)
            checked = subprocess.run([sys.executable, str(ROOT / 'skills/render_page.py'), str(self.note),
                                      '--check', '--review', '--sync-labels', '--markdown-only'], capture_output=True, text=True)
            self.assertNotEqual(checked.returncode, 0)
            self.assertIn('Front matter', checked.stderr)
        page.check_review('---\nhead: ' + 'a' * 40 + '\nbase: ' + 'b' * 40 + '\nrepository: acme/widgets\n---\n' + REPORT, self.note)
        for heading in ('Questions for the author', 'Gaps', 'Changed files', 'Provenance'):
            self.reject(REPORT.replace(heading, 'Other'), heading)
        with_plan = REPORT.replace('### Changed files', '### Inventory').replace('## Behavior changes', '## Reading plan\n\n[source.py](source.py): inspect the counter.\n\n## Behavior changes')
        page.check_review(with_plan, self.note)

    def test_title_anchor_works_in_markdown_and_html(self):
        source = REPORT.replace('## Evidence and record', '[Back to title](#count-distinct-entries)\n\n## Evidence and record')
        page.check_review(source, self.note)
        page.check(source, page.render(source, self.note.name), self.note)

    def test_each_required_section_and_scope_cannot_disappear(self):
        self.reject(REPORT.replace('# Count distinct entries', 'Count distinct entries'), 'opening H1')
        for heading in ("What the change does", "Requirements", "Behavior changes", "Verification", "Evidence and record", "What to look at"):
            with self.subTest(heading=heading):
                self.reject(REPORT.replace("## " + heading, "## Other"), "requires exactly one")
        self.reject(REPORT.replace("**Coverage:**", "Coverage:"), "opening requires")

    def test_small_shape_leaves_out_requirements_only_without_intent(self):
        start, end = REPORT.index("## Requirements"), REPORT.index("\n## ", REPORT.index("## Requirements") + 1) + 1
        small = REPORT[:start] + REPORT[end:]
        self.reject(small, "No intent source")
        page.check_review(small.replace("### Provenance\n", "### Provenance\n\nNo intent source: no PR description, ticket, or spec.\n"), self.note)

    def test_requirement_status_and_trace_link_are_checked(self):
        for status in page.FULFILLMENT:
            page.check_review(REPORT.replace("| Unmet |", f"| {status} |"), self.note)
        self.reject(REPORT.replace("| Unmet |", "| Looks fine |"), "unsupported status")
        self.reject(REPORT.replace("[Duplicate entries](#duplicate-entries): source", "Duplicate entries: source"), "link Behavior")
        self.reject(REPORT.replace('([intent.md:1](intent.md#L1))', '(no accessible intent)'), "link the intent")
        page.check_review(REPORT.replace('([intent.md:1](intent.md#L1))', '(inferred; intent unknown)').replace('| Unmet |', '| Needs clarification |'), self.note)

    def test_behavior_fields_scenarios_and_unknowns(self):
        self.reject(REPORT.replace("**Consumers:**", "Consumers:"), "Consumers")
        self.reject(REPORT.replace("**Open question:** does the author intend distinct counting?", "**Open question:**"), "Open question")
        self.reject(REPORT.replace("| Consumer consequence |", "| Files |"), "Consumer consequence")
        self.reject(REPORT.replace("| Not inspected |", "|  |"), "every table cell")
        page.check_review(REPORT.replace("| [source.py:2](source.py#L2) |", "| Unknown; inspect the base first |"), self.note)

    def test_unrun_checks_cannot_claim_execution_results(self):
        for origin in ("Source inspected", "Proposed"):
            for result in ("Passed", "Failed", "Mixed"):
                with self.subTest(origin=origin,result=result):
                    self.reject(REPORT.replace("| Not run | Source inspected |", f"| {result} | {origin} |"), "must say Not run")
        page.check_review(REPORT.replace("| Not run | Source inspected |", "| Passed | Recorded run |"), self.note)
        self.reject(REPORT.replace("| Not run | Source inspected |", "| Passed | Executed here |").replace("| [Duplicate entries](#duplicate-entries) |", "| Duplicate entries |"), "linked run record")

    def test_no_checks_branch_does_not_hide_bad_result_table(self):
        source = REPORT.replace("Tests inspected: none.", "No checks selected: intent unclear.\n\nTests inspected: none.")
        self.reject(source.replace("| Not run | Source inspected |", "| Passed | Proposed |"), "must say Not run")
        start, end = REPORT.index("| [Duplicate entries](#duplicate-entries) | Not run"), REPORT.index("## Evidence and record")
        only_probes = REPORT[:start] + "| [Bug probes](#possible-bugs) | Not run | Proposed | abc; no probe ran | No path was probed |\n\n" + REPORT[end:]
        page.check_review(only_probes.replace("| Check or scenario", "No checks selected: clarify intent first.\n\n| Check or scenario"), self.note)
        # The search for bugs keeps its row when no other check is selected.
        start = REPORT.index("| Check or scenario")
        self.reject(REPORT[:start]+"No checks selected: clarify intent first.\n\n"+REPORT[end:], "Bug probes")

    def test_no_behavior_and_early_overview_are_explicit(self):
        start, end = REPORT.index("### Duplicate entries"), REPORT.index("## Verification")
        for declaration in ("No consequential behavior change: inspected formatting only, source.py:1.", "Not yet inspected: caller path remains unknown."):
            source = (REPORT[:start]+declaration+"\n\n"+REPORT[end:]).replace("#duplicate-entries", "#behavior-changes")
            page.check_review(source, self.note)

    def test_template_prompts_fail_but_source_literals_remain_valid(self):
        self.reject(REPORT.replace("Caller gets fewer entries", "{{consumer_consequence}}"), "template prompts")
        page.check_review(REPORT + '\n```text\n{{literal_template}}\n## Requirements\n```\n', self.note)

    def test_markdown_only_links_and_duplicate_anchors(self):
        self.reject(REPORT.replace("(source.py#L2)", "(missing.py#L2)"), "Missing local file")
        self.reject(REPORT.replace("Look at: [Duplicate entries](#duplicate-entries)", "Look at: [Duplicate entries](#missing)"), "Missing fragment")
        self.reject(REPORT + '\n### Provenance\n\nDuplicate.\n', "distinct names")
        linked_heading = REPORT.replace('### Duplicate entries', '### [Duplicate entries](source.py#L2)')
        page.check_review(linked_heading, self.note)
        page.check(linked_heading, page.render(linked_heading, self.note.name), self.note)

    def test_badges_keep_labels_links_and_visible_tables(self):
        source = REPORT.replace("## Requirements\n", "## Requirements\n\n> Requirements are source-inspected.\n")
        soup = page.parse(page.render(source, self.note.name))
        self.assertEqual([s.get_text() for s in soup.select(".review-table .status")], ["Unmet", "Not run", "Not run"])
        self.assertIsNone(soup.select_one("#requirements details"))
        self.assertIsNone(soup.select_one("#verification details"))
        self.assertIsNotNone(soup.select_one("#evidence-and-record details"))
        self.assertIsNotNone(soup.select_one(".review-conclusion"))
        self.assertTrue(all(th.get("scope") == "col" for th in soup.select(".review-table th")))
        page.check(source, str(soup), self.note)
        source = REPORT.replace('| Unmet |', '| [Unmet](#duplicate-entries) |')
        linked = page.render(source, self.note.name)
        page.check(source, linked, self.note)
        self.assertIsNotNone(page.parse(linked).select_one('.status a'))

    def test_attention_routes_preserve_inline_markup_and_long_context(self):
        source = REPORT.replace("was deduplication intended?", "does `Settle: literal` preserve [intent](intent.md#L1)?")
        for separator in ("\n   ", "\n\n   "):
            with self.subTest(separator=separator):
                variant = source.replace("\n   Look at:", separator + "Look at:")
                html = page.render(variant, self.note.name)
                soup = page.parse(html)
                self.assertEqual([x.get_text() for x in soup.select('.attention-route dt')], ['Look at', 'Settle'])
                self.assertEqual(len(soup.select('.attention-heading .chip')), 2)
                self.assertIn('Source uses a set', soup.select_one('.attention-body').get_text())
                self.assertEqual(soup.select_one('.attention-route code').get_text(), 'Settle: literal')
                self.assertEqual(len(soup.select('.attention-route a')), 2)
                if separator == "\n   ":
                    page.check(variant, html, self.note)

    def test_font_is_embedded_and_other_asset_urls_stay_rejected(self):
        html = page.render(REPORT, self.note.name)
        self.assertIn('data:font/woff2;base64,d09GMg', html)
        self.assertIn('SIL OPEN FONT LICENSE', html)
        page.check(REPORT, html, self.note)
        for url in ('https://example.com/font.woff2', 'data:text/html;base64,d09GMg=='):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, 'CSS URLs'):
                page.check(REPORT, html.replace('</style>', f'.bad{{background:url({url})}}</style>', 1), self.note)
        for data in ('bad!', 'YWJjZA=='):
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, 'Invalid embedded WOFF2'):
                page.check(REPORT, html.replace('</style>', f'@font-face{{src:url(data:font/woff2;base64,{data})}}</style>', 1), self.note)

    def test_diagram_theme_preserves_source_and_removes_only_unused_neo_rules(self):
        def run(command, **kwargs):
            source = Path(command[command.index('-i') + 1]).read_text()
            self.assertEqual(source, 'sequenceDiagram\n A->>B: Test')
            config = json.loads(Path(command[command.index('-c') + 1]).read_text())
            self.assertEqual(config['theme'], 'base')
            self.assertFalse(config['sequence']['mirrorActors'])
            self.assertIn('data:font/woff2;base64,', config['themeCSS'])
            Path(command[command.index('-o') + 1]).write_text('<svg><style>[data-look="neo"].node{stroke:url(#gradient)}.actor{fill:#243858}</style><text>Test</text></svg>')
        with patch.object(page, 'mermaid_command', return_value=['mmdc']), patch.object(page.subprocess, 'run', side_effect=run):
            svg = page.mermaid_svg('sequenceDiagram\n A->>B: Test', 'diagram-1')
        self.assertNotIn('url(#gradient)', svg)
        self.assertIn('.actor{fill:#243858}', svg)
        self.assertIn('<text>Test</text>', svg)

    def test_beautiful_mermaid_preserves_source_and_namespaces_svg(self):
        source = 'sequenceDiagram\n A->>B: Test'
        result = subprocess.CompletedProcess([], 0, stdout='<svg><defs><marker id="arrow"/></defs><path marker-end="url(#arrow)"/><text>Test</text></svg>')
        with patch.object(page.subprocess, 'run', return_value=result) as run:
            svg = page.beautiful_mermaid_svg(source, 'diagram-2')
        self.assertEqual(run.call_args.kwargs['input'], source)
        self.assertTrue(run.call_args.kwargs['check'])
        soup = page.parse(svg)
        self.assertEqual(soup.svg['data-renderer'], 'beautiful-mermaid')
        self.assertEqual(soup.marker['id'], 'diagram-2-arrow')
        self.assertEqual(soup.path['marker-end'], 'url(#diagram-2-arrow)')
        self.assertEqual(soup.find('text').get_text(), 'Test')
        with patch.object(page, 'beautiful_mermaid_svg', return_value=svg) as render_svg:
            page.render('# Fixture\n\n```mermaid\n' + source + '\n```', 'note.md', 'beautiful-mermaid')
        self.assertEqual(render_svg.call_args.args[0].strip(), source)

    def test_beautiful_mermaid_failure_is_explicit(self):
        for error in (FileNotFoundError('node'), subprocess.CalledProcessError(1, 'node', stderr='unsupported syntax'), subprocess.TimeoutExpired('node', 30, stderr=b'partial output')):
            with self.subTest(error=error), patch.object(page.subprocess, 'run', side_effect=error):
                with self.assertRaisesRegex(ValueError, 'Beautiful Mermaid failed.*--diagram-renderer mermaid'):
                    page.beautiful_mermaid_svg('bad', 'diagram-1')
        with patch.object(page.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, stdout='')):
            with self.assertRaisesRegex(ValueError, 'returned no SVG'):
                page.beautiful_mermaid_svg('bad', 'diagram-1')

    def test_behavior_labels_preserve_all_authored_text_and_links(self):
        html = page.render(REPORT, self.note.name)
        original = page.parse(page.MARKDOWN.render(REPORT))
        soup = page.parse(html)
        fields = soup.select('.behavior-fact')
        self.assertEqual(len(fields), 5)
        for field in fields:
            label = field.strong.get_text()
            before = next(p for p in original.find_all('p') if p.strong and p.strong.get_text() == label)
            self.assertEqual(field.get_text(), before.get_text())
            self.assertEqual(page.link_targets(field), page.link_targets(before))
            self.assertIsNotNone(field.select_one('.fact-copy'))
        page.check(REPORT, html, self.note)

    def test_inline_route_words_do_not_start_a_route(self):
        for inline in ('[record](source.py#L2)', '**record**', '`record`'):
            with self.subTest(inline=inline):
                source = REPORT.replace('Source uses a set', f'The {inline} Settle: flag is only a field name; source uses a set')
                html = page.render(source, self.note.name)
                soup = page.parse(html)
                self.assertIn('Settle: flag is only a field name', soup.select_one('.attention-body').get_text())
                self.assertEqual(soup.select('.attention-route dd')[1].get_text().strip(), 'was deduplication intended?')
                page.check(source, html, self.note)

    def test_scenarios_preserve_long_text_inline_links_and_unique_ids(self):
        long_text = 'More context is needed to understand the boundary. ' * 12
        source = REPORT.replace('Source predicts one', long_text + '`one` ([source](source.py#L2))')
        html = page.render(source, self.note.name)
        soup = page.parse(html)
        scenario = soup.select_one('article.scenario')
        self.assertEqual(scenario.select_one('.scenario-title').name, 'h4')
        self.assertEqual(scenario.select_one('.scenario-label').name, 'h5')
        self.assertEqual([cell['data-column'] for cell in scenario.select('[data-column]')], list(page.SCENARIO_COLUMNS))
        self.assertIn(long_text.strip(), scenario.get_text())
        self.assertIsNotNone(scenario.select_one('[data-column="After"] a'))
        self.assertIsNone(soup.select_one('.scenarios-table'))
        page.check(source, html, self.note)
        page.check_review_tables(source, html)
        scenario.select_one('[data-column="Evidence"]').decompose()
        with self.assertRaisesRegex(ValueError, 'table content differs'):
            page.check_review_tables(source, str(soup))

    def test_cli_enforces_same_contract_with_and_without_html(self):
        command = [sys.executable, str(ROOT / "skills/render_page.py"), str(self.note), "--review"]
        self.assertEqual(subprocess.run(command+["--check", "--sync-labels"], capture_output=True).returncode, 0)
        self.assertFalse(self.note.with_suffix('.html').exists())
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run(command+["--check"], capture_output=True).returncode, 0)
        self.note.write_text(REPORT.replace('| Not run | Source inspected |','| Passed | Source inspected |'))
        self.assertNotEqual(subprocess.run(command+["--check"], capture_output=True).returncode, 0)

    def test_markdown_only_retains_review_structure_checks(self):
        self.note.with_suffix('.html').write_text('An old companion awaiting regeneration.')
        command = [sys.executable, str(ROOT / 'skills/render_page.py'), str(self.note),
                   '--check', '--markdown-only', '--review', '--sync-labels']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.note.write_text(self.note.read_text().replace('## Verification', '## Old verification'))
        before = self.note.read_bytes()
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one '## Verification'", result.stderr)
        self.assertEqual(self.note.read_bytes(), before)
        self.assertEqual(self.note.with_suffix('.html').read_text(), 'An old companion awaiting regeneration.')

    def test_check_reports_every_failure_at_once(self):
        # Agents reran --check once per failure; one run names them all, numbered, and still exits 1.
        self.note.write_text(REPORT.replace("| Not inspected |", "|  |")
                             .replace('([intent.md:1](intent.md#L1))', '(no accessible intent)'))
        command = [sys.executable, str(ROOT / "skills/render_page.py"), str(self.note), "--review", "--check"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        for number, message in enumerate(("fill every table cell", "link the intent source",
                                          "label key is missing or stale"), 1):
            self.assertRegex(result.stderr, rf"(?m)^{number}\. .*{message}")
        self.assertNotRegex(result.stderr, r"(?m)^4\. ")

    def test_page_check_reports_every_failure_at_once(self):
        html = (page.render(REPORT, self.note.name).replace('tabindex="0"', '')
                .replace('</head>', '<link rel="stylesheet" href="https://example.com/s.css"></head>'))
        with self.assertRaises(ValueError) as caught:
            page.check(REPORT, html.replace('</main>', '<a href="#absent">x</a></main>'), self.note)
        for message in ("keyboard scrolling", "Missing fragment: #absent", "self-contained"):
            self.assertIn(message, str(caught.exception))
        self.assertRegex(str(caught.exception), r"(?m)^3\. ")

    def test_auto_renderer_prefers_beautiful_mermaid_then_the_cli_and_warns_on_source(self):
        source = '# Fixture\n\n```mermaid\nflowchart LR\n  A --> B\n```\n'
        fixture = '<svg id="diagram-1" role="img" aria-label="Fixture"/>'
        refuse = AssertionError('wrong renderer')
        with patch.object(page, 'beautiful_mermaid_runs', return_value=True), \
                patch.object(page, 'beautiful_mermaid_svg', return_value=fixture), patch.object(page, 'mermaid_svg', side_effect=refuse):
            self.assertIsNotNone(page.parse(page.render(source, 'note.md', 'auto')).select_one('figure.diagram svg'))
        with patch.object(page, 'beautiful_mermaid_runs', return_value=False), \
                patch.object(page, 'beautiful_mermaid_svg', side_effect=refuse), patch.object(page, 'mermaid_svg', return_value=fixture):
            self.assertIsNotNone(page.parse(page.render(source, 'note.md', 'auto')).select_one('figure.diagram svg'))
        for explicit, used, unused in (('mermaid', 'mermaid_svg', 'beautiful_mermaid_svg'),
                                       ('beautiful-mermaid', 'beautiful_mermaid_svg', 'mermaid_svg')):
            with self.subTest(explicit=explicit), patch.object(page, 'beautiful_mermaid_runs', side_effect=refuse), \
                    patch.object(page, used, return_value=fixture), patch.object(page, unused, side_effect=refuse):
                self.assertIsNotNone(page.parse(page.render(source, 'note.md', explicit)).select_one('figure.diagram svg'))
        stderr = io.StringIO()
        with patch.object(page, 'beautiful_mermaid_runs', return_value=False), patch.object(page, 'mermaid_command', return_value=None), \
                contextlib.redirect_stderr(stderr):
            html = page.render(source + source[len('# Fixture'):], 'note.md', 'auto')
        self.assertEqual(len(page.parse(html).select('pre.mermaid-source')), 2)
        self.assertEqual(stderr.getvalue().splitlines(), [
            f'Diagram {n} left as source: no diagram renderer runs here (install Beautiful Mermaid:'
            f' npm ci --prefix {ROOT / "skills/diagram-renderer"}, or the Mermaid CLI).' for n in (1, 2)])

    def test_auto_renderer_tries_the_cli_when_beautiful_mermaid_rejects_a_diagram(self):
        source = '# Fixture\n\n```mermaid\nsequenceDiagram\n  A-xB: stop\n```\n'
        rejected = ValueError('Beautiful Mermaid failed. Termination crosses are unsupported')
        fixture = '<svg id="diagram-1" role="img" aria-label="Fixture"/>'
        with patch.object(page, 'beautiful_mermaid_runs', return_value=True), patch.object(page, 'beautiful_mermaid_svg', side_effect=rejected):
            with patch.object(page, 'mermaid_svg', return_value=fixture):
                self.assertIsNotNone(page.parse(page.render(source, 'note.md')).select_one('figure.diagram svg'))
            stderr = io.StringIO()
            with patch.object(page, 'mermaid_command', return_value=None), contextlib.redirect_stderr(stderr):
                html = page.render(source, 'note.md')
            self.assertIsNotNone(page.parse(html).select_one('pre.mermaid-source'))
            self.assertEqual(stderr.getvalue(), 'Diagram 1 left as source: Beautiful Mermaid does not support its syntax, such as'
                             ' termination-cross arrows, and the Mermaid CLI did not render it (install the Mermaid CLI).\n')
            with self.assertRaisesRegex(ValueError, 'Termination crosses'):
                page.render(source, 'note.md', 'beautiful-mermaid')

    def test_review_check_refuses_an_unrecorded_source_only_diagram(self):
        diagram = ('The counter keeps one entry per value. Observed case.\n\n```mermaid\nflowchart LR\n  E[entries] --> S[set]\n```\n\n'
                   'Source map:\n- E → S — [source.py:2](source.py#L2)\n\n## Requirements')
        source = REPORT.replace('## Requirements', diagram, 1)
        recorded = source.replace('### Provenance\n', '### Provenance\n\nDiagram renderer unavailable: neither backend runs here.\n')
        command = [sys.executable, str(ROOT / 'skills/render_page.py'), str(self.note), '--check']
        for text, refused in ((source, True), (recorded, False)):
            with self.subTest(refused=refused):
                self.note.write_text(page.with_label_key(text))
                with patch.object(page, 'beautiful_mermaid_runs', return_value=False), patch.object(page, 'mermaid_command', return_value=None), \
                        contextlib.redirect_stderr(io.StringIO()):
                    self.note.with_suffix('.html').write_text(page.render(self.note.read_text(), self.note.name))
                review = subprocess.run(command + ['--review'], capture_output=True, text=True)
                self.assertEqual(review.returncode != 0, refused, review.stderr)
                if refused:
                    self.assertIn("'diagram renderer unavailable' to '## Evidence and record'", review.stderr)
                plain = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(plain.returncode, 0, plain.stderr)

    def test_html_cannot_silently_change_fulfillment_or_results(self):
        html = page.render(REPORT, self.note.name)
        page.check_review_tables(REPORT, html)
        for before, after in ((">Unmet<", ">Met<"), (">Not run<", ">Passed<"),
                              ("Caller gets fewer entries", "Caller gets more entries")):
            with self.subTest(before=before), self.assertRaisesRegex(ValueError, "table content differs"):
                page.check_review_tables(REPORT, html.replace(before, after))

    def test_html_scenarios_cannot_move_to_another_behavior(self):
        start, end = REPORT.index('### Duplicate entries'), REPORT.index('## Verification')
        other = REPORT[start:end].replace('Duplicate entries', 'Other behavior').replace('Two equal entries', 'Two different entries')
        source = REPORT[:end] + other + REPORT[end:]
        html = page.render(source, self.note.name)
        page.check_review(source, self.note)
        page.check_review_tables(source, html)
        soup = page.parse(html)
        groups = soup.select('.scenario-list')
        groups[1].append(groups[0].article.extract())
        with self.assertRaisesRegex(ValueError, 'table content differs'):
            page.check_review_tables(source, str(soup))


if __name__ == "__main__":
    unittest.main()
