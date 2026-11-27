"""The pictures of a rework map and a change card.

- The structure view: files grouped by design part, the dependencies between them, and the places that
  decide each rule, today and under the proposal; plus a table of who writes and reads each key of
  shapeless data. The author writes it once, as a `structure-view` fence of JSON.
- A focused view: a `structure-focus` fence names rules and files of that data, and the page draws only
  those, today and proposed side by side, beside the problem they belong to.
- A change history: a `change-history` fence lists the places that decide one rule and the commits that
  changed it; the page draws which places each commit changed, and marks the places it missed.
- A behavior map: a `behavior-map` fence lists the component's behaviors and the files that decide, call
  through, or store state for each; the page draws one row per behavior and one column per file, and names
  each row's weak point.

A file of the structure view can carry a module change the plan proposes: `"renamed": "<new path>"`,
`"removed": true`, or `"added": true`. Today shows a file to be added as an outline; the proposal shows a
removed file struck through and a renamed file under its new path. A merge removes files and adds or keeps
one; a split removes one and adds several.

render_page.py lays them out here as static SVG, so the page reads without scripts; structure-view.js adds
the Today/Proposed switch and rule selection to the full view. check() is the Markdown check of the fences.
"""
import json
import math
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ("as stated", "not stated", "not found", "not compared")
# The arrow and line style of each result, as a class name.
STYLES = tuple(r.replace(" ", "-") for r in RESULTS)
OUTCOMES = {"moves": "moves to its owner", "stays": "stays where it is", "waits": "waits for your answer"}
PARTLY = "partly waits for your answer"
PIN = re.compile(r"^(?:proposed\b.*|[\w./@+-]+\.\w{1,6}:\d+(?:-\d+)?(?:,\s*[\w./@+-]+\.\w{1,6}:\d+(?:-\d+)?)*)$")
# Each carries a white letter at 6:1 or better.
COLORS = ("#1d6d73", "#8a5508", "#5a48a3", "#2c6e44", "#a03a66", "#475a6c", "#8f3f22", "#2a5ea8")
BOX_W, GAP, LANE_PAD, HEAD, CHANNEL, SIDE_GAP, SIDE_W, DOT, PER_ROW = 196, 34, 16, 32, 50, 56, 188, 26, 6
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def problems(data):
    """What makes the data unusable or unsupported, as messages; empty when it passes."""
    found = []
    if not isinstance(data, dict):
        return ["the fence holds no JSON object"]
    parts, files = data.get("parts"), data.get("files")
    if not isinstance(parts, list) or not isinstance(files, list) or not files:
        return ["give `parts` (the design's parts, in the direction dependencies may point, or [] when the project states none) and `files`"]
    part_ids = [p.get("id") for p in parts]
    file_ids = [f.get("id") for f in files]
    for label, ids in (("part", part_ids), ("file", file_ids)):
        if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
            found.append(f"every {label} needs a unique `id`")
    for f in files:
        if f.get("part") not in part_ids and f.get("part") != "outside":
            found.append(f"file {f.get('id')}: `part` must be a part id or \"outside\"")
        if not f.get("path"):
            found.append(f"file {f.get('id')}: give its `path`")
        changes = [key for key in ("renamed", "removed", "added") if f.get(key)]
        if len(changes) > 1:
            found.append(f"file {f.get('id')}: give one of `renamed`, `removed`, `added`")
        if f.get("renamed") is not None and not isinstance(f.get("renamed"), str):
            found.append(f"file {f.get('id')}: `renamed` is the new path")
    for d in data.get("dependencies", []):
        name = f"dependency {d.get('from')} -> {d.get('to')}"
        if d.get("from") not in file_ids or d.get("to") not in file_ids:
            found.append(f"{name}: `from` and `to` must be file ids")
        for view in ("today", "proposed"):
            if d.get(view) not in (*RESULTS, None):
                found.append(f"{name}: `{view}` is one of {', '.join(RESULTS)}, or null when it does not exist")
        if d.get("today") is None and d.get("proposed") is None:
            found.append(f"{name}: it exists in neither view")
        if not PIN.match(str(d.get("at", ""))):
            found.append(f"{name}: `at` is the pinned line that shows it, as path.ext:12, or starts with \"proposed\"")
    rules = data.get("rules", [])
    if len(rules) > len(LETTERS):
        found.append(f"{len(rules)} rules: show at most {len(LETTERS)}, the ones the findings name")
    for r in rules:
        name = f"rule {r.get('name')!r}"
        if not r.get("name") or not r.get("sites"):
            found.append(f"{name}: give its `name` and its `sites`")
        if r.get("owner") not in file_ids:
            found.append(f"{name}: `owner` must be a file id")
        if r.get("outcome") not in OUTCOMES:
            found.append(f"{name}: `outcome` is one of {', '.join(OUTCOMES)}")
        for s in r.get("sites", []):
            if s.get("file") not in file_ids:
                found.append(f"{name}: site file {s.get('file')!r} is not a file id")
            if not PIN.match(str(s.get("at", ""))):
                found.append(f"{name}: each site's `at` is its pinned line, as path.ext:12")
    for item in data.get("data", []):
        for k in item.get("keys", []):
            for use in ("writes", "reads"):
                for s in k.get(use, []):
                    if s.get("file") not in file_ids:
                        found.append(f"data {item.get('name')!r} key {k.get('key')!r}: {use} file {s.get('file')!r} is not a file id")
                    if not PIN.match(str(s.get("at", ""))):
                        found.append(f"data {item.get('name')!r} key {k.get('key')!r}: each of its {use} needs `at`, the pinned line")
    return found


def rounded(points, radius=9):
    """An SVG path through the points with rounded corners."""
    d = f"M{points[0][0]:.1f} {points[0][1]:.1f}"
    for (px, py), (x, y), (nx, ny) in zip(points, points[1:], points[2:]):
        d1, d2 = math.hypot(x - px, y - py), math.hypot(nx - x, ny - y)
        if not d1 or not d2:
            continue
        k = min(radius, d1 / 2, d2 / 2)
        d += (f"L{x - (x - px) / d1 * k:.1f} {y - (y - py) / d1 * k:.1f}"
              f"Q{x:.1f} {y:.1f} {x + (nx - x) / d2 * k:.1f} {y + (ny - y) / d2 * k:.1f}")
    return d + f"L{points[-1][0]:.1f} {points[-1][1]:.1f}"


def site_homes(data, view):
    """[(rule index, site index, file id)] where each site sits in the view."""
    homes = []
    for ri, r in enumerate(data.get("rules", [])):
        for si, s in enumerate(r["sites"]):
            moves = view == "proposed" and r["outcome"] == "moves" and not s.get("waits")
            homes.append((ri, si, r["owner"] if moves else s["file"]))
    return homes


def dot_positions(data, boxes, view):
    """(rule index, site index) -> (x, y); two sites of one rule in one file share a dot."""
    slots, placed, positions = {}, {}, {}
    for ri, si, home in site_homes(data, view):
        key = (ri, home)
        if key not in placed:
            n = slots.get(home, 0)
            slots[home] = n + 1
            box = boxes[home]
            placed[key] = (box["x"] + 20 + (n % PER_ROW) * DOT, box["y"] + 46 + (n // PER_ROW) * 24)
        positions[(ri, si)] = placed[key]
    return positions


def layout(data):
    """Boxes, lanes, edges, and dot positions for both views."""
    files = data["files"]
    # No stated design, or a focus whose files are all outside it: one unnamed lane holds every file.
    unnamed = not data["parts"]
    parts = [{"id": "outside", "label": data.get("lane", "No stated design")}] if unnamed else data["parts"]
    per_file = {}
    for view in ("today", "proposed"):
        counts = {}
        for ri, si, home in site_homes(data, view):
            counts.setdefault(home, set()).add(ri)
        for home, rules in counts.items():
            per_file[home] = max(per_file.get(home, 0), len(rules))
    height = {f["id"]: 44 + max(1, math.ceil(per_file.get(f["id"], 0) / PER_ROW)) * 24 for f in files}
    in_part = {p["id"]: [f for f in files if f["part"] == p["id"]] for p in parts}
    per_row = 4
    lane_w = max(LANE_PAD * 2 + min(per_row, max(1, len(v))) * (BOX_W + GAP) - GAP for v in in_part.values())
    lane_w = max(lane_w, 560)
    boxes, lanes, y = {}, [], 16
    for p in parts:
        members = in_part[p["id"]]
        rows = [members[i:i + per_row] for i in range(0, len(members), per_row)] or [[]]
        top, row_y = y, y + HEAD
        for row in rows:
            row_h = max([height[f["id"]] for f in row] or [44])
            for i, f in enumerate(row):
                boxes[f["id"]] = {"x": 16 + LANE_PAD + i * (BOX_W + GAP), "y": row_y, "w": BOX_W, "h": height[f["id"]], "lane": len(lanes)}
            row_y += row_h + 20
        lanes.append({"id": p["id"], "label": p.get("label", p["id"]), "said": p.get("said", ""), "x": 16, "y": top, "w": lane_w, "h": row_y - top - 4})
        y = row_y - 4 + CHANNEL
    total_h = y - CHANNEL + 16
    outside = [] if unnamed else [f for f in files if f["part"] == "outside"]
    side = None
    if outside:
        sx = 16 + lane_w + SIDE_GAP
        stack = sum(height[f["id"]] for f in outside) + 20 * (len(outside) - 1)
        oy = max(lanes[0]["y"] + HEAD, (total_h - stack) / 2)
        for f in outside:
            boxes[f["id"]] = {"x": sx + (SIDE_W - 170) / 2, "y": oy, "w": 170, "h": height[f["id"]], "lane": None}
            oy += height[f["id"]] + 20
        side = {"x": sx, "y": lanes[0]["y"], "w": SIDE_W, "h": total_h - 32}
        total_h = max(total_h, oy + 16)
    width = 16 + lane_w + (SIDE_GAP + SIDE_W if outside else 0) + 16
    edges = route(data, boxes, lanes, side)
    return {"boxes": boxes, "lanes": lanes, "side": side, "edges": edges, "width": width, "height": total_h,
            "dots": {view: dot_positions(data, boxes, view) for view in ("today", "proposed")}}


def route(data, boxes, lanes, side):
    """Orthogonal paths: down or up into the channel beside the target's lane, across, into the target.
    An end in the side column joins through the gutter left of it. Ports and tracks spread overlapping runs."""
    plans = []
    for index, d in enumerate(data.get("dependencies", [])):
        a, b = boxes[d["from"]], boxes[d["to"]]
        if a["lane"] is not None and b["lane"] is not None:
            if b["lane"] > a["lane"]:
                plans.append((index, "bottom", "top", ("below", b["lane"] - 1), ("below", a["lane"]) if b["lane"] - a["lane"] > 1 else None))
            elif b["lane"] < a["lane"]:
                plans.append((index, "top", "bottom", ("below", b["lane"]), ("below", a["lane"] - 1) if a["lane"] - b["lane"] > 1 else None))
            else:
                plans.append((index, "bottom", "bottom", ("below", a["lane"]), None))
        elif a["lane"] is not None:
            plans.append((index, "bottom", "left", ("below", a["lane"]), None))
        elif b["lane"] is not None:
            plans.append((index, "left", "top", ("below", b["lane"] - 1) if b["lane"] else ("above", 0), None))
        else:
            plans.append((index, "left", "left", None, None))
    deps = data.get("dependencies", [])
    ports = {}
    for index, from_side, to_side, _, _ in plans:
        ports.setdefault((deps[index]["from"], from_side), []).append((index, deps[index]["to"]))
        ports.setdefault((deps[index]["to"], to_side), []).append((index, deps[index]["from"]))

    def port(file_id, where, index):
        box, users = boxes[file_id], ports[(file_id, where)]
        users = sorted(users, key=lambda u: (boxes[u[1]]["x"], boxes[u[1]]["y"], u[0]))
        k = [u[0] for u in users].index(index)
        if where == "left":
            span = box["h"] * 0.6
            return (box["x"], box["y"] + box["h"] * 0.2 + span * (k + 1) / (len(users) + 1))
        span = box["w"] * 0.7
        x = box["x"] + box["w"] * 0.15 + span * (k + 1) / (len(users) + 1)
        return (x, box["y"] + (box["h"] if where == "bottom" else 0))

    def channel_y(where):
        kind, lane = where
        if kind == "above":
            return lanes[0]["y"] - 8
        return lanes[lane]["y"] + lanes[lane]["h"] + CHANNEL / 2 - 2

    runs = {}
    for index, from_side, to_side, where, first in plans:
        for channel in (where, first):
            if channel:
                runs.setdefault(channel, []).append(index)
    track = {}
    for where, members in runs.items():
        for k, index in enumerate(members):
            track[(index, where)] = (k - (len(members) - 1) / 2) * 6

    def free_x(lane_range, near, taken):
        """An x between boxes in every lane the run crosses, closest to near and not yet used."""
        crossed = [box for box in boxes.values() if box["lane"] in lane_range]
        candidates = sorted({lanes[0]["x"] + LANE_PAD / 2, lanes[0]["x"] + lanes[0]["w"] - LANE_PAD / 2}
                            | {box["x"] + box["w"] + GAP / 2 for box in crossed} | {box["x"] - GAP / 2 for box in crossed})
        free = [x for x in candidates if all(not (box["x"] - 8 < x < box["x"] + box["w"] + 8) for box in crossed)]
        x = min(free or candidates, key=lambda c: abs(c - near))
        while round(x) in taken:
            x += 6
        taken.add(round(x))
        return x
    taken = set()
    gutter = {}
    if side:
        side_members = [p[0] for p in plans if "left" in (p[1], p[2])]
        for k, index in enumerate(side_members):
            gutter[index] = side["x"] - 14 - k * 6
    paths = {}
    for index, from_side, to_side, where, first in plans:
        d = deps[index]
        s, t = port(d["from"], from_side, index), port(d["to"], to_side, index)
        if from_side == "left" and to_side == "left":
            g = side["x"] - 14
            points = [s, (g, s[1]), (g, t[1]), t]
        elif to_side == "left":
            cy = channel_y(where) + track[(index, where)]
            points = [s, (s[0], cy), (gutter[index], cy), (gutter[index], t[1]), t]
        elif from_side == "left":
            cy = channel_y(where) + track[(index, where)]
            points = [s, (gutter[index], s[1]), (gutter[index], cy), (t[0], cy), t]
        elif first:  # over a layer: across in the first channel, through a gap, across in the last
            cy1, cy2 = channel_y(first) + track[(index, first)], channel_y(where) + track[(index, where)]
            crossed = range(min(boxes[d["from"]]["lane"], boxes[d["to"]]["lane"]) + 1, max(boxes[d["from"]]["lane"], boxes[d["to"]]["lane"]))
            gx = free_x(crossed, (s[0] + t[0]) / 2, taken)
            points = [s, (s[0], cy1), (gx, cy1), (gx, cy2), (t[0], cy2), t]
        else:
            cy = channel_y(where) + track[(index, where)]
            points = [s, (s[0], cy), (t[0], cy), t] if abs(s[0] - t[0]) > 1 else [s, t]
        paths[index] = rounded(points)
    return paths


def follows(present, view):
    """How many drawn dependencies follow the documented design, and how the others break it, in plain words."""
    compared = [d for d in present if d[view] != "not compared"]
    if not compared:
        return f'<b>{len(present)}</b> {"dependency" if len(present) == 1 else "dependencies"} drawn; no stated design to compare with'
    ok = sum(1 for d in compared if d[view] == "as stated")
    forbidden = sum(1 for d in compared if d[view] == "not stated")
    missing = sum(1 for d in compared if d[view] == "not found")
    text = f'<b>{ok} of {len(compared)}</b> {"dependency follows" if len(compared) == 1 else "dependencies follow"} the documented design'
    breaks = ([f'{forbidden} the design forbids'] if forbidden else []) + ([f'{missing} it expects {"is" if missing == 1 else "are"} missing'] if missing else [])
    unchecked = len(present) - len(compared)
    return text + (": " + ", ".join(breaks) if breaks else "") + (f"; {unchecked} not compared" if unchecked else "")


def module_changes(data):
    """(kind, file) for each file the plan renames, removes, or adds."""
    return [(kind, f) for f in data["files"] for kind in ("renamed", "removed", "added") if f.get(kind)]


def file_label(f, view):
    """A file's path as a view shows it: a renamed file under its new path in the proposal."""
    path = f["renamed"] if view == "proposed" and f.get("renamed") else f["path"]
    return path if len(path) <= 24 else "…" + path[-23:]


def file_state(f, view):
    """How a file stands in a view: present, ghost (not there yet, or gone), or renamed."""
    if f.get("added") and view == "today":
        return "ghost"
    if f.get("removed") and view == "proposed":
        return "gone"
    if f.get("renamed") and view == "proposed":
        return "renamed"
    return ""


def facts(data, view):
    present = [d for d in data.get("dependencies", []) if d.get(view)]
    off_design = sum(1 for d in present if d[view] in ("not stated", "not found"))
    spread = 0
    for ri, r in enumerate(data.get("rules", [])):
        homes = {home for i, _, home in site_homes(data, view) if i == ri}
        spread += len(homes) > 1
    waiting = sum(1 for r in data.get("rules", []) if r["outcome"] == "waits" or any(s.get("waits") for s in r["sites"]))
    deps = (f'<span class="sv-fact {"bad" if off_design else "good"}">{follows(present, view)}</span>'
            if present else '<span class="sv-fact"><b>0</b> dependencies drawn in this view</span>')
    changes = module_changes(data)
    moved = ""
    if view == "proposed" and changes:
        counts = {kind: sum(1 for k, _ in changes if k == kind) for kind in ("renamed", "removed", "added")}
        moved = ('<span class="sv-fact">' + ", ".join(f'<b>{n}</b> {"module" if n == 1 else "modules"} {kind}'
                                                       for kind, n in counts.items() if n) + '</span>')
    return (deps
            + f'<span class="sv-fact {"bad" if spread else "good"}"><b>{spread}</b> {"rule" if spread == 1 else "rules"} decided in more than one file</span>'
            f'<span class="sv-fact wait"><b>{waiting}</b> waiting for your answer</span>' + moved)


def state_of(rule):
    if rule["outcome"] == "moves" and any(s.get("waits") for s in rule["sites"]):
        return PARTLY
    return OUTCOMES[rule["outcome"]]


def figure(data, index):
    """The figure for one structure-view fence, as an HTML string."""
    plan = layout(data)
    files = {f["id"]: f for f in data["files"]}
    rules = data.get("rules", [])
    out = [f'<div class="sv-svg"><svg viewBox="0 0 {plan["width"]:.0f} {plan["height"]:.0f}" width="{plan["width"]:.0f}" role="img" '
           f'aria-label="Structure: files by design part, their dependencies, and where each rule is decided. The tables below hold the same content.">'
           '<defs>' + "".join(f'<marker id="sv{index}-{c}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" orient="auto">'
                              f'<path d="M0 0L10 5L0 10z" class="sv-head-{c}"/></marker>' for c in STYLES) + '</defs>']
    out.append('<g class="sv-lanes">')
    for lane in plan["lanes"]:
        out.append(f'<rect class="sv-lane" x="{lane["x"]}" y="{lane["y"]}" width="{lane["w"]}" height="{lane["h"]}" rx="12"/>')
    if plan["side"]:
        s = plan["side"]
        out.append(f'<rect class="sv-lane sv-side" x="{s["x"]}" y="{s["y"]}" width="{s["w"]}" height="{s["h"]}" rx="12"/>')
    out.append('</g><g class="sv-edges">')
    for i, d in enumerate(data.get("dependencies", [])):
        today, proposed = d.get("today"), d.get("proposed")
        cls = (today or "as stated").replace(" ", "-")
        hidden = "" if today else ' style="display:none"'
        title = f'{files[d["from"]]["path"]} uses {files[d["to"]]["path"]}: today {today or "absent"}, proposed {proposed or "removed"}. {d.get("why", "")} ({d["at"]})'
        out.append(f'<g class="sv-edge {cls}" data-today="{escape(today or "")}" data-proposed="{escape(proposed or "")}"{hidden}>'
                   f'<path class="sv-line" d="{plan["edges"][i]}" marker-end="url(#sv{index}-{cls})"/>'
                   f'<path class="sv-hit" d="{plan["edges"][i]}"><title>{escape(title)}</title></path></g>')
    out.append('</g><g class="sv-labels">')
    for lane in plan["lanes"]:
        out.append(f'<text class="sv-lane-name" x="{lane["x"] + 14}" y="{lane["y"] + 21}">{escape(lane["label"])}'
                   + (f'<tspan class="sv-said" dx="12">“{escape(lane["said"])}”</tspan>' if lane["said"] else "") + '</text>')
    if plan["side"]:
        s, side = plan["side"], data.get("outside", {})
        out.append(f'<text class="sv-said sv-side-label" x="{s["x"] + 12}" y="{s["y"] + 21}" data-today="{escape(side.get("today", "Not named in the design"))}" '
                   f'data-proposed="{escape(side.get("proposed", side.get("today", "Not named in the design")))}">{escape(side.get("today", "Not named in the design"))}</text>')
    out.append('</g><g class="sv-files">')
    for fid, box in plan["boxes"].items():
        f = files[fid]
        path = f["path"]
        change = next((kind for kind in ("renamed", "removed", "added") if f.get(kind)), "")
        state = file_state(f, "today")
        title = path + {"renamed": f' (proposed: renamed to {f.get("renamed")})', "removed": " (proposed: removed)",
                        "added": " (proposed: new)"}.get(change, "")
        out.append(f'<g class="sv-file{" " + state if state else ""}" data-file="{escape(fid)}" data-path="{escape(path)}" data-change="{change}" tabindex="0">'
                   f'<rect x="{box["x"]}" y="{box["y"]}" width="{box["w"]}" height="{box["h"]}" rx="10"/>'
                   f'<text x="{box["x"] + 12}" y="{box["y"] + 24}" data-today="{escape(file_label(f, "today"))}" data-proposed="{escape(file_label(f, "proposed"))}">'
                   f'{escape(file_label(f, "today"))}</text><title>{escape(title)}</title></g>')
    out.append('</g><g class="sv-dots">')
    for ri, r in enumerate(rules):
        color = COLORS[ri % len(COLORS)]
        for si, s in enumerate(r["sites"]):
            tx, ty = plan["dots"]["today"][(ri, si)]
            px, py = plan["dots"]["proposed"][(ri, si)]
            waits = r["outcome"] == "waits" or s.get("waits")
            out.append(f'<g class="sv-dot{" waits" if waits else ""}" data-rule="{ri}" data-today="{tx:.1f},{ty:.1f}" data-proposed="{px:.1f},{py:.1f}" '
                       f'transform="translate({tx:.1f} {ty:.1f})"><circle r="10.5" fill="{color}"/><text>{LETTERS[ri]}</text>'
                       f'<title>{escape(r["name"])}: {escape(s["at"])}, {escape(s.get("what", ""))}</title></g>')
    out.append('</g></svg></div>')
    svg = "".join(out)

    buttons = "".join(
        f'<li><button type="button" class="sv-rule" data-rule="{ri}" aria-pressed="false"><span class="sv-badge" style="background:{COLORS[ri % len(COLORS)]}">{LETTERS[ri]}</span>'
        f'<span>{escape(r["name"])}</span><span class="sv-count" data-today="{len({s["file"] for s in r["sites"]})}" '
        f'data-proposed="{len({h for i, _, h in site_homes(data, "proposed") if i == ri})}"></span></button></li>' for ri, r in enumerate(rules))
    details = "".join(
        f'<div class="sv-detail" data-rule="{ri}" hidden><h3>{escape(r["name"])}</h3><span class="sv-state">{escape(state_of(r))}</span><ul>'
        + "".join(f'<li><span class="sv-code">{escape(s["at"])}</span> {escape(s.get("what", ""))}'
                  + ('' if r["outcome"] != "moves" or s.get("waits") or s["file"] == r["owner"]
                     else f' <span class="sv-moves">→ moves to <span class="sv-code">{escape(files[r["owner"]]["path"])}</span></span>') + '</li>' for s in r["sites"])
        + f'</ul><p>{escape(r.get("note", ""))}</p></div>' for ri, r in enumerate(rules))
    legend = ('<p class="sv-legend"><span><span class="sv-key-line as-stated"></span>dependency the design allows</span>'
              '<span><span class="sv-key-line not-stated"></span>dependency the design does not allow</span>'
              '<span><span class="sv-key-line not-found"></span>the design expects it; the code lacks it</span>'
              '<span><span class="sv-key-line not-compared"></span>dependency not compared with a design</span>'
              '<span><span class="sv-key-dot"></span>a file that decides a rule</span>'
              '<span><span class="sv-key-dot waits"></span>waits for your answer</span></p>')
    table = ('<details class="sv-table-box"><summary>The rules as a table</summary><table class="sv-table"><thead><tr><th>Rule</th><th>Decided today in</th><th>Proposed owner</th><th>Under the proposal</th></tr></thead><tbody>'
             + "".join(f'<tr><td><b>{LETTERS[ri]}</b> {escape(r["name"])}</td><td>' + "<br>".join(f'<span class="sv-code">{escape(s["at"])}</span> {escape(s.get("what", ""))}' for s in r["sites"])
                       + f'</td><td><span class="sv-code">{escape(files[r["owner"]]["path"])}</span></td><td>{escape(state_of(r))}. {escape(r.get("note", ""))}</td></tr>' for ri, r in enumerate(rules))
             + '</tbody></table></details>') if rules else ""
    names = {"today": "Today", "proposed": "Proposed", **data.get("labels", {})}
    controls = ('<div class="sv-bar"><div class="sv-switch" role="group" aria-label="Which structure to show" hidden>'
                f'<button type="button" data-view="today" aria-pressed="true">{escape(names["today"])}</button>'
                f'<button type="button" data-view="proposed" aria-pressed="false">{escape(names["proposed"])}</button></div>'
                f'<div class="sv-facts" aria-live="polite" data-today="{escape(facts(data, "today"))}" data-proposed="{escape(facts(data, "proposed"))}">{facts(data, "today")}</div></div>')
    panel = (f'<aside class="sv-panel"><h3 class="sv-panel-title">Rules, and where each is decided</h3><ul class="sv-rules">{buttons}</ul>'
             f'<div class="sv-details" aria-live="polite"><p class="sv-hint">Select a rule to follow it across files.</p>{details}</div></aside>') if rules else ""
    html = [f'<figure class="structure-view" data-view="today" role="region" aria-label="Structure view {index}">', controls,
            f'<div class="sv-grid">{svg}{panel}</div>', legend, table, data_view(data, files), '</figure>']
    return "".join(html)


def focus(data, spec):
    """The part of the structure data one problem is about: its rules, the files that decide them or own
    them, the files the spec names, and the dependencies between those files. Each rule keeps its index
    in the full view, so its letter and colour match."""
    chosen = [(i, r) for i, r in enumerate(data.get("rules", [])) if r["name"] in spec.get("rules", [])]
    keep = set(spec.get("files", []))
    for _, r in chosen:
        keep |= {s["file"] for s in r["sites"]} | {r["owner"]}
    files = [f for f in data["files"] if f["id"] in keep]
    parts = [p for p in data["parts"] if any(f["part"] == p["id"] for f in files)]
    deps = [d for d in data.get("dependencies", []) if d["from"] in keep and d["to"] in keep]
    rules = [{**r, "index": i} for i, r in chosen]
    # Every file of the focus outside a design that exists: its one lane says so, not "No stated design".
    lane = data.get("outside", {}).get("today", "Not named in the design") if data["parts"] and not parts else "No stated design"
    return {**data, "parts": parts, "files": files, "dependencies": deps, "rules": rules, "data": [], "lane": lane}


def view_svg(data, index, view):
    """One view of the structure, today or proposed, as a static SVG string."""
    plan = layout(data)
    files = {f["id"]: f for f in data["files"]}
    name = f"svf{index}{view[0]}"
    out = [f'<svg viewBox="0 0 {plan["width"]:.0f} {plan["height"]:.0f}" role="img" aria-label="{"Today" if view == "today" else "Proposed"}: '
           f'the files of this problem, their dependencies, and where each rule is decided.">'
           '<defs>' + "".join(f'<marker id="{name}-{c}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" orient="auto">'
                              f'<path d="M0 0L10 5L0 10z" class="sv-head-{c}"/></marker>' for c in STYLES) + '</defs>']
    for lane in plan["lanes"]:
        out.append(f'<rect class="sv-lane" x="{lane["x"]}" y="{lane["y"]}" width="{lane["w"]}" height="{lane["h"]}" rx="12"/>')
    if plan["side"]:
        s = plan["side"]
        out.append(f'<rect class="sv-lane sv-side" x="{s["x"]}" y="{s["y"]}" width="{s["w"]}" height="{s["h"]}" rx="12"/>')
    for i, d in enumerate(data.get("dependencies", [])):
        status = d.get(view)
        if status:
            cls = status.replace(" ", "-")
            out.append(f'<g class="sv-edge {cls}"><path class="sv-line" d="{plan["edges"][i]}" marker-end="url(#{name}-{cls})"/>'
                       f'<title>{escape(files[d["from"]]["path"])} uses {escape(files[d["to"]]["path"])}: {escape(status)} ({escape(d["at"])})</title></g>')
    for lane in plan["lanes"]:
        out.append(f'<text class="sv-lane-name" x="{lane["x"] + 14}" y="{lane["y"] + 21}">{escape(lane["label"])}</text>')
    for fid, box in plan["boxes"].items():
        f = files[fid]
        state = file_state(f, view)
        out.append(f'<g class="sv-file{" " + state if state else ""}"><rect x="{box["x"]}" y="{box["y"]}" width="{box["w"]}" height="{box["h"]}" rx="10"/>'
                   f'<text x="{box["x"] + 12}" y="{box["y"] + 24}">{escape(file_label(f, view))}</text><title>{escape(f["path"])}</title></g>')
    for ri, r in enumerate(data.get("rules", [])):
        number = r.get("index", ri)
        for si, s in enumerate(r["sites"]):
            x, y = plan["dots"][view][(ri, si)]
            waits = r["outcome"] == "waits" or s.get("waits")
            out.append(f'<g class="sv-dot{" waits" if waits else ""}" transform="translate({x:.1f} {y:.1f})"><circle r="10.5" fill="{COLORS[number % len(COLORS)]}"/>'
                       f'<text>{LETTERS[number]}</text><title>{escape(r["name"])}: {escape(s["at"])}, {escape(s.get("what", ""))}</title></g>')
    return "".join(out) + "</svg>"


def summary(data, view):
    """One line under a view: how many files decide each rule, and the dependencies that break the design."""
    parts = []
    for ri, r in enumerate(data.get("rules", [])):
        homes = [home for i, _, home in site_homes(data, view) if i == ri]
        # A site that moves to its owner merges there; every other site keeps its own place.
        places = len(set(homes)) if view == "proposed" and r["outcome"] == "moves" else len(homes)
        files = len(set(homes))
        where = f'{files} {"file" if files == 1 else "files"}'
        parts.append(f'{escape(r["name"])}: decided ' + (f'at {places} places in {where}' if places > files else f'in {where}'))
    forbidden = sum(1 for d in data.get("dependencies", []) if d.get(view) == "not stated")
    missing = sum(1 for d in data.get("dependencies", []) if d.get(view) == "not found")
    if forbidden:
        parts.append(f'{forbidden} {"dependency" if forbidden == 1 else "dependencies"} the design forbids')
    if missing:
        parts.append(f'{missing} {"dependency" if missing == 1 else "dependencies"} the design expects {"is" if missing == 1 else "are"} missing')
    if view == "proposed":
        for kind, f in module_changes(data):
            parts.append(f'{escape(f["path"].rsplit("/", 1)[-1])} {kind}' + (f' to {escape(f["renamed"].rsplit("/", 1)[-1])}' if kind == "renamed" else ""))
    return "; ".join(parts) or "no rule drawn"


def focus_figure(data, spec, index):
    """Today and proposed, side by side, for the part of the structure one problem is about."""
    part = focus(data, spec)
    names = {"today": "Today", "proposed": "Proposed", **data.get("labels", {})}
    panels = "".join(f'<div class="sv-pane {view}"><p class="sv-pane-label">{escape(names[view])}</p>'
                     f'<div class="sv-pane-canvas">{view_svg(part, index, view)}</div><p class="sv-pane-sum">{summary(part, view)}</p></div>'
                     for view in ("today", "proposed"))
    legend = ('<figcaption class="sv-legend"><span><span class="sv-key-dot"></span>a place that decides the rule; the letter names it</span>'
              '<span><span class="sv-key-line as-stated"></span>dependency the design allows</span>'
              '<span><span class="sv-key-line not-stated"></span>dependency the design does not allow</span>'
              '<span><span class="sv-key-line not-found"></span>the design expects it; the code lacks it</span>'
              '<span><span class="sv-key-line not-compared"></span>dependency not compared with a design</span></figcaption>')
    return f'<figure class="sv-focus" role="group" aria-label="Today and proposed">{panels}{legend}</figure>'


def history_figure(data, index):
    """Which places of one rule each commit changed, oldest first, with the places a commit missed."""
    sites, commits = data["sites"], data["commits"]
    order = [c["sha"] for c in commits]
    exists = lambda site, at: not site.get("since") or order.index(at) >= order.index(site["since"])
    label_w, col, row, top = max(150, 16 + 8 * max(len(s["label"]) for s in sites)), 76, 34, 58
    width, height = label_w + col * len(commits) + 16, top + row * len(sites) + 12
    out = [f'<svg viewBox="0 0 {width} {height}" width="{width}" role="img" aria-label="Changes to {escape(data.get("rule", "the rule"))}: '
           f'which of its places each commit changed.">']
    partial = 0
    for ci, c in enumerate(commits):
        x = label_w + ci * col + col / 2
        out.append(f'<text class="hx-sha" x="{x:.0f}" y="18">{escape(c["sha"][:7])}</text><text class="hx-date" x="{x:.0f}" y="34">{escape(str(c.get("date", ""))[:10])}</text>'
                   f'<title>{escape(c.get("subject", ""))}</title>')
        present = [s for s in sites if exists(s, c["sha"])]
        added = [s for s in sites if s.get("since") == c["sha"]]
        changed = set(c["changed"])
        missed = [s for s in present if s["id"] not in changed and s not in added]
        if missed and changed - {s["id"] for s in added}:
            partial += 1
        for si, s in enumerate(sites):
            y = top + si * row + row / 2
            if not exists(s, c["sha"]):
                out.append(f'<circle class="hx-none" cx="{x:.0f}" cy="{y:.0f}" r="2.5"/>')
            elif s["id"] in changed:
                out.append(f'<circle class="hx-changed" cx="{x:.0f}" cy="{y:.0f}" r="9"><title>{escape(c["sha"][:7])} changed {escape(s["label"])}: '
                           f'{escape(c.get("subject", ""))}</title></circle>')
            elif s in missed and changed - {a["id"] for a in added}:
                out.append(f'<circle class="hx-missed" cx="{x:.0f}" cy="{y:.0f}" r="8"><title>{escape(c["sha"][:7])} did not change {escape(s["label"])}</title></circle>')
            else:
                out.append(f'<circle class="hx-none" cx="{x:.0f}" cy="{y:.0f}" r="2.5"/>')
    for si, s in enumerate(sites):
        y = top + si * row + row / 2
        out.append(f'<line class="hx-row" x1="{label_w - 8}" x2="{width - 8}" y1="{y:.0f}" y2="{y:.0f}"/>'
                   f'<text class="hx-site" x="{label_w - 16}" y="{y + 4:.0f}">{escape(s["label"])}</text>')
    out.append("</svg>")
    out = [out[0], *[line for line in out[1:] if "hx-row" in line], *[line for line in out[1:] if "hx-row" not in line]]
    total = len(commits)
    caption = (f'{total} {"commit" if total == 1 else "commits"} changed {escape(data.get("rule", "this rule"))}; '
               f'{partial} of them changed only some of its places')
    return (f'<figure class="history-view" role="group" aria-label="Change history"><div class="hx-canvas">{"".join(out)}</div>'
            f'<figcaption><span><span class="hx-key changed"></span>changed in this commit</span><span><span class="hx-key missed"></span>'
            f'not changed, while another place was</span><b>{caption}.</b></figcaption></figure>')


ROLES = {"decides": "●", "calls": "○", "stores": "■"}


def behavior_problems(data):
    """What makes a behavior-map fence unusable."""
    if not isinstance(data, dict) or not data.get("files") or not data.get("behaviors"):
        return ["give `files` (each with `id` and `path`) and `behaviors` (each with `feature`, `name`, and `sites`)"]
    found, ids = [], [f.get("id") for f in data["files"]]
    if len(set(ids)) != len(ids) or not all(ids) or not all(f.get("path") for f in data["files"]):
        found.append("every file needs a unique `id` and its `path`")
    for b in data["behaviors"]:
        name = f"behavior {b.get('name')!r}"
        if not b.get("feature") or not b.get("name") or not b.get("sites"):
            found.append(f"{name}: give its `feature`, `name`, and `sites`")
        for site in b.get("sites", []):
            if site.get("file") not in ids:
                found.append(f"{name}: site file {site.get('file')!r} is not a file id")
            if site.get("role") not in ROLES:
                found.append(f"{name}: each site's `role` is one of {', '.join(ROLES)}")
            if not PIN.match(str(site.get("at", ""))):
                found.append(f"{name}: each site's `at` is its pinned line, as path.ext:12")
        if b.get("problem") is not None and not isinstance(b.get("problem"), int):
            found.append(f"{name}: `problem` is the number of the problem that holds its weak point")
    return found


def behavior_figure(data, index):
    """One row per behavior, grouped by feature; one column per file; each cell what that file does for the
    behavior; and each row's weak point, linked to its problem."""
    files = data["files"]
    head = "".join(f'<th scope="col" title="{escape(f["path"])}"><span class="bm-file">{escape(f["path"].rsplit("/", 1)[-1])}</span></th>' for f in files)
    rows, spread, feature = [], 0, None
    for b in data["behaviors"]:
        if b["feature"] != feature:
            feature = b["feature"]
            rows.append(f'<tr class="bm-feature"><th scope="rowgroup" colspan="{len(files) + 2}">{escape(feature)}</th></tr>')
        deciders = {s["file"] for s in b["sites"] if s["role"] == "decides"}
        spread += len(deciders) > 1
        cells = []
        for f in files:
            mine = [s for s in b["sites"] if s["file"] == f["id"]]
            role = next((r for r in ROLES if any(s["role"] == r for s in mine)), "")
            title = "; ".join(f'{s["role"]} at {s["at"]}' for s in mine)
            cells.append(f'<td class="bm-{role}" title="{escape(title)}">{ROLES.get(role, "")}</td>' if role else '<td></td>')
        weak = escape(b.get("weak", ""))
        link = (f' <a class="bm-problem" href="#problems" data-problem="{b["problem"]}">problem {b["problem"]}</a>' if b.get("problem") else "")
        rows.append(f'<tr class="{"bm-spread" if len(deciders) > 1 else ""}"><th scope="row">{escape(b["name"])}</th>{"".join(cells)}'
                    f'<td class="bm-weak">{weak}{link}</td></tr>')
    total = len(data["behaviors"])
    caption = (f'{total} {"behavior" if total == 1 else "behaviors"}; {spread} decided in more than one file')
    return (f'<figure class="behavior-map" role="group" aria-label="Behavior map {index}"><div class="table-scroll"><table class="bm-table">'
            f'<thead><tr><th scope="col">Behavior</th>{head}<th scope="col">Weak point</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            f'<figcaption><span><b class="bm-key">●</b> decides</span><span><b class="bm-key">○</b> calls through</span>'
            f'<span><b class="bm-key">■</b> stores state</span><b>{caption}.</b></figcaption></figure>')


def data_view(data, files):
    """Per piece of shapeless data: one row per key, one column per file that touches it."""
    blocks = []
    order = [f["id"] for f in data["files"]]
    for item in data.get("data", []):
        keys = item.get("keys", [])
        touched = [fid for fid in order if any(s["file"] == fid for k in keys for s in k.get("writes", []) + k.get("reads", []))]
        head = "".join(f'<th scope="col"><span class="sv-code">{escape(files[fid]["path"].rsplit("/", 1)[-1])}</span></th>' for fid in touched)
        rows = []
        for k in keys:
            writers = {s["file"] for s in k.get("writes", [])}
            defaults = {s.get("default") for s in k.get("reads", []) if s.get("default") is not None}
            signs = ([f"written in {len(writers)} files"] if len(writers) > 1 else []) + (["defaults differ"] if len(defaults) > 1 else []) \
                + (["never written here"] if not writers else [])
            cells = []
            for fid in touched:
                marks = [("W", s) for s in k.get("writes", []) if s["file"] == fid] + [("R", s) for s in k.get("reads", []) if s["file"] == fid]
                text = " ".join((f'{m}·{escape(str(s["default"]))}' if m == "R" and s.get("default") is not None else m) for m, s in marks)
                title = "; ".join(f'{"writes" if m == "W" else "reads"} at {s["at"]}' + (f', default {s["default"]}' if s.get("default") is not None else "") for m, s in marks)
                kinds = " ".join(sorted({"w" if m == "W" else ("d" if s.get("default") is not None else "r") for m, s in marks}))
                cells.append(f'<td class="{kinds}" title="{escape(title)}">{text}</td>')
            rows.append(f'<tr data-files="{escape(" ".join(sorted(writers | {s["file"] for s in k.get("reads", [])})))}"><th scope="row"><span class="sv-code">{escape(str(k.get("key")))}</span></th>'
                        + "".join(cells) + f'<td class="sv-signs">{escape("; ".join(signs)) or "—"}</td></tr>')
        proposed = f'<p class="sv-proposed-shape"><b>Proposed:</b> {escape(item["proposed"])}</p>' if item.get("proposed") else ""
        blocks.append(f'<div class="sv-data"><h3>{escape(item.get("name", "Data"))}: who writes and reads each key</h3>'
                      f'<p class="sv-hint">W writes the key. R reads it; R·x reads it with the default x. Select a row to see its files above.</p>'
                      f'<table class="sv-matrix"><thead><tr><th scope="col">Key</th>{head}<th scope="col">Signs</th></tr></thead>'
                      f'<tbody>{"".join(rows)}</tbody></table>{proposed}</div>')
    return "".join(blocks)


def assets():
    """The view's style and script, once per page."""
    return (f'<style class="structure-view-style">{(ROOT / "structure-view.css").read_text()}</style>'
            f'<script class="structure-view-script">{(ROOT / "structure-view.js").read_text()}</script>')


def fences(source, kind="structure-view"):
    """(line number, JSON text) for each fence of the kind in a note."""
    found, lines, i = [], source.split("\n"), 0
    while i < len(lines):
        opening = re.match(rf"^(`{{3,}}|~{{3,}})\s*{re.escape(kind)}\s*$", lines[i])
        if opening:
            j = i + 1
            while j < len(lines) and not re.match(rf"^{re.escape(opening.group(1))}\s*$", lines[j]):
                j += 1
            found.append((i + 1, "\n".join(lines[i + 1:j])))
            i = j
        i += 1
    return found


def focus_problems(spec, data):
    """What makes a structure-focus fence unusable against the note's structure view."""
    if not isinstance(spec, dict) or not (spec.get("rules") or spec.get("files")):
        return ["give `rules`, the names of rules in the structure view, and or `files`, its file ids"]
    if data is None:
        return ["the note has no structure-view fence for it to draw from"]
    found = []
    names = {r.get("name") for r in data.get("rules", [])}
    found += [f"rule {name!r} is not a rule of the structure view" for name in spec.get("rules", []) if name not in names]
    ids = {f.get("id") for f in data.get("files", [])}
    found += [f"file {fid!r} is not a file id of the structure view" for fid in spec.get("files", []) if fid not in ids]
    return found


SHA = re.compile(r"^[0-9a-f]{7,40}$")


def history_problems(data):
    """What makes a change-history fence unusable."""
    if not isinstance(data, dict) or not data.get("sites") or not data.get("commits"):
        return ["give `rule`, `sites` (each with `id` and `label`), and `commits` (each with `sha`, `date`, `subject`, `changed`)"]
    found, shas = [], [c.get("sha") for c in data["commits"]]
    ids = [s.get("id") for s in data["sites"]]
    if len(set(ids)) != len(ids) or not all(ids):
        found.append("every site needs a unique `id`")
    for site in data["sites"]:
        if not site.get("label"):
            found.append(f"site {site.get('id')!r}: give its `label`, the place as path:line")
        if site.get("since") and site["since"] not in shas:
            found.append(f"site {site.get('id')!r}: `since` must be the sha of a listed commit")
    for c in data["commits"]:
        if not SHA.match(str(c.get("sha", ""))):
            found.append(f"commit {c.get('sha')!r}: `sha` is a commit id, 7 to 40 hex digits")
        if not c.get("changed") or any(i not in ids for i in c.get("changed", [])):
            found.append(f"commit {c.get('sha')!r}: `changed` lists the site ids it changed")
    return found


def check(source):
    """Every structure-view fence holds valid data with a pinned line behind each edge and site; every focus
    names what that data holds; every change history is well formed."""
    messages, views = [], []
    for line, text in fences(source):
        try:
            data = json.loads(text)
        except ValueError as error:
            messages.append(f"Structure view at line {line}: the fence is not valid JSON ({error}).")
            continue
        views.append(data)
        messages.extend(f"Structure view at line {line}: {message}." for message in problems(data))
    if len(views) > 1:
        messages.append("Use one structure-view fence per note; a problem draws its part of it with a structure-focus fence.")
    for line, text in fences(source, "structure-focus"):
        try:
            spec = json.loads(text)
        except ValueError as error:
            messages.append(f"Structure focus at line {line}: the fence is not valid JSON ({error}).")
            continue
        messages.extend(f"Structure focus at line {line}: {message}." for message in focus_problems(spec, views[0] if views else None))
    for line, text in fences(source, "behavior-map"):
        try:
            data = json.loads(text)
        except ValueError as error:
            messages.append(f"Behavior map at line {line}: the fence is not valid JSON ({error}).")
            continue
        messages.extend(f"Behavior map at line {line}: {message}." for message in behavior_problems(data))
    for line, text in fences(source, "change-history"):
        try:
            data = json.loads(text)
        except ValueError as error:
            messages.append(f"Change history at line {line}: the fence is not valid JSON ({error}).")
            continue
        messages.extend(f"Change history at line {line}: {message}." for message in history_problems(data))
    if messages:
        raise ValueError(" ".join(messages))
