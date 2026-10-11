#!/usr/bin/env python3
"""Intersect added source lines between two commits with an existing coverage report.

Run from the repository root, or pass --repo. Coverage keys must be relative to
that root or absolute within it. Use coverage.py JSON or Istanbul/Vitest JSON.
The caller must establish that the report describes --head and the tested setup.
This command does not measure working-tree changes or generate coverage.

Excluded and unclassified lines are not evidence of execution. Istanbul reports
statement-start lines here; multiline interiors and untested branches remain
unknown. Renames are treated as deletion/addition. Binary files have no line data.
Exit 2 for invalid inputs or failed Git operations. No files are written.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def git(repo, *args):
    # Read the requested checkout, not a repository selected by inherited Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    result = subprocess.run(['git', '-C', str(repo), *args], env=env, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or f'git failed with exit {result.returncode}')
    return result.stdout


def line_set(value):
    if not isinstance(value, list) or any(type(n) is not int or n < 1 for n in value):
        raise ValueError('coverage line numbers must be lists of positive integers')
    return set(value)


def coverage_lines(data, repo):
    if not isinstance(data, dict):
        raise ValueError('coverage report must be a JSON object')
    python = 'files' in data
    files = data['files'] if python else data
    if not isinstance(files, dict):
        raise ValueError('coverage files must be an object')
    result = {}
    for name, entry in files.items():
        if not name or not isinstance(entry, dict):
            raise ValueError('coverage entries need a file path and an object')
        if python:
            executed = line_set(entry.get('executed_lines'))
            missing = line_set(entry.get('missing_lines'))
            excluded = line_set(entry.get('excluded_lines', []))
            if executed & missing or excluded & missing:
                raise ValueError(f'contradictory coverage lines for {name!r}')
            excluded -= executed  # Exclusion from coverage obligations does not prevent execution.
        else:
            counts, locations = entry.get('s'), entry.get('statementMap')
            if not isinstance(counts, dict) or not isinstance(locations, dict) or counts.keys() != locations.keys():
                raise ValueError(f'invalid Istanbul statement data for {name!r}')
            executed, missing, excluded = set(), set(), set()
            for statement, count in counts.items():
                location = locations[statement]
                start = location.get('start') if isinstance(location, dict) else None
                line = start.get('line') if isinstance(start, dict) else None
                if type(count) is not int or count < 0 or type(line) is not int or line < 1:
                    raise ValueError(f'invalid Istanbul statement location/count for {name!r}')
                (executed if count else missing).add(line)
            missing -= executed  # A hit on a line does not establish every statement/branch ran.
        key = Path(os.path.abspath(repo / name))
        if key in result:
            raise ValueError(f'ambiguous coverage paths for {name!r}')
        result[key] = executed, missing, excluded
    return result, 'line coverage' if python else 'statement-start coverage'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--cov', help='coverage JSON; default searches conventional paths at the repo root')
    parser.add_argument('--src', default='.', help='repository-relative Git path filter; tests/docs/config excluded')
    parser.add_argument('--repo', default='.')
    args = parser.parse_args()
    try:
        repo = Path(git(args.repo, 'rev-parse', '--show-toplevel').strip()).resolve()
        base, head = [git(repo, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').strip()
                      for ref in (args.base, args.head)]
        candidates = [args.cov] if args.cov else ['cov.json', '.cov.json', 'coverage.json',
                                                 'cov/coverage-final.json', '.cov/coverage-final.json',
                                                 'coverage/coverage-final.json']
        report = next((repo / name for name in candidates if (repo / name).is_file()), None)
        if report is None:
            raise ValueError('no coverage report found; supply a report produced at the head')
        coverage, kind = coverage_lines(json.loads(report.read_text()), repo)
        options = ['diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--no-relative', '--no-color']
        names = git(repo, *options, '--name-only', '-z', '--diff-filter=AMT', base, head, '--', args.src,
                    ':!tests', ':!test', ':!docs', ':!docs_src', ':!*.md', ':!*.lock', ':!*.toml',
                    ':!*.json', ':!*.yml', ':!*.yaml').split('\0')
        totals = Counter()
        rows = []
        for name in filter(None, names):
            # NUL-delimited names avoid decoding Git's quoted patch headers.
            diff = git(repo, '--literal-pathspecs', *options, '-U0', '--inter-hunk-context=0',
                       base, head, '--', name)
            added = set()
            for start, count in re.findall(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', diff, re.M):
                added.update(range(int(start), int(start) + int(count or 1)))
            label = json.dumps(name, ensure_ascii=False)
            if not added:
                rows.append(f'{label}: no added text lines (binary or deletion-only change)')
                continue
            known = coverage.get(repo / name)
            executed, missing, excluded = known if known is not None else (set(), set(), set())
            groups = {'executed': added & executed, 'missing': added & missing,
                      'excluded': added & excluded, 'unclassified': added - executed - missing - excluded}
            counts = Counter({key: len(lines) for key, lines in groups.items()})
            totals.update(counts)
            suffix = '' if known is not None else '; file absent from coverage report'
            rows.append(f'{label}: {len(added)} added lines; ' +
                        ', '.join(f'{count} {key}' for key, count in counts.items()) + suffix)
            if groups['missing']:
                rows.append('  missing lines: ' + ', '.join(map(str, sorted(groups['missing']))))
        print(f'comparison: {base}..{head}; {kind}; report: {report}')
        for row in rows:
            print(row)
        print(f'total: {sum(totals.values())} added text lines; ' +
              ', '.join(f'{totals[key]} {key}' for key in ('executed', 'missing', 'excluded', 'unclassified')))
        print('Unclassified means non-executable or unmeasured; coverage does not establish input or branch coverage.')
    except (OSError, ValueError) as error:
        print(f'coverage comparison failed: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
