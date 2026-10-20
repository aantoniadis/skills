# Evidence for every claim

Use this reference for behavior claims in explanations, plans, reports, and
diagrams. Keep the claim, its source conditions, and its evidence limits together.

## Contents

- [Identify the evidence](#identify-the-evidence)
- [Capture a local snapshot](#capture-a-local-snapshot)
- [Diagrams](#diagrams)
- [Check before delivery](#check-before-delivery)

## Identify the evidence

A behavior claim carries one of these in its sentence, list item, or table row:

- **Inspected source:** a pinned file and line supporting the claim. Identify the
  revision or retained local snapshot actually read. A docstring, comment, or
  test name describes intent; inspect controlling code to establish behavior.
- **Executed here:** an observation or measurement from this session, including
  delegated execution. Retain the command, output, source revision, configuration,
  and limits. A named probe can refer to that recorded run.
- **Recorded evidence:** a prior source inspection or run whose provenance is
  retained. Check its applicability to the current question, relevant source,
  inputs, and environment. Cite the original record and identify what was reused;
  reuse does not turn an earlier run into a new execution.
- **Documented intent:** a relevant quotation and link to the requirement,
  decision, issue, PR body, or documentation. It establishes the stated intent,
  not implementation or execution.
- **An explicit limit:** *inferred* from named evidence and reasoning,
  *proposed* behavior, *not inspected*, *unknown* with what would settle it,
  or *background* knowledge outside the repository.

A cross-reference names the claim carrying the evidence. Summaries and chat
replies can restate supported claims from the artifact without repeating every
citation, provided they add no claim or stronger conclusion. Unsupported behavior
claims need evidence or an explicit limit.

Reuse valid evidence from earlier sessions and investigators. Verify the source
identity and conditions, and inspect the decisive evidence for consequential or
conflicting conclusions. Reopen affected claims when source, scope, assumptions,
or configuration changes; an unrelated revision does not invalidate everything.
Keep original run records intact and link corrections or later results.

A negative or universal claim names the controlling invariant and the relevant
paths and configurations inspected. One search or one passing probe cannot
establish a broader guarantee.

## Capture a local snapshot

Uncommitted or non-Git code has no commit URL. Keep the inspected bytes beside
the note and cite them by relative path. Capture only the source files the
note cites; credentials and environment files such as `.env` stay out of the
copy. From the project root, with the note's
directory in `note_dir`:

```bash
cap="$note_dir/sources/$(date -u +%Y%m%dT%H%M%SZ)"; mkdir -p "$cap"
tar -cf - src/pkg/handler.py src/other.py | tar -xf - -C "$cap"
{ echo "captured $(date -u +%Y-%m-%dT%H:%M:%SZ) from $PWD"; echo "base $(git rev-parse HEAD 2>/dev/null || echo none)"; (cd "$cap" && find . -type f ! -name MANIFEST.txt -exec shasum -a 256 {} +); } > "$cap/MANIFEST.txt"
```

The copy keeps relative paths, and the manifest records capture time, base
revision, and a hash per file. Cite `sources/<capture>/src/pkg/handler.py#L17`
from the note. Add a later capture beside the first instead of replacing it.

## Diagrams

Every node and edge is a claim. Map existing behavior to its inspected source
lines. Name relevant conditions on branches and distinguish changed or removed
review steps using the appropriate head or base source. Split a flow by phase
when that helps the reader follow it.

A proposed component or transition can have no implementation yet. Label each
such map item `proposed:` and link its decision, requirement, or proposal.
Agreement and implementation are separate: an agreed future design still uses
proposed mappings until implementation evidence exists. In a mixed diagram,
existing behavior keeps source-line mappings.

Put a source map under every Mermaid fence, covering its nodes and edges:

```text
Source map:
- Existing request handler — [handler.py:17](sources/handler.py#L17).
- Queue — proposed: [durable delivery decision](#durable-delivery).
- Handler to queue — proposed: [delivery requirement](requirements.md#delivery).
```

The sentence before the fence states the takeaway and evidence kind: *source*
for inspected current behavior, *observed* with the current or original run
record, or *proposed* for candidate behavior. A mixed flow identifies its
proposed parts. Keep source provenance alongside recorded observations; neither
an observed diagram nor a proposal establishes behavior outside its evidence.

## Check before delivery

Compare consequential claims with their evidence as you write. After a material
claim change, recheck the affected source or record. After a presentation-only
edit, check that conditions, qualifications, evidence status, and links survived;
repeat the investigation only if the meaning or evidence changed.

Use a [second reader](FRESH-REVIEW.md) when useful. Name its checked scope and
limits. A self-check is not an independent review; source inspection is not a
runtime test. Correct, qualify, or remove unsupported claims.

`render_page.py --check` ([page workflow](HTML-PAGES.md)) checks these markers,
diagram maps, links, and shared tables mechanically; it cannot establish
semantic support or actual execution.

Done when consequential claims have supporting evidence or explicit limits,
reused evidence retains its provenance, and material corrections have been checked.
