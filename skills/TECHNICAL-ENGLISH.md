# Clear technical English

Use STE principles for prose in this package's skill instructions and outputs:
conversation, questions, Markdown notes, HTML text and diagram labels, specs,
tickets, and PR descriptions. Carry this guide into helper calls and handoffs
that produce those outputs. Honor an explicit request for another language or
style while preserving technical meaning.

This guide adapts [ASD-STE100 principles](https://www.asd-ste100.org/STE_faq.html)
for software work. It does not establish compliance with the full standard.

## Write for understanding

- Use short sentences with one main idea. Keep related sentences in a coherent
  paragraph; use numbered steps when order matters.
- Name the actor and action. Prefer active voice. If the actor is unknown,
  state that uncertainty instead of inventing one.
- Make conditions and consequences explicit. Put a condition first when the
  reader needs it to interpret the result. Keep causal connections when splitting
  a long sentence.
- Use familiar, literal words. Use one term for one concept and follow the
  project's glossary. Explain unfamiliar technical terms at first use; keep the
  terms that readers need to find the code.
- Preserve exact identifiers, commands, code, quotations, and source references.
  Simplify the surrounding explanation. Keep pseudocode distinct from source.
- Keep the explanation shorter than the evidence it cites. Lead with the
  answer; show the decisive excerpt; leave out what the reader gets from the
  cited code. A section earns its length by changing what the reader does next.
- Preserve conditions, exceptions, timing, quantities, and the strength of each
  claim. Keep obligations, possibilities, observations, and predictions distinct.
  Keep proposed behavior separate from agreed behavior.

For example, in a scenario where session issuance already records a success
event:

> Setting `session.authenticated` to `False` blocks dashboard access. The
> `login_success` event remains. The notification worker still selects the
> account for a login notification.

## Write for a reader who was not there

The reader saw none of the work: not the task list, the probes, the workers,
or the log. Every name, label, and status they meet is plain, or explained
where they meet it.

- Refer to each finding, decision, question, probe, scenario, and hypothesis
  by a short name that says what it is, such as *duplicates no longer
  counted*. Numbered IDs such as F2, D1, H3, W1, or P3 belong in the log and
  the evidence record; a cross-reference names or links its target. Code
  identifiers stay exact, as above. A product name with the same shape goes
  in a code span, such as `T5` for the model; Cloudflare R2, AWS S3, and
  Backblaze B2 stay plain.
- Describe the subject, not the skill's own workflow: the names of its passes
  and roles, its milestones, and its run state belong in the log. The
  deliverable says what was checked in plain words: "we ran it", "a second
  reader compared each claim with its line". Work done during the review is
  "we", whoever in the review did it.
- Write a status or a classification as a plain phrase, or give its meaning
  where the reader first meets it. A skill's fixed phrases, such as the review
  report's *you decide* and *we ran it*, are plain already.

## Check the meaning before delivery

Compare the explanation with its source evidence or decision record. Can the
reader identify who acts, under which conditions, and what happens next? Does
the wording retain every qualification that changes the conclusion? Resolve
unclear terms and references. Treat sentence length as a readability aid;
retain the detail needed to explain the behavior correctly.

## When full ASD-STE100 compliance is requested

Consult the [official standard](https://asd-ste100.org/STE_downloads.html) for
the requested issue, or the current issue if none is specified. Review the
applicable writing rules, dictionary meanings, and use of technical terms.
Identify the issue and scope reviewed. Claim compliance only when that review
supports it; state any unchecked requirements if a full review is unavailable.
Continue with usable prose and its stated limits. Clear wording or an automated
checker alone does not establish compliance.
