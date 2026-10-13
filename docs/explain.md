# explain

Learn how a feature or code flow works before you touch it, with every claim
tied to inspected source or an observed run.

## How it works

1. **Answer and establish scope.** Start with the supported answer and decisive
   sources. A kickoff round asks the choices the prompt leaves open: familiarity,
   a note or a note with HTML, and the scope boundary; stated choices are
   applied without asking. Report tool limitations
   when they affect the answer.
2. **Trace, explain, challenge.** Follow a concrete flow through producers and
   consumers. Show decisive excerpts and use a diagram when it clarifies the
   relationships, mapping its nodes and edges to source. Challenge assumptions
   when a changed condition could change the answer. Use focused probes within
   existing authorization; a material new cost, side effect, or scope choice
   may need a checkpoint. Native delegation can help with a separate question.
3. **Keep the useful result.** A narrow answer can stay in chat. A reusable
   explanation or requested artifact gets an `understanding.md` at the project's
   investigation location, with source conditions, walkthrough, alternatives,
   evidence, and unknowns. Cite committed code at its commit; retain the relevant
   inspected files as local snapshots for uncommitted or non-Git source.
   Optional HTML presents the same findings and qualifications.
4. **Check and finish.** Compare consequential claims with their sources and
   account for each learning question. Independent reader review is optional.
   Offer follow-ups when useful, without a fixed count. Describe incidental
   defects with their evidence; draft issues when requested or useful within
   scope. Publication reuses existing authorization or needs approval of the
   concrete draft and destination.

When called as a helper for another workflow's report, return scoped findings
or update the designated section. Reuse its context and artifact.

Before delivery, `render_page.py <note.md> --check --sync-labels` checks the
note and writes the label key when it uses status tables or diagrams.
Mechanical checks do not establish that a citation supports an explanation.

Prompt shape:

```text
/aantoniadis-skills:explain <what you need to understand, and the change you have in mind if any>
```

## Continue into planning

For a visual recap, such as a component tree, a file tree, or a code-shape
diff, run HumanLayer's original `show-me` afterwards; it is user-invoked, so
this skill hands you the command and keeps ownership of the explanation and
optional HTML companion. Give the note path to our `plan-change` to plan a
change from those findings. The [combined workflow](workflow.md) continues
through spec/ticket drafting, implementation, and PR creation.

