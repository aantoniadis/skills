# Renderer reference

Read this from the [shared page workflow](HTML-PAGES.md) when a render or
`--check` run prints a message you must act on, when a custom page needs its
fingerprint, or when a diagram needs a backend. Authoring guidance stays in
HTML-PAGES.md.

## Contents

- [Source fingerprint and custom pages](#source-fingerprint-and-custom-pages)
- [Code peek](#code-peek)
- [What --check refuses](#what---check-refuses)
- [Optional diagram renderer](#optional-diagram-renderer)

## Source fingerprint and custom pages

The renderer stores a `source-fingerprint` meta element derived from the
Markdown body and front matter, excluding the generated label key. The checker
requires that fingerprint to match the current source. Regenerate an older
companion after content changes or when it lacks this element. A fingerprint
detects stale source; it does not prove prose agreement or actual execution.

For a requested custom composition, reconcile its content with the Markdown
first. Then obtain the fingerprint with the shared helper:

```sh
python3 -c 'import runpy, sys; from pathlib import Path; page = runpy.run_path(sys.argv[1]); print(page["source_fingerprint"](Path(sys.argv[2]).read_text()))' <package>/skills/render_page.py <note.md>
```

Store the returned value in `<meta name="source-fingerprint" content="…">`
in the HTML head. Preserve it during layout-only changes. Refresh it only after
reconciling changed content, then run the normal check; the checker never stamps
or rewrites HTML. Custom composition still needs the meaning review below.

## Code peek

A link to a pinned GitHub line (`/blob/<full SHA>/path#L10-L24`) opens a
code peek on the page: the cited file, embedded whole and highlighted by the
bundled highlight.js. The link stays the GitHub link, and that link remains
the citation. A peek of a pinned link shows committed bytes, never
working-tree edits. Cite a saved local snapshot for changed or non-Git source,
following the calling skill's source-identity guidance. A relative link to a
file beside the note, such as a probe script, its output, or a saved snapshot,
opens the same peek with the file as it is on disk, with buttons that copy its
path and its code and no GitHub link; a `#L10-L24` fragment marks the cited
lines. Links to `.md` and `.html` pages, anchors, and files outside the note's
directory stay plain links. A fence with a language draws as highlighted rows
on the page, numbered from the cited line when its `url` carries one; a `diff`
fence keeps its split table.
The renderer reads the commit from a local checkout: the git
repository that contains the note, or `--repo <checkout>` when the note is
elsewhere. When the front matter gives `base` and `head`, a link to either
commit opens the file's diff. Front matter is a leading block between `---`
lines in which every non-blank line is `key: value`; any other leading `---`
is a thematic break. When the checkout has a git repository and `base` or
`head` does not resolve to a commit in it, rendering stops with
`Front matter <key> does not resolve to a commit in <checkout>: <value>`.
For each link it leaves without a code peek, the
renderer prints `No code peek for <href>: <reason>`, with the reason
`commit not in the local clone`, `binary, non-UTF-8, or over 20,000 lines`, or
`no git repository to read`. Record those links in the review record. A cited
file that is missing at its commit stops rendering with
`Cited file does not exist at its commit: <href> (Markdown line <n>)`.

## What --check refuses

`--check` takes the same `--repo <checkout>` as rendering. It refuses front
matter with an unfilled `{{…}}` prompt, a code peek for a link that the
Markdown lacks, a mismatch between the links marked `data-peek` and the links
that have peek data, embedded code that differs from git or from the file
beside the note, an embedded highlighter that differs from the vendored
highlight.js, and malformed peek data. It also refuses peek data that contradicts what it can derive without
git: each link's commit, path, and lines; each file key as a full commit SHA
and path; each diff, recomputed from its two embedded texts; and, when the
front matter gives `base` and `head`, a missing diff for a link at either
commit whose two embedded texts differ. When no checkout is found or it lacks
a file's commit, `--check` cannot compare that file with git: it prints
`Embedded code not compared with git (<reason>): <commit>:<path>`, with the
reason `no git repository to read` or `commit not in the local clone`, and
does not fail for it. Record those files in the review record too.

## Optional diagram renderer

By default the renderer uses Beautiful Mermaid when its pinned package is
installed and renders a probe diagram. Otherwise the default uses the Mermaid CLI (`mmdc`, or
`npx @mermaid-js/mermaid-cli` once cached; a cached `npx` package stops
resolving when the registry publishes a newer version, until
`npx @mermaid-js/mermaid-cli --version` installs it again). To select a backend,
pass `--diagram-renderer beautiful-mermaid` or `--diagram-renderer mermaid`. For
an existing page, reuse the backend named in its review record unless the user
requests a change or the diagram syntax requires another one. Record the
chosen backend and any change or fallback in that record.

Beautiful Mermaid remains an optional dependency. When it is needed but missing,
follow [tool setup and recovery](CODE-TOOLS.md), reusing any
existing installation authorization. Its pinned install command is
`npm ci --prefix skills/diagram-renderer`. Resolve this path from the package
location when using installed skills. This backend uses Node.js to produce
inline SVG; the delivered page needs neither Node nor a network connection.
When `--diagram-renderer beautiful-mermaid` selects it, a missing package or a
render error stops generation. By default, a diagram that Beautiful Mermaid
rejects goes to the Mermaid CLI.

When no backend renders a diagram, the renderer prints `Diagram N left as
source` with the reason and an install command, and keeps the fence as labeled
source. Record the backends tried in the review record. In a PR review, also
put a line containing `diagram renderer unavailable` in `report.md` under
`## Evidence and record`, which `render_page.py --check --review` reads; it
refuses a page with a diagram left as source when that line is absent.

Beautiful Mermaid supports a subset of Mermaid syntax, including sequence,
state, and flow diagrams. Termination-cross arrows are rejected because
this backend renders them as ordinary arrows. For every diagram, compare the
rendered nodes, edges, labels, and conditions with the source map under
[EVIDENCE.md](EVIDENCE.md), even when generation succeeds. Do not simplify a
behavioral condition merely to fit the renderer; use `--diagram-renderer mermaid`
when necessary.
