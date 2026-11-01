# Delegation

Use the host's native subagent tools when a separate investigation or review
would help. Let Codex, Claude Code, or OpenCode manage communication,
scheduling, waiting, continuation, and retries.

Give a worker the question, relevant source revision and conditions, existing
evidence, the output it should contribute, and the path of the guidance file it
follows: [INVESTIGATE.md](INVESTIGATE.md) or [FRESH-REVIEW.md](FRESH-REVIEW.md). Carry the user's scope and
authorization into the assignment; workers reuse that authority and escalate
only work or consequential choices outside it. A recommendation is not user agreement.

The [investigator](INVESTIGATE.md) offers tracing guidance; the
[second reader](FRESH-REVIEW.md) offers source and reader checks. Choose the
useful guidance for the question.

Integrate findings into the current artifact with their evidence and limits.
Compare conflicting results against their source conditions. A worker that
fails, stops early, or returns no result checked nothing: start it once more,
and if it fails again, record its scope as *not run* with the reason. An empty
result never counts as nothing found. If a worker cannot answer, continue with
the available evidence and state the gap.
