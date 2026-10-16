# Delegation

Use the host's native subagent tools when a separate investigation or review
would help. Let Codex, Claude Code, or OpenCode manage communication,
scheduling, waiting, continuation, and retries.

Give a worker the question, relevant source revision and conditions, existing
evidence, the output it should contribute, and the path of the guidance file it
follows: [INVESTIGATE.md](INVESTIGATE.md) or [FRESH-REVIEW.md](FRESH-REVIEW.md). Carry the user's scope and
authorization into the assignment; workers reuse that authority and escalate
only work or consequential choices outside it. A recommendation is not user agreement.

When the host lists the `aantoniadis-skills:investigator` or
`aantoniadis-skills:second-reader` agent, dispatch the role through it; the
agent reads its guidance file before it starts. Otherwise dispatch a general
worker. The second-reader agent has no file-editing tools, so an assignment
that authorizes edits to the artifact goes to a general worker.

The [investigator](INVESTIGATE.md) offers tracing guidance; the
[second reader](FRESH-REVIEW.md) offers source and reader checks. Choose the
useful guidance for the question.

Integrate findings into the current artifact with their evidence and limits.
Compare conflicting results against their source conditions. If a worker
cannot answer, continue with the available evidence and state the gap.
