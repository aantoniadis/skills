"""Check rendering boundaries with python3 tests/test_reading_page.py."""
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import sys
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reading_page", ROOT / "skills/render_page.py")
page = importlib.util.module_from_spec(spec)
spec.loader.exec_module(page)


def rejected(action, message):
    try:
        action()
    except ValueError as error:
        assert message in str(error), error
    else:
        raise AssertionError("Expected rejection: " + message)


with tempfile.TemporaryDirectory(prefix="reading page ") as directory:
    root = Path(directory)
    note = root / "sample note.md"
    source = '''# Reading <source> safely

Fixture at a fixed revision. [Markdown](sample%20note.md). [Source][origin].

> **Source inspected; not executed.** Preserve that limit.

1. **Inspect parsing.** [Follow the result](#result).
2. **Inspect escaping.** Keep source text intact.

## Result

> **Proposed behavior.** No agreement is recorded by rendering this page.

<script>alert("not executable")</script>

```python
## This is a comment inside code, not a section
\tprint("<script>& \\"text\\"</script>")
```

### Source details

[Jump to details](#source-details). [Remote source](https://example.com/source).

| Value | Meaning |
| --- | --- |
| `<node>` | Literal code |

[origin]: https://example.com/original
'''
    note.write_text(source)
    with patch("subprocess.Popen", side_effect=AssertionError("Renderer started a process")):
        html = page.render(source, note.name, "auto")  # auto probes a diagram backend only for a Mermaid fence
        page.check(source, html, note)
    soup = page.parse(html)
    assert len(soup.select("main > section")) == 2
    scripts = soup.find_all("script")  # the template script, and the peek that highlights the python fence
    assert len(scripts) == 3 and soup.select_one("body > script#peek-data") and soup.select_one("body > script.peek-script")
    assert soup.find("pre").get_text() == page.parse(page.MARKDOWN.render(source)).pre.get_text()
    assert soup.select_one("#source-details")
    assert len(soup.select(".reading-route > li")) == 2
    assert soup.find("a", href="https://example.com/original").get_text() == "Source"
    # Mechanical checks cannot distinguish changed evidence claims. The workflow
    # requires a separate meaning review even when this check passes.
    changed = source.replace("not executed", "executed")
    rejected(lambda: page.check(changed, html, note), "source fingerprint")
    page.check(changed, page.render(changed, note.name), note)
    rejected(lambda: page.check(source, html.replace('print(', 'print( '), note), "Displayed code differs")
    rejected(lambda: page.check(source, html.replace('id="result"', 'id="overview"'), note), "Duplicate IDs")
    rejected(lambda: page.check(source, html.replace('href="#result"', 'href="#absent"'), note), "Source links differ")
    broken = source.replace('](#result)', '](#absent)')
    rejected(lambda: page.check(broken, page.render(broken, note.name), note), "Missing fragment")
    rejected(lambda: page.check(source, html.replace('https://example.com/original', 'https://example.com/other'), note), "Source links differ")
    note.unlink()
    rejected(lambda: page.check(source, html, note), "Missing local file")
    note.write_text(source)
    plain = source.replace("> **Proposed behavior.**", "**Proposed behavior.**")
    plain_html = page.render(plain, note.name)
    page.check(plain, plain_html, note)
    assert not page.parse(plain_html).select_one("#result details")
    rejected(lambda: page.check(source, html.replace('</head>', '<link rel="stylesheet" href="https://example.com/style.css"></head>'), note), "self-contained")
    # An authored page need not use the renderer's sections, heading schema,
    # class names, code order, or link order. Diagram labels may repeat prose.
    custom_source = '''# Flexible composition

Preparation precedes transmission. `prepare()` returns a request.

## Evidence

[First](https://example.com/first). [Second](https://example.com/second).

```python
prepare()
```

```python
send()
```
'''
    custom_html = '''<!doctype html><html lang="en"><title>Flexible composition</title>
<main><article><h1>Flexible composition</h1><p>Preparation precedes transmission.</p>
<svg role="img" aria-label="Preparation precedes transmission" viewBox="0 0 200 80">
<defs><marker id="arrow"><path d="M0 0 L5 5 L0 10"/></marker></defs>
<path d="M0 0 L80 0" marker-end="url(#arrow)"/>
<text x="0" y="40">Preparation precedes transmission.</text></svg>
<h2>Evidence</h2><a href="https://example.com/second">Second</a>
<pre tabindex="0"><code>send()
</code></pre><p><code>prepare()</code> returns a request.</p>
<a href="https://example.com/first">First</a><pre tabindex="0"><code>prepare()
</code></pre><p>Start with <code>prepare()</code>.</p>
</article></main></html>'''
    custom_html = custom_html.replace('<title>', f'<meta name="source-fingerprint" content="{page.source_fingerprint(custom_source)}"><title>')
    with patch.object(page, "render", side_effect=AssertionError("Checker invoked renderer")):
        page.check(custom_source, custom_html, note)
    page.check(custom_source, custom_html.replace('aria-label="Preparation precedes transmission"', 'aria-label="Illustration of url(example) syntax"'), note)
    rejected(lambda: page.check(custom_source, custom_html.replace('send()', 'send(1)'), note), "Displayed code differs")
    rejected(lambda: page.check(custom_source, custom_html.replace('https://example.com/first', 'https://example.com/other'), note), "Source links differ")
    rejected(lambda: page.check(custom_source, custom_html.replace('</main>', '<a href="https://example.com/new">New source</a></main>'), note), "Add the source link")
    rejected(lambda: page.check(custom_source, custom_html.replace('url(#arrow)', 'url(https://example.com/arrow.svg)'), note), "CSS URLs")
    rejected(lambda: page.check(custom_source, custom_html.replace('</svg>', '<use href="https://example.com/arrow.svg"/></svg>'), note), "SVG assets")
    page.check(custom_source, custom_html.replace('</svg>', '<a xlink:href="https://example.com/first"><text>First</text></a></svg>'), note)
    rejected(lambda: page.check(custom_source, custom_html.replace('</svg>', '<a xlink:href="#missing-target"><text>Source</text></a></svg>'), note), "Missing fragment")
    rejected(lambda: page.check(custom_source, custom_html.replace('</svg>', '<a xlink:href="https://example.com/new"><text>Source</text></a></svg>'), note), "Add the source link")
    rejected(lambda: page.check(custom_source, custom_html.replace('<article>', '<article style="background:url(https://example.com/bg.png)">'), note), "CSS URLs")
    # Author headings retain their anchors when they resemble generated IDs.
    headings = '# Title\n\n[Section](#overview).\n\n## Overview\n\nPlain text.\n\n### Overview heading\n\nMore detail.\n'
    heading_html = page.render(headings, note.name)
    page.check(headings, heading_html, note)
    heading_soup = page.parse(heading_html)
    assert heading_soup.select_one('#overview > h2').get_text() == 'Overview'
    assert heading_soup.select_one('h3#overview-heading')
    # An explicit filename can still refer to this same companion, including
    # while it is being rendered for the first time.
    local_source = '# Local links\n\n[Jump](sample%20note.html#result).\n\n## Result\n\nVisible answer.\n'
    local_html = page.render(local_source, note.name)
    page.check(local_source, local_html, note)
    broken_local = local_source.replace('#result', '#missing')
    rejected(lambda: page.check(broken_local, page.render(broken_local, note.name), note), 'Missing fragment')
print("Reading-page checks passed: flexible composition, code/link preservation, escaping, IDs, local assets, and renderer-independent checking. Prose meaning requires agent review.")

# Mermaid fences: id prefixing is pure; rendering depends on the CLI and falls back to labeled source.
svg = '<svg id="diagram-1"><style>#diagram-1 .a{fill:red}#actor0{x:1}</style><marker id="arrowhead"/><path marker-end="url(#arrowhead)" id="actor0"/><use href="#arrowhead"/></svg>'
fixed = page.prefix_svg_ids(svg, "diagram-1")
assert 'id="diagram-1-arrowhead"' in fixed and 'url(#diagram-1-arrowhead)' in fixed and 'href="#diagram-1-arrowhead"' in fixed
assert 'id="diagram-1-actor0"' in fixed and '#diagram-1-actor0{x:1}' in fixed and '#diagram-1 .a' in fixed
with tempfile.TemporaryDirectory(prefix="reading page ") as directory:
    note = Path(directory) / "flow.md"
    diagram_source = """# Flow

Fixture. [Markdown](flow.md).

## Sequence

The request reaches the store before the event. Observed case.

```mermaid
sequenceDiagram
    A->>B: reserve
    B-->>A: ok
```

Source map:
- A → B reserve — [flow.md:1](flow.md#L1)
- B → A ok — [flow.md:2](flow.md#L2)

```mermaid
sequenceDiagram
    A->>B: release
```

- A → B release — [flow.md:3](flow.md#L3)
"""
    note.write_text(diagram_source)
    html = page.render(diagram_source, note.name, "mermaid")
    page.check(diagram_source, html, note)
    # A diagram is a set of claims: every fence needs a source map with a pinned line per item (EVIDENCE.md).
    unmapped = diagram_source.replace("\n- A → B release — [flow.md:3](flow.md#L3)\n", "\n")
    rejected(lambda: page.check_diagrams(unmapped, note), "no source map")
    rejected(lambda: page.check_diagrams(diagram_source.replace("(flow.md#L3)", "(flow.md)"), note), "lacks a pinned line")
    rejected(lambda: page.check_diagrams(diagram_source.replace("(flow.md#L3)", "(absent.md#L3)"), note), "missing local file")
    rejected(lambda: page.check_diagrams(diagram_source.replace("- B → A ok — [flow.md:2](flow.md#L2)\n", ""), note), "map every node and edge")
    page.check_diagrams(diagram_source.replace("    A->>B: release", "    participant A\n    Note over A: cached\n    A->>B: release"), note)
    prose = subprocess.run([sys.executable, str(page.__file__), str(note), "--check", "--sync-labels"], capture_output=True, text=True)
    assert prose.returncode == 0 and "has no page" in prose.stdout, prose
    note.write_text(unmapped)
    prose = subprocess.run([sys.executable, str(page.__file__), str(note), "--check"], capture_output=True, text=True)
    assert prose.returncode == 1 and "no source map" in prose.stderr, prose
    note.write_text(diagram_source)
    soup = page.parse(html)
    if page.mermaid_command():
        figures = soup.select("figure.diagram")
        assert len(figures) == 2 and all(f.svg and f.details.pre.code for f in figures), "diagrams render to inline SVG with their source kept"
        assert soup.select_one("#diagram-1") and soup.select_one("#diagram-2")
    else:
        assert len(soup.select("pre.mermaid-source")) == 2, "without the CLI, fences stay as labeled source"
    with patch.object(page, "mermaid_command", return_value=None):
        fallback = page.render(diagram_source, note.name, "mermaid")
        page.check(diagram_source, fallback, note)
        assert len(page.parse(fallback).select("pre.mermaid-source")) == 2
    with patch.object(page, "mermaid_svg", side_effect=lambda source, identifier: f'<svg id="{identifier}" role="img" aria-label="Fixture diagram"/>'):
        illustrated = page.render(diagram_source, note.name, "mermaid")
        page.check(diagram_source, illustrated, note)
        first = page.parse(illustrated).select_one("figure.diagram")
        assert first.get("tabindex") == "0" and first.details.ul.a["href"] == "flow.md#L1"
        assert first.details.pre.code.get_text().startswith("sequenceDiagram")
print("Reading page: diagrams passed")

# Report components: attention cards with chips, code cards with a pinned link, nested navigation.
components = """# Guide

Fixture. [Markdown](g.md).

**Bottom line:** one rule for CORS and CSRF widens the bound to every subdomain; decide whether that is wanted.

## What the change does

The change adds a podium mode and one origin rule for a reader new to the PR ([g.md:1](g.md#L1)).

## What to look at

1. **Podium leaderboards** · *read lightly* · *read at the line* — the new top-3 mode. Correct; one extra request, deliberate ([g.md:1](g.md#L1)).
2. **Origins** · *you decide* · *not read* — one rule for CORS and CSRF. Widens to every subdomain.
   Look at: [g.md:1](g.md#L1), the rule, beside the old allowlist ([g.md:1](g.md#L1)). Settle: is every subdomain inside the bound?

## The parts

### Podium leaderboards: three rows

**Before.** paging. **After.** three rows.

```ts url="https://example.com/o/r/blob/abc123/backend/src/config/allowedOrigins.ts#L20-L24"
export function isAllowedOrigin(o) { return o.endsWith(domain) }
```

```diff url="https://example.com/o/r/blob/abc123/backend/src/server.ts#L230"
- allowlist
+ isAllowedOrigin
```

### Second part: other

Text.
"""
with tempfile.TemporaryDirectory(prefix="reading page ") as directory:
    note = Path(directory) / "g.md"
    note.write_text(components)
    html = page.render(components, note.name)
    page.check(components, html, note)
    # Every claim block carries evidence (EVIDENCE.md): a pinned line, an observation, a quote, or a label.
    claims = """# Note

Fixture. [Markdown](g.md). The title section is a summary and is not checked here at all.

## Answers

The handler reads the body before the dependencies are resolved, then validates ([g.md:1](g.md#L1)).
A parse error becomes a 400 response, and the endpoint never runs. Observed with `probe.py`.

- Middleware raises go straight to the server error handler, so the 403 handler never runs.
- Action: add a test for the middleware path before changing it.

| Scenario | Result |
| --- | --- |
| chunked body, no length header | observed: 413 |

> "any https origin" — the requirement as the issue states it.

## Worth asking next

1. Does the form branch close the file stack on a failed parse, and what would show it?
"""
    gaps = page.claim_gaps(claims)
    assert len(gaps) == 1 and gaps[0][0] == 10 and gaps[0][1].startswith("- Middleware raises go straight"), gaps
    rejected(lambda: page.check_claims(claims), "without evidence")
    page.check_claims(claims.replace("so the 403 handler never runs.", "so the 403 handler never runs (inferred from g.md:1)."))
    assert page.claim_gaps(claims.replace("| observed: 413 |", "| 413 |"))[-1][1].startswith("| chunked body, no length header | 413 |")
    soup = page.parse(html)
    chips = soup.select("ol.attention > li .chip")
    assert [c.get_text() for c in chips] == ["read lightly", "read at the line", "you decide", "not read"]
    assert [c["class"][1] for c in chips] == ["chip-skim", "chip-source", "chip-decide", "chip-not-inspected"]
    assert [c.figcaption.a.get_text() for c in soup.select("figure.code-card")] == ["allowedOrigins.ts:20-24", "server.ts:230"]
    assert [s.get_text() for s in soup.select("code.language-diff .add")] == ["+ isAllowedOrigin"] and soup.select_one("code.language-diff .del") is not None
    split = soup.select_one("figure.code-card table.diff-split")
    assert split is not None and [c.get_text() for c in split.select("tbody td")] == [" allowlist", " isAllowedOrigin"]
    assert [c["class"] for c in split.select("tbody td")] == [["del"], ["add"]]
    assert split.parent.get("tabindex") == "0" and split.find_next("details").summary.get_text() == "Unified diff"
    assert page.split_rows("ctx\n-a\n-b\n+c\n ctx2") == [("ctx", "ctx", False), ("a", "c", True), ("b", None, True), ("ctx2", "ctx2", False)]
    assert [a.get_text() for a in soup.select("aside nav ul a")] == ["Podium leaderboards: three rows", "Second part: other"]
    rejected(lambda: page.check(components, html.replace("abc123/backend/src/server.ts", "abc123/backend/src/other.ts"), note), "Source links differ")
    # Attention items: one action phrase and one evidence phrase before the dash; an actionable item carries its reading
    # route; a read-lightly item rests on we-ran-it or read-at-the-line evidence (report-format.md). The codes behind the
    # phrases are internal and not accepted.
    assert page.attention_gaps(components) == []
    assert page.attention_gaps(components.replace("*you decide* · *not read*", "*you decide*"))[0][0] == 2
    assert "you decide" in page.attention_gaps(components.replace("*you decide* · *not read*", "*not read*"))[0][1]
    assert page.attention_gaps(components.replace("*you decide* · *not read*", "*Decide* · *not inspected*"))[0][0] == 2
    assert "Settle" in page.attention_gaps(components.replace("Settle: is every", "Is every"))[0][1]
    assert page.attention_gaps(components.replace("*read lightly* · *read at the line*", "*read lightly* · *reasoned, not run*"))[0][0] == 1
    assert page.attention_gaps(components.replace("*read lightly* · *read at the line*", "*no action* · *reasoned, not run*")) == []
    rejected(lambda: page.check_attention(components.replace("*you decide* · *not read*", "*you decide*")), "what to do")
    lazy = components.replace("\n   Look at: [g.md:1]", "\nLook at: [g.md:1]")  # a Markdown lazy continuation is still the item
    assert page.attention_gaps(lazy) == [], page.attention_gaps(lazy)
    dashed = components.replace("**Origins** · *you decide*", "**Origins — one rule** · *you decide*")  # an em dash inside the part name
    assert page.attention_gaps(dashed) == [], page.attention_gaps(dashed)
    assert page.claim_gaps("# N\n\n## Answers\n\n- Next the queue drains before the flush completes here.\n")[0][0] == 5
    # The opening of a review report: a bottom line under the title, then 'What the change does' (report-format.md).
    opening = "# G\n\n**Bottom line:** one rule.\n\n## What the change does\n\nThe change adds a mode.\n\n## What to look at\n\n1. x\n"
    assert page.opening_gaps(opening) == []
    assert page.opening_gaps(opening.replace("## What the change does\n\nThe change adds a mode.\n\n", "")) == ["no 'What the change does' section (an acceptance report: 'What was asked') before the items"]
    assert page.opening_gaps(opening.replace("## What to look at", "## Answers")) == []  # not a review report
    rejected(lambda: page.check_opening(opening.replace("**Bottom line:** one rule.\n\n", "")), "Bottom line")
    rejected(lambda: page.check(components.replace("*you decide* · *not read*", "*you decide*"), html, note), "what to do")
    # Names, not bookkeeping IDs: a bare F2, D1, or H3 in prose is rejected; code, link targets, and URLs are not prose.
    assert page.name_gaps(components) == []
    named = "# N\n\n## Answers\n\nThe bucket is `S3`; see [line 2](g.md#L2) and https://x.test/P9.\n"
    assert page.name_gaps(named) == [], page.name_gaps(named)
    assert [gap[1] for gap in page.name_gaps(named + "\nD1 is agreed, and see F2.\n")] == ["D1", "F2"]
    # Cloudflare R2, AWS S3, and Backblaze B2 are product names, not IDs; other ID-shaped names go in code spans.
    products = "# N\n\n## Answers\n\nThe probe uploaded the file to R2, then to AWS S3 and Backblaze B2.\n"
    assert page.name_gaps(products) == [], page.name_gaps(products)
    assert [gap[1] for gap in page.name_gaps(products + "\nThe copy in F2 differs.\n")] == ["F2"]
    rejected(lambda: page.check_names(named + "\nThe only suspicion is H1.\n"), "name")
    # The skills' own process words are the log's vocabulary; domain uses of "provisional" or "lower-tier" are prose.
    assert [gap[1] for gap in page.name_gaps("# Review (provisional)\n\nThe fresh review and a lower-tier review ran.\n")] == [
        "(provisional)", "fresh review", "lower-tier review"]
    assert page.name_gaps("# Orders\n\nA provisional order for lower-tier customers.\n") == []
    # The short report shape (report-format.md): bottom line, what the change does, items, questions, collapsed record.
    short = """# count_items now counts distinct values

**Bottom line:** the change contradicts the stated intent ([PR.md:1](PR.md#L1)); decide whether distinct counting is wanted.

## What the change does

The PR says duplicates count ([PR.md:1](PR.md#L1): "count_items should keep counting every input entry"). The new line counts distinct values ([counter.py:2](counter.py#L2)).

## What to look at

1. **Duplicates no longer count** — *you decide* · *we ran it*
   We ran `count_items([1, 1, 2])`: 3 before, 2 after.
   Look at: [counter.py:2](counter.py#L2), beside [PR.md:1](PR.md#L1).
   Settle: was deduplication intended?
2. **Names unchanged** — *no action* · *read at the line*
   The signature is the same ([counter.py:1](counter.py#L1)).

## Questions for the author

- Was counting distinct values intended ([counter.py:2](counter.py#L2))?

## Evidence and record

### Provenance

- Head `4ac1e4e`, read at [counter.py:1](counter.py#L1).
"""
    assert page.attention_gaps(short) == [], page.attention_gaps(short)
    assert page.opening_gaps(short) == []
    assert page.opening_gaps(short.replace("**Bottom line:** the change", "The change")) == ["no '**Bottom line:**' paragraph under the title"]
    assert "Settle" in page.attention_gaps(short.replace("   Settle: was deduplication intended?\n", ""))[0][1]
    assert page.attention_gaps(short.replace("*no action* · *read at the line*", "*read lightly* · *not read*"))[0][0] == 2
    rendered = page.parse(page.render(short, "g.md"))
    assert [c.get_text() for c in rendered.select("ol.attention > li .chip")] == ["you decide", "we ran it", "no action", "read at the line"]
    record = rendered.select_one("section#evidence-and-record details")
    assert record is not None and record.summary.get_text() == "Show the evidence and record" and record.find("h3")
    note = Path(directory) / "short.md"
    note.write_text(short)
    (Path(directory) / "PR.md").write_text("count_items should keep counting every input entry\n")
    (Path(directory) / "counter.py").write_text("def count_items(items):\n    return len(set(items))\n")
    page.check(short, page.render(short, note.name), note)
print("Reading page: report components passed")
