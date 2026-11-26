// Structure notes (workbench.py): the page is light; this button switches to dark for a reader who asks,
// and remembers the choice in this browser only. The page reads the same without it.
(function () {
  const root = document.documentElement;
  const button = document.querySelector(".theme-toggle");
  const KEY = "structure-note-theme";
  function apply(theme) {
    root.dataset.theme = theme;
    if (button) {
      button.setAttribute("aria-pressed", String(theme === "dark"));
      button.textContent = theme === "dark" ? "Light theme" : "Dark theme";
    }
  }
  let saved = "light";
  try { saved = localStorage.getItem(KEY) || "light"; } catch (e) { /* storage blocked: stay light */ }
  apply(saved === "dark" ? "dark" : "light");
  if (button) button.addEventListener("click", () => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    apply(next);
    try { localStorage.setItem(KEY, next); } catch (e) { /* not remembered */ }
  });
})();
