# whats-next

Ask it at any point. It reads the checkout and the notes and reports already
written, places you on the [workflow](workflow.md), and gives the next command
and the session to run it in. It writes nothing and starts nothing; you run
the next step.

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
3. **Answer.** Six lines: where you are with the evidence, the next skill,
   the command in your host's form with real paths, same or new session and
   why, what to carry into a fresh session, and one alternative.

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
