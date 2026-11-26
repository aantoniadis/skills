"""The workbench layout for the structure skills' pages: a rework map (untangle) and a change card
(fit-change). The page renders as usual; this rearranges it around the structure view. Above the view:
the title, counts, and the summary lines. Below it: panels for what the user must decide, the findings,
and the rework or reshape steps, each a short copy of rows from the note's own tables. The full note
follows as text. Hovering or focusing a panel item lights up the files it names in the view
(workbench.js). The panels copy content and never move or drop it, so every check on the page still
compares it with the Markdown.
"""
import copy
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KINDS = ("rework-map", "change-card")
OPEN = re.compile(r"^\s*(?:open|not answered)\b", re.I)


def section(soup, identifier):
    return soup.main.find("section", id=identifier)


def table_rows(soup, identifier):
    """The cells of each body row of the first table in a section, or []."""
    found = section(soup, identifier)
    table = found.find("table") if found else None
    return [row.find_all("td") for row in table.select("tbody tr")] if table else []


def clone(soup, node):
    """A copy of a node for a panel: no ids, no peek markers, so the page keeps one of each."""
    if isinstance(node, str):
        return soup.new_string(str(node))
    copied = copy.copy(node)
    for tag in [copied, *copied.find_all(True)]:
        for attribute in ("id", "aria-labelledby", "aria-expanded"):
            tag.attrs.pop(attribute, None)
    return copied


def cell(soup, td, name="div", cls=None):
    holder = soup.new_tag(name, attrs={"class": cls} if cls else {})
    for child in list(td.contents):
        holder.append(clone(soup, child))
    return holder


def card(soup, cls, title, *parts):
    item = soup.new_tag("li", attrs={"class": f"wb-card {cls}", "tabindex": "0"})
    item.append(title)
    for part in parts:
        if part is not None:
            item.append(part)
    return item


def small(soup, label, td):
    line = soup.new_tag("p", attrs={"class": "wb-meta"})
    strong = soup.new_tag("span", attrs={"class": "wb-meta-label"})
    strong.string = label
    line.append(strong)
    for child in list(td.contents):
        line.append(clone(soup, child))
    return line


def panel(soup, title, identifier, items, empty):
    box = soup.new_tag("section", attrs={"class": "wb-panel", "aria-label": title})
    head = soup.new_tag("h2", attrs={"class": "wb-panel-title"})
    link = soup.new_tag("a", href=f"#{identifier}") if identifier and section(soup, identifier) else None
    if link:
        link.string = title
        head.append(link)
    else:
        head.string = title
    count = soup.new_tag("span", attrs={"class": "wb-count"})
    count.string = str(sum(1 for item in items if "wb-card" in item.get("class", [])))
    head.append(count)
    box.append(head)
    listing = soup.new_tag("ul", attrs={"class": "wb-list"})
    for item in items:
        listing.append(item)
    if not items:
        note = soup.new_tag("li", attrs={"class": "wb-empty"})
        note.string = empty
        listing.append(note)
    box.append(listing)
    return box


def heading(soup, text, cls="wb-sub"):
    item = soup.new_tag("li", attrs={"class": cls})
    item.string = text
    return item


def decide_items(soup):
    items = []
    behavior = table_rows(soup, "behavior-to-decide")
    if behavior:
        items.append(heading(soup, "Behavior to decide"))
    for cells in behavior:
        if len(cells) >= 3:
            items.append(card(soup, "wb-behavior", cell(soup, cells[0], "p", "wb-title"), small(soup, "Shown by ", cells[1]),
                              small(soup, "Next: ", cells[2])))
    questions = table_rows(soup, "questions-for-the-user")
    if questions:
        items.append(heading(soup, "Questions for you"))
    for cells in questions:
        if len(cells) >= 4:
            is_open = bool(OPEN.match(cells[3].get_text()))
            badge = soup.new_tag("span", attrs={"class": "wb-badge " + ("open" if is_open else "answered")})
            badge.string = "open" if is_open else "answered"
            title = cell(soup, cells[0], "p", "wb-title")
            title.insert(0, badge)
            items.append(card(soup, "wb-question" + (" is-open" if is_open else ""), title,
                              small(soup, "Until answered: " if is_open else "Answer: ", cells[2] if is_open else cells[3])))
    return items


def finding_items(soup, identifier):
    items = []
    for cells in table_rows(soup, identifier):
        if len(cells) < 4:
            continue
        kind = cells[1].get_text(" ", strip=True)
        chip = soup.new_tag("span", attrs={"class": "wb-kind", "data-kind": re.sub(r"\W+", "-", kind.lower()).strip("-")})
        chip.string = kind
        title = cell(soup, cells[0], "p", "wb-title")
        title.insert(0, chip)
        items.append(card(soup, "wb-finding", title, small(soup, "Where: ", cells[2]), small(soup, "", cells[3])))
    return items


def step_items(soup, identifier):
    items = []
    found = section(soup, identifier)
    steps = found.find("ol") if found else None
    if steps:
        for number, li in enumerate(steps.find_all("li", recursive=False), 1):
            body = soup.new_tag("p", attrs={"class": "wb-title"})
            mark = soup.new_tag("span", attrs={"class": "wb-step"})
            mark.string = str(number)
            body.append(mark)
            for child in list(li.contents):
                body.append(clone(soup, child))
            items.append(card(soup, "wb-step-card", body))
    return items


def lock_items(soup):
    items = []
    rows = table_rows(soup, "lock-tests")
    if rows:
        items.append(heading(soup, f"Lock tests ({len(rows)}), each red under its break"))
    for cells in rows:
        if len(cells) >= 4:
            items.append(card(soup, "wb-lock", cell(soup, cells[0], "p", "wb-title"), small(soup, "Locks: ", cells[1]),
                              small(soup, "Red under: ", cells[2])))
    return items


def target_line(soup):
    found = section(soup, "targets")
    if not found:
        return None
    first = next((p for p in found.find_all("p") if p.get_text().startswith("Recommendation:")), None)
    return clone(soup, first) if first else None


def chips(soup, kind):
    """Counts for the top bar: what needs the user, what was found, what protects the rework."""
    count = lambda identifier: len(table_rows(soup, identifier))
    open_questions = sum(1 for cells in table_rows(soup, "questions-for-the-user") if len(cells) >= 4 and OPEN.match(cells[3].get_text()))
    findings = "findings" if kind == "rework-map" else "structure-findings"
    values = [("decide", count("behavior-to-decide"), "to decide"), ("open", open_questions, "open questions"),
              ("finding", count(findings), "findings"), ("lock", count("lock-tests"), "lock tests")]
    bar = soup.new_tag("div", attrs={"class": "wb-chips", "aria-label": "Counts"})
    for cls, value, label in values:
        if cls == "lock" and kind != "rework-map":
            continue
        chip = soup.new_tag("span", attrs={"class": f"wb-chip {cls}" + (" zero" if not value else "")})
        number = soup.new_tag("b")
        number.string = str(value)
        chip.append(number)
        chip.append(" " + label)
        bar.append(chip)
    return bar


def summary(soup, overview):
    """The bold opening lines, side by side; the rest of the opening stays in the full text."""
    strip = soup.new_tag("div", attrs={"class": "wb-summary"})
    for paragraph in overview.find_all("p", recursive=False):
        label = paragraph.find("strong")
        if (label and paragraph.contents and paragraph.contents[0] is label
                and not paragraph.get_text().startswith(("Scope:", "Inspected source:", "Reviewed:"))):
            block = soup.new_tag("div", attrs={"class": "wb-summary-item"})
            title = soup.new_tag("h2", attrs={"class": "wb-summary-label"})
            title.string = label.get_text().rstrip(":")
            block.append(title)
            text = clone(soup, paragraph)
            text.find("strong").decompose()
            text["class"] = "wb-summary-text"
            block.append(text)
            strip.append(block)
    return strip if strip.contents else None


def build(soup, kind):
    """Rearrange a rendered page of a workbench kind in place."""
    main = soup.main
    soup.body["class"] = soup.body.get("class", []) + ["workbench"]
    overview = main.find("section")
    title = overview.find("h1")
    view = main.find("figure", class_="structure-view")
    top = soup.new_tag("header", attrs={"class": "wb-top"})
    heading_row = soup.new_tag("div", attrs={"class": "wb-heading"})
    heading_row.append(title.extract())
    heading_row.append(chips(soup, kind))
    top.append(heading_row)
    nav = soup.find("nav", attrs={"aria-label": "Sections"})
    if nav:
        links = clone(soup, nav)
        links.attrs = {"class": "wb-nav", "aria-label": "Parts of this page"}
        top.append(links)
    strip = summary(soup, overview)
    hero = soup.new_tag("section", attrs={"class": "wb-hero", "aria-label": "Structure"})
    if view:
        place = soup.new_tag("p", attrs={"class": "wb-moved"})
        place.string = "The structure view is at the top of the page."
        view.insert_before(place)
        hero.append(view.extract())
    if kind == "rework-map":
        rework = lock_items(soup) + ([heading(soup, "Steps of the recommended target")] if section(soup, "rework-steps") else []) + step_items(soup, "rework-steps")
        target = target_line(soup)
        panels = [panel(soup, "Decide", "behavior-to-decide", decide_items(soup), "Nothing waits for you."),
                  panel(soup, "Findings", "findings", finding_items(soup, "findings"), "No structure findings."),
                  panel(soup, "Rework", "rework-steps", rework, "No rework proposed.")]
        if target is not None:
            target["class"] = "wb-target"
            panels[2].insert(1, target)
    else:
        panels = [panel(soup, "Decide", "questions-for-the-user", decide_items(soup), "Nothing waits for you."),
                  panel(soup, "Findings", "structure-findings", finding_items(soup, "structure-findings"), "No structure findings."),
                  panel(soup, "Reshape first", "reshape-first", step_items(soup, "reshape-first"), "The change fits: no reshape.")]
    grid = soup.new_tag("div", attrs={"class": "wb-panels"})
    for box in panels:
        grid.append(box)
    full = soup.new_tag("div", attrs={"class": "wb-full"})
    label = soup.new_tag("p", attrs={"class": "wb-full-label"})
    label.string = "The full text"
    full.append(label)
    for child in list(main.children):
        if getattr(child, "name", None) != "footer":
            full.append(child.extract())
    footer = main.find("footer")
    data = None
    if view and view.find(class_="sv-data"):
        data = soup.new_tag("section", attrs={"class": "wb-data", "aria-label": "Data and its keys"})
        for block in view.find_all(class_="sv-data"):
            data.append(block.extract())
    for block in (top, strip, hero if view else None, grid, data, full):
        if block is not None:
            (footer.insert_before(block) if footer else main.append(block))
    soup.body.extend(list(soup.__class__(assets(), "html.parser").contents))


def assets():
    return (f'<style class="workbench-style">{(ROOT / "workbench.css").read_text()}</style>'
            f'<script class="workbench-script">{(ROOT / "workbench.js").read_text()}</script>')
