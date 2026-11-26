// Workbench pages (workbench.py): a panel card lights up the files it names in the structure view while
// it is hovered or focused; a click keeps it lit until another click.
(function () {
  const files = [...document.querySelectorAll(".structure-view .sv-file")];
  if (!files.length) return;
  const paths = files.map(f => [f, (f.dataset.path || "").toLowerCase()]);
  function named(cardEl) {
    // A pinned link names a file by its path; inline code can name it by its path or its file name.
    const said = new Set();
    for (const a of cardEl.querySelectorAll("a[href]")) {
      const m = a.getAttribute("href").match(/(?:blob\/[0-9a-f]{7,40}\/)?([^#?]+?\.[\w]{1,6})(?:#|$)/i);
      if (m) said.add(decodeURIComponent(m[1]).toLowerCase());
    }
    for (const c of cardEl.querySelectorAll("code, .sv-code")) said.add(c.textContent.trim().replace(/:\d+(?:-\d+)?$/, "").toLowerCase());
    const hit = new Set();
    for (const [f, p] of paths) {
      if (!p) continue;
      const base = p.split("/").pop();
      for (const s of said) if (s && (p.endsWith(s) || s.endsWith(p) || s === base)) hit.add(f);
    }
    return hit;
  }
  let pinned = null;
  const light = set => files.forEach(f => f.classList.toggle("hl", set.has(f)));
  for (const cardEl of document.querySelectorAll(".wb-card")) {
    const hit = named(cardEl);
    if (!hit.size) continue;
    cardEl.classList.add("wb-linked");
    cardEl.addEventListener("mouseenter", () => light(hit));
    cardEl.addEventListener("focus", () => light(hit));
    cardEl.addEventListener("mouseleave", () => light(pinned ? named(pinned) : new Set()));
    cardEl.addEventListener("blur", () => light(pinned ? named(pinned) : new Set()));
    cardEl.addEventListener("click", ev => {
      if (ev.target.closest("a")) return;
      if (pinned) pinned.classList.remove("pinned");
      pinned = pinned === cardEl ? null : cardEl;
      if (pinned) pinned.classList.add("pinned");
      light(pinned ? hit : new Set());
    });
  }
})();
