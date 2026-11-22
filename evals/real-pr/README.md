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
  `e6538e1`. Held out: no answer key was read and no run is recorded yet.
- `results/`: one `results.json` for each set of runs, with every final
  message and grader verdict. `ev-prose` and `ev-prose2` are runs of the
  `find-bugs-recall` fixture, which lives on the `find-bugs-improvements`
  branch.
- `arm-passes-SKILL.md`: the `find-bugs` text of the independent-passes arm,
  frozen before the held-out runs.
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
| `find-bugs-improvements` ledger | 1 | 9 | not measured | $2.54 |
| `main` on Fable 5.2 | 1 | 8 | not measured | $1.97 |

Five `main` runs merged find 8.7 on average, for $5.95. No arm found the
`APIRoute.tags` typing break; `static_delta.py` over `docs_src` prints it.
The runner marked all three independent-passes runs `T`; one was scored on its
longest message, not its last.

These numbers come from one PR and one model. The state finder's instruction
was written after this PR showed the cache race missed, so its three hits are
not a confirmation.

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
