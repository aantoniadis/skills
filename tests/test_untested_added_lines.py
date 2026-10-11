"""Exercise coverage candidates against real disposable Git histories."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/find-bugs/scripts/untested_added_lines.py'


class CoverageCandidatesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'app.py').write_text('old = 0\n')
        self.base = self.commit()
        (self.repo / 'app.py').write_text('first = 1\nsecond = 2\nthird = 3\n# comment\n\n')
        self.head = self.commit()
        self.report({'app.py': {'executed_lines': [1], 'missing_lines': [2], 'excluded_lines': [3]}})

    def git(self, *args):
        env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
        return subprocess.check_output(['git', '-C', str(self.repo), *args], env=env, text=True).strip()

    def commit(self):
        self.git('add', 'app.py')
        self.git('commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def report(self, files):
        (self.repo / 'cov.json').write_text(json.dumps({'files': files}))

    def run_cli(self, *options, expected=0, env=None):
        result = subprocess.run([sys.executable, str(SCRIPT), '--repo', str(self.repo),
                                 '--base', self.base, '--head', self.head, *options],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
        self.assertNotIn('Traceback', result.stderr)
        return result.stdout + result.stderr

    def test_line_evidence_keeps_comments_and_exclusions_distinct(self):
        before = self.git('status', '--porcelain')
        output = self.run_cli()
        self.assertIn('5 added lines; 1 executed, 1 missing, 1 excluded, 2 unclassified', output)
        self.assertIn('missing lines: 2', output)
        self.assertNotIn('all 5 added lines executed', output)
        self.assertEqual(self.git('status', '--porcelain'), before)

    def test_excluded_lines_that_ran_are_counted_once(self):
        self.report({'app.py': {'executed_lines': [1], 'missing_lines': [2], 'excluded_lines': [1, 3]}})
        self.assertIn('5 added lines; 1 executed, 1 missing, 1 excluded, 2 unclassified', self.run_cli())

    def test_git_failures_and_report_errors_are_explicit(self):
        self.assertIn('coverage comparison failed', self.run_cli('--base', 'no-such-revision', expected=2))
        self.assertIn('coverage comparison failed', self.run_cli('--repo', str(self.repo / 'absent'), expected=2))
        self.assertIn('no coverage report', self.run_cli('--cov', 'absent.json', expected=2))
        for value in ('{', '[]', '{"files":null}', '{"files":{"app.py":{}}}',
                      '{"files":{"app.py":{"executed_lines":[true],"missing_lines":[]}}}'):
            with self.subTest(value=value):
                (self.repo / 'cov.json').write_text(value)
                self.assertIn('coverage comparison failed', self.run_cli(expected=2))

    def test_absent_files_and_unrelated_suffixes_remain_unknown(self):
        for files in ({}, {'other/app.py': {'executed_lines': [1, 2, 3, 4, 5], 'missing_lines': []}}):
            self.report(files)
            output = self.run_cli()
            self.assertIn('0 executed, 0 missing, 0 excluded, 5 unclassified', output)
            self.assertIn('file absent from coverage report', output)
            self.assertNotIn('covers every added line', output)

    def test_paths_with_git_quoting_are_not_lost_or_misattributed(self):
        names = ['café.py', 'tab\tfile.py', 'line\nfile.py', 'space file.py']
        for name in names:
            (self.repo / name).write_text('x = 1\ny = 2\n')
            self.git('add', '--', name)
        self.head = self.commit()
        self.report({name: {'executed_lines': [], 'missing_lines': [1, 2]} for name in names})
        output = self.run_cli()
        for name in names:
            self.assertIn(json.dumps(name, ensure_ascii=False) + ': 2 added lines; 0 executed, 2 missing', output)
        self.assertIn('total: 13 added text lines; 0 executed, 8 missing, 0 excluded, 5 unclassified', output)

    def test_absolute_paths_and_ambiguous_aliases(self):
        entry = {'executed_lines': [1], 'missing_lines': [2]}
        self.report({str(self.repo / 'app.py'): entry})
        self.assertIn('1 executed, 1 missing', self.run_cli())
        self.report({'app.py': entry, './app.py': entry})
        self.assertIn('ambiguous coverage paths', self.run_cli(expected=2))

    def test_istanbul_uses_statement_starts_not_multiline_interiors(self):
        data = {str(self.repo / 'app.py'): {
            's': {'0': 1, '1': 0, '2': 0},
            'statementMap': {'0': {'start': {'line': 1}, 'end': {'line': 3}},
                             '1': {'start': {'line': 1}, 'end': {'line': 1}},
                             '2': {'start': {'line': 3}, 'end': {'line': 3}}}}}
        (self.repo / 'cov.json').write_text(json.dumps(data))
        output = self.run_cli()
        self.assertIn('statement-start coverage', output)
        self.assertIn('1 executed, 1 missing, 0 excluded, 3 unclassified', output)
        data[str(self.repo / 'app.py')]['s']['2'] = -1
        (self.repo / 'cov.json').write_text(json.dumps(data))
        self.assertIn('invalid Istanbul', self.run_cli(expected=2))

    def test_pins_ignore_dirty_files_and_inherited_git_selection(self):
        (self.repo / 'app.py').write_text('changed again\n')
        env = dict(os.environ, GIT_DIR=str(self.repo / 'wrong'), GIT_WORK_TREE=str(self.repo / 'wrong'))
        self.assertIn('5 added lines', self.run_cli(env=env))
        self.assertEqual((self.repo / 'app.py').read_text(), 'changed again\n')
        (self.repo / 'subdirectory').mkdir()
        self.assertIn('5 added lines', self.run_cli('--repo', str(self.repo / 'subdirectory')))

    def test_binary_rename_and_path_filter_bound_the_output(self):
        (self.repo / 'binary.bin').write_bytes(b'\0binary')
        self.git('mv', 'app.py', 'renamed.py')
        self.git('add', 'binary.bin')
        self.git('commit', '-qm', 'rename and binary')
        self.head = self.git('rev-parse', 'HEAD')
        output = self.run_cli()
        self.assertIn('"binary.bin": no added text lines', output)
        self.assertIn('"renamed.py": 5 added lines', output)
        filtered = self.run_cli('--src', 'renamed.py')
        self.assertNotIn('binary.bin', filtered)
        self.assertIn('5 unclassified', filtered)


if __name__ == '__main__':
    unittest.main()
