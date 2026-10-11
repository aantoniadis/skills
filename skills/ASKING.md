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
`ToolSearch` query `select:AskUserQuestion`), `question` in OpenCode. Without
such a tool, the first reply carries only the round as numbered text and the
artifact location, asked once; the work continues after the answers, and a
plain-text answer counts.

The recommendations apply when the user answers "go", names only some
choices, or the tool returns no answer, as in a non-interactive session. The
next reply then states every applied choice, supplied or defaulted, in one
line that starts with `Kickoff:` or `Checkpoint:`, so the user can correct it.

A **kickoff** is the round each skill names. Ask it first, before any work
beyond identifying the target. A choice the request already states, in any
wording, is settled: "I'm new to this code" answers familiarity, "HTML" or
"text only" the deliverable, "find bugs" or "skip the bug search" the search,
"go deep", "full review", or "quick overview" the depth. Skip those questions
and ask only the open ones; when none is open, ask nothing. A small change
still gets its open questions.

A **checkpoint** settles a new choice during the work and never re-asks what
the kickoff settled. Honor a stop or redirect through the host's normal
conversation controls.

For routine artifact locations, use the project's `Investigations:` record,
else its convention, else `.scratch/<topic>/`.

For publication, use the authorization already supplied for the destination
and content. If it is missing, show the concrete draft and destination before
asking. A recommendation, silence, or a worker's answer is not permission.
For consequential decisions, distinguish explicit agreement from an authorized
autopilot policy or an assumption that remains open.

Done when the choices needed for the current work are settled or their
affected work is clearly pending, no settled question was asked again, and
the reply states the applied choices.
