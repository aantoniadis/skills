// The structure view of a rework map (structure_view.py draws it; this adds the switch and selection).
(function () {
  for (const fig of document.querySelectorAll("figure.structure-view")) {
    const switcher = fig.querySelector(".sv-switch");
    const facts = fig.querySelector(".sv-facts");
    const dots = [...fig.querySelectorAll(".sv-dot")];
    const edges = [...fig.querySelectorAll(".sv-edge")];
    const files = [...fig.querySelectorAll(".sv-file")];
    const ruleButtons = [...fig.querySelectorAll(".sv-rule")];
    const hint = fig.querySelector(".sv-hint");
    const sideLabel = fig.querySelector(".sv-side-label");
    let view = "today", selected = null;
    const fileOf = (dot, v) => {  // the file box under a dot in a view
      const [x, y] = dot.dataset[v].split(",").map(Number);
      return files.find(f => { const r = f.querySelector("rect"), rx = +r.getAttribute("x"), ry = +r.getAttribute("y");
        return x >= rx && x <= rx + +r.getAttribute("width") && y >= ry && y <= ry + +r.getAttribute("height"); });
    };
    function render() {
      fig.dataset.view = view;
      switcher.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b.dataset.view === view));
      facts.innerHTML = facts.dataset[view];
      if (sideLabel) sideLabel.textContent = sideLabel.dataset[view];
      for (const e of edges) {
        const status = e.dataset[view];
        e.style.display = status ? "" : "none";
        if (status) {
          const cls = status.replace(" ", "-");
          e.classList.remove("as-stated", "not-stated", "not-found"); e.classList.add(cls);
          const line = e.querySelector(".sv-line"), marker = line.getAttribute("marker-end");
          line.setAttribute("marker-end", marker.replace(/-(as-stated|not-stated|not-found)\)$/, "-" + cls + ")"));
        }
        e.classList.toggle("dim", selected !== null);
      }
      const keep = new Set();
      for (const d of dots) {
        const [x, y] = d.dataset[view].split(",");
        d.setAttribute("transform", `translate(${x} ${y})`);
        const mine = selected === null || d.dataset.rule === selected;
        d.classList.toggle("dim", !mine);
        if (selected !== null && mine) keep.add(fileOf(d, view));
      }
      files.forEach(f => f.classList.toggle("dim", selected !== null && !keep.has(f)));
      for (const b of ruleButtons) {
        b.setAttribute("aria-pressed", b.dataset.rule === selected);
        const c = b.querySelector(".sv-count"), n = +c.dataset[view];
        c.textContent = `${n} ${n === 1 ? "file" : "files"}`; c.classList.toggle("many", n > 1);
      }
      fig.querySelectorAll(".sv-detail").forEach(d => { d.hidden = d.dataset.rule !== selected; });
      if (hint) hint.hidden = selected !== null;
    }
    switcher.hidden = false;
    switcher.addEventListener("click", ev => { const b = ev.target.closest("button"); if (b) { view = b.dataset.view; render(); } });
    ruleButtons.forEach(b => b.addEventListener("click", () => { selected = selected === b.dataset.rule ? null : b.dataset.rule; render(); }));
    dots.forEach(d => d.addEventListener("click", () => { selected = selected === d.dataset.rule ? null : d.dataset.rule; render(); }));
    for (const row of fig.querySelectorAll(".sv-matrix tbody tr")) {
      row.addEventListener("click", () => {
        const on = !row.classList.contains("on");
        fig.querySelectorAll(".sv-matrix tbody tr").forEach(r => r.classList.remove("on"));
        row.classList.toggle("on", on);
        const ids = new Set(on ? row.dataset.files.split(" ") : []);
        files.forEach(f => f.classList.toggle("hl", ids.has(f.dataset.file)));
      });
    }
    render();
  }
})();
