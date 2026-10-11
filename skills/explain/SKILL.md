---
name: explain
description: Explains how existing code behaves for one question or feature, tracing a concrete flow to pinned source lines, with a reusable note or HTML page when selected. Use when the user asks how something works, wants a flow traced, needs onboarding to an area of a codebase, or wants to understand code before changing it. Not for deciding what to change (plan-change) or finding defects in a diff (find-bugs).
argument-hint: "<what you need to understand, and the change you have in mind if any>"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md), with every claim
bounded by its [evidence](../EVIDENCE.md).

# Explain

Build a mental model grounded in inspected code: the reader can follow a concrete flow, predict a relevant alternative, and find the code supporting that prediction. A possible future change focuses the investigation; planning starts when the user requests it. Follow the workflow below.

## Orient before tracing

Establish the learning questions, scope, reader's familiarity, and one concrete scenario from context. For registration before considering 2FA, useful questions include when an account exists, when a session authenticates it, and what each state permits. Find code facts yourself.

Hold the kickoff round from [asking](../ASKING.md) first, with the questions
the request leaves open: the reader's familiarity; the deliverable, a note or
a note with HTML (recommend HTML for broad onboarding or relationships that
benefit from visual layout, and text for a narrow question); and the scope
boundary, with a proposed starting point. Apply a choice the request states
without asking. A helper run, where another workflow owns the report, holds
no round and reuses the caller's choices.

Start with the central answer and decisive source references. Include a
small mapped diagram when it helps and the inspected lines support it. Surface
tool limitations when they affect the answer. The first delivery states the
applied choices in its `Kickoff:` line.

Resolve the repository root and revision from the source directory being inspected, which may differ from the workspace. Reuse existing notes and conversation findings, checking their revision, relevant local changes, configuration, and dependency assumptions against that source. Reopen affected claims while retaining supported findings; a new revision alone does not invalidate the whole note. Reused experiments keep their original run revision and conditions.

Before tracing, use [CODE-TOOLS.md](../CODE-TOOLS.md) to select useful capabilities and reuse local preparation. Surface a setup gap when it affects the answer; use its recovery guidance when a tool cannot run.

Start tracing once the learning questions and starting scenario are concrete enough to investigate.

## Trace, explain, and challenge

Repeat this loop as the explanation develops. Share supported partial answers during the investigation.

Trace the main flow and cite the lines you read. Use an [investigator](../INVESTIGATE.md) when a separate trace or probe would help answer a learning question. Follow [native delegation](../WORKERS.md), supplying the source conditions, settled scope, and question. Integrate findings into one walkthrough: show where one question's outcome decides another's. Keep conflicting evidence and unresolved gaps visible.

1. **Trace a concrete flow.** Follow an actor, request, or record through its producers and consumers, starting at the entry point that begins it (a request, a command, an event). Keep the frames a reader needs for orientation. Connect domain concepts to symbols, state transitions, ownership, lifetime, and observable effects. Separate phases hidden behind one feature name. Follow relevant asynchronous boundaries and alternate entry points far enough to explain who relies on the state and what they do next; causal relevance sets the boundary.
2. **Explain the connection.** Answer a learning question, then justify it with the walkthrough. Where a branch or transformation decides the outcome, show a short actual source excerpt with its input, resulting state, and consequence for the next consumer, as a fence whose info string carries the pinned link; the [page workflow](../HTML-PAGES.md) renders such a fence as a code card. Use a diagram when it makes the relationships easier to follow: a sequence for interactions, a flowchart for branching, a state diagram for lifecycle transitions, or a schema for stored data. A short call tree, pseudocode, or prose may suffice. For a view this list lacks, such as a component tree, a file tree, or a code-shape diff, load [humanlayer:show-me](../REFERENCES.md) and keep this skill's artifact and delivery scope; if resolution fails, report the limitation and continue with the views above. Map every diagram's nodes and edges to sources as [evidence](../EVIDENCE.md) says. Explain unfamiliar terms where they matter; label pseudocode and omissions. A list of symbols alone does not explain the behavior.
3. **Challenge a consequential assumption.** When a contrast could change the answer, vary one condition: repetition, interruption, or another supported path. State the prediction and why, then inspect the decisive code. Explain what supports or corrects the model. If uncertainty remains, run the smallest useful existing test, isolated reproduction, or throwaway model within existing authorization. Ask at a checkpoint only when a material cost, side effect, or scope choice is not covered by that authorization. State the question and predicted observable result first, and stop when it is answered. Tests are optional; model results do not establish integration behavior.
4. **Choose the next branch.** Ask about depth or a relevant alternative when the answer would change the investigation. Ask a focused follow-up only when it would reveal a learning gap or select useful depth. Connect it to what was just explained and reuse settled context. If the reader is confused, change the example, representation, or depth. Continue directly when the next step is evident.

## Bound each claim to its evidence

Every claim carries its pinned line, observation, quote, or label as [evidence](../EVIDENCE.md) says. State the conditions under which an answer holds and expose discrepancies between intent and implementation. Failed or unavailable probes leave named gaps.

A negative or universal claim follows the evidence rule for its controlling invariant and inspected paths: a check in one registration endpoint cannot establish that unverified users never authenticate through another route. Narrow the factual claim to the inspected boundary and name the gap; expand investigation only where the learning question requires it.

A pinned line is a commit-pinned repository URL, or the relative path with a `#L` anchor for a local snapshot, naming the file, symbol, and inspected lines. Cite the version actually inspected. A commit URL supports the committed bytes; recording "HEAD plus local changes" does not make that URL support a changed excerpt. For a retained explanation of uncommitted or non-Git code, [capture the inspected files](../EVIDENCE.md#capture-a-local-snapshot) beside the note and link them relative to it, such as `sources/<capture>/src/handler.py#L17`. Keep prior captures when refreshing affected findings. For a narrow chat answer, identify the local file and current source conditions; retain a snapshot if the answer needs reuse.

## Maintain the explanation

For a reusable explanation or requested artifact, keep one scope-specific `understanding.md` at the routine location from [asking](../ASKING.md). A narrow chat answer can stand on its own evidence. For a new note, fill [understanding-template.md](references/understanding-template.md), adapting its sections to the learning questions and removing unused prompts. Before delivering, run `python3 <package>/skills/render_page.py <note.md> --check --sync-labels --markdown-only` for text, and without `--markdown-only` for HTML; it checks the note and writes the label key when the note uses status tables or diagrams. Organize it around the current learning questions. Update affected sections as the conversation develops, preserving still-valid findings outside the follow-up's scope. Put useful investigation chronology, review resolutions, and presentation history in an existing log or nearby `review.md`.

Include what the reader needs to reuse the explanation:

- Learning questions, explored boundary, and any future change mentioned as context.
- Answers and a concrete walkthrough linking concepts, state, ownership, dependencies, and effects to decisive source references.
- Relevant alternatives, their predictions, and supporting or correcting evidence.
- Inspected revision, local modifications, configuration/dependency assumptions, and experiment provenance, rerun commands, results, and limits.
- Unknowns and intent/behavior discrepancies, tool limitations, and worthwhile setup recommendations. Keep possible changes as questions or hypotheses separate from today's behavior.

When HTML was chosen, produce a self-contained `understanding.html` beside the note: read and apply the [shared page workflow](../HTML-PAGES.md) and [reading-page guidance](references/reading-page.md), choosing the composition for the learning questions. The Markdown is the source of findings for both the page and the planning handoff. Keep material findings and qualifications in text, including alternatives exposed by interactions. Keep questions in the conversation; the page has no agent connection unless the environment provides one.

When independent review is requested or consequential onboarding warrants its cost, read [reader-check.md](references/reader-check.md). This optional reader check tests whether the second reader can predict a scoped alternative before consulting source; it adds to the source check of [evidence](../EVIDENCE.md), which can be done by the author or a second reader.

## Finish or return findings

Before delivering, check that:

- Each learning question has an evidence-backed answer, or is explicitly unresolved with the blocking gap and next useful check. For multiple questions, compare the Questions answered rows with the user's questions; for one, check the opening. Label partial understanding accordingly.
- The explanation connects the concrete flow, relevant alternatives, and decisive code; a reader can trace why the predicted outcome follows.
- The note and any companion presented in this delivery agree on findings, evidence status, and limitations. A deferred HTML update is recorded explicitly.
- Every claim carries its evidence, every diagram element is mapped, the answers have been compared with their sources, and material edits retain their evidence limits.

State the central answer and link any delivered artifacts. Offer follow-up questions when they identify useful next work, with how each could be settled. Use as many as help, including none when the question is settled. A follow-up reuses supported findings and traces only the new question, with native delegation when useful.

When another workflow asked for this trace and owns the report, return the scoped answer and evidence for integration, or update only its designated section when asked. Reuse its question, pinned source conditions, and deliverable instead of starting another note.

When an alternative suggests a defect, describe its trigger, consequence, and evidence status. Draft an issue when requested or useful within the caller's scope, retaining the sequence and source trail. Follow [publication guidance](../ASKING.md): use existing authorization for that destination and content, or show the draft and ask when it is missing. A question about code does not authorize feature implementation or publication.

If this exploration fills a gap in a plan, return the scoped findings and flag evidence that challenges an agreement for the planning workflow to resolve. Reuse the plan's context rather than restarting its interview. When a possible change was mentioned, offer the planning handoff if it would help. When the user chooses it, give them the command that starts [plan-change](../plan-change/SKILL.md) with the note, for example `/aantoniadis-skills:plan-change Plan <change>. Reuse the note at <note path>.` (`$` instead of `/` in Codex), or the start of their chosen workflow. Keep the inspected conditions in the note so the planning run can recheck only what changed.
