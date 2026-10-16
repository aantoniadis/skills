"""Render or check a Markdown reading page. Run with --help for usage."""
import argparse
import base64
import binascii
import json
from collections import Counter
import hashlib
from html import escape
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit, quote

from bs4 import BeautifulSoup, NavigableString
from markdown_it import MarkdownIt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reader_text import reader_gaps  # noqa: E402
import source_peek  # noqa: E402

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "page-template.html"
LABELS = json.loads((ROOT / "report-labels.json").read_text())
LABEL_KEY = "Status and label key"
MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable("table")
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
FRONT_LINE = re.compile(r"^[A-Za-z_][\w.-]*:(?:\s.*)?$")
PROMPT = re.compile(r"\{\{[^{}]+\}\}")


def front_matter(source):
    """The leading `---` block when every non-blank line in it is `key: value`, else None (a thematic break)."""
    match = FRONT_MATTER.match(source)
    lines = [line for line in match[1].splitlines() if line.strip()] if match else []
    return match if lines and all(FRONT_LINE.match(line) for line in lines) else None


def split_front_matter(source):
    """Front matter `key: value` lines as a dict, and the source with those lines blanked so line numbers hold.
    ponytail: flat keys only, which is all report front matter uses; a YAML parser if nesting is ever needed."""
    match = front_matter(source)
    if not match:
        return {}, source
    meta = {}
    for line in match[1].splitlines():
        key, colon, value = line.partition(":")
        if colon:
            meta[key.strip()] = value.strip().strip("\"'")
    return meta, "\n" * match[0].count("\n") + source[match.end():]


def with_front_matter(original, body):
    """Put the original front matter back over the blank lines split_front_matter left."""
    match = front_matter(original)
    return original[:match.end()] + body[match[0].count("\n"):] if match else body


class Failures(ValueError):
    """Every mechanical failure one check found, so one rerun can fix them all; one failure reads as before."""
    def __init__(self, messages):
        self.messages = list(dict.fromkeys(messages))
        super().__init__(self.messages[0] if len(self.messages) == 1 else f"{len(self.messages)} problems:\n"
                         + "\n".join(f"{number}. {message}" for number, message in enumerate(self.messages, 1)))


def keep(problems, check, *args, **kwargs):
    """Run one check, add its failures to problems, and go on; return its result, or None after a failure."""
    try:
        return check(*args, **kwargs)
    except ValueError as error:
        problems.extend(getattr(error, "messages", [str(error)]))


def raise_all(problems):
    if problems:
        raise Failures(problems)


def check_front_matter(front, review=False):
    unfilled = [key for key, value in front.items() if PROMPT.search(value)]
    if unfilled:
        raise ValueError(f"Front matter contains unfilled template prompts: {', '.join(unfilled)}.")
    if review:
        for key in ("base", "head"):
            if key in front and not source_peek.SHA.fullmatch(front[key]):
                raise ValueError(f"Front matter {key} must be a full commit SHA.")
        if "repository" in front and not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", front["repository"]):
            raise ValueError("Front matter repository must be owner/name.")


def source_fingerprint(source):
    """Track source freshness independently of HTML composition and generated label definitions."""
    front, body = split_front_matter(source)
    body, _ = split_label_key(body)
    return hashlib.sha256((json.dumps(front, sort_keys=True) + "\n" + body.strip()).encode()).hexdigest()


def slug(title):
    return re.sub(r"[^\w]+", "-", title.lower()).strip("-")


def parse(markup):
    return BeautifulSoup(markup, "html.parser")


def link_targets(soup):
    return [tag.get("href", tag.get("xlink:href")) for tag in soup.find_all("a")
            if tag.has_attr("href") or tag.has_attr("xlink:href")]


def fence_languages(soup):
    """The languages of the page's fences that the peek script draws highlighted: diffs split into tables and
    diagrams render on their own, so neither counts. Render and check derive the embedded grammars from this."""
    return sorted({name[len("language-"):] for code in soup.select("main pre > code") for name in code.get("class", [])
                   if name.startswith("language-") and name not in ("language-diff", "language-mermaid")})


def check_prompts(source):
    visible = parse(MARKDOWN.render(source))
    for code in visible.find_all(["pre", "code"]):
        code.decompose()
    if PROMPT.search(visible.get_text()):
        raise ValueError("Report contains unfilled template prompts.")


def check_links(hrefs, document, ids):
    problems = []
    for href in dict.fromkeys(hrefs):
        url = urlsplit(href)
        if url.scheme in ("https", "http", "mailto"):
            continue  # Static validation does not request remote sources.
        if url.scheme or url.netloc:
            problems.append(f"Unsupported link: {href}")
            continue
        target = (document.parent / unquote(url.path)).resolve()
        # A Markdown file can also be cited as source, with GitHub-style line anchors.
        source_line = url.path and document.suffix == ".md" and source_peek.LINES.fullmatch(url.fragment)
        if not url.path or (target == document.resolve() and not source_line):
            if url.fragment and unquote(url.fragment) not in ids:
                problems.append(f"Missing fragment: {href}")
        elif not target.is_file():
            problems.append(f"Missing local file: {href}")
        elif url.fragment and target.suffix in (".md", ".html"):
            if target.suffix == ".md" and source_peek.LINES.fullmatch(url.fragment):
                continue
            target_source = target.read_text()
            if target.suffix == ".md":
                _, target_source = split_front_matter(target_source)
                headings = parse(MARKDOWN.render(target_source)).find_all(re.compile(r"^h[1-6]$"))
                target_ids = {slug(h.get_text()) for h in headings}
            else:
                target_ids = {tag["id"] for tag in parse(target_source).find_all(id=True)}
            if unquote(url.fragment) not in target_ids:
                problems.append(f"Missing fragment: {href}")
    raise_all(problems)


def template_hash():
    return hashlib.sha256(TEMPLATE.read_bytes() + (ROOT / "assets/manrope-latin.woff2").read_bytes()
                          + (ROOT / "diagram-theme.json").read_bytes()
                          + (ROOT / "report-labels.json").read_bytes()
                          + (ROOT / "diagram-renderer/render.mjs").read_bytes()
                          + (ROOT / "peek.js").read_bytes() + (ROOT / "peek.css").read_bytes()).hexdigest()


def font_css():
    data = base64.b64encode((ROOT / "assets/manrope-latin.woff2").read_bytes()).decode("ascii")
    return ('/* Manrope — SIL Open Font License; license included in this document. */'
            '@font-face{font-family:Manrope;font-style:normal;font-weight:400 800;font-display:swap;'
            f'src:url(data:font/woff2;base64,{data}) format("woff2");}}')


# Attention items and findings carry one action word and one evidence word (report-format.md).
ACTIONS = ("decide", "verify", "discuss", "skim", "note")
def is_file_link(anchor):
    """A link whose text is a file name and whose target is not an anchor in this page."""
    return not anchor.get("href", "#").startswith("#") and re.fullmatch(r"[\w./-]+\.\w+(?::\d+(?:-\d+)?)?", anchor.get_text(strip=True)) is not None


READING_DEPTHS = {"Read": "inspect fully, in this order", "Skim": "read the assigned portions only", "Skip": "no further reading, reason given"}
EVIDENCE_STATUS = ("observed", "source", "quoted", "inferred", "not inspected", "unknown")
ROUTE = ("Look at:", "Settle:")  # the reading route of an actionable item
ATTENTION = r"what to look at"  # the item list's heading
# The reader sees plain phrases (report-format.md); checks and chip styles use the code each phrase stands for.
ACTION_PHRASES = {"you decide": "decide", "check it": "verify", "ask the author": "discuss", "read lightly": "skim", "no action": "note"}
EVIDENCE_PHRASES = {"we ran it": "observed", "read at the line": "source", "documented": "quoted",
                    "reasoned, not run": "inferred", "not read": "not inspected", "unknown": "unknown"}
INTENT_PHRASES = {"matches the stated intent": "supported", "partly matches the stated intent": "partial",
                  "contradicts the stated intent": "contradicted", "intent unclear": "unresolved",
                  "nobody asked for this": "intent-unconfirmed"}
# Possible bugs cards (report-format.md): an evidence chip and an origin chip, then labeled fields.
BUG_SECTION = "Possible bugs"
BUG_FORMS = ("The search for bugs has not run:", "No bugs found:")  # the two sentence forms; otherwise ### cards
BUG_EVIDENCE = {"we ran it": "observed", "suspected, not run": "suspected"}
BUG_ORIGIN = {"new in this change": "new", "pre-existing, made worse": "made-worse",
              "from an unrelated commit": "unrelated", "no base pinned": "origin-unknown"}
# A diagnosis note (fix-bug) holds its one cause as a card under "Cause"; the card renders like a bug card, with the
# diagnosis chip families below, and keeps the per-paragraph evidence floor instead of the review card rules.
CAUSE_SECTION = "Cause"
CAUSE_ORIGIN = {"regression": "new", "always broken": "made-worse", "origin not checked": "origin-unknown"}
DIAGNOSIS_CHECKS = {"reproduced": "supported", "not reproduced": "unresolved", "fixed": "supported", "fix proposed": "unresolved",
                    "no fix proposed": "skipped", "test red then green": "supported", "test not verified": "unresolved",
                    "no test seam": "unresolved", "origin checked": "supported",
                    "origin skipped": "skipped", "reach checked": "supported", "reach skipped": "skipped",
                    "consequence checked": "supported", "consequence skipped": "skipped"}
BUG_FIELDS = ("Where", "Trigger", "Introduced by", "Who / impact", "Fix direction", "Reproduce", "Probe that would settle it")
BUG_CHIPS = re.compile(rf"^\*({'|'.join(map(re.escape, BUG_EVIDENCE))})\*\s*·\s*\*({'|'.join(map(re.escape, BUG_ORIGIN))})\*\s*$")
BUG_ITEM_SHAPE = "an item that links to its bug card is one line; the card holds the detail"
ITEM_EVIDENCE = {"we ran it": "observed", "suspected, not run": "inferred"}  # card chip -> its attention item's evidence
REQUIREMENT_COLUMNS = ("Requirement and intent", "Status", "Behavior and evidence", "Next action")
SCENARIO_COLUMNS = ("Scenario", "Before", "After", "Consumer consequence", "Evidence")
EXPLANATION_COLUMNS = ("Scenario", "Condition", "Outcome", "Why it matters", "Evidence")
PLAN_COLUMNS = ("Scenario", "Current", "Planned", "Consumer consequence", "Status and evidence")
COMPARISON_COLUMNS = (SCENARIO_COLUMNS, EXPLANATION_COLUMNS, PLAN_COLUMNS)
DECISION_COLUMNS = ("Decision", "Status", "Meaning and evidence", "Next action")
DECISION_STATUSES = ("Agreed", "Proposed", "Open", "Reopened", "Superseded")
QUESTION_COLUMNS = ("Question", "Status", "Answer and evidence", "Follow-up")
QUESTION_STATUSES = ("Answered", "Partial", "Unresolved")
BLOCKER_COLUMNS = ("Blocker", "What would settle it", "Affected work")
VERIFICATION_COLUMNS = ("Check or scenario", "Result", "Evidence origin", "Revision and configuration", "Scope and limits")
FULFILLMENT = ("Met", "Partial", "Unmet", "Not verified", "Needs clarification", "Not applicable")
CHECK_RESULTS = ("Passed", "Failed", "Mixed", "Not run", "Blocked")
CHECK_ORIGINS = ("Executed here", "Recorded run", "Source inspected", "Proposed")
STATUS_TABLES = {
    REQUIREMENT_COLUMNS: ("requirements", FULFILLMENT),
    VERIFICATION_COLUMNS: ("verification", CHECK_RESULTS),
    DECISION_COLUMNS: ("decisions", DECISION_STATUSES),
    QUESTION_COLUMNS: ("questions", QUESTION_STATUSES),
    BLOCKER_COLUMNS: ("blockers", ()),
}
TABLE_LABELS = {
    REQUIREMENT_COLUMNS: ("requirements",),
    VERIFICATION_COLUMNS: ("verification-results", "verification-origins"),
    DECISION_COLUMNS: ("decisions",),
    QUESTION_COLUMNS: ("questions",),
}


def split_label_key(source):
    """Remove only the reserved top-level key, preserving any later report sections."""
    tokens = MARKDOWN.parse(source)
    lines = source.splitlines(keepends=True)
    matches = []
    for index, token in enumerate(tokens):
        if (token.type == "heading_open" and token.tag == "h2" and token.level == 0
                and tokens[index + 1].content == LABEL_KEY):
            end = next((other.map[0] for other in tokens[index + 1:]
                        if other.type == "heading_open" and other.level == 0
                        and other.tag in ("h1", "h2")), len(lines))
            matches.append((token.map[0], end))
    if len(matches) > 1:
        raise ValueError("Use one Status and label key section.")
    if not matches:
        return source, None
    start, end = matches[0]
    return "".join(lines[:start] + lines[end:]), "".join(lines[start:end])


def label_groups(source):
    document = parse(MARKDOWN.render(split_label_key(source)[0]))
    groups = set()
    for table in document.find_all("table"):
        columns = tuple(th.get_text(" ", strip=True) for th in table.select("thead th"))
        groups.update(TABLE_LABELS.get(columns, ()))
    if document.select("code.language-mermaid"):
        groups.add("diagram-evidence")
    if bug_card_headings(document):
        groups.update(("bug-evidence", "bug-origin"))
    cause = bool(bug_card_headings(document, CAUSE_SECTION))
    if cause:
        groups.update(("bug-evidence", "cause-origin"))
    for code in document.find_all(["pre", "code"]):
        code.decompose()
    if any(re.search(ATTENTION, h.get_text(), re.I) for h in document.find_all("h2")):
        groups.update(("review-actions", "review-evidence"))
    if any(h.get_text().strip().lower() == "reading plan" for h in document.find_all("h2")):
        groups.add("reading-depth")
    text = document.get_text(" ", strip=True).lower()
    if any(phrase in text for phrase in INTENT_PHRASES) or re.search(r"\bintent\s*:", text):
        groups.add("intent-alignment")
    if re.search(r"\bresolution\s*:", text):
        groups.add("finding-resolution")
    for marker in document.find_all("em"):
        word = marker.get_text(strip=True).rstrip(".").lower()
        line = marker.find_parent("p")
        if word in DIAGNOSIS_CHECKS and line is not None and line.get_text().startswith("Checked:"):
            groups.add("diagnosis-checks")  # only a diagnosis note's Checked line renders these as chips
            continue
        if word in CAUSE_ORIGIN or (cause and word in BUG_EVIDENCE):
            continue  # the card families above cover these
        code = code_of(marker.get_text(strip=True))
        if code in ACTIONS:
            groups.add("review-actions")
        if code in EVIDENCE_STATUS:
            groups.add("review-evidence")
    return [group for group in LABELS if group in groups]


def label_key_markdown(source):
    groups = label_groups(source)
    if not groups:
        return ""
    sections = [f"## {LABEL_KEY}\n\nThese labels describe separate judgments. Read each against its stated scope and evidence; no label alone establishes overall readiness or approval."]
    for group in groups:
        definition = LABELS[group]
        rows = "\n".join(f"| {label} | {meaning} |" for label, meaning in definition["options"].items())
        sections.append(f"### Key: {definition['title']}\n\n| Option | Meaning |\n| --- | --- |\n{rows}")
    return "\n\n".join(sections) + "\n"


def with_label_key(source):
    body, _ = split_label_key(source)
    key = label_key_markdown(body)
    return body.rstrip() + "\n\n" + key if key else body


def check_label_key(source, html=None, require=False):
    _, actual = split_label_key(source)
    expected = label_key_markdown(source)
    if (actual is not None or require) and (actual or "").strip() != expected.strip():
        raise ValueError("Status and label key is missing or stale; regenerate with --sync-labels.")
    if html is not None and expected:
        section = parse(html).select_one("main #status-and-label-key")
        # Presentation may change tables to definition lists; the words and their order remain exact.
        normalized = lambda text: re.sub(r"\s+", " ", text).strip()
        expected_doc = parse(MARKDOWN.render(expected))
        for header in expected_doc.select("thead"):
            header.decompose()
        if section is None:
            raise ValueError("HTML needs the complete Status and label key.")
        section = parse(str(section))
        for chrome in section.select("summary, thead"):
            chrome.decompose()
        if normalized(section.get_text(" ", strip=True)) != normalized(expected_doc.get_text(" ", strip=True)):
            raise ValueError("HTML status definitions differ from the shared label key.")


def code_of(label):
    word = label.strip().rstrip(".").lower()
    return (ACTION_PHRASES.get(word) or EVIDENCE_PHRASES.get(word) or INTENT_PHRASES.get(word)
            or BUG_EVIDENCE.get(word) or BUG_ORIGIN.get(word) or CAUSE_ORIGIN.get(word) or DIAGNOSIS_CHECKS.get(word) or word)
FENCE_ATTR = re.compile(r'(\w[\w-]*)="([^"]*)"')


def fence_attributes(source):
    """Attributes in fence info strings, in document order, e.g. ```ts url="...": the renderer
    turns a url into a code-card caption; other Markdown readers ignore the attributes."""
    return [dict(FENCE_ATTR.findall(token.info)) for token in MARKDOWN.parse(source, {}) if token.type == "fence"]


def chip(soup, label):
    span = soup.new_tag("span", attrs={"class": ["chip", "chip-" + code_of(label).replace(" ", "-")]})
    span.string = label
    return span


def bug_card_headings(document, section=BUG_SECTION):
    """The ### cards under '## Possible bugs' (or the named section), in rendered Markdown or on the page."""
    title = next((h for h in document.find_all("h2") if h.get_text(strip=True) == section), None)
    cards = []
    for sibling in title.find_next_siblings() if title else ():
        if sibling.name == "h2":
            break
        if sibling.name == "h3":
            cards.append(sibling)
    return cards


def card_parts(heading):
    """The elements after a heading, up to the next card or section."""
    parts = []
    for sibling in heading.find_next_siblings():
        if sibling.name in ("h2", "h3"):
            break
        parts.append(sibling)
    return parts


def split_fields(soup, paragraph):
    """Give each line-start **Field:** of a bug card its own paragraph; fields may share one Markdown paragraph."""
    pieces = [[]]
    for child in list(paragraph.contents):
        previous = pieces[-1][-1] if pieces[-1] else None
        if (getattr(child, "name", None) == "strong" and child.get_text().rstrip(":") in BUG_FIELDS
                and child.get_text().endswith(":") and isinstance(previous, NavigableString) and str(previous).endswith("\n")):
            pieces[-1][-1] = NavigableString(str(previous).rstrip("\n"))
            pieces.append([])
        pieces[-1].append(child.extract())
    for piece in pieces:
        new = soup.new_tag("p")
        new.extend(piece)
        paragraph.insert_before(new)
    paragraph.decompose()


def field_label(part):
    """The bug-card field a paragraph opens with, such as 'Where', or None."""
    label = part.contents[0] if part.name == "p" and part.contents else None
    text = label.get_text() if getattr(label, "name", None) == "strong" else ""
    return text[:-1] if text.endswith(":") and text[:-1] in BUG_FIELDS else None


def card_fields(heading):
    """A card's field paragraphs by label, after split_fields."""
    return {field_label(part): part for part in card_parts(heading) if field_label(part)}


def chip_line(paragraph, first_line=False):
    """The (evidence, origin) chips a card opens with, or None; the whole paragraph must be the chip line."""
    text = re.sub(r"<em>([^<]*)</em>", r"*\1*", paragraph.decode_contents())
    match = BUG_CHIPS.match((text.split("\n")[0] if first_line else text).strip())
    return match.groups() if match else None


def split_rows(diff):
    """Pair a unified diff's removed and added runs into (left, right, changed) rows; context goes to both sides."""
    rows, removed, added = [], [], []
    def flush():
        for index in range(max(len(removed), len(added))):
            rows.append((removed[index] if index < len(removed) else None, added[index] if index < len(added) else None, True))
        removed.clear(); added.clear()
    for line in diff.split("\n"):
        if line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        else:
            flush()
            text = line[1:] if line.startswith(" ") else line
            rows.append((text, text, False))
    flush()
    return rows


def card_label(url):
    parts = urlsplit(url)
    lines = parts.fragment.lstrip("L").replace("-L", "-") if parts.fragment else ""
    return unquote(parts.path).rsplit("/", 1)[-1] + (":" + lines if lines else "")


_MERMAID = []  # the probed command, cached for the process: [] unprobed, [None] unavailable


def mermaid_command():
    """The Mermaid CLI when it runs here; None means fences stay as labeled source.

    A cached npx package stops resolving when the registry publishes a newer version, so the
    command is probed once rather than assumed from the presence of npx.
    """
    if not _MERMAID:
        candidates = [["mmdc"]] if shutil.which("mmdc") else []
        if shutil.which("npx"):
            candidates.append(["npx", "--no-install", "@mermaid-js/mermaid-cli"])
        found = None
        for command in candidates:
            try:
                if subprocess.run(command + ["--version"], capture_output=True, timeout=60).returncode == 0:
                    found = command
                    break
            except (subprocess.SubprocessError, OSError):
                continue
        _MERMAID.append(found)
    return _MERMAID[0]


def prefix_svg_ids(svg, prefix):
    """Make one diagram's internal ids unique on the page; the root keeps the prefix as its id."""
    ids = set(re.findall(r'\bid="([^"]+)"', svg)) - {prefix}
    for identifier in sorted(ids, key=len, reverse=True):
        escaped = re.escape(identifier)
        svg = re.sub(rf'\bid="{escaped}"', f'id="{prefix}-{identifier}"', svg)
        svg = re.sub(rf'#{escaped}(?![\w-])', f'#{prefix}-{identifier}', svg)
    return svg


def mermaid_svg(source, svg_id):
    """Render one Mermaid fence to inline SVG, or None when the CLI is missing or fails."""
    command = mermaid_command()
    if command is None:
        return None
    with tempfile.TemporaryDirectory(prefix="mermaid ") as directory:
        diagram, output = Path(directory) / "diagram.mmd", Path(directory) / "diagram.svg"
        diagram.write_text(source)
        config = json.loads((ROOT / "diagram-theme.json").read_text())
        config["themeCSS"] = font_css()
        config_path = Path(directory) / "theme.json"
        config_path.write_text(json.dumps(config))
        try:
            subprocess.run(command + ["-i", str(diagram), "-o", str(output), "-b", "transparent", "--svgId", svg_id, "-c", str(config_path)],
                           check=True, capture_output=True, timeout=120)
        except (subprocess.SubprocessError, OSError):
            return None
        svg = parse(output.read_text())
        # Mermaid emits neo-only gradient references even for classic diagrams without those definitions.
        if not svg.select('[data-look="neo"]'):
            for style in svg.find_all("style"):
                style.string = re.sub(r'[^{}]*\[data-look="neo"\][^{}]*\{[^{}]*\}', '', style.get_text())
        return prefix_svg_ids(str(svg), svg_id)


def beautiful_mermaid_svg(source, svg_id):
    script = ROOT / "diagram-renderer/render.mjs"
    try:
        result = subprocess.run(["node", str(script)], input=source, text=True,
                                capture_output=True, check=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as error:
        detail = getattr(error, "stderr", "") or str(error)
        if isinstance(detail, bytes):
            detail = detail.decode(errors="replace")
        raise ValueError("Beautiful Mermaid failed. Run npm ci --prefix " + str(script.parent)
                         + " or use --diagram-renderer mermaid. " + detail[:500]) from error
    svg = parse(prefix_svg_ids(result.stdout, svg_id)).svg
    if svg is None:
        raise ValueError("Beautiful Mermaid returned no SVG.")
    svg["id"] = svg_id
    svg["data-renderer"] = "beautiful-mermaid"
    svg["role"] = "img"
    svg["aria-label"] = "Diagram; explanation and source map in surrounding text"
    return str(svg)


_BEAUTIFUL = []  # the probe result, cached for the process like _MERMAID


def beautiful_mermaid_runs():
    """Whether the pinned Beautiful Mermaid package is installed and renders a probe diagram."""
    if not _BEAUTIFUL:
        runs = (ROOT / "diagram-renderer/node_modules").is_dir()
        if runs:
            try:
                beautiful_mermaid_svg("flowchart LR\n  A --> B", "probe")
            except ValueError:
                runs = False
        _BEAUTIFUL.append(runs)
    return _BEAUTIFUL[0]


SOURCE_ONLY_RECORD = "diagram renderer unavailable"


def check_source_diagrams(source, html):
    """A review page that leaves a diagram as source must record why in Evidence and record."""
    if (parse(html).select("pre.mermaid-source")
            and SOURCE_ONLY_RECORD not in dict(markdown_sections(source, 2)).get("Evidence and record", "").lower()):
        raise ValueError("A diagram is left as source: render it with Beautiful Mermaid or the Mermaid CLI, or add a line"
                         f" containing '{SOURCE_ONLY_RECORD}' to '## Evidence and record'.")


def render(source, source_name, diagram_renderer="auto", repo=None, directory=None):
    """The page for a note. repo holds the cited commits; directory is the note's, where relative links find files beside it."""
    fingerprint = source_fingerprint(source)
    front, source = split_front_matter(source)
    source = with_label_key(source)
    lines = source.splitlines(keepends=True)
    environment = {}
    headings = [token for token in MARKDOWN.parse(source, environment)
                if token.type == "heading_open" and token.tag == "h2" and token.level == 0]
    document = parse(MARKDOWN.render(source, environment))
    used_ids = {slug(heading.get_text()) for heading in document.find_all(re.compile(r"^h[1-6]$"))}

    def generated_id(base):
        identifier, suffix = base, 2
        while identifier in used_ids:
            identifier = f"{base}-{suffix}"
            suffix += 1
        used_ids.add(identifier)
        return identifier

    overview_id = generated_id("overview")
    title_id = slug(document.h1.get_text()) if document.h1 else generated_id("overview-heading")
    opening = parse(MARKDOWN.render("".join(lines[:headings[0].map[0]]) if headings else source, environment))
    if not opening.h1 or len(document.find_all("h1")) != 1:
        raise ValueError("Use one H1 title before the opening.")
    title = opening.h1.get_text()
    opening.h1.attrs.update({"class": "page-title", "id": title_id})
    page_label, overview_label = "Reading guide", "Overview and reading order"
    if opening.p:
        lead = opening.p.get_text()
        if lead.startswith(("Answer:", "Outcome:")):
            opening.p["class"] = "page-summary"
            page_label, overview_label = (("Code walkthrough", "Answer and scope") if lead.startswith("Answer:")
                                           else ("Change plan", "Outcome and readiness"))
        else:
            opening.p["class"] = "review-conclusion" if lead.startswith("Bottom line:") else "scope"
    for paragraph in opening.find_all("p", recursive=False):
        if paragraph.get_text().startswith(("Reviewed:", "Scope:", "Inspected source:")):
            paragraph["class"] = "scope"
        elif paragraph.get_text().startswith("Readiness:"):
            paragraph["class"] = "readiness"
        elif paragraph.get_text().startswith("Read next:"):
            paragraph["class"] = "reading-next"
        elif paragraph.get_text().startswith("Checked:"):
            paragraph["class"] = "checked-line"
            for marker in paragraph.find_all("em"):
                if marker.get_text(strip=True).rstrip(".").lower() in DIAGNOSIS_CHECKS:
                    marker.replace_with(chip(opening, marker.get_text(strip=True)))
    if opening.blockquote:
        opening.blockquote["class"] = "evidence-boundary"
    if opening.ol:
        opening.ol["class"] = "reading-route"
    nav = f'<a href="#{overview_id}">{overview_label}</a>'
    body = f'<section id="{overview_id}" aria-labelledby="{title_id}">{opening}</section>'
    for index, heading in enumerate(headings):
        start, end = heading.map
        following = headings[index + 1].map[0] if index + 1 < len(headings) else len(lines)
        title_html = parse(MARKDOWN.render("".join(lines[start:end]), environment)).h2
        content = "".join(lines[end:following])
        identifier = slug(title_html.get_text())
        record = re.search(r"evidence and record", title_html.get_text(), re.I)  # reference, shown collapsed
        label_key = title_html.get_text() == LABEL_KEY
        heading_id = generated_id(identifier + "-heading")
        title_html["id"] = heading_id
        rendered = parse(MARKDOWN.render(content, environment))
        first = rendered.find()
        # A leading blockquote opts into the compact evidence layout.
        # Other sections retain their normal Markdown presentation.
        if (first is not None and first.name == "blockquote" and first.get_text(strip=True)
                and title_html.get_text() not in ("Requirements", "Verification", "Behavior changes")):
            takeaway = first.extract()
            label = escape(title_html.get_text() + ": details and evidence", quote=True)
            details = f'<details><summary aria-label="{label}">Details and evidence</summary><div class="detail-body">{rendered}</div></details>' if rendered.get_text(strip=True) else ""
            rendered = f"{takeaway}{details}"
        subsections = rendered.find_all("h3") if hasattr(rendered, "find_all") else []
        if record:
            rendered = f'<details><summary>Show the evidence and record</summary><div class="detail-body">{rendered}</div></details>'
        elif label_key:
            rendered = f'<details class="label-key"><summary>What these labels mean</summary><div class="detail-body">{rendered}</div></details>'
            subsections = []
        body += f'<section class="question" id="{identifier}" aria-labelledby="{heading_id}">{title_html}{rendered}</section>'
        nav += f'<a href="#{identifier}">{escape(title_html.get_text())}</a>'
        if subsections:
            nav += "<ul>" + "".join(f'<li><a href="#{slug(sub.get_text())}">{escape(sub.get_text())}</a></li>' for sub in subsections) + "</ul>"
    values = {"TITLE": escape(title), "BODY": body, "NAV": nav, "PAGE_LABEL": page_label,
              "SOURCE": quote(source_name), "SOURCE_FINGERPRINT": fingerprint, "TEMPLATE_HASH": template_hash(), "OVERVIEW_ID": overview_id,
              "FONT_CSS": font_css(), "FONT_LICENSE": escape((ROOT / "assets/OFL-Manrope.txt").read_text())}
    html = re.sub(r"\{\{(\w+)\}\}", lambda match: values[match[1]], TEMPLATE.read_text())
    soup = parse(html)

    def label_help(before, groups):
        help_text = soup.new_tag("p", attrs={"class": "label-help"})
        help_text.append("What these labels mean: ")
        for index, group in enumerate(groups):
            if index:
                help_text.append(" · ")
            title = LABELS[group]["title"]
            link = soup.new_tag("a", href="#" + slug("Key: " + title))
            link.string = title.lower()
            help_text.append(link)
        if before.name == "h2":
            before.insert_after(help_text)
        else:
            before.insert_before(help_text)

    groups = label_groups(source)
    for selector, choices in (("#what-to-look-at > ol, #where-to-pay-attention > ol", ("review-actions", "review-evidence")),
                              ("#behavior-changes > h2", ("intent-alignment", "finding-resolution")),
                              ("#reading-plan > h2", ("reading-depth",)),
                              ("#possible-bugs > h2", ("bug-evidence", "bug-origin")),
                              ("#cause > h2", ("bug-evidence", "cause-origin")),
                              (".checked-line", ("diagnosis-checks",))):
        target = soup.select_one(selector)
        available = [group for group in choices if group in groups]
        if target is not None and available:
            label_help(target, available)
    # Keep the authored labels and prose together while giving them a consistent reading column.
    for paragraph in soup.select("#behavior-changes > p, #walkthrough > p, #decisions > p, #delivery-slices > p"):
        label = paragraph.find("strong", recursive=False)
        if not label or paragraph.contents[0] is not label or label.get_text().rstrip(":") not in (
                "Purpose and tradeoff", "Conditions", "Consumers", "Preserved", "Depends on", "Deployment", "Open question",
                "Trigger", "State before", "Action", "State after", "Why it matters", "Evidence",
                "Status", "Choice", "Reason", "Acceptance", "Delivery", "Authority", "Scope", "Verification", "Readiness"):
            continue
        paragraph["class"] = ["behavior-fact"]
        copy = soup.new_tag("span", attrs={"class": "fact-copy"})
        for child in list(label.next_siblings):
            copy.append(child.extract())
        paragraph.append(copy)
    # Code cards: a fence with url="..." gets a caption that links to the pinned source.
    for pre, attributes in zip(soup.main.find_all("pre"), fence_attributes(source)):
        url = attributes.get("url")
        if not url:
            continue
        figure = soup.new_tag("figure", attrs={"class": ["code-card"]})
        cited = source_peek.citation(url) or source_peek.local_citation(url, directory)
        if cited and cited.start:
            figure["data-first"] = str(cited.start)  # the page numbers the fence's rows from the cited line (peek.js)
        caption = soup.new_tag("figcaption")
        link = soup.new_tag("a", href=url)
        link.string = attributes.get("title") or card_label(url)
        caption.append(link)
        language = next((c[len("language-"):] for c in (pre.code.get("class", []) if pre.code else []) if c.startswith("language-")), "")
        if language:
            note = soup.new_tag("span")
            note.string = "diff · base → head" if language == "diff" else language
            caption.append(note)
        pre.replace_with(figure)
        figure.append(caption)
        figure.append(pre)
    # Split view: a diff fence also renders side by side (base left, head right); the unified fence stays beneath as its source.
    for code in soup.select("pre > code.language-diff"):
        pre = code.parent
        table = soup.new_tag("table", attrs={"class": ["diff-split"]})
        head = soup.new_tag("thead"); row = soup.new_tag("tr")
        for title in ("base", "head"):
            cell = soup.new_tag("th"); cell.string = title; row.append(cell)
        head.append(row); table.append(head)
        body = soup.new_tag("tbody")
        for left, right, changed in split_rows(code.get_text().rstrip("\n")):
            row = soup.new_tag("tr")
            for text, kind in ((left, "del"), (right, "add")):
                cell = soup.new_tag("td")
                if text is None:
                    cell["class"] = ["empty"]
                else:
                    cell.string = text
                    if changed:
                        cell["class"] = [kind]
                row.append(cell)
            body.append(row)
        table.append(body)
        details = soup.new_tag("details"); summary = soup.new_tag("summary"); summary.string = "Unified diff"; details.append(summary)
        pre.replace_with(table)
        table.insert_after(details)
        details.append(pre)
    # Diff colouring: added and removed lines inside a diff fence; the code text is unchanged.
    for code in soup.select("pre > code.language-diff"):
        text = code.get_text()
        code.clear()
        for index, line in enumerate(text.split("\n")):
            if index:
                code.append("\n")
            if line.startswith("+") or line.startswith("-"):
                span = soup.new_tag("span", attrs={"class": ["add" if line.startswith("+") else "del"]})
                span.string = line
                code.append(span)
            else:
                code.append(line)
    # Bug cards: each ### under "Possible bugs" with its chips, field rows, Base/Head table, and Reproduce as a code card.
    for heading in bug_card_headings(soup.main) + bug_card_headings(soup.main, CAUSE_SECTION):
        for part in card_parts(heading):
            if part.name == "p":
                split_fields(soup, part)
        parts, fields = card_parts(heading), card_fields(heading)
        article = soup.new_tag("article", attrs={"class": ["bug-card"]})
        heading.insert_before(article)
        article.extend([heading, *parts])
        first = parts[0] if parts else None
        if (first is not None and first.name == "p" and first.find("em", recursive=False)
                and all(getattr(child, "name", None) == "em" or not str(child).strip(" ·\n") for child in first.contents)):
            labels = [em.get_text(strip=True) for em in first.find_all("em", recursive=False)]
            first.clear()
            first["class"] = ["bug-chips"]
            first.extend([chip(soup, label) for label in labels])
        for label, paragraph in fields.items():
            if label == "Reproduce":
                continue
            paragraph["class"] = ["behavior-fact"]
            copy = soup.new_tag("span", attrs={"class": "fact-copy"})
            copy.extend([child.extract() for child in list(paragraph.strong.next_siblings)])
            paragraph.append(copy)
        for table in article.find_all("table"):
            if [th.get_text(" ", strip=True) for th in table.select("thead th")][1:] == ["Base", "Head"]:
                table["class"] = ["base-head"]
        reproduce = fields.get("Reproduce")
        if reproduce is not None:
            details = soup.new_tag("details", attrs={"class": ["bug-reproduce"], "open": ""})
            summary = soup.new_tag("summary")
            summary.string = "Reproduce"
            reproduce.insert_before(details)
            details.append(summary)
            reproduce.strong.decompose()  # the summary carries the label
            following = parts[parts.index(reproduce) + 1:]
            details.extend(([reproduce] if reproduce.get_text(strip=True) else []) + following)
            if not reproduce.get_text(strip=True):
                reproduce.decompose()
            script = next((a["href"] for a in details.find_all("a", href=True)
                           if not urlsplit(a["href"]).scheme and urlsplit(a["href"]).path), None)
            for pre in details.find_all("pre", recursive=False):
                figure = soup.new_tag("figure", attrs={"class": ["code-card"]})
                caption = soup.new_tag("figcaption")
                if script:
                    caption.append(unquote(urlsplit(script).path))  # plain text; the Output line carries the link
                language = next((c[len("language-"):] for c in (pre.code.get("class", []) if pre.code else []) if c.startswith("language-")), "")
                note = soup.new_tag("span")
                note.string = language or "command"
                caption.append(note)
                pre.replace_with(figure)
                figure.extend([caption, pre])
            # The Output: line: its label and probe link on one row, the excerpt as a block beneath (page-template.html).
            for paragraph in details.find_all("p", recursive=False):
                first = paragraph.contents[0] if paragraph.contents else None
                if not isinstance(first, NavigableString) or not str(first).startswith("Output:"):
                    continue
                paragraph["class"] = ["probe-output"]
                label = soup.new_tag("span", attrs={"class": "probe-label"})
                label.string = "Output:"
                first.replace_with(label)
                for node in list(paragraph.contents)[1:]:
                    if isinstance(node, NavigableString) and node.strip():
                        joiner = soup.new_tag("span", attrs={"class": "probe-sep"})
                        joiner.string = node.strip()
                        node.replace_with(joiner)
    # Attention cards: the ordered list under "What to look at"; the item's *what to do* and *how we know* phrases become chips.
    for heading in soup.select("main h2"):
        if re.search(ATTENTION, heading.get_text(), re.I):
            listing = heading.find_next("ol")
            if listing is not None:
                listing["class"] = listing.get("class", []) + ["attention"]
                for item in listing.find_all("li", recursive=False):
                    # ponytail: the first two vocabulary words in italics; an italicized "source" later in the item would also chip.
                    markers = [em for em in item.find_all("em") if code_of(em.get_text(strip=True)) in ACTIONS + EVIDENCE_STATUS][:2]
                    for marker in markers:
                        marker.replace_with(chip(soup, marker.get_text(strip=True).rstrip(".")))
                    # Split only line-start labels, leaving inline links and code intact.
                    copy = parse(str(item)).li
                    for paragraph in copy.find_all("p", recursive=False):
                        paragraph.insert_before("\n")
                        paragraph.unwrap()
                    groups = {"body": []}
                    current = "body"
                    line_start = True
                    for child in list(copy.contents):
                        if isinstance(child, NavigableString):
                            boundary = r"(?:^|\n)" if line_start else r"\n"
                            text = str(child)
                            pieces = re.split(boundary + r"[ \t]*(Look at|Settle):[ \t]*", text)
                            line_start = (line_start and not text.strip()) or bool(re.search(r"\n[ \t]*$", text))
                            groups[current].append(pieces[0])
                            for label, value in zip(pieces[1::2], pieces[2::2]):
                                current = label
                                groups.setdefault(current, []).append(value)
                        else:
                            line_start = False
                            groups[current].append(child.extract())
                    if not all(label in groups for label in ("Look at", "Settle")):
                        continue
                    body = soup.new_tag("div", attrs={"class": "attention-body"})
                    for child in groups["body"]:
                        body.append(child)
                    title = body.find("strong", recursive=False)
                    if title:
                        header = soup.new_tag("div", attrs={"class": "attention-heading"})
                        header.append(title.extract())
                        for marker in body.select(".chip"):
                            header.append(marker.extract())
                        for node in list(body.contents):
                            if not isinstance(node, NavigableString):
                                break
                            cleaned = re.sub(r"^[\s—·]+", "", str(node))
                            node.replace_with(cleaned)
                            if cleaned:
                                break
                    item.clear()
                    if title:
                        item.append(header)
                    item.append(body)
                    routes = soup.new_tag("dl", attrs={"class": "attention-route"})
                    for label in ("Look at", "Settle"):
                        term = soup.new_tag("dt"); term.string = label
                        value = soup.new_tag("dd")
                        for child in groups[label]:
                            value.append(child)
                        routes.extend([term, value])
                    item.append(routes)
    # Reading plan: the list whose items open with *Read*, *Skim*, or *Skip* is grouped by that depth; each item keeps its
    # reason on the left and its file links, as chips, on the right. Any other shape stays a plain list.
    plan = soup.select_one("#reading-plan > ul")
    if plan is not None:
        items = plan.find_all("li", recursive=False)
        depths = [item.find("strong") for item in items]
        if items and all(d is not None and d.get_text(strip=True) in READING_DEPTHS for d in depths):
            groups = {depth: [] for depth in READING_DEPTHS}
            for item, depth in zip(items, depths):
                depth.extract()
                nodes = list(item.contents)
                first = next((i for i, n in enumerate(nodes) if getattr(n, "name", None) == "a" and is_file_link(n)), len(nodes))
                groups[depth.get_text(strip=True)].append((nodes[:first], nodes[first:]))
            wrap = soup.new_tag("div", attrs={"class": "reading-groups"})
            for depth, entries in groups.items():
                if not entries:
                    continue
                group = soup.new_tag("section", attrs={"class": "reading-group"})
                heading = soup.new_tag("h3")
                label = soup.new_tag("span", attrs={"class": f"depth depth-{depth.lower()}"}); label.string = depth
                files = sum(sum(1 for n in links if getattr(n, "name", None) == "a" and is_file_link(n)) for _, links in entries)
                count = soup.new_tag("span"); count.string = f"{READING_DEPTHS[depth]} · {files} file{'s' if files != 1 else ''}"
                heading.extend([label, count]); group.append(heading)
                listing = soup.new_tag("ol", attrs={"class": "reading-items"})
                for why, links in entries:
                    entry = soup.new_tag("li")
                    reason = soup.new_tag("p", attrs={"class": "reading-why"})
                    reason.extend(why)
                    if reason.contents and isinstance(reason.contents[0], NavigableString):
                        reason.contents[0].replace_with(re.sub(r"^\s*:\s*", "", reason.contents[0]))
                    if reason.contents and isinstance(reason.contents[-1], NavigableString):
                        reason.contents[-1].replace_with(reason.contents[-1].rstrip())
                    chips = soup.new_tag("p", attrs={"class": "reading-files"})
                    for node in links:
                        if isinstance(node, NavigableString):
                            text = re.sub(r"^[\s,.]+|[\s,.]+$", "", node)
                            if text:
                                note = soup.new_tag("span", attrs={"class": "note"}); note.string = text; chips.append(note)
                        else:
                            chips.append(node)
                    entry.extend([reason, chips]); listing.append(entry)
                group.append(listing); wrap.append(group)
            plan.replace_with(wrap)
    explicit = diagram_renderer != "auto"
    for index, code in enumerate(soup.select("pre > code.language-mermaid"), 1):
        pre = code.parent
        if diagram_renderer == "auto":  # probed only for a page with a fence
            diagram_renderer = "beautiful-mermaid" if beautiful_mermaid_runs() else "mermaid"
        reason = ("no diagram renderer runs here (install Beautiful Mermaid: npm ci --prefix "
                  f"{ROOT / 'diagram-renderer'}, or the Mermaid CLI)")
        if diagram_renderer == "mermaid":
            svg = mermaid_svg(code.get_text(), f"diagram-{index}")
        else:
            try:
                svg = beautiful_mermaid_svg(code.get_text(), f"diagram-{index}")
            except ValueError:
                if explicit:  # an explicit Beautiful Mermaid stops on its error
                    raise
                svg = mermaid_svg(code.get_text(), f"diagram-{index}")
                reason = ("Beautiful Mermaid does not support its syntax, such as termination-cross arrows,"
                          " and the Mermaid CLI did not render it (install the Mermaid CLI)")
        label_help(pre, ("diagram-evidence",))
        if svg is None:
            pre["class"] = pre.get("class", []) + ["mermaid-source"]
            print(f"Diagram {index} left as source: {reason}.", file=sys.stderr)
            continue
        figure = soup.new_tag("figure", attrs={"class": "diagram", "tabindex": "0", "role": "region",
                                             "aria-label": f"Diagram {index}; description and source map in surrounding text"})
        figure.append(parse(svg).svg)
        details = soup.new_tag("details")
        summary = soup.new_tag("summary")
        summary.string = f"Diagram {index} source and evidence"
        details.append(summary)
        pre.replace_with(figure)
        details.append(pre)
        figure.append(details)
        following = figure.find_next_sibling()
        if following and following.name == "p" and following.get_text(strip=True).lower() == "source map:":
            mapping = following.find_next_sibling()
            if mapping and mapping.name == "ul":
                details.append(following.extract())
                details.append(mapping.extract())
    for index, table in enumerate(soup.find_all("table"), 1):
        columns = tuple(th.get_text(" ", strip=True) for th in table.select("thead th"))
        if table.find_parent(id="status-and-label-key"):
            title = table.find_previous("h3").get_text()
            group = next(key for key, value in LABELS.items() if title == "Key: " + value["title"])
            definitions = soup.new_tag("dl", attrs={"class": "label-definitions"})
            for row in table.select("tbody tr"):
                for tag, cell in zip(("dt", "dd"), row.find_all("td")):
                    item = soup.new_tag(tag)
                    item.string = cell.get_text(" ", strip=True)
                    if tag == "dt":
                        label = item.get_text()
                        if group in ("requirements", "verification-results", "decisions", "questions"):
                            badge = soup.new_tag("span", attrs={"class": ["status", "status-" + slug(label)]})
                            badge.string = label
                            item.clear(); item.append(badge)
                        elif group in ("review-actions", "review-evidence", "intent-alignment", "bug-evidence", "bug-origin"):
                            item.clear(); item.append(chip(soup, label))
                    definitions.append(item)
            table.replace_with(definitions)
            continue
        if columns in TABLE_LABELS:
            label_help(table, TABLE_LABELS[columns])
        if columns in COMPARISON_COLUMNS:
            scenarios = soup.new_tag("div", attrs={"class": "scenario-list"})
            owner = next((heading for heading in table.find_all_previous(re.compile(r"^h[2-5]$"))
                          if not heading.find_parent(class_="scenario")), None)
            level = min(int(owner.name[1]) + 1, 5) if owner else 3
            for row in table.select("tbody tr"):
                article = soup.new_tag("article", attrs={"class": "scenario"})
                for column, layout_column, cell in zip(columns, SCENARIO_COLUMNS, row.find_all("td")):
                    if column == "Scenario":
                        field = soup.new_tag(f"h{level}", attrs={"data-column": column, "class": "scenario-title",
                            "id": generated_id("scenario-" + slug(cell.get_text()))})
                        article["aria-labelledby"] = field["id"]
                        article.append(field)
                    else:
                        group = soup.new_tag("div", attrs={"class": "scenario-" + slug(layout_column)})
                        label = soup.new_tag(f"h{level + 1}", attrs={"class": "scenario-label"}); label.string = column
                        field = soup.new_tag("div", attrs={"data-column": column})
                        group.extend([label, field]); article.append(group)
                    for child in list(cell.contents):
                        field.append(child.extract())
                scenarios.append(article)
            table.replace_with(scenarios)
            continue
        if columns in STATUS_TABLES:
            kind, statuses = STATUS_TABLES[columns]
            table["class"] = ["review-table", kind + "-table"]
            table["role"] = "table"
            for heading in table.select("thead th"):
                heading["scope"] = "col"
            for row in table.select("tbody tr"):
                row["role"] = "row"
                for column, cell in zip(columns, row.find_all("td")):
                    cell.attrs.update({"data-label": column, "role": "cell"})
            for row in table.select("tbody tr"):
                cell = row.find_all("td")[1]
                label = cell.get_text(" ", strip=True)
                if label in statuses:
                    badge = soup.new_tag("span", attrs={"class": ["status", "status-" + slug(label)]})
                    # Preserve any author links or inline emphasis inside the status.
                    for child in list(cell.contents):
                        badge.append(child.extract())
                    cell.append(badge)
        table.wrap(soup.new_tag("div", attrs={"class": "table-scroll", "tabindex": "0", "role": "region", "aria-label": f"Scrollable table {index}"}))
    for index, pre in enumerate(soup.find_all("pre"), 1):
        pre.attrs.update({"tabindex": "0", "role": "region", "aria-label": f"Scrollable source excerpt {index}"})
    for heading in soup.select("main h3, main h4, main h5, main h6"):
        if not heading.get("id"):
            heading["id"] = generated_id(slug(heading.get_text())) if heading.find_parent(class_="scenario") else slug(heading.get_text())
    for anchor in soup.main.find_all("a", href=True):
        if is_file_link(anchor):
            anchor["class"] = anchor.get("class", []) + ["file-link"]  # a file name never breaks inside; the cell scrolls
    # Code peek: pinned GitHub links and links to files beside the note open the cited file or diff inline, and
    # fences with a language draw as highlighted rows (peek.js); the data sits outside <main>.
    payload, skipped = source_peek.build(link_targets(soup.main), front, repo, source, directory, fence_languages(soup))
    for href, reason in skipped:
        print(f"No code peek for {href}: {reason}", file=sys.stderr)
    if payload:
        for link in soup.main.find_all("a", href=True):
            if link["href"] in payload["links"]:
                link["data-peek"] = ""
        styles = (ROOT / "assets/highlight/intellij-light.min.css").read_text() + (ROOT / "peek.css").read_text()
        # Parse rather than new_tag(...).string: bs4 would entity-escape the script's < and &.
        assets = parse(f'<style class="peek-style">{styles}</style>'
                       f'<script type="application/octet-stream" id="peek-data">{source_peek.encode(payload)}</script>'
                       f'<script class="peek-script">{(ROOT / "peek.js").read_text()}</script>')
        soup.body.extend(list(assets.contents))
    return str(soup)


# Fence lines that draw nothing: declarations, styling, notes, and grouping keywords.
UNDRAWN = re.compile(r"^\s*(?:%%|participant\b|actor\b|subgraph\b|end\b|direction\b|classDef\b|class\b|style\b|linkStyle\b|click\b"
                     r"|title\b|accTitle\b|accDescr\b|[Nn]ote\b|loop\b|alt\b|else\b|opt\b|par\b|and\b|rect\b|critical\b|option\b|break\b|activate\b|deactivate\b)")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


# Sections whose blocks are questions, scope, conditions, provenance, or records rather than claims.
CLAIM_FREE = re.compile(r"question|scope|boundar|condition|revision|provenance|worth asking|unknown|\bopen\b|next|files|\blog\b|review|history"
                        r"|kickoff|default|summary|source map|reading order|possible|prompt|feedback|generators|record"
                        r"|motivat|workflow|outcome|event|milestone|timeline|collection|acceptance|slice", re.I)
# Words that mark an observation, a status, or an honest label; a pinned line or a quoted link also counts.
EVIDENCE_WORDS = re.compile(r"\b(?:observed|executed|inferred|proposed|not (?:yet )?(?:inspected|run|checked|probed|verified)|unknown|background|documented"
                            r"|quoted|agreed|accepted|empty|ran|run|supported|partial|contradicted|unresolved|intent-unconfirmed|pending|prepared|usable"
                            r"|unavailable|declined|broken|absent|substitute|confirmed|reproduced|measured|probe[sd]?|benchmark|see"
                            r"|not read|reasoned|read at the line|contradicts|intent unclear|nobody asked for this"
                            r"|recorded|passed|fail(?:s|ed)?|returned|emits|installed|not needed|when chosen|verify when|optional|alternative"
                            r"|self-checked|matches|differs|no evidence|trap)\b", re.I)
COMMAND = re.compile(r"`[^`\n]{24,}`")  # a reproducible command or recipe line
# A pinned link, or the bare `path.ext:12` / `path.ext:12-20` form a note uses for a local snapshot.
PINNED = re.compile(r"\]\([^)\s]*#L\d+|\b[\w./-]+\.\w{1,4}:\d+(?:-\d+)?\b")
QUOTED_LINK = re.compile(r"[\"“][^\"”]{6,}[\"”][^\n]*\]\(|\]\([^)]*\)[^\n]*[\"“][^\"”]{6,}[\"”]")


def claim_gaps(source):
    """Blocks that carry no pinned line, observation, quote, or label (EVIDENCE.md), as (line, text).

    ponytail: a floor by block and word, not a reading of the code; the author's check and the second reader do that.
    The title section is read as a summary; sections named in CLAIM_FREE hold questions, scope, conditions, or records.
    """
    lines = source.split("\n")
    gaps = []
    skipping = True  # until the first section heading
    bugs = False  # inside '## Possible bugs'
    fence = None
    block, start = [], 0

    def flush():
        if not block:
            return
        text = " ".join(line.strip() for line in block)
        # Prose under eight words is a title or a pointer; a table row under four is a legend entry.
        words = len(text.replace("|", " ").split())
        if skipping or words < (4 if text.lstrip().startswith("|") else 8) or text.lstrip().startswith(">"):
            return
        if text.startswith("**Open question:**") and text.endswith("?"):
            return  # A question asks for evidence; it does not assert an answer.
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+\**(?:Action|Next(?: action)?|Fix|Recommendation):", block[0]):
            return  # a recommendation, not a claim
        if PINNED.search(text) or EVIDENCE_WORDS.search(text) or QUOTED_LINK.search(text) or COMMAND.search(text):
            return
        gaps.append((start + 1, text[:80]))

    for i, line in enumerate(lines):
        if fence:
            if re.match(rf"^{re.escape(fence)}\s*$", line):
                fence = None
            continue
        opening = re.match(r"^(`{3,}|~{3,})", line)
        if opening:
            flush(); block = []
            fence = opening.group(1)
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            flush(); block = []
            level = len(heading.group(1))
            bugs = heading.group(2).strip() == BUG_SECTION if level == 2 else bugs
            # A bug card's evidence chip labels the whole card; check_bug_cards checks its pinned lines, run, and predictions.
            chips = next((other for other in lines[i + 1:] if other.strip()), "")
            skipping = (level == 1 or bool(CLAIM_FREE.search(heading.group(2)))
                        or (bugs and level == 3 and bool(BUG_CHIPS.match(chips.strip()))))
            continue
        if not line.strip():
            flush(); block = []
            continue
        if re.match(r"^\s*\|?\s*:?-{3,}", line):
            continue  # table separator
        if line.lstrip().startswith("|"):
            flush(); block = []
            cells = [c for c in line.strip().strip("|").split("|")]
            if i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
                continue  # header row
            block, start = [line], i
            flush(); block = []
            continue
        item = re.match(r"^(\s*)(?:[-*+]|\d+[.)])\s+", line)
        if item and block and re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", block[0]) and len(item.group(1)) > len(re.match(r"^\s*", block[0]).group(0)):
            block.append(line)  # a nested item: its evidence covers the parent item
            continue
        if item:
            flush()
            block, start = [line], i
            continue
        if block and re.match(r"^\s+\S", line) and re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", block[0]):
            block.append(line)  # continuation of a list item
            continue
        if not block:
            start = i
        block.append(line)
    flush()
    return gaps


def check_claims(source):
    """Every claim block carries a pinned line, an observation, a quote, or a label (EVIDENCE.md)."""
    gaps = claim_gaps(split_label_key(source)[0])
    if gaps:
        shown = "; ".join(f"line {n}: {text!r}" for n, text in gaps[:5])
        raise ValueError(f"{len(gaps)} claim block(s) without evidence — {shown}. Add a pinned line, an observation, a quote, or a label (EVIDENCE.md).")


def attention_items(source):
    """The ordered list under 'What to look at': one list of lines per item, continuation lines included."""
    items, current, inside = [], None, False
    for line in source.split("\n"):
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            if inside:
                break
            inside = bool(re.search(ATTENTION, heading.group(2), re.I))
            continue
        if not inside:
            continue
        if re.match(r"^\d+[.)]\s+", line):
            current = [line.strip()]
            items.append(current)
        elif current is not None and line.strip():
            current.append(line.strip())  # an indented or lazy continuation of the item
        else:
            current = None  # a blank line ends the item; the list is one tight ol
    return items


def output_line(paragraph):
    """True when an Output: paragraph is one line holding only code spans and links, joined by · or commas."""
    contents = list(paragraph.contents)
    if not contents or not isinstance(contents[0], NavigableString) or not str(contents[0]).startswith("Output:"):
        return False
    rest = [NavigableString(str(contents[0])[len("Output:"):])] + contents[1:]
    return (any(getattr(child, "name", None) == "code" for child in rest)
            and all(child.name in ("code", "a") if getattr(child, "name", None) else re.fullmatch(r"[ ·,]*", str(child))
                    for child in rest))


def bug_card_items(source):
    """Attention items that link to a Possible bugs card, as {item number: (its lines, the first card's evidence chip,
    every card anchor it links)}."""
    cards = {}
    for heading in bug_card_headings(parse(MARKDOWN.render(source))):
        parts = card_parts(heading)
        chips = chip_line(parts[0], first_line=True) if parts and parts[0].name == "p" else None
        cards["#" + slug(heading.get_text())] = chips[0] if chips else None
    items = {}
    for number, lines in enumerate(attention_items(source), 1):
        linked = [target for target in map(unquote, re.findall(r"\]\((#[^)\s]+)\)", " ".join(lines))) if target in cards]
        if linked:
            items[number] = (lines, cards[linked[0]], linked)
    return items


def bug_item_gaps(source):
    """Attention items that link to a bug card and break its item shape, as (item number, problem): one line,
    *you decide* or *check it*, and the card's evidence (*we ran it* or *reasoned, not run*)."""
    gaps = []
    for number, (lines, evidence, _) in bug_card_items(source).items():
        if len(lines) > 1:
            gaps.append((number, BUG_ITEM_SHAPE))
        title = re.sub(r"\*\*[^*]+\*\*", "", lines[0], count=1)
        markers = [code_of(m) for m in re.findall(r"\*([^*]+)\*", title)]
        if next((m for m in markers if m in ACTIONS), None) not in ("decide", "verify"):
            gaps.append((number, "an item that links to a bug card says *you decide* or *check it*"))
        marked = next((m for m in markers if m in EVIDENCE_STATUS), None)
        expected = ITEM_EVIDENCE.get(evidence)
        if expected and marked and marked != expected:
            phrase = next(word for word, code in EVIDENCE_PHRASES.items() if code == expected)
            gaps.append((number, f"its card says *{evidence}*, so the item's evidence is *{phrase}*"))
    return gaps


def attention_gaps(source):
    """Items that break the item shape of report-format.md, as (item number, problem).

    The title line carries what to do and how we know, each an italic phrase. A you-decide, check-it, or
    ask-the-author item carries its reading route (Look at, Settle).
    A read-lightly item rests on we-ran-it or read-at-the-line evidence. An item that links to its Possible bugs
    card is one concise line and needs no route of its own.
    """
    gaps = []
    linked, bug_gaps = bug_card_items(source), bug_item_gaps(source)  # a bug's item is one line; its card holds the route
    for number, lines in enumerate(attention_items(source), 1):
        text = " ".join(lines)
        title = re.sub(r"\*\*[^*]+\*\*", "", lines[0], count=1)  # the bold title may hold italics or a dash
        words = [m.strip().rstrip(".").lower() for m in re.findall(r"\*([^*]+)\*", title)]  # phrases only; the codes are internal
        action = next((ACTION_PHRASES[w] for w in words if w in ACTION_PHRASES), None)
        evidence = next((EVIDENCE_PHRASES[w] for w in words if w in EVIDENCE_PHRASES), None)
        if not action or not evidence:
            gaps.append((number, f"needs what to do ({', '.join(ACTION_PHRASES)}) and how we know ({', '.join(EVIDENCE_PHRASES)}), "
                                 "each in italics, on its title line"))
        elif any(gap[0] == number for gap in bug_gaps):
            gaps.extend(gap for gap in bug_gaps if gap[0] == number)
        elif action in ("decide", "verify", "discuss") and number not in linked and any(label not in text for label in ROUTE):
            missing = [label for label in ROUTE if label not in text]
            gaps.append((number, f"an item to decide, check, or ask about needs its reading route: {', '.join(missing)}"))
        elif action == "skim" and evidence not in ("observed", "source"):
            gaps.append((number, f"a read-lightly item needs we-ran-it or read-at-the-line evidence covering the whole part, not '{evidence}'"))
    return gaps


def name_gaps(source):
    """Bookkeeping IDs and the skills' process words in prose, as (line, text) (TECHNICAL-ENGLISH.md)."""
    return reader_gaps(source)


def check_names(source):
    """Every finding, decision, question, probe, and scenario is referred to by name."""
    gaps = name_gaps(source)
    if gaps:
        shown = "; ".join(f"line {n}: {ident}" for n, ident in gaps[:5])
        raise ValueError(f"{len(gaps)} bookkeeping ID(s) or process word(s) in prose — {shown}. Refer to each "
                         "thing by its name and say what was checked in plain words; keep IDs and process state in "
                         "the log, and write a product or version name such as S3 as code.")


def check_attention(source):
    """Every attention item has the shape report-format.md gives it."""
    gaps = attention_gaps(source)
    if gaps:
        shown = "; ".join(f"item {n}: {text}" for n, text in gaps[:5])
        raise ValueError(f"{len(gaps)} attention item(s) off shape — {shown} (report-format.md).")


def opening_gaps(source):
    """A review report opens with its bottom line and 'What the change does'
    (an acceptance report: 'What was asked') (report-format.md).
    Returns problems, empty when fine. ponytail: checks presence, not meaning."""
    section = re.search(r"^(#{1,6})\s+what (?:the change does|was asked)[^\n]*\n(.*?)(?=^#{1,6}\s|\Z)", source, re.I | re.M | re.S)
    paragraphs = [b for b in re.split(r"\n\s*\n", section.group(2)) if b.strip()
                  and not b.lstrip().startswith(("|", "-", "*", ">", "```"))] if section else []
    if not re.search(r"^#{1,6}\s+what to look at", source, re.I | re.M):
        return []
    opening = re.split(r"^##\s", source, maxsplit=1, flags=re.M)[0]
    if not re.search(r"^\*\*Bottom line:\*\*\s*\S", opening, re.M):
        return ["no '**Bottom line:**' paragraph under the title"]
    if not paragraphs:
        return ["no 'What the change does' section before the items"]
    return []


def check_opening(source):
    gaps = opening_gaps(source)
    if gaps:
        raise ValueError(f"{gaps[0]} (report-format.md).")


def markdown_sections(source, level):
    """Return real heading sections, excluding headings inside fenced code."""
    tokens = MARKDOWN.parse(source)
    result = []
    lines = source.splitlines(keepends=True)
    for index, token in enumerate(tokens):
        if token.type != "heading_open" or token.tag != f"h{level}" or token.level:
            continue
        end = next((other.map[0] for other in tokens[index + 1:]
                    if other.type == "heading_open" and other.level == 0
                    and int(other.tag[1:]) <= level), len(lines))
        name = parse(MARKDOWN.render(tokens[index + 1].content)).get_text().strip()
        result.append((name, "".join(lines[token.map[1]:end])))
    return result


def review_table(source, columns, section, problems):
    """Validate table shape without interpreting the evidence in its cells. A missing table raises: its rows
    are what the caller checks next. An unfilled cell is added to problems, and the rows still return."""
    tables = parse(MARKDOWN.render(source)).find_all("table")
    matched = [table for table in tables
               if tuple(th.get_text(" ", strip=True) for th in table.select("thead th")) == columns]
    if len(matched) != 1 or not matched[0].select("tbody tr"):
        raise ValueError(f"{section}: use one nonempty table with columns: {' | '.join(columns)}.")
    rows = [row.find_all("td") for row in matched[0].select("tbody tr")]
    for row in rows:
        if len(row) != len(columns) or any(cell.get_text(strip=True) in ("", "-", "—", "TODO", "TBD") for cell in row):
            problems.append(f"{section}: fill every table cell; state unknowns and their limits explicitly.")
    # A short row would break the callers' cell indexes; only full rows go on to their checks.
    return [row for row in rows if len(row) == len(columns)]


def check_bug_cards(source, note, required=True):
    """'## Possible bugs' holds the not-run sentence, the none-found sentence, or one card per bug (report-format.md).
    Without required, a report without the section passes (reports written before it existed).
    ponytail: checks the card's shape, labels, and probe script location, not whether the bug is real."""
    names = [name for name, _ in markdown_sections(source, 2)]
    if not required and BUG_SECTION not in names:
        return
    if names.count(BUG_SECTION) != 1:
        raise ValueError(f"Review requires exactly one '## {BUG_SECTION}' section: one card per bug, or the "
                         f"'{BUG_FORMS[1]}' or '{BUG_FORMS[0]}' sentence.")
    if "What to look at" in names and names.index(BUG_SECTION) < names.index("What to look at"):
        raise ValueError(f"Place '## {BUG_SECTION}' after '## What to look at'.")
    document = parse(MARKDOWN.render(source))
    title = next(h for h in document.find_all("h2") if h.get_text(strip=True) == BUG_SECTION)
    lead, cards = card_parts(title), bug_card_headings(document)
    forms = (f"{BUG_SECTION}: write one paragraph starting '{BUG_FORMS[0]}' with the reason, one starting "
             f"'{BUG_FORMS[1]}' naming what was probed, or one ### card per bug, and nothing else.")
    if not cards:
        text = lead[0].get_text(" ", strip=True) if len(lead) == 1 and lead[0].name == "p" else ""
        if not any(text.startswith(form) and text[len(form):].strip() for form in BUG_FORMS):
            raise ValueError(forms)
    elif lead:
        raise ValueError(forms)
    bugs = (note.parent / "runs/bugs").resolve()

    # One card stops at its first failure: its later rules read the chip and fields the earlier ones checked.
    def check_card(number, heading):
        name = heading.get_text(strip=True)
        card = f"Possible bug '{name}'"
        if not re.match(rf"{number}\.\s+\S", name):
            raise ValueError(f"{card}: cards are numbered 1., 2., ... in rank order; this is card {number}.")
        for part in card_parts(heading):
            if part.name == "p":
                split_fields(document, part)
        parts, fields = card_parts(heading), card_fields(heading)
        chips = chip_line(parts[0]) if parts and parts[0].name == "p" else None
        if not chips:
            raise ValueError(f"{card}: open with the evidence chip (*{'* or *'.join(BUG_EVIDENCE)}*) and the origin chip "
                             f"(*{'* or *'.join(BUG_ORIGIN)}*), joined by ' · '.")

        def value(label):
            paragraph = fields.get(label)
            return paragraph.get_text(" ", strip=True)[len(paragraph.strong.get_text(" ", strip=True)):].strip() if paragraph else ""

        where = fields["Where"].find_all("a", href=True) if "Where" in fields else []
        if not any(re.search(r"#L\d+", link["href"]) for link in where):
            raise ValueError(f"{card}: needs **Where:** with at least one pinned line.")
        for label in ("Trigger", "Who / impact"):
            if not value(label):
                raise ValueError(f"{card}: needs **{label}:** with its content.")
        impact = fields["Who / impact"]
        if not (any(re.search(r"#L\d+", link["href"]) for link in impact.find_all("a", href=True))
                or any(em.get_text(strip=True) == "reasoned, not run" for em in impact.find_all("em"))
                or "predicted:" in value("Who / impact").lower()):
            raise ValueError(f"{card}: **Who / impact:** shows its basis: a pinned line, *reasoned, not run*, or 'predicted:'.")
        fix = fields.get("Fix direction")
        if not (fix and re.match(r"Suggestion:\s*\S", value("Fix direction"))
                and any(em.get_text(strip=True) == "Suggestion:" for em in fix.find_all("em"))):
            raise ValueError(f"{card}: needs **Fix direction:** starting with *Suggestion:*.")
        tables = [table for part in parts for table in ([part] if part.name == "table" else part.find_all("table"))
                  if [th.get_text(" ", strip=True) for th in table.select("thead th")][1:] == ["Base", "Head"]]
        rows = [row.find_all("td") for row in tables[0].select("tbody tr")] if len(tables) == 1 else []
        if not rows or any(len(row) != 3 or not all(cell.get_text(strip=True) for cell in row) for row in rows):
            raise ValueError(f"{card}: needs one filled table with a label column, then exactly Base and Head.")
        if chips[1] == "no base pinned" and any(cell.get_text(" ", strip=True) != "no base pinned" for row in rows for cell in row[1:2]):
            raise ValueError(f"{card}: a no-base-pinned card reads *no base pinned* in every Base cell.")
        if chips[1] == "from an unrelated commit" and not re.search(r"\b[0-9a-f]{7,40}\b", value("Introduced by")):
            raise ValueError(f"{card}: a bug from an unrelated commit names that commit under **Introduced by:** as a SHA.")
        if chips[0] == "suspected, not run":
            if any(not cell.get_text(" ", strip=True).lower().startswith("predicted:") for row in rows for cell in row[1:][chips[1] == "no base pinned":]):
                raise ValueError(f"{card}: a suspected card starts each Base and Head value with 'predicted:'.")
            probe = fields.get("Probe that would settle it")
            following = probe.find_next_sibling() if probe else None
            if not (value("Probe that would settle it") or getattr(following, "name", None) == "pre"):
                raise ValueError(f"{card}: a suspected card needs **Probe that would settle it:** in place of a reproduction.")
            if "Reproduce" in fields:
                raise ValueError(f"{card}: a suspected card has no **Reproduce:**; a probe that ran makes it *we ran it*.")
        else:
            if "Reproduce" not in fields:
                raise ValueError(f"{card}: needs **Reproduce:** with the command, its output, and a link to the probe script under runs/bugs/.")
            if "Probe that would settle it" in fields:
                raise ValueError(f"{card}: a we-ran-it card shows its run under **Reproduce:**, not a probe still to run.")
            if any(row[2].get_text(" ", strip=True).lower().startswith("predicted:") for row in rows):
                raise ValueError(f"{card}: a we-ran-it card shows each Head value its run observed; only a Base value "
                                 "no run observed starts with 'predicted:'.")
            tail = parts[parts.index(fields["Reproduce"]):]
            if not any(part.name == "pre" or part.find("pre") for part in tail):
                raise ValueError(f"{card}: **Reproduce:** needs the command as a code fence.")
            scripts = []
            for link in (a for part in tail for a in part.find_all("a", href=True)):
                url = urlsplit(link["href"])
                if url.scheme or url.netloc or not url.path:
                    continue
                target = (note.parent / unquote(url.path)).resolve()
                if not target.is_relative_to(bugs) or not target.is_file():
                    raise ValueError(f"{card}: **Reproduce:** links {link['href']}; link the probe script as an existing file under runs/bugs/.")
                scripts.append(unquote(url.path))
            if not scripts:
                raise ValueError(f"{card}: **Reproduce:** needs a link to the probe script saved under runs/bugs/.")
            fence = next(pre for part in tail for pre in ([part] if part.name == "pre" else part.find_all("pre")))
            if not any(script in fence.get_text() for script in scripts):
                raise ValueError(f"{card}: the **Reproduce:** command runs the linked script; name {scripts[0]} in the fence.")
            if not any(part.name == "p" and re.match(r"Output:\s*\S", part.get_text(" ", strip=True)) for part in tail):
                raise ValueError(f"{card}: **Reproduce:** needs an 'Output:' line with an excerpt of what the probe printed.")
        # A closed shape: text outside the fields would carry claims that no field rule checks.
        # After Reproduce: one fence (the command) and one Output: line. After Probe: a fence only when the probe is that fence.
        seen, opened, fences, outputs = set(), None, 0, 0
        for part in parts[1:]:
            label = field_label(part)
            if label:
                if label in seen:
                    raise ValueError(f"{card}: **{label}:** appears twice.")
                seen.add(label)
                if label in ("Reproduce", "Probe that would settle it"):
                    opened, fences = label, (0 if label == "Reproduce" or not value(label) else 1)
            elif any(part is table for table in tables):
                continue
            elif opened and part.name == "pre":
                fences += 1
                if fences > 1:
                    raise ValueError(f"{card}: **{opened}:** holds one code fence; put the command in one fence.")
            elif opened == "Reproduce" and part.name == "p" and part.get_text(strip=True).startswith("Output:"):
                outputs += 1
                if outputs > 1 or "\n" in part.get_text() or not output_line(part):
                    raise ValueError(f"{card}: the Output: line is one line holding the output excerpt as inline code "
                                     "and the script link, nothing else.")
            else:
                raise ValueError(f"{card}: '{part.get_text(' ', strip=True)[:60]}' sits outside the card's fields. A card holds "
                                 "its chip line, its **Field:** paragraphs, the Base/Head table, and after **Reproduce:** or "
                                 "**Probe that would settle it:** a code fence and the Output: line; move the text into a field or cut it.")

    problems = []
    for number, heading in enumerate(cards, 1):
        keep(problems, check_card, number, heading)
    problems += [f"What to look at: item {item}: {gap}." for item, gap in bug_item_gaps(source)]
    linked = Counter(target for _, _, targets in bug_card_items(source).values() for target in set(targets))
    for heading in cards:
        if linked["#" + slug(heading.get_text())] != 1:
            problems.append(f"Possible bug '{heading.get_text(strip=True)}': link it from exactly one *you decide* or "
                             f"*check it* item in What to look at; {linked['#' + slug(heading.get_text())]} items link it.")
    raise_all(problems)


def bug_origin_gaps(source, base):
    """Card-origin problems against whether a base is pinned; cards without a chip line fail check_bug_cards instead."""
    problems = []
    for heading in bug_card_headings(parse(MARKDOWN.render(source))):
        parts = card_parts(heading)
        chips = chip_line(parts[0], first_line=True) if parts and parts[0].name == "p" else None
        if not chips or (chips[1] == "no base pinned") != base:
            continue
        card = f"Possible bug '{heading.get_text(strip=True)}'"
        problems.append(f"{card}: a base is pinned, so attribute its origin; *no base pinned* is for reports without a base." if base
                        else f"{card}: no base is pinned, so its origin is *no base pinned*.")
    return problems


def check_verification(source):
    """Validate the shared verification table wherever it is used, independently of PR structure."""
    problems = []
    for table in parse(MARKDOWN.render(source)).find_all("table"):
        columns = tuple(th.get_text(" ", strip=True) for th in table.select("thead th"))
        if columns[:1] != VERIFICATION_COLUMNS[:1]:
            continue
        rows = table.select("tbody tr")
        if columns != VERIFICATION_COLUMNS or not rows:
            problems.append(f"Verification: use a nonempty table with columns: {' | '.join(VERIFICATION_COLUMNS)}.")
            continue
        for row in rows:
            cells = row.find_all("td")
            if len(cells) != len(columns) or any(cell.get_text(strip=True) in ("", "-", "—", "TODO", "TBD") for cell in cells):
                problems.append("Verification: fill every table cell; state unknowns and their limits explicitly.")
                continue
            result, origin = (cell.get_text(" ", strip=True) for cell in cells[1:3])
            if result not in CHECK_RESULTS or origin not in CHECK_ORIGINS:
                problems.append("Verification: use the documented Result and Evidence origin values.")
            if (origin == "Source inspected" and result != "Not run") or (origin == "Proposed" and result not in ("Not run", "Blocked")):
                problems.append("Verification: source inspection must say Not run; proposed checks must say Not run or Blocked. They do not establish execution.")
            if origin in ("Executed here", "Recorded run") and result == "Not run":
                problems.append("Verification: executed or recorded evidence needs its actual result.")
            if origin in ("Executed here", "Recorded run") and not cells[0].find("a", href=True):
                problems.append("Verification: an execution result needs a linked run record in Check or scenario.")
    raise_all(problems)


def check_bug_probes(document, bugs, rows):
    """One Verification row links #possible-bugs, and its result retains the actual evidence origin (report-format.md)."""
    probes = [row for row in rows if any(link["href"] == "#" + slug(BUG_SECTION) for link in row[0].find_all("a", href=True))]
    if len(probes) != 1:
        raise ValueError(f"Verification: needs exactly one row whose Check or scenario links [Bug probes](#{slug(BUG_SECTION)}); "
                         f"{len(probes)} found.")
    row = probes[0]
    result, origin = (cell.get_text(" ", strip=True) for cell in row[1:3])
    chips = [chip_line(card_parts(heading)[0], first_line=True)[0] for heading in bug_card_headings(document)]
    if bugs.startswith(BUG_FORMS[0]):
        if result not in ("Not run", "Blocked") or origin != "Proposed":
            raise ValueError("Verification: a search that has not run uses Not run or Blocked / Proposed in Bug probes.")
    elif "we ran it" in chips:
        if result not in ("Passed", "Failed", "Mixed", "Blocked") or origin not in ("Executed here", "Recorded run"):
            raise ValueError("Verification: Bug probes with a 'we ran it' card needs an actual execution result / Executed here or Recorded run.")
    if origin in ("Executed here", "Recorded run") and ("we ran it" not in chips or origin == "Recorded run"):
        if result == "Not run":
            raise ValueError("Verification: Bug probes with executed or recorded evidence needs its actual result.")
        if not any(a["href"] != "#possible-bugs" for a in row[0].find_all("a", href=True)):
            raise ValueError("Verification: Bug probes needs a linked run record for reused checks or executions without an executed card.")
    elif bugs.startswith(BUG_FORMS[1]) and origin not in ("Source inspected", "Executed here", "Recorded run"):
        raise ValueError("Verification: a source-only search with no bugs found uses Source inspected in Bug probes.")


def check_review(source, note):
    """The final review contract; presence and vocabulary are not proof of investigation.
    Raises every failure at once (Failures)."""
    raise_all(review_problems(source, note))


def opening_gap(source, kind):
    """The problem when the opening lacks Bottom line, Reviewed, or Coverage; kind names the report."""
    opening = source.split("\n## ", 1)[0]
    if not all(re.search(rf"\*\*{label}:\*\*\s*\S", opening) for label in ("Bottom line", "Reviewed", "Coverage")):
        return [f"{kind} opening requires Bottom line, Reviewed, and Coverage with explicit scope and limits."]
    return []


def record_gaps(body, names):
    """Problems for each '### name' under Evidence and record that is not one nonempty section."""
    record = markdown_sections(body, 3)
    return [f"Evidence and record requires one nonempty '### {name}' section; state none or unknown when appropriate."
            for name in names if len([text for title, text in record if title == name]) != 1
            or not [text for title, text in record if title == name][0].strip()]


def verification_problems(document, verification, cards, cards_failed):
    """Problems in the Verification section: summaries, table, and the Bug probes row (judged against the cards)."""
    problems = []
    if not all(label in verification for label in ("Tests inspected:", "Recorded runs:", "Executed:")):
        problems.append("Verification: retain Tests inspected:, Recorded runs:, and Executed: summaries, including explicit none.")
    checked = (keep(problems, review_table, verification, VERIFICATION_COLUMNS, "Verification", problems)
               if parse(MARKDOWN.render(verification)).find("table") or not re.search(r"^No checks selected:\s*\S", verification, re.M)
               else [])
    keep(problems, check_verification, verification)
    # The Bug probes row is judged against the cards and the Verification table; when either failed, its verdict
    # would only repeat that failure.
    if not cards_failed and checked is not None:
        keep(problems, check_bug_probes, document, cards.strip(), checked)
    return problems


def anchor_gaps(document, kind):
    """Problems when two headings share an anchor, plus the ids for the link check."""
    ids = [slug(tag.get_text()) for tag in document.find_all(re.compile(r"^h[1-6]$"))]
    return ids, ([f"{kind} headings need distinct names for stable anchors."] if len(ids) != len(set(ids)) else [])


def review_problems(source, note):
    """Every failure of the review contract, in reading order; empty when the review passes."""
    problems = []
    front, source = split_front_matter(source)
    keep(problems, check_front_matter, front, review=True)
    document = parse(MARKDOWN.render(source))
    if len(document.find_all("h1")) != 1 or document.find().name != "h1":
        problems.append("Review requires one opening H1 title.")
    keep(problems, check_prompts, source)
    sections = markdown_sections(source, 2)
    names = [name for name, _ in sections]
    required = ("What the change does", "Requirements", "What to look at", "Behavior changes", "Questions for the author", "Verification", "Evidence and record")
    for name in required:
        if names.count(name) != 1:
            problems.append(f"Review requires exactly one '## {name}' section.")
    if any(names.count(name) != 1 for name in required):
        return problems  # Stop: the checks below read these sections, and without them they would only crash.
    bodies = dict(sections)
    problems += record_gaps(bodies["Evidence and record"], ("Gaps", "Provenance", *(() if "Reading plan" in bodies else ("Changed files",))))
    for name in ("Questions for the author", "Reading plan"):
        if name in bodies and (names.count(name) != 1 or not bodies[name].strip()):
            problems.append(f"Review requires one nonempty '## {name}' section; state none when appropriate.")
    problems += opening_gap(source, "Review")
    before = len(problems)
    keep(problems, check_bug_cards, source, note)
    problems += bug_origin_gaps(source, base=True)
    cards_failed = len(problems) > before
    behavior = bodies["Behavior changes"]
    parts = markdown_sections(behavior, 3)
    if not parts and not re.search(r"^(?:No consequential behavior change|Not yet inspected):\s*\S", behavior, re.M):
        problems.append("Behavior changes: name each behavior under H3, or state 'No consequential behavior change:' / 'Not yet inspected:' with scope and evidence.")
    for name, body in parts:
        labels = {tag.get_text().rstrip(":").lower() for tag in parse(MARKDOWN.render(body)).find_all("strong")
                  if tag.parent.get_text(" ", strip=True).replace(tag.get_text(" ", strip=True), "", 1).strip()}
        for label in ("Purpose and tradeoff", "Conditions", "Consumers", "Preserved", "Open question"):
            if label.lower() not in labels:
                problems.append(f"Behavior '{name}' needs **{label}:** with content or an explicit gap.")
        for row in keep(problems, review_table, body, SCENARIO_COLUMNS, f"Behavior '{name}'", problems) or []:
            if not row[4].find("a", href=True) and not re.search(r"unknown|not (?:yet )?(?:inspected|verified|run)", row[4].get_text(), re.I):
                problems.append(f"Behavior '{name}': each scenario needs linked evidence or an explicit unknown.")
    behavior_targets = {"#" + slug(name) for name, _ in parts} or {"#behavior-changes"}
    for row in keep(problems, review_table, bodies["Requirements"], REQUIREMENT_COLUMNS, "Requirements", problems) or []:
        status = row[1].get_text(" ", strip=True)
        if status not in FULFILLMENT:
            problems.append(f"Requirements: unsupported status '{status}'; use {', '.join(FULFILLMENT)}.")
        if status != "Needs clarification" and not row[0].find("a", href=True):
            problems.append("Requirements: link the intent source, or use Needs clarification for missing intent.")
        if not any(link.get("href") in behavior_targets for link in row[2].find_all("a", href=True)):
            problems.append("Requirements: link Behavior and evidence to a named behavior section.")
    problems += verification_problems(document, bodies["Verification"], bodies.get(BUG_SECTION, ""), cards_failed)
    ids, gaps = anchor_gaps(document, "Review")
    problems += gaps
    keep(problems, check_links, link_targets(document), note, ids)
    return problems


ACCEPTANCE_SECTIONS = ("What was asked", "What to look at", "Requirements", "Nobody asked for this", BUG_SECTION,
                       "Questions for the author", "Verification", "Evidence and record")
ACCEPTANCE_RECORD = ("Gaps", "Provenance", "Feature scope")


def check_acceptance(source, note):
    """The final acceptance contract; presence and vocabulary are not proof of investigation.
    Raises every failure at once (Failures)."""
    raise_all(acceptance_problems(source, note))


def acceptance_problems(source, note):
    """Every failure of the acceptance contract, in reading order; empty when the report passes.
    source includes its front matter. ponytail: checks shape and evidence markers, not whether a requirement is met."""
    problems = []
    front, source = split_front_matter(source)
    keep(problems, check_front_matter, front, review=True)
    if "head" not in front:
        problems.append("Acceptance front matter requires head as a full commit SHA.")
    document = parse(MARKDOWN.render(source))
    if len(document.find_all("h1")) != 1 or document.find().name != "h1":
        problems.append("Acceptance requires one opening H1 title.")
    keep(problems, check_prompts, source)
    sections = markdown_sections(source, 2)
    names = [name for name, _ in sections]
    for name in ACCEPTANCE_SECTIONS:
        if names.count(name) != 1:
            problems.append(f"Acceptance report requires exactly one '## {name}' section.")
    if any(names.count(name) != 1 for name in ACCEPTANCE_SECTIONS):
        return problems  # Stop: the checks below read these sections, and without them they would only crash.
    bodies = dict(sections)
    problems += opening_gap(source, "Acceptance")
    problems += record_gaps(bodies["Evidence and record"], ACCEPTANCE_RECORD)
    sources = markdown_sections(bodies["Requirements"], 3)
    if not sources:
        problems.append("Requirements: put each source's table under its own '### <source title>'.")
    for name, body in sources:
        for row in keep(problems, review_table, body, REQUIREMENT_COLUMNS, f"Requirements '{name}'", problems) or []:
            status = row[1].get_text(" ", strip=True)
            if status not in FULFILLMENT:
                problems.append(f"Requirements '{name}': unsupported status '{status}'; use {', '.join(FULFILLMENT)}.")
            if status != "Needs clarification" and not row[0].find("a", href=True):
                problems.append(f"Requirements '{name}': link the intent source, or use Needs clarification for missing intent.")
            if not row[2].find("a", href=True) and not re.search(r"not verified|not inspected|unknown", row[2].get_text(), re.I):
                problems.append(f"Requirements '{name}': each Behavior and evidence cell links pinned source, a run record, "
                                "or a bug card, or states not verified, not inspected, or unknown.")
    if len({name for name, _ in sources}) != len(sources):
        problems.append("Requirements: give each source heading a distinct name.")
    unasked = bodies["Nobody asked for this"]
    if not (re.search(r"^\s*(?:[-*+]|\d+\.|\|)\s", unasked, re.M) or re.search(r"^None found:\s*\S", unasked, re.M)):
        problems.append("Nobody asked for this: list the delivered behavior no source asked for, or write 'None found:' with the scope inspected.")
    questions = bodies["Questions for the author"]
    if not all(label in questions for label in ("**Spec owner:**", "**Author:**")):
        problems.append("Questions for the author: keep **Spec owner:** and **Author:** lists; state none with the reason.")
    before = len(problems)
    keep(problems, check_bug_cards, source, note)
    problems += bug_origin_gaps(source, base="base" in front)
    cards_failed = len(problems) > before
    problems += verification_problems(document, bodies["Verification"], bodies.get(BUG_SECTION, ""), cards_failed)
    ids, gaps = anchor_gaps(document, "Acceptance report")
    problems += gaps
    keep(problems, check_links, link_targets(document), note, ids)
    return problems


def check_learning_plan(source):
    """Check declared question and decision coverage, not completeness or factual support."""
    document = parse(MARKDOWN.render(source))
    headings = {slug(h.get_text()): h for h in document.find_all(re.compile(r"^h[1-6]$"))}

    def linked_headings(element, label, slices=False):
        targets = []
        for link in element.select('a[href^="#"]'):
            heading = headings.get(unquote(link["href"][1:]))
            if heading is None:
                raise ValueError(f"{label}: missing heading {link['href']}.")
            if slices:
                section = heading.find_previous("h2")
                if heading.name != "h3" or section is None or slug(section.get_text()) != "delivery-slices":
                    raise ValueError(f"{label}: link to a named slice under Delivery slices.")
            targets.append(heading)
        if not targets:
            raise ValueError(f"{label}: include a local heading link.")
        return targets

    problems = []
    for table in document.find_all("table"):
        columns = tuple(th.get_text(" ", strip=True) for th in table.select("thead th"))
        if columns not in (QUESTION_COLUMNS, DECISION_COLUMNS, BLOCKER_COLUMNS):
            continue
        label = "Questions answered" if columns == QUESTION_COLUMNS else "Decisions" if columns == DECISION_COLUMNS else "Blockers"
        if not table.select("tbody tr"):
            problems.append(f"{label}: add rows or remove the unused table.")

        # One row stops at its first failure: its later rules read the cells and links the earlier ones checked.
        def check_row(row, columns=columns, label=label):
            cells = row.find_all("td")
            if len(cells) != len(columns) or any(not cell.get_text(strip=True) for cell in cells):
                raise ValueError(f"{label}: fill every cell, including gaps and next actions.")
            if columns == QUESTION_COLUMNS:
                if cells[1].get_text(strip=True) not in QUESTION_STATUSES:
                    raise ValueError("Questions answered: use Answered, Partial, or Unresolved.")
                linked_headings(cells[2], label)
            elif columns == BLOCKER_COLUMNS:
                linked_headings(cells[2], label, slices=True)
            else:
                status = cells[1].get_text(strip=True)
                if status not in DECISION_STATUSES:
                    raise ValueError("Decisions: use Agreed, Proposed, Open, Reopened, or Superseded.")
                if status != "Agreed":
                    return
                targets = linked_headings(cells[0], label)
                section = targets[0].find_previous("h2")
                if (len(targets) != 1 or targets[0].name != "h3" or section is None
                        or slug(section.get_text()) != "decisions"):
                    raise ValueError("Agreed decision: link to one named decision detail heading.")
                fields = {}
                for sibling in targets[0].next_siblings:
                    if getattr(sibling, "name", None) in ("h1", "h2", "h3"):
                        break
                    if (getattr(sibling, "name", None) == "p" and sibling.strong
                            and sibling.contents[0] is sibling.strong):
                        key = sibling.strong.get_text().rstrip(":")
                        if sibling.get_text(strip=True) != sibling.strong.get_text(strip=True):
                            fields[key] = sibling
                for field in ("Acceptance", "Delivery", "Authority"):
                    if field not in fields:
                        raise ValueError(f"Agreed decision {targets[0].get_text()}: add {field} with its content.")
                linked_headings(fields["Delivery"], "Decision delivery", slices=True)

        for row in table.select("tbody tr"):
            keep(problems, check_row, row)
    raise_all(problems)


def check_review_tables(source, html):
    """Keep structured comparisons, decisions, fulfillment, and results faithful to Markdown."""
    def owner_of(element):
        section = element.find_previous("h2")
        heading = next((heading for heading in element.find_all_previous(["h2", "h3"])
                        if not heading.find_parent(class_="scenario")), None)
        return (section.get_text() if section else "", heading.get_text() if heading else "")

    def rows(document):
        result = Counter()
        for table in document.find_all("table"):
            columns = tuple(th.get_text(" ", strip=True) for th in table.select("thead th"))
            if columns in (*COMPARISON_COLUMNS, *STATUS_TABLES):
                owner = owner_of(table)
                for row in table.select("tbody tr"):
                    result[(owner, columns, tuple(re.sub(r"\s+", " ", cell.get_text(" ", strip=True))
                                           for cell in row.find_all("td")))] += 1
        for scenario in document.select("article.scenario"):
            owner = owner_of(scenario)
            cells = scenario.select("[data-column]")
            columns = tuple(cell["data-column"] for cell in cells)
            if columns not in COMPARISON_COLUMNS:
                continue
            result[(owner, columns, tuple(re.sub(r"\s+", " ", cell.get_text(" ", strip=True))
                                         for cell in cells))] += 1
        return result
    if rows(parse(MARKDOWN.render(source))) != rows(parse(html).main):
        raise ValueError("Structured table content differs between Markdown and HTML; regenerate after changing statuses, scenarios, or results.")


def check_diagrams(source, note):
    """Every Mermaid fence is followed by its source map: one linked item per node and edge (EVIDENCE.md).
    Raises every diagram's failures at once (Failures)."""
    lines = source.split("\n")
    ids = {slug(h.get_text()) for h in parse(MARKDOWN.render(source)).find_all(re.compile(r"^h[1-6]$"))}
    problems = []
    i = 0
    while i < len(lines):
        opening = re.match(r"^(`{3,}|~{3,})\s*mermaid\b", lines[i])
        if not opening:
            i += 1
            continue
        fence, start = opening.group(1), i
        j = i + 1
        while j < len(lines) and not re.match(rf"^{re.escape(fence)}\s*$", lines[j]):
            j += 1
        # ponytail: counts drawing lines, not nodes and edges; a per-type parser if this floor proves too low.
        drawn = sum(1 for line in lines[i + 2:j] if line.strip() and not UNDRAWN.match(line))
        k = j + 1
        while k < len(lines) and not lines[k].strip():
            k += 1
        if k < len(lines) and re.match(r"^\**Source map\**:?\s*$", lines[k], re.I):
            k += 1
        items = []
        while k < len(lines) and LIST_ITEM.match(lines[k]):
            items.append(lines[k])
            k += 1
        if not items:
            problems.append(f"Diagram at line {start + 1} has no source map: map each node and edge to source lines or explicitly proposed references (EVIDENCE.md).")
        for item in items:
            link = re.search(r"\]\(([^)\s]+)\)", item)
            visible = parse(MARKDOWN.render(item)).get_text(" ", strip=True)
            proposed = re.search(r"\bproposed\s*:", visible, re.I)
            if not link or (not proposed and not re.search(r"#L\d+", link.group(1))):
                requirement = "a linked proposal, decision, or requirement" if proposed else "a pinned line"
                problems.append(f"Source map item lacks {requirement}: {item.strip()[:80]}")
                continue
            href = link.group(1)
            url = urlsplit(href)
            if not (url.scheme or url.netloc) and url.path and not (note.parent / unquote(url.path)).is_file():
                problems.append(f"Source map points at a missing local file: {href}")
            else:
                keep(problems, check_links, [href], note, ids)
        if items and len(items) < drawn:
            problems.append(f"Diagram at line {start + 1} draws {drawn} lines but its source map has {len(items)} items: map every node and edge.")
        i = k
    raise_all(problems)


def check_peek(soup, front, repo, directory=None):
    data = soup.find("script", id="peek-data")
    if data is None:
        return
    if data.find_parent("main") is not None:
        raise ValueError("Keep the code peek data outside <main>.")
    try:
        payload = source_peek.decode(data.string or "")
    except ValueError:
        raise ValueError("Code peek data is malformed; re-render the page.") from None
    present = set(link_targets(soup.main))
    for href in payload["links"]:
        if href not in present:
            raise ValueError(f"Code peek for a link the report does not have: {href}")
    marked = {a["href"] for a in soup.main.select("a[data-peek]")}
    for href in payload["links"].keys() - marked:
        raise ValueError(f"Peekable link lacks data-peek: {href}")
    for href in marked - payload["links"].keys():
        raise ValueError(f"data-peek on a link without peek data: {href}")
    if payload["hljs"] != source_peek.highlighter(payload["files"], fence_languages(soup)):
        raise ValueError("Embedded highlighter differs from the vendored highlight.js; re-render the page.")
    for key, reason in source_peek.verify(payload, front, repo, directory):
        print(f"Embedded code not compared with git ({reason}): {key}", file=sys.stderr)


def check(source, html, note, repo=None):
    """Check mechanical invariants without rendering or judging page composition.
    Raises every failure at once (Failures)."""
    raise_all(page_problems(source, html, note, repo))


def markdown_problems(source, note):
    """The checks a Markdown note passes with or without its page."""
    problems = []
    for check_one, *args in ((check_prompts, source), (check_claims, source), (check_names, source), (check_attention, source),
                             (check_opening, source), (check_learning_plan, source), (check_verification, source), (check_diagrams, source, note)):
        keep(problems, check_one, *args)
    keep(problems, check_bug_cards, source, note, required=False)
    return problems


def page_problems(source, html, note, repo=None):
    """Every mechanical failure of the page against its note, in check order; empty when it passes."""
    original_source = source
    front, source = split_front_matter(source)
    problems = []
    keep(problems, check_front_matter, front)
    problems += markdown_problems(source, note)
    soup = parse(html)
    fingerprints = soup.find_all("meta", attrs={"name": "source-fingerprint"})
    if len(fingerprints) != 1 or fingerprints[0].get("content") != source_fingerprint(original_source):
        problems.append("HTML source fingerprint is missing or stale; reconcile the page with the current Markdown before checking.")
    expected = parse(MARKDOWN.render(source))
    ids = [tag["id"] for tag in soup.find_all(id=True)]
    if len(ids) != len(set(ids)):
        problems.append("Duplicate IDs: use distinct headings and anchors.")
    if len(soup.find_all("main")) != 1:
        # Stop: every check below reads the one main region.
        return problems + ["Use one main reading region."]
    keep(problems, check_review_tables, source, html)
    keep(problems, check_label_key, source, html)
    expected_code = Counter(code.get_text() for code in expected.find_all("code"))
    actual_code = Counter(code.get_text() for code in soup.main.find_all("code"))
    if expected_code - actual_code or actual_code.keys() - expected_code.keys():
        problems.append("Displayed code differs from the Markdown code blocks or inline code.")
    expected_links = Counter(link_targets(expected)) + Counter(a["url"] for a in fence_attributes(source) if a.get("url"))
    actual_links = Counter(link_targets(soup.main))
    if expected_links - actual_links:
        problems.append("Source links differ between Markdown and HTML.")
    for href in actual_links.keys() - expected_links.keys():
        url = urlsplit(href)
        if not href.startswith("#") and (url.scheme or url.netloc or unquote(url.path) != note.name):
            problems.append(f"Add the source link to Markdown first: {href}")
    try:
        check_peek(soup, front, repo, note.parent)
    except ValueError as error:
        problems.append(str(error))
    except (AttributeError, KeyError, TypeError, EOFError, OSError, IndexError):
        problems.append("Code peek data is malformed; re-render the page.")
    if any(pre.get("tabindex") != "0" for pre in soup.find_all("pre")):
        problems.append("Code blocks need keyboard scrolling.")
    if any(table.parent.get("tabindex") != "0" for table in soup.find_all("table")):
        problems.append("Tables need keyboard scrolling.")
    keep(problems, check_links, link_targets(soup), note.with_suffix(".html"), ids)
    if soup.find_all(["link", "iframe", "object", "embed", "form", "base"]) or soup.select("script[src], img[src], video, audio, [srcset]"):
        problems.append("Keep the reading page self-contained. External assets and embedded applications are unsupported.")
    for tag in soup.select("svg [href], svg [xlink\\:href]"):
        href = tag.get("href", tag.get("xlink:href", ""))
        if tag.name != "a" and (not href.startswith("#") or href[1:] not in ids):
            problems.append("SVG assets must reference an existing element in this page.")
    styles = "\n".join([tag.get_text() for tag in soup.find_all("style")]
                       + [tag["style"] for tag in soup.select("[style]")]
                       + [tag[attr] for tag in soup.select("svg, svg *")
                          for attr in ("fill", "stroke", "filter", "clip-path", "mask", "cursor",
                                       "marker-start", "marker-mid", "marker-end") if attr in tag.attrs])
    # ponytail: this checks literal CSS URLs, not arbitrary CSS or JavaScript.
    # The agent's page check reads the remaining styles and scripts for other requests.
    if re.search(r"@import", styles, re.I):
        problems.append("Styles must not load external assets.")
    for target in re.findall(r"url\s*\(([^)]*)\)", styles, re.I):
        target = target.strip().strip("\"'")
        if target.startswith("data:font/woff2;base64,"):
            try:
                font = base64.b64decode(target.split(",", 1)[1], validate=True)
            except (ValueError, binascii.Error):
                problems.append("Invalid embedded WOFF2 font.")
                continue
            if not font.startswith(b"wOF2"):
                problems.append("Invalid embedded WOFF2 font.")
            continue
        if not target.startswith("#") or target[1:] not in ids:
            problems.append("CSS URLs must reference an existing element in this page or an embedded WOFF2 font.")
    return problems


def main():
    parser = argparse.ArgumentParser(description="Optionally render a reading page, or check agent-authored HTML with --check. Does not judge prose or start a browser.")
    parser.add_argument("note", type=Path, help="authoritative .md note; HTML is written beside it")
    parser.add_argument("--check", action="store_true", help="check the existing HTML without rewriting it")
    parser.add_argument("--markdown-only", action="store_true", help="with --check, validate only Markdown even when an HTML companion exists")
    parser.add_argument("--review", action="store_true", help="require the current PR report structure and evidence table contract")
    parser.add_argument("--acceptance", action="store_true", help="require the acceptance report structure and evidence table contract")
    parser.add_argument("--sync-labels", action="store_true", help="refresh the shared status definitions in Markdown before rendering or checking")
    parser.add_argument("--diagram-renderer", choices=("auto", "mermaid", "beautiful-mermaid"), default="auto",
                        help="diagram engine; auto uses Beautiful Mermaid when npm ci in skills/diagram-renderer installed it and it runs, else the Mermaid CLI")
    parser.add_argument("--repo", type=Path,
                        help="git checkout that holds the cited commits (default: the repository containing the note)")
    args = parser.parse_args()
    if args.markdown_only and not args.check:
        parser.error("--markdown-only requires --check")
    if args.review and args.acceptance:
        parser.error("--acceptance and --review are separate contracts; pass one")
    note = args.note.resolve()
    if note.suffix != ".md":
        parser.error("the authoritative note must have a .md suffix")
    # Every check runs and every failure prints at once, numbered; nothing is written unless all pass.
    problems = []
    try:
        original = note.read_text()
        front, source = split_front_matter(original)
        keep(problems, check_front_matter, front)
        if args.sync_labels:
            source = with_label_key(source)
        if args.review:
            problems += review_problems(with_front_matter(original, source), note)
        if args.acceptance:
            problems += acceptance_problems(with_front_matter(original, source), note)
        output = note.with_suffix(".html")
        if args.check and (args.markdown_only or not output.exists()):
            problems += markdown_problems(source, note)
            document = parse(MARKDOWN.render(source))
            ids = {slug(heading.get_text()) for heading in document.find_all(re.compile(r"^h[1-6]$"))}
            hrefs = link_targets(document) + [attrs["url"] for attrs in fence_attributes(source) if attrs.get("url")]
            keep(problems, check_links, hrefs, note, ids)
            keep(problems, check_label_key, source, require=True)
            raise_all(problems)
            if args.sync_labels:
                note.write_text(with_front_matter(original, source))
            scope = "HTML was not checked" if args.markdown_only else f"{note.name} has no page"
            print(f"Markdown checks passed: {scope}; evidence markers, names, structure, template prompts, local links, and diagram source maps checked. Meaning is not checked.")
            return
        repo = args.repo or note.parent
        html = output.read_text() if args.check else render(with_front_matter(original, source), note.name,
                                                             args.diagram_renderer, repo=repo, directory=note.parent)
        problems += page_problems(with_front_matter(original, source), html, note, repo=repo)
        if args.check:
            keep(problems, check_label_key, source, require=True)
            if args.review or args.acceptance:
                keep(problems, check_source_diagrams, source, html)
        raise_all(problems)
        if args.sync_labels:
            note.write_text(with_front_matter(original, source))
        if not args.check:
            output.write_text(html)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Page check failed: {Failures(problems + getattr(error, 'messages', [str(error)]))}\n")
    print(f"Mechanical checks passed: {output.name}. Meaning agreement and visual quality are not checked; read the page as HTML-PAGES.md says.")


if __name__ == "__main__":
    main()
