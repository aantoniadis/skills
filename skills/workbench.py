"""The page layout of the structure skills' notes: a rework map (untangle) and a change card (fit-change).

The note leads with *In short* (the problem, what we propose, what you decide), then *What it does*, the
component's behavior as a spec with the tests that verify each behavior, then the map of each behavior to
the code, then one section per problem, each with its picture, its evidence, its proposed fix, and its
decision. This module arranges the rendered page around that reading order:

- the sidebar lists the problems under *Problems*, each with the state of its decision;
- the header carries counts: problems, possible bugs, and decisions that wait for the reader;
- *In short* gathers every decision still open, each linked to its problem, those that block a step first;
- each problem becomes an article: its kind and how sure the note is as tags, labelled paragraphs, code
  excerpts side by side, and the decision set apart; a problem written in brief, with no evidence of its
  own, is drawn compact;
- the design principles become a scorecard, today against proposed, with each item's evidence folded;
- each behavior of the spec is marked by how it is verified: tested, locked, or untested;
- each row of the behavior map links to the problem that holds its weak point;
- *How it works today* is reference, folded until opened.

It moves and copies the note's own elements; it writes no claim of its own. The theme is light; a button
switches to dark for a reader who wants it (workbench.js remembers the choice in this browser).
"""
import copy
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KINDS = ("rework-map", "change-card")
DECISIONS = ("default applied", "none needed", "decided", "open")  # the longest first: "open" is a prefix of none
WAITING = ("open", "default applied")


def section(soup, identifier):
    return soup.main.find("section", id=identifier)


def clone(soup, node):
    """A copy of a node for the overview: no ids, so the page keeps one of each."""
    if isinstance(node, str):
        return soup.new_string(str(node))
    copied = copy.copy(node)
    for tag in [copied, *copied.find_all(True)]:
        for attribute in ("id", "aria-labelledby", "aria-expanded"):
            tag.attrs.pop(attribute, None)
    return copied


def label_of(paragraph):
    """The bold label a paragraph starts with, without its colon, or None."""
    first = next((child for child in paragraph.children if not (isinstance(child, str) and not child.strip())), None)
    if getattr(first, "name", None) != "strong":
        return None
    return first.get_text(strip=True).rstrip(":")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def status_of(text):
    value = text.lower()
    return next((option for option in DECISIONS if value.startswith(option)), "open")


def kind_class(kind):
    if kind.startswith("behavior to decide"):
        return "bug"
    if kind.startswith("corner case"):
        return "corner"
    return "structure"


def problems(soup):
    """Group each problem's heading and the elements under it into an article, and return their facts."""
    found = []
    holder = section(soup, "problems")
    if not holder:
        return found
    for heading in holder.find_all("h3", recursive=False):
        parts = [heading]
        for sibling in heading.find_next_siblings():
            if sibling.name == "h3":
                break
            parts.append(sibling)
        article = soup.new_tag("article", attrs={"class": "problem", "aria-labelledby": heading.get("id", "")})
        heading.insert_before(article)
        for part in parts:
            article.append(part.extract())
        number = re.match(r"^\s*(\d+)\.\s*", heading.get_text())
        if number:  # the number becomes a badge; the heading's text is unchanged
            text = heading.find(string=True)
            if text is not None and text.lstrip().startswith(number.group(1)):
                rest = soup.new_string(text.lstrip()[len(number.group(0).lstrip()):])
                badge = soup.new_tag("span", attrs={"class": "problem-number"})
                badge.string = number.group(0).strip()
                text.replace_with(rest)
                rest.insert_before(badge)
        facts = {"id": heading.get("id", ""), "title": heading.get_text(" ", strip=True), "number": number.group(1) if number else "",
                 "kind": "", "status": "none needed", "decision": None, "when": "", "brief": True}
        grid = None
        for element in list(article.children):
            if getattr(element, "name", None) == "figure" and "code-card" in element.get("class", []):
                if grid is None:  # excerpts that follow each other sit side by side
                    grid = soup.new_tag("div", attrs={"class": "code-grid"})
                    element.insert_before(grid)
                grid.append(element.extract())
                continue
            if getattr(element, "name", None) is not None:
                grid = None
            if getattr(element, "name", None) != "p":
                continue
            label = label_of(element)
            if label == "Kind":
                element["class"] = element.get("class", []) + ["problem-facts"]
                facts["kind"] = element.get_text(" ", strip=True).split(":", 1)[1].split(" · ")[0].strip()
            elif label == "Decision":
                text = element.get_text(" ", strip=True).split(":", 1)[1].strip()
                facts["status"] = status_of(text)
                when = re.match(r"(?:open|default applied)\b[,;:]?\s*(blocks steps? [\d, and]+\d|can wait)", text.lower())
                facts["when"] = when.group(1) if when else ""
                box = soup.new_tag("div", attrs={"class": f"decision {slug(facts['status'])}"})
                element.insert_before(box)
                box.append(element.extract())
                facts["decision"] = box
            elif label:
                element["class"] = element.get("class", []) + ["field", f"field-{slug(label)}"]
                if label == "Evidence":
                    facts["brief"] = False
        article["class"] = article.get("class", []) + [kind_class(facts["kind"]), f"decision-{slug(facts['status'])}"]
        if facts["brief"]:
            article["class"].append("brief")
            tag = soup.new_tag("span", attrs={"class": "brief-tag"})
            tag.string = "in brief"
            heading.append(tag)
        found.append(facts)
    return found


def rail(soup, found):
    """Under *Problems* in each list of sections, one link per problem with the state of its decision."""
    for link in soup.select('nav a[href="#problems"]'):
        listing = soup.new_tag("ol", attrs={"class": "nav-problems"})
        for facts in found:
            item = soup.new_tag("li", attrs={"class": f"{kind_class(facts['kind'])} decision-{slug(facts['status'])}"})
            anchor = soup.new_tag("a", href=f"#{facts['id']}")
            anchor.string = facts["title"]
            mark = soup.new_tag("span", attrs={"class": "nav-status", "title": facts["status"]})
            item.extend([mark, anchor])
            listing.append(item)
        if found:
            following = link.find_next_sibling()
            if getattr(following, "name", None) == "ul":  # the template's plain list of the same headings
                following.decompose()
            link.insert_after(listing)


def header(soup, found):
    title = soup.main.find("h1")
    if not title:
        return
    opened = sum(1 for f in found if f["status"] == "open")
    defaults = sum(1 for f in found if f["status"] == "default applied")
    bugs = sum(1 for f in found if kind_class(f["kind"]) == "bug")
    counts = [("count-problems", len(found), "problem" if len(found) == 1 else "problems"),
              ("count-bugs", bugs, "possible bug" if bugs == 1 else "possible bugs"),
              ("count-waiting", opened, "decision open" if opened == 1 else "decisions open"),
              ("count-defaults", defaults, "default applied" if defaults == 1 else "defaults applied")]
    bar = soup.new_tag("p", attrs={"class": "report-counts"})
    for cls, value, words in counts:
        chip = soup.new_tag("span", attrs={"class": f"count {cls}" + (" zero" if not value else "")})
        number = soup.new_tag("b")
        number.string = str(value)
        chip.append(number)
        chip.append(" " + words)
        bar.append(chip)
    title.insert_after(bar)
    toggle = soup.new_tag("button", attrs={"type": "button", "class": "theme-toggle", "aria-pressed": "false"})
    toggle.string = "Dark theme"
    soup.body.insert(0, toggle)


def in_short(soup, found):
    holder = section(soup, "in-short")
    if not holder:
        return
    holder["class"] = holder.get("class", []) + ["in-short"]
    for paragraph in holder.find_all("p", recursive=False):
        label = label_of(paragraph)
        if label in ("The problem", "What we propose", "What you decide"):
            paragraph["class"] = paragraph.get("class", []) + ["field", f"field-{slug(label)}"]
    waiting = [f for f in found if f["status"] in WAITING and f["decision"] is not None]
    if not waiting:
        return
    box = soup.new_tag("div", attrs={"class": "waiting", "role": "region", "aria-label": "Decisions that wait for you"})
    head = soup.new_tag("h3", attrs={"class": "waiting-title"})
    head.string = "Waiting for your decision"
    box.append(head)
    listing = soup.new_tag("ul")
    waiting.sort(key=lambda f: not f["when"].startswith("blocks"))  # what blocks the rework is answered first
    for facts in waiting:  # an index: the decision itself stands under its problem
        item = soup.new_tag("li", attrs={"class": f"decision-{slug(facts['status'])}"})
        state = soup.new_tag("span", attrs={"class": "waiting-state"})
        state.string = facts["status"]
        link = soup.new_tag("a", href=f"#{facts['id']}")
        link.string = facts["title"].removesuffix(" in brief")
        item.extend([state, link])
        if facts["when"]:
            when = soup.new_tag("span", attrs={"class": "waiting-when" + (" blocks" if facts["when"].startswith("blocks") else "")})
            when.string = facts["when"]
            item.append(when)
        listing.append(item)
    box.append(listing)
    anchor = holder.find("p", class_="field-what-you-decide") or holder.find_all("p", recursive=False)[-1]
    following = anchor.find_next_sibling()
    if getattr(following, "name", None) in ("ol", "ul"):  # the note's own list of decisions comes first
        anchor = following
    anchor.insert_after(box)


def reference(soup):
    """*How it works today* folds until opened: it is the evidence behind the problems, not the argument."""
    holder = section(soup, "how-it-works-today")
    if not holder:
        return
    heading = holder.find("h2")
    parts = [child for child in list(holder.children) if child is not heading and getattr(child, "name", None)]
    names = [h.get_text(" ", strip=True) for h in holder.find_all("h3")]
    details = soup.new_tag("details", attrs={"class": "reference"})
    summary = soup.new_tag("summary")
    summary.string = "Open the reference" + (f": {', '.join(names).lower()}" if names else "")
    details.append(summary)
    for part in parts:
        details.append(part.extract())
    holder.append(details)


def spec(soup):
    """Mark each behavior of *What it does* by its verification, so untested behavior stands out."""
    holder = section(soup, "what-it-does")
    if not holder:
        return
    for item in holder.find_all("li"):
        verified = re.search(r"Verified by:\s*(tested|locked|untested)", item.get_text(" ", strip=True), re.I)
        if verified:
            item["class"] = item.get("class", []) + ["behavior", f"verified-{verified.group(1).lower()}"]


RESULTS = ("not applicable", "broken", "met")


def scorecard(soup):
    """The design principles as a grid of today against proposed; each item's evidence folds beneath it."""
    heading = soup.main.find("h3", id="design-principles")
    listing = heading.find_next_sibling() if heading else None
    if getattr(listing, "name", None) not in ("ul", "ol"):
        return
    table = soup.new_tag("table", attrs={"class": "scorecard"})
    head = soup.new_tag("thead")
    row = soup.new_tag("tr")
    for text in ("Principle", "Today", "Proposed"):
        cell = soup.new_tag("th", attrs={"scope": "col"})
        cell.string = text
        row.append(cell)
    head.append(row)
    table.append(head)
    body = soup.new_tag("tbody")
    fixed = 0
    for item in listing.find_all("li", recursive=False):
        name = item.strong.get_text(strip=True).rstrip(":") if item.strong else ""
        rest = item.get_text(" ", strip=True).split(":", 1)[-1].strip().lower()
        pair = re.match(r"(not applicable|broken|met)\s*(?:→|->)\s*(not applicable|broken|met)", rest)
        today, proposed = pair.groups() if pair else (("not applicable",) * 2 if rest.startswith("not applicable") else ("", ""))
        fixed += today == "broken" and proposed == "met"
        row = soup.new_tag("tr")
        cell = soup.new_tag("th", attrs={"scope": "row"})
        cell.string = name
        row.append(cell)
        for value in (today, proposed):
            cell = soup.new_tag("td")
            chip = soup.new_tag("span", attrs={"class": f"result result-{slug(value) or 'unknown'}"})
            chip.string = value or "unknown"
            cell.append(chip)
            row.append(cell)
        body.append(row)
    table.append(body)
    caption = soup.new_tag("caption")
    caption.string = f"The rework restores {fixed} of {len(listing.find_all('li', recursive=False))} principles."
    table.insert(0, caption)
    holder = soup.new_tag("div", attrs={"class": "table-scroll scorecard-box", "tabindex": "0", "role": "region",
                                         "aria-label": "Design principles scorecard"})
    holder.append(table)
    details = soup.new_tag("details", attrs={"class": "scorecard-evidence"})
    summary = soup.new_tag("summary")
    summary.string = "The evidence for each principle"
    details.append(summary)
    listing.insert_before(holder)
    holder.insert_after(details)
    details.append(listing.extract())


def problem_links(soup, found):
    """A behavior-map row names its problem by number; point it at the problem's section."""
    by_number = {f["number"]: f["id"] for f in found}
    for link in soup.select("a.bm-problem[data-problem]"):
        if link["data-problem"] in by_number:
            link["href"] = f"#{by_number[link['data-problem']]}"


def build(soup, kind):
    """Arrange a rendered page of a structure note in place."""
    soup.body["class"] = soup.body.get("class", []) + ["report", kind]
    found = problems(soup)
    spec(soup)
    scorecard(soup)
    problem_links(soup, found)
    rail(soup, found)
    header(soup, found)
    in_short(soup, found)
    reference(soup)
    soup.body.extend(list(soup.__class__(assets(), "html.parser").contents))


def assets():
    return (f'<style class="workbench-style">{(ROOT / "workbench.css").read_text()}</style>'
            f'<script class="workbench-script">{(ROOT / "workbench.js").read_text()}</script>')
