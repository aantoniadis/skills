# whats-next

Ask it at any point. It reads the checkout and the notes and reports already
written, places you on the [workflow](workflow.md), and gives the next command
and the session to run it in. It also says when that session is finished and
which sessions you can close. It writes nothing to the project; you run the
next step, or inside herdr-core you say yes and it opens the session for you.

## How it works

1. **Scan.** `workflow_state.py` prints the branch and its distance from the
   default branch, uncommitted files, the investigation location, every note
   and report our skills left (understanding note, plan, diagnosis note, PR
   review guide, acceptance report) with its summary line, local tickets,
   `visual-pr` tasks, Matt's tracker setup, and whether a local tool record
   exists. The skill adds what the scan cannot see: what this conversation
   just finished, an open PR, and the installed originals from the tool record.
2. **Place.** The evidence table in the skill maps what was found to a row:
   the next skill and the session, the same wording as the workflow's
   [which-skill table](workflow.md#which-skill-in-which-session). When two
   rows fit, it asks one question, recommendation first.
3. **Answer.** Where you are with the evidence, the next skill, the command
   in your host's form with real paths, same or new session and why, what to
   carry into a fresh session, the evidence that ends the step, which session
   to close and when, and one alternative.
4. **Open, inside herdr-core.** When the next step needs a new session and
   the skill runs in a herdr-core terminal under Claude Code, it shows the
   exact `hc run` command and asks. On your yes it opens one of two things:
   a session in a new tab that you work in, which stays alive when you close
   the planning session; or a worker with no tab, for a step that ends in a
   report, which reports back to the session that started it and ends with
   it. Without your yes it opens nothing.

Prompt shapes:

```text
/aantoniadis-skills:whats-next
/aantoniadis-skills:whats-next I finished the plan at .scratch/order/plan.md. What now?
/aantoniadis-skills:whats-next I have to review PR 42 and have never seen this code.
```

## Limits

The scan is offline and read-only: Git, the files under the investigation
location, `.scratch/`, and `docs/`, and the local tool record. An open PR is
checked only when the host's Git tooling can reach it. The answer names the
next step; it does not run it, and it does not replace the kickoff round the
named skill holds.

Inside herdr-core the scan also lists the live sessions that work in the
project, from `hc ls` and `hc get`, and the answer says keep or close for
each. The verdict comes from Git and the files: a session at `done` has only
ended its last turn. A session gets a verdict when `whats-next` opened it, or
when one of our skills created its notes folder there: the skill's
`investigation_dir.py` call labels the session with that folder, also in a
session you opened by hand. Any other session, such as one running Matt's
`implement`, is listed with its title and status and gets no verdict.
A session in a linked worktree outside the project directory is not listed. The skill opens sessions only from Claude Code; on
Codex and OpenCode it gives the command, as it does outside herdr-core. It
closes a worker only when you say so, and never a session it did not start.
