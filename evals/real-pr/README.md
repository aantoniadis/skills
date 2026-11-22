# Real-PR recall experiment for find-bugs

This folder is the record of one experiment. It is not a shipped eval:
`evals/run.py` does not pick these cases up, and each run costs real money.

The question: a second `find-bugs` run on the same pins reports defects the
first run missed. How much do runs differ, and what closes the gap?

## What is here

- `find-bugs-fastapi/`: fastapi/fastapi PR 15745, base `016ab76`, head
  `1e70f7c`. Fourteen issues are verified by the base-versus-head probes in
  `probes/`, with one grader each. `probes/p10_custom_handler_deps.py` shows a
  fifteenth that no grader scores.
- `find-bugs-filelock/`: tox-dev/filelock PR 659, base `126cab7`, head
  `e6538e1`. Held out: the arm text was frozen and all eight runs finished
  before any later fix was read. Its graders were written afterwards, one for
  each of 17 distinct findings the runs reported (`f01` to `f17`) and one for
  each of 4 defects that later fixes attribute to this PR (`ka` to `kd`).
  `probes/` reproduces 10 of the 17, three of them only under an injected
  fault or a forced interleaving.
- `results/`: one `results.json` for each set of runs, with every final
  message and grader verdict. `ev-prose` and `ev-prose2` are runs of the
  `find-bugs-recall` fixture, which lives on the `find-bugs-improvements`
  branch.
- `results/finder-reports-judged.json`: the same graders applied to what each
  finder returned to its lead.
- `arm-passes-SKILL.md`: the `find-bugs` text of the independent-passes arm,
  frozen before the held-out runs. `arm-solo-SKILL.md`: one finder and a
  verifying lead; no run of it is recorded here.
- `run_overlap.py`: `evals/run.py` as of commit fdf0248 (`--evals-dir`, runs
  for each case, pairwise overlap, a `T` mark for a run with more than one
  result event), with Docker, `curl`, `wget`, and package installs blocked.
- `static_delta.py`: prints the type-checker or linter diagnostics that the
  head has and the base lacks.

## Results on fastapi PR 15745, Opus 5.5

| Arm | Runs | Found of 14 | Pairwise overlap | Cost for each run |
|---|---|---|---|---|
| `main` | 6 | 5.3 mean, 3 to 8 | 0.53 | $1.19 |
| class questions and `## Minor observations` | 5 | 6.0 mean | 0.60 | $1.17 |
| independent passes | 3 | 11, 10, 11 | 0.83 | $5.86 |
| `find-bugs-improvements` ledger | 3 | 9, 8, 7 | 0.78 | $4.05 |
| `main` on Fable 5.2 | 1 | 8 | not measured | $1.97 |

Five `main` runs merged find 8.7 on average, for $5.95. No arm found the
`APIRoute.tags` typing break; `static_delta.py` over `docs_src` prints it.
The runner marked all three independent-passes runs `T`; one was scored on its
longest message, not its last. The third ledger run probed the cache race and
listed it as a minor observation; the judge scored that a miss. A fourth
ledger run was cut off by a usage limit and is not recorded.

The state finder's instruction was written after this PR showed the cache
race missed, so its three hits here are not a confirmation.

## Results on filelock PR 659, Opus 5.5, held out

| Arm | Runs | Findings of 17 | Reproduced of 10 | Pairwise overlap | Cost for each run |
|---|---|---|---|---|---|
| `main` | 5 | 3.6 mean: 5, 2, 6, 3, 2 | 2.4 mean | 0.22 | $1.57 |
| independent passes | 3 | 10.3 mean: 9, 11, 11 | 7.3 mean | 0.51 | $8.23 |

Five `main` runs merged reach 10.0 findings and 7.0 reproduced, for $7.86: the
same as one independent-passes run for the same money. No run of either arm
found any of the 4 defects that later fixes attribute to this PR.

"Reproduced" means a behavior change observed at the head and not at the
base, or a failure in new code under the stated fault. It does not mean a
maintainer fixed it. The 17 graders were written after reading the runs, so
they score agreement between runs, not recall against an independent list.

## Later runs

- `arm-solo-SKILL.md` (one finder and a verifying lead): 8.3 of 14 on fastapi
  for $2.85 a run and 6.0 of 17 on filelock for $3.75 (`results/ev-oss-solo`,
  `results/ev-fl-solo`): about what merged plain reads find for the same money.
- `find-bugs-fl738/`: tox-dev/filelock PR 738, base `20929f7`, head `ed3fdd0`,
  with one grader for each of the 3 defects later fixes attribute to it. A
  summary of those defects was in the author's context before the fault finder
  was written. Skill text from commit 95c22ae on `find-bugs-depth`:

| Arm | Runs | Defects delivered | Later-fixed defects found | Cost for each run |
|---|---|---|---|---|
| one read | 3 | 1, 1, 1 (the same one) | 0 | $0.98 |
| thorough, five finders | 2 | 4, 4 | 0; the FIFO half of one, filed as minor in run 0 | $8.06 |

`remaining.py` estimated 57% and 90% in the two thorough runs.

## What the two PRs support

- One `main` run reports a fraction of what repeated runs report.
- For the same money, independent passes match merged plain runs. The gain is
  repeated reading with a checked merge in one run, at about five times the
  cost of one read.
- Runs of a structured arm agree more with each other: 0.51 to 0.83 against
  0.22 to 0.53.
- One plain finder returned 7.0 (fastapi) and 5.8 (filelock) findings to its
  lead, against 5.3 and 3.6 delivered by a whole `main` run. No run has tested
  a single finder with a verifying lead.
- The ledger was not run on filelock, so it is not ranked against
  independent passes.

## Rebuild and run

The fixtures clone from `/tmp/real-pr-cache`, and the prompts name the
environments there.

```bash
mkdir -p /tmp/real-pr-cache/fastapi && cd /tmp/real-pr-cache/fastapi
git init -q --bare fastapi.git
git -C fastapi.git fetch -q --depth 300 https://github.com/fastapi/fastapi.git \
  1e70f7cdc8c05cc16146f9a40c3776912384caf6 016ab760faba1813ba235d5582a014a58bd2f417
git -C fastapi.git branch main 016ab760faba1813ba235d5582a014a58bd2f417
git -C fastapi.git branch refactor/router-tree 1e70f7cdc8c05cc16146f9a40c3776912384caf6
git -C fastapi.git symbolic-ref HEAD refs/heads/main
git clone -q fastapi.git src && git -C src checkout -q refactor/router-tree
(cd src && uv export --frozen --no-emit-project --no-dev --group tests --extra all \
  --no-hashes -o ../req.txt -q)
uv venv -q venv && VIRTUAL_ENV=$PWD/venv uv pip install -q -r req.txt
```

For filelock, fetch `e6538e1d99f71ad6f7bf47a41b7031a2681b6c48` and
`126cab74567d3c9bb52b402580dd7615409d10e7` into
`/tmp/real-pr-cache/filelock/filelock.git` with branches `main` and
`feat/strict-owner-claims`. The project has no lock file, so install its `test`
dependency group and `ty` with `uv pip install --exclude-newer 2026-07-16`.

```bash
python3 evals/real-pr/run_overlap.py --evals-dir evals/real-pr \
  --plugin-dir <checkout> --out <new dir> --case find-bugs-fastapi --runs 3
```

Each run leaves a full checkout under `--out`. On a memory-backed `/tmp`,
delete it when the run's `results.json` is saved: the inode limit fills first.
