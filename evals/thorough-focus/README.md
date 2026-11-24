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

## Next version on a held-out PR

The next version (commit 1fd1a47 on this branch) drops the general finder,
starts the fault finder only when `failure_points.py` lists five or more
lines, and keeps a confirmed head-only behavior under `## Minor observations`
instead of dropping it.

It ran against `main` on urllib3/urllib3 PR 5095, base `d7030c0`, head
`8486f9a`, which shaped none of the focuses. `cases/find-bugs-urllib3/` holds
the fixture, prompt, and graders. Build the cache at `/tmp/real-pr-cache/urllib3`
as for filelock: fetch the PR head into branch `fix-percent-encode-hosts` and
the base into `main`, then install the `dev` dependency group and `mypy`.

The maintainers attribute three regressions to this PR in #5260. Only one
reproduces at the PR's own head: an unbracketed scoped IPv6 host such as
`fe80::1%eth0` is rejected (`ka`, `probe_known_regression.py`). The other two
come from later commits. The other graders were written after both arms ran,
one for each distinct finding; `probe_minor_findings.py` confirms `f04` and
`f05` at base and head.

| Arm | Finders | Graders passed, of 6 | Mean | Cost for each run |
|---|---|---|---|---|
| `main` | 5 | 6, 4, 3 | 4.3 | $5.30 |
| next version | 3 | 4, 4, 5 | 4.3 | $4.04 |

Every run of both arms found `ka`, `f01`, and `f02`. The PR has one failure
point, so the next version started no fault finder. One finder in the next
version made an outbound request to example.com against the prompt; its lead
reported it. Results are in `results/urllib3-*.json`.

The PR is small and its defects are few, so both arms come near the ceiling:
this run shows the same recall for 24% less, not a recall gain.

## The drop check on a held-out PR with file operations

The next version plus the drop check (commit b7ed077 on this branch) ran
against `main` on pypa/pipx PR 2229, base `af5f5a1`, head `5323afc`. The
change moves an environment into pipx's trash and restores it on failure;
`failure_points.py` lists 11 lines, so the fault finder starts.
`cases/find-bugs-pipx/` holds the fixture, prompt, and graders. Build the
cache at `/tmp/real-pr-cache/pipx`: fetch `refs/pull/2229/head` into branch
`fix/force-retry-keeps-venv` and the base into `main`, then install the
project's dependencies, its `test` group, and `ty`.

The maintainers fixed one regression of this PR in #2350: a failed move into
the trash deletes the live environment (`ka`, `probe_known_regression.py`).
The other graders were written after both arms ran, one for each distinct
finding. Two findings are not graded: one run reported a restore blocked by a
locked file, which another run showed is the same at base, and the lost
"Not removing existing venv" warning is documented in the changelog.

| Arm | Finders | Graders passed, of 5 | Mean | Cost for each run |
|---|---|---|---|---|
| `main` | 5 | 5, 5, 4 | 4.7 | $6.61 |
| next version plus the drop check | 4 | 5, 4, 4 | 4.3 | $4.85 |

The fault finder started in every run of the focused version. Every drop in
its `candidates.md` names an allowed ground. It missed `f02`, the uv backend
restoring an environment uv already changed, in two runs: in all three `main`
runs that finding came from a general finder, and no focused finder reported
it. Results are in `results/pipx-*.json`. A first attempt of the `main` arm
stopped at a usage limit and is not recorded.

## What each finder contributed in the first focused arm

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
