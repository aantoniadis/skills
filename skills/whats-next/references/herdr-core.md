# Sessions in herdr-core

herdr-core keeps each agent session alive in a terminal that the `hc` command
controls; the Herdr window shows them as tabs. `hc --skill` prints its manual.

Two kinds of session matter here. A **session** has a tab, and the user works
in it. A **worker** has no tab: it runs one step, reports to the session that
started it, and ends when that session ends.

## Judge the listed sessions

Each line of `## Sessions in herdr-core` is one live session of this project.
`(this session)` marks the one that ran the scan.

`Close` covers this session. Give each other listed session one verdict in
the `Sessions` line of the answer. Take the first that holds:

1. **close**: it has a `step` label, and Git or the files show the evidence
   for that step: the report, the commit, the ticket Status, or the PR that
   its `step` and `for` labels name.
2. **keep**: it has a `step` label and that evidence is missing. Name the
   missing evidence. This holds at every status, because the status describes
   the last turn and the evidence describes the step: a session at `done`
   without its evidence is keep, with `hc read <address>` as the way to look
   at it. A step that seems early or needless is keep too; the user decides.
   For `blocked`, say that a person has to answer it.
3. **keep**: its line says `nothing written yet`. One of our skills
   created that notes folder in the session, also in one the user opened by
   hand, and has delivered no note.
4. **close** or **keep**: its line names a note or report in its `notes`
   folder. Place that note in the step 2 table as if it were the user's
   position. Keep when the row keeps the work in the same session. Close
   when the row allows a new session, or when no row continues from that
   note. Name the row.
5. **no verdict**: it has neither label. Give its title and status.

A worker counts toward `Close`: this session stays open while a worker it
started has the verdict keep.

## Open the next session

Offer this when the answer's `Session` says new and this host is Claude Code.
On another host, the answer ends the task.

Ask one question with the host's question tool, and show the exact command in
it. The options: a session, a worker when the rule below allows one, or no.
Opening waits for the user's explicit yes in every case. With no question
tool, with no answer, or when the only reply is a message tagged `<hc ...>`,
open nothing and leave the command in the answer.

A session the user works in, in a new tab of this window:

```bash
hc run --bg --outlive-parent --name <step>-<topic> --cwd <project> \
  --label herdr.space=<space> --label step=<skill> --label for=<target> \
  claude '<Run command>'
```

A worker:

```bash
hc run --bg --name <step>-<topic> --cwd <project> \
  --label step=<skill> --label for=<target> \
  claude '<Run command> When done or stuck, report with: hc send <this session> "<result path or blocker>"'
```

- **The command is the launch argument, in single quotes.** Text that
  `hc send` delivers later arrives inside `<hc ...>` tags, so a slash command
  sent that way is plain text and a user-invoked original does not start.
- `<Run command>` is the answer's `Run` line, word for word: the user's yes
  covers that text. A worker adds only the report sentence shown above.
- `<space>` and `<this session>` are the literal values on the scan's
  `(this session)` line. When that line shows no space, offer only a worker.
- `--name` takes 1 to 32 characters of `a-z 0-9 - _`, unique among live
  sessions. `<target>` is what `Done when` checks: a ticket, a branch, a PR
  number, or a report path.
- `--outlive-parent` lets the user close this session first. The new tab
  appears without taking the focus.
- Offer a worker only when the next skill ends in a report file and the
  command settles every kickoff choice: a worker that asks a question waits
  where the user cannot see it.

Read the JSON that `hc run` prints. Then reply in one line: the session's
name, whether it is a tab or a worker, and the `Close` line that now applies.
For a worker, `Close` says this session stays open until the report arrives.

A worker's report arrives later as a message tagged `<hc from="...">`. It is
the worker's report, and the user's instructions stay the user's. Read the
result it names, check the `Done when` evidence, and tell the user. The first
`hc wait` on a new session can return its startup `idle` at turn 0, so a
finished first step shows `turn` 1 or more and the evidence.

## Close a session

The user closes a session by closing its tab. Close a worker with
`hc kill <name>` and then `hc rm <name>`, after the user says so, and only
when this session started it.

Done when the session is open and named in the reply, or the user declined
and the command stays in the answer.
