# Focused finders in the thorough search

This folder records one experiment. It is not a shipped eval: `evals/run.py`
does not pick it up, and each run costs real money.

The question: the thorough search in `main` starts five finders, and three of
them get the same assignment. Can different assignments find more for the same
cost?

## The two arms

- **`main`** (commit 08d72db): three general finders, a state finder, and a
  fault finder. Every finder runs the static deltas, and the lead reruns every
  probe a finder saved.
- **Focused finders** (commit 38c7964 on this branch): one general finder and
  four focused finders, for consumers, inputs, state, and faults. The lead runs
  the static deltas, `weakened_checks.py`, and the base's edited tests once.
  Finders run code when the source leaves the outcome open, and return the
  other candidates as inferred. The lead confirms each distinct candidate once.

The focuses come from sorting the defects that general finders found in two or
fewer of nine reads on these two PRs. These PRs are therefore not held out:
the results favor the focused arm.

## Cases

`cases/` holds the prompts: the `find-bugs-fastapi` and `find-bugs-filelock`
cases from `evals/real-pr` on the `find-bugs-variance` branch, with "thorough"
added. The fixtures, graders, and `run_overlap.py` are on that branch. Both
arms ran on Opus 5.5, three runs for each case, through `run_overlap.py` with
`--runs 3 -j 3`.

## Results

| PR | Arm | Defects found | Mean | Cost for each run |
|---|---|---|---|---|
| fastapi PR 15745, of 14 | `main` | 12, 10, 9 | 10.3 | $7.74 |
| | focused finders | 12, 11, 12 | 11.7 | $7.97 |
| filelock PR 659, of 17 graded and 4 later fixed | `main` | 8, 8 | 8.0 | $10.66 |
| | focused finders | 10, 10, 12 | 10.7 | $10.07 |

The third `main` run on filelock is not counted. `claude -p` exited while one
finder still ran, so the lead never delivered; it cost $11.02. Two earlier
attempts of both arms stopped at a usage limit and are not recorded.

No run of either arm delivered any of the four defects that later fixes
attribute to filelock PR 659. A fault finder found one of them, a non-regular
node at a private-record name, in two focused runs, and the lead dropped it
both times as a message-quality issue.

Defects that only one arm found:

- fastapi, only focused: mount timing and the `APIRoute.tags` typing break,
  one run each.
- filelock, only focused: re-entry timeout, hostname space, pickle, pid
  placeholder, dropped close error, orphan claim.
- filelock, only `main`: dual holders and claims `IndexError`, one run each.

## What each focused finder contributed

`judge_finders.py` judges each finder's own report against the case graders,
with Sonnet 5.5. The reports are in `results/focused-finder-reports/` and the
verdicts in `results/focused-finder-reports-judged.json`. A defect counts as
one finder's alone when no other finder reported it in the same run.

| Finder | Defects reported in six runs | Reported by that finder alone |
|---|---|---|
| consumers | 43 | 9 |
| inputs | 44 | 8 |
| fault | 25 | 5, all on filelock |
| state | 23 | 4 |
| general | 39 | 3 |

The finders together reported 13.0 of 14 fastapi defects and 12.3 filelock
defects on average; the lead delivered 11.7 and 10.7. The lead dropped nine
graded defects across the six runs. Its reasons are in each run's
`candidates.md`, which `run_overlap.py` leaves in the run's workspace.

## Rerun

Build the fixtures as `evals/real-pr/README.md` on `find-bugs-variance` says.
Copy each case folder from there into a scratch folder, replace its
`prompt.md` with the one from `cases/`, then run each arm:

```bash
python3 run_overlap.py --evals-dir <scratch cases> --plugin-dir <checkout> \
  --out <new dir> --runs 3 -j 3
```

To judge the finder reports, extract the last text message of each finder
into `<scratch>/finder-reports/<case>-<run>--<focus>.md`, put the case folders
in `<scratch>/arm-cases/` and `run_overlap.py` in `<scratch>`, then run
`python3 judge_finders.py <scratch>`.
