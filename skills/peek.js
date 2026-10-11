/* Code peek: opens a cited file, or its base ↔ head diff, under the link that cites it.
   Data: #peek-data, written by source_peek.py. Pure helpers are exported for tests/peek.test.cjs. */
(function (exports) {
  "use strict";
  const TAG = /<span class="([^"]*)">|<\/span>|\n/g;
  const DEFINITION = /<span class="hljs-title (?:function_|class_)">([^<]*)<\/span>/;
  const ENTITIES = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#x27;": "'"};

  function splitLines(text) {
    const lines = text.split("\n");
    return lines[lines.length - 1] === "" ? lines.slice(0, -1) : lines;
  }

  function escapeHtml(text) {
    return text.replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;"})[c]);
  }

  /** Split highlighted HTML into lines, closing spans that cross a line end and reopening them on the next line. */
  function splitHighlighted(html) {
    const lines = [], open = [];
    let line = "", last = 0;
    for (const match of html.matchAll(TAG)) {
      line += html.slice(last, match.index);
      last = match.index + match[0].length;
      if (match[0] === "\n") {
        lines.push(line + "</span>".repeat(open.length));
        line = open.map(name => `<span class="${name}">`).join("");
      } else {
        if (match[0] === "</span>") open.pop(); else open.push(match[1]);
        line += match[0];
      }
    }
    lines.push(line + html.slice(last));
    return lines;
  }

  /** Function and class scopes: a definition line opens one that ends before the next non-blank line indented at or
      below it; a line that starts with a closing bracket at that depth still belongs to it.
      ponytail: indentation heuristic; tree-sitter scopes at render time if brace-heavy code misleads it. */
  function scopes(rawLines, htmlLines) {
    const done = [], open = [];
    const depthOf = raw => raw.match(/^[ \t]*/)[0].replace(/\t/g, "    ").length;
    rawLines.forEach((raw, index) => {
      if (!raw.trim()) return;
      const depth = depthOf(raw), closing = /^\s*[)\]}]/.test(raw);
      while (open.length) {
        const top = open[open.length - 1];
        if (depth > top.depth || (depth === top.depth && closing)) break;
        top.end = index;
        done.push(open.pop());
      }
      const match = DEFINITION.exec(htmlLines[index] || "");
      if (match) open.push({name: match[1].replace(/&[#\w]+;/g, e => ENTITIES[e] || e), depth, start: index + 1, end: rawLines.length});
    });
    return done.concat(open).sort((a, b) => a.start - b.start).map(({name, start, end}) => ({name, start, end}));
  }

  function chainAt(found, line) {
    return found.filter(s => s.start <= line && line <= s.end).map(s => s.name);
  }

  function loadHighlighter(core, languages) {
    const hljs = new Function(core)();
    for (const [name, body] of Object.entries(languages)) hljs.registerLanguage(name, new Function(body)());
    return hljs;
  }

  if (exports) {
    Object.assign(exports, {splitLines, escapeHtml, splitHighlighted, scopes, chainAt, loadHighlighter});
    return;
  }
  const KINDS = {"=": ["", ""], "~": ["peek-del", "peek-add"], "-": ["peek-del", ""], "+": ["", "peek-add"]};
  const SIDES = ["base", "head"];
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  };
  const cited = (link, line) => line != null && link.start != null && link.start <= line && line <= link.end;

  async function unpack(text) {
    const bytes = Uint8Array.from(atob(text.trim()), c => c.charCodeAt(0));
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    const payload = JSON.parse(await new Response(stream).text());
    payload.highlighter = loadHighlighter(payload.hljs.core, payload.hljs.languages);
    payload.views = {};
    return payload;
  }

  function fileView(payload, key) {
    if (payload.views[key]) return payload.views[key];
    const file = payload.files[key], raw = splitLines(file.text), hljs = payload.highlighter;
    const html = (file.language && hljs.getLanguage(file.language)
      ? splitHighlighted(hljs.highlight(file.text, {language: file.language, ignoreIllegals: true}).value)
      : splitLines(escapeHtml(file.text))).slice(0, raw.length);
    return (payload.views[key] = {raw, html, scopes: scopes(raw, html)});
  }

  /** Wrap [start, end) character ranges of a line's text in <mark>, splitting highlight spans' text nodes. */
  function markRanges(element, ranges) {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT), nodes = [];
    for (let node; (node = walker.nextNode());) nodes.push(node);
    let offset = 0;
    for (const node of nodes) {
      const start = offset;
      offset += node.data.length;
      const cuts = ranges.filter(([a, b]) => a < offset && b > start).map(([a, b]) => [Math.max(a, start) - start, Math.min(b, offset) - start]);
      if (!cuts.length) continue;
      const fragment = document.createDocumentFragment();
      let at = 0;
      for (const [a, b] of cuts) {
        if (a > at) fragment.append(node.data.slice(at, a));
        fragment.append(el("mark", "peek-mark", node.data.slice(a, b)));
        at = b;
      }
      if (at < node.data.length) fragment.append(node.data.slice(at));
      node.replaceWith(fragment);
    }
  }

  function codeRow(view, line, classes, marks) {
    const row = el("div", ("peek-row " + classes).trim());
    if (line == null) {
      row.classList.add("peek-filler");
      row.append(el("span", "peek-ln"), el("span", "peek-text", " "));
      return row;
    }
    row.dataset.line = line;
    const text = el("span", "peek-text");
    text.innerHTML = view.html[line - 1] || " ";  // highlight.js output or escapeHtml: source text is escaped
    row.append(el("span", "peek-ln", String(line)), text);
    if (marks && marks.length) markRanges(text, marks);
    return row;
  }

  function codeBody(payload, link) {
    const view = fileView(payload, link.file), side = el("div", "peek-side");
    view.raw.forEach((_, index) => side.append(codeRow(view, index + 1, cited(link, index + 1) ? "peek-cited" : "")));
    return {columns: [{name: link.side || "head", view, element: side}]};
  }

  /** `expanded` holds the folds the reader opened, by first row, so a redraw keeps them open. */
  function diffBody(payload, link, scroller, expanded) {
    const diff = payload.diffs[link.diff], at = SIDES.indexOf(link.side) + 1;
    const columns = SIDES.filter(name => diff[name]).map(name => ({name, view: fileView(payload, diff[name]), element: el("div", "peek-side")}));
    const folds = diff.folds.filter(([from, to]) => !expanded.has(from) && !diff.rows.slice(from, to).some(row => cited(link, row[at])));
    let fold = 0;
    diff.rows.forEach(([kind, ...lines], index) => {
      const active = folds[fold];
      if (active && index === active[0]) {
        for (const column of columns) {
          const button = el("button", "peek-fold", `⋯ ${active[1] - active[0]} unchanged lines · expand`);
          button.type = "button";
          button.dataset.fold = active[0];
          button.addEventListener("click", () => {
            expanded.add(active[0]);
            for (const node of scroller.querySelectorAll(`[data-fold="${active[0]}"]`)) {
              if (node.matches(".peek-fold")) node.remove(); else node.hidden = false;
            }
            scroller.focus({preventScroll: true});  // the clicked button is gone; keep focus inside the peek
          });
          column.element.append(button);
        }
      }
      const hidden = active && index >= active[0] && index < active[1];
      if (active && index === active[1] - 1) fold++;
      for (const column of columns) {
        const side = SIDES.indexOf(column.name), line = lines[side];
        const classes = KINDS[kind][side] + (column.name === link.side && cited(link, line) ? " peek-cited" : "");
        const row = codeRow(column.view, line, classes, (diff.marks[index] || [[], []])[side]);
        if (hidden) { row.hidden = true; row.dataset.fold = active[0]; }
        column.element.append(row);
      }
    });
    return {columns};
  }

  function whereText(payload, link, mode) {
    const lines = link.start == null ? "" : `L${link.start}` + (link.end !== link.start ? `–L${link.end}` : "");
    if (mode === "diff") {
      const diff = payload.diffs[link.diff];
      return [lines, `base ${diff.commits[0].slice(0, 7)} ↔ head ${diff.commits[1].slice(0, 7)}`, `+${diff.added} −${diff.removed}`]
        .filter(Boolean).join(" · ");
    }
    return [lines, link.commit && link.commit.slice(0, 7)].filter(Boolean).join(" · ");
  }

  /** A button that copies `value`: the path, the cited lines, or a fence's text. */
  function copyAction(label, title, value) {
    const button = el("button", "peek-action", label);
    button.type = "button";
    button.title = title;
    button.addEventListener("click", () => navigator.clipboard?.writeText(typeof value === "function" ? value() : value)
      .then(() => { button.textContent = "Copied"; }, () => {}));
    return button;
  }

  /** The peek's content; the dialog that holds it carries the label. */
  function buildPeek(payload, link, anchor, close) {
    const region = el("div", "peek");
    let mode = link.diff ? "diff" : "code";
    const expanded = new Set();

    function draw() {
      const bar = el("div", "peek-bar");
      bar.append(el("strong", "peek-path", link.path), el("span", "peek-where", whereText(payload, link, mode)), el("span", "peek-space"));
      if (link.diff) {
        const tabs = el("span", "peek-tabs");
        tabs.setAttribute("role", "tablist");
        for (const name of ["diff", "code"]) {
          const tab = el("button", "peek-tab", name === "diff" ? "Diff" : "Code");
          tab.type = "button";
          tab.setAttribute("role", "tab");
          tab.setAttribute("aria-selected", String(name === mode));
          tab.addEventListener("click", () => { mode = name; draw(); region.querySelector(".peek-tab[aria-selected=true]").focus(); });
          tabs.append(tab);
        }
        bar.append(tabs);
      }
      const ranged = link.start != null;
      const code = copyAction("⧉ code", ranged ? `Copy lines ${link.start}–${link.end}` : "Copy the file", () => {
        const raw = fileView(payload, link.file).raw;  // the cited file, whichever tab is open
        return (ranged ? raw.slice(link.start - 1, link.end) : raw).join("\n") + "\n";
      });
      bar.append(copyAction("⧉ path", "Copy the file path", link.path), code);
      if (link.commit) {  // a file beside the report has no GitHub page
        const github = el("a", "peek-action peek-github", "GitHub ↗");
        github.href = anchor.href;
        bar.append(github);
      }
      const shut = el("button", "peek-close", "✕");
      shut.type = "button";
      shut.setAttribute("aria-label", "Close the code peek");
      shut.addEventListener("click", close);
      bar.append(shut);

      const scope = el("div", "peek-scope", " ");
      const scroller = el("div", "peek-code");
      scroller.tabIndex = 0;
      scroller.setAttribute("aria-label", `${link.path}, ${mode === "diff" ? "diff" : "code"}`);
      const body = mode === "diff" ? diffBody(payload, link, scroller, expanded) : codeBody(payload, {...link, side: null});
      const grid = el("div", `peek-cols peek-cols-${body.columns.length}`);
      body.columns.forEach(column => grid.append(column.element));
      scope.hidden = body.columns.every(column => !column.view.scopes.length);  // no function or class: no strip
      scroller.append(grid);
      const lead = body.columns.find(column => column.name === link.side) || body.columns[body.columns.length - 1];
      // Narrow screens hide the base column; the head column is always shown, and the columns' rows line up.
      const shown = () => lead.element.offsetWidth ? lead : body.columns[body.columns.length - 1];
      const updateScope = () => {
        const lead = shown(), box = lead.element.getBoundingClientRect(), top = scroller.getBoundingClientRect().top;
        const row = document.elementFromPoint(box.left + 40, top + 4)?.closest(".peek-row[data-line]");
        if (row && lead.element.contains(row)) scope.textContent = chainAt(lead.view.scopes, Number(row.dataset.line)).join(" › ") || " ";
      };
      let pending = false;
      scroller.addEventListener("scroll", () => {
        if (!pending) { pending = true; requestAnimationFrame(() => { pending = false; updateScope(); }); }
      }, {passive: true});
      region.replaceChildren(bar, scope, scroller);
      // The first draw runs before the dialog opens; offsets exist from the next frame.
      requestAnimationFrame(() => {
        const cited = lead.element.querySelector(".peek-cited:not([hidden])");
        const target = cited && shown().element.children[[...lead.element.children].indexOf(cited)];
        scroller.scrollTop = target ? Math.max(0, target.offsetTop - 3 * target.offsetHeight) : 0;
        updateScope();
      });
    }

    draw();
    return region;
  }

  /** The page's fences drawn as peek rows: highlighted when their grammar ships, numbered from the cited line when
      the fence cites one (data-first, set by render_page.py), with copy buttons in the caption. Diffs and diagrams
      keep their own rendering. The static <pre> stays in the HTML file; only the DOM changes. */
  function enhanceCards(payload, main) {
    const hljs = payload.highlighter;
    for (const code of main.querySelectorAll("pre > code[class*='language-']")) {
      const pre = code.parentElement, name = [...code.classList].find(c => c.startsWith("language-")).slice(9);
      if (name === "diff" || name === "mermaid" || pre.classList.contains("mermaid-source")) continue;
      let figure = pre.closest("figure.code-card");
      if (!figure) {  // a bare fence gets a caption that names its language
        figure = el("figure", "code-card");
        const caption = el("figcaption");
        caption.append(el("span", "", name));
        pre.replaceWith(figure);
        figure.append(caption, pre);
      }
      const text = code.textContent, raw = splitLines(text), first = Number(figure.dataset.first) || 0;
      const language = hljs.getLanguage(name) ? name : null;
      const html = (language ? splitHighlighted(hljs.highlight(text, {language, ignoreIllegals: true}).value)
        : splitLines(escapeHtml(text))).slice(0, raw.length);
      const side = el("div", "peek-side");
      raw.forEach((_, index) => {
        const row = el("div", "peek-row"), body = el("span", "peek-text");
        body.innerHTML = html[index] || " ";  // highlight.js output or escapeHtml: fence text is escaped
        if (first) row.append(el("span", "peek-ln", String(first + index)));
        row.append(body);
        side.append(row);
      });
      const scroller = el("div", "peek-code peek-card-code");
      if (/^(sh|bash|shell|zsh|console|shell-session)$/.test(name)) scroller.classList.add("peek-wrap");  // a command wraps; copy keeps it exact
      for (const attribute of ["tabindex", "role", "aria-label"]) {
        if (pre.hasAttribute(attribute)) scroller.setAttribute(attribute, pre.getAttribute(attribute));
      }
      scroller.append(side);
      pre.replaceWith(scroller);
      const caption = figure.querySelector(":scope > figcaption"), actions = el("span", "peek-card-actions");
      const anchor = caption.querySelector("a"), entry = anchor && payload.links[anchor.getAttribute("href")];
      const path = entry ? entry.path : caption.firstChild?.nodeType === Node.TEXT_NODE ? caption.firstChild.data.trim() : "";
      if (path) actions.append(copyAction("⧉ path", "Copy the file path", path));
      actions.append(copyAction("⧉ code", "Copy the code", text));
      caption.append(actions);
    }
  }

  function start() {
    const data = document.getElementById("peek-data"), main = document.querySelector("main");
    if (!data || !main || !("DecompressionStream" in window)) return;
    let loading = null, ticket = null, dialog = null, opener = null;
    if (main.querySelector("pre > code[class*='language-']")) {
      (window.requestIdleCallback || (callback => setTimeout(callback, 0)))(async () => {
        try {
          enhanceCards(await (loading = loading || unpack(data.textContent)), main);
        } catch (error) {
          console.error("Code highlighting unavailable", error);
        }
      });
    }
    const dialogFor = () => {
      if (dialog) return dialog;
      dialog = el("dialog", "peek-dialog");
      // A press on the backdrop targets the dialog itself, outside its box. Close only when the press started there
      // (a selection dragged out of the code ends on the dialog too), and not on a double-click's second click.
      const outside = event => {
        const box = dialog.getBoundingClientRect();
        return event.target === dialog && (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom);
      };
      let downOutside = false;
      dialog.addEventListener("pointerdown", event => { downOutside = outside(event); });
      dialog.addEventListener("click", event => {
        if (downOutside && event.detail < 2 && outside(event)) dialog.close();
      });
      dialog.addEventListener("close", () => {
        dialog.replaceChildren();
        opener.setAttribute("aria-expanded", "false");
        opener.focus();
        opener = null;
      });
      document.body.append(dialog);
      return dialog;
    };
    for (const link of main.querySelectorAll("a[data-peek]")) link.setAttribute("aria-expanded", "false");
    main.addEventListener("click", async event => {
      const link = event.target.closest("a[data-peek]");
      if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      if (event.detail > 1) return;  // a double-click opens one modal
      const mine = ticket = {link};  // a later click while the payload loads replaces this one
      let payload;
      try {
        payload = await (loading = loading || unpack(data.textContent));
      } catch (error) {
        if (ticket !== mine) return;
        console.error("Code peek unavailable", error);
        location.href = link.href;
        return;
      }
      if (ticket !== mine) return;
      const entry = payload.links[link.getAttribute("href")];
      if (!entry) { location.href = link.href; return; }
      const modal = dialogFor();
      modal.setAttribute("aria-label", `Code: ${entry.path}`);
      modal.replaceChildren(buildPeek(payload, entry, link, () => modal.close()));
      opener = link;
      modal.showModal();
      link.setAttribute("aria-expanded", "true");
      modal.querySelector(".peek-code").focus({preventScroll: true});
    });
  }

  start();
})(typeof module === "object" ? module.exports : null);
