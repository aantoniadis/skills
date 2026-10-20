# Asking the user

Use context and existing authorization before asking. Find code and
environment facts yourself. Apply routine project conventions and state an
assumption when the user might want to correct it.

Ask when a missing preference or consequential behavior choice changes the
work: audience, deliverable, scope, cost, or intended behavior. Continue work
that does not depend on an open answer.

A **round** is one set of the open questions, at most four, each with its
recommended option first and the reason. Ask it with the host's question tool:
`AskUserQuestion` in Claude Code (when it is deferred, load it first with
`ToolSearch` query `select:AskUserQuestion`), `question` in OpenCode,
`request_user_input` in Codex when it is listed, and wait for the answers.
When the tool is missing:

- **Claude Code or OpenCode:** the session is unattended, as in `claude -p`
  or CI. Apply the recommendations and continue, and list the round as
  numbered text in the reply so the user can change a choice later.
- **Codex or another host:** a chat can lack the tool, so ask the round as
  numbered text and wait; a plain-text answer counts. When the prompt says the
  run is unattended, as with `codex exec` or CI, apply the recommendations and
  continue instead.

Work that needs an explicit answer, such as committing, publishing, or
stopping to confirm a list, waits for it in every case.

The recommendations apply when the user answers "go", names only some
choices, or the tool returns no answer, as in a non-interactive session. The
next reply then states every applied choice, supplied or defaulted, in one
line that starts with `Kickoff:` or `Checkpoint:`, so the user can correct it.

A **kickoff** is the round each skill names. Ask it first. Before it, identify
the target and look at its size, such as the diff stat, the failing test, or
the file list, so the recommendations fit it. A choice the request already
states, in any wording, is settled: "I'm new to this code" answers familiarity, "HTML" or
"text only" the deliverable, "find bugs" or "skip the bug search" the search,
"go deep", "full review", or "quick overview" the depth. Skip those questions
and ask only the open ones; when none is open, ask nothing. A small change
still gets its open questions.

A **checkpoint** settles a new choice during the work and never re-asks what
the kickoff settled. Honor a stop or redirect through the host's normal
conversation controls.

The **investigation location** holds a skill's notes, reports, and probes:
the path on an `Investigations:` line in the project's instructions, else
`.scratch/<topic>/` in the project root. `python3 <package>/skills/investigation_dir.py <topic>`
creates it and prints it; for `.scratch/` in a Git checkout it also adds
`/.scratch/` to the local exclude file, which Git never commits.

A review of the working tree leaves the investigation location out of
its scope.

For publication, use the authorization already supplied for the destination
and content. If it is missing, show the concrete draft and destination before
asking. A recommendation, silence, or a worker's answer is not permission.
For consequential decisions, distinguish explicit agreement from an authorized
autopilot policy or an assumption that remains open.

Done when the choices needed for the current work are settled or their
affected work is clearly pending, no settled question was asked again, and
the reply states the applied choices.
