import sys, json, glob, os
from concurrent.futures import ThreadPoolExecutor
S = sys.argv[1]
sys.path.insert(0, S)
import run_overlap as ro
cases = {c: ro.load_case(__import__('pathlib').Path(f'{S}/arm-cases/{c}')) for c in ('find-bugs-fastapi', 'find-bugs-filelock')}
jobs = []
for f in sorted(glob.glob(f'{S}/finder-reports/*.md')):
    run, finder = os.path.basename(f)[:-3].split('--')
    case = run.rsplit('-', 1)[0]
    text = open(f).read()
    for name, meta, body in cases[case]['graders']:
        if meta['type'] == 'llm':
            jobs.append((run, finder, name, body, text))
def work(j):
    run, finder, name, body, text = j
    ok, why = ro.judge(body.replace('final message', 'finder report'), text, 'claude-sonnet-5-5')
    return run, finder, name, ok, why
out = {}
with ThreadPoolExecutor(8) as pool:
    for run, finder, name, ok, why in pool.map(work, jobs):
        out.setdefault(f'{run}--{finder}', {})[name] = {'passed': ok, 'why': why}
json.dump(out, open(f'{S}/finder-reports-judged.json', 'w'), indent=1)
print(len(jobs), 'judgements')
