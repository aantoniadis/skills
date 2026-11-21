#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/../notes-base.sh"

cat > notes/cli.py <<'EOF'
"""Command line entry point: python -m notes.cli <command> [args]."""
import sys

from . import index, store


def main(argv):
    command = argv[1] if len(argv) > 1 else "list"
    if command == "list":
        print(", ".join(store.ids()))
        return 0
    if command == "search":
        print(", ".join(index.search(argv[2] if len(argv) > 2 else "")))
        return 0
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
EOF
python3 - <<'PY'
from pathlib import Path
t = Path("tests/test_notes.py"); s = t.read_text()
s = s.replace('''

if __name__''', '''
    def test_cli_list_and_unknown_command(self):
        import contextlib
        import io
        from notes import cli, store
        store.save("Weekly Plan", "ship the parser")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["notes", "list"]), 0)
        self.assertEqual(out.getvalue().strip(), "weekly-plan")
        self.assertEqual(cli.main(["notes", "bogus"]), 2)


if __name__''')
t.write_text(s)
PY
git add -A && git commit -qm "Add a command line entry point"

git checkout -q -b feature/batch-import
cat > notes/batch.py <<'EOF'
"""Bulk import and export of notes."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import index, store


def import_dir(source):
    """Import every Markdown file under source. Returns the new note ids."""
    paths = sorted(Path(source).rglob("*.md"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(_import_one, paths))


def _import_one(path):
    text = path.read_text(encoding="utf-8")
    note_id = store.save(path.stem, text, note_id=path.stem)
    index.refresh()
    return note_id


def replace_all(source):
    """Replace the whole note set with the contents of source."""
    for note_id in store.ids():
        store.delete(note_id)
    return import_dir(source)


def average_words(source):
    """Mean word count of the Markdown files under source."""
    paths = sorted(Path(source).rglob("*.md"))
    total = sum(len(p.read_text(encoding="utf-8").split()) for p in paths)
    return total / len(paths)


def export_search(term, target):
    """Write the ids matching term to target, one per line. Returns the count."""
    hits = index.search(term)
    Path(target).write_text("\n".join(note_id for note_id, _ in hits), encoding="utf-8")
    return len(hits)


def export_note(note_id, target):
    """Copy one note to target. A note deleted since listing is skipped."""
    try:
        text = store.load(note_id)
    except FileNotFoundError:
        return False
    Path(target).write_text(text, encoding="utf-8")
    return True
EOF
python3 - <<'PY'
from pathlib import Path

p = Path("notes/store.py"); s = p.read_text()
s = s.replace('''def save(title, text):
    note_id = slug(title)''', '''def save(title, text, note_id=None):
    """Write a note. note_id overrides the slug of the title."""
    note_id = note_id or slug(title)''')
s = s.replace('''def ids():''', '''def delete(note_id):
    (data_dir() / f"{note_id}.md").unlink()


def ids():''')
p.write_text(s)

p = Path("notes/index.py"); s = p.read_text()
s = s.replace('''def search(term):
    refresh()
    return sorted(note_id for note_id, (_, words) in _cache.items() if term.lower() in words)''', '''def search(term):
    """Return (note_id, score) pairs, best match first."""
    refresh()
    words = term.lower().split()
    scored = []
    for note_id, (_, cached) in _cache.items():
        hits = sum(1 for word in words if word in cached)
        if hits:
            scored.append((note_id, hits))
    return sorted(scored, key=lambda pair: (-pair[1], pair[0]))''')
p.write_text(s)

p = Path("notes/sync.py"); s = p.read_text()
s = s.replace('remote.put(f"notes/{note_id}.md"', 'remote.put(f"notes/v2/{note_id}.md"')
p.write_text(s)

t = Path("tests/test_notes.py"); s = t.read_text()
s = s.replace('''        os.environ["NOTES_DIR"] = self.dir.name''',
              '''        os.environ["NOTES_DIR"] = self.dir.name
        from notes import index
        index._cache.clear()''')
s = s.replace('self.assertEqual(index.search("parser"), ["retro", "weekly-plan"])',
              'self.assertEqual(index.search("parser"), [("retro", 1), ("weekly-plan", 1)])')
s = s.replace('self.assertEqual(remote.keys(), ["notes/retro.md", "notes/weekly-plan.md"])',
              'self.assertIn("notes/v2/retro.md", remote.keys())')
s = s.replace('''

if __name__''', '''
    def test_delete_removes_file(self):
        from notes import store
        store.save("Weekly Plan", "ship the parser")
        store.delete("weekly-plan")
        self.assertEqual(store.ids(), [])

    def test_import_dir_and_average_words(self):
        from notes import batch, store
        src = tempfile.TemporaryDirectory()
        self.addCleanup(src.cleanup)
        Path(src.name, "plan.md").write_text("ship the parser", encoding="utf-8")
        Path(src.name, "retro.md").write_text("parser notes", encoding="utf-8")
        self.assertEqual(sorted(batch.import_dir(src.name)), ["plan", "retro"])
        self.assertEqual(store.load("plan"), "ship the parser")
        self.assertEqual(batch.average_words(src.name), 2.5)

    def test_replace_all(self):
        from notes import batch, store
        store.save("Old Note", "gone soon")
        src = tempfile.TemporaryDirectory()
        self.addCleanup(src.cleanup)
        Path(src.name, "plan.md").write_text("ship the parser", encoding="utf-8")
        self.assertEqual(batch.replace_all(src.name), ["plan"])
        self.assertEqual(store.ids(), ["plan"])

    def test_export_search(self):
        from notes import batch, store
        store.save("Weekly Plan", "ship the parser")
        out = Path(self.dir.name, "hits.txt")
        self.assertEqual(batch.export_search("parser", out), 1)
        self.assertEqual(out.read_text(encoding="utf-8"), "weekly-plan")

    def test_export_note_skips_deleted(self):
        from notes import batch, store
        store.save("Weekly Plan", "ship the parser")
        store.delete("weekly-plan")
        out = Path(self.dir.name, "copy.md")
        self.assertFalse(batch.export_note("weekly-plan", out))
        self.assertFalse(out.exists())


if __name__''')
s = s.replace("import os\nimport tempfile\nimport unittest",
              "import os\nimport tempfile\nimport unittest\nfrom pathlib import Path")
t.write_text(s)
PY
git add -A && git commit -qm "Import and export notes in bulk"
