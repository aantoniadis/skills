# Sourced by case fixtures: builds the "notes" repository on main in the current directory.
set -euo pipefail
export GIT_AUTHOR_NAME=eval GIT_AUTHOR_EMAIL=eval@example.invalid GIT_COMMITTER_NAME=eval GIT_COMMITTER_EMAIL=eval@example.invalid
git init -q -b main
mkdir -p notes tests
printf '__pycache__/\n/.scratch/\n' > .gitignore
: > notes/__init__.py
cat > notes/store.py <<'EOF'
"""Notes are Markdown files under NOTES_DIR, named by the slug of their title."""
import os
import re
from pathlib import Path


def data_dir():
    return Path(os.environ.get("NOTES_DIR", "data"))


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def save(title, text):
    note_id = slug(title)
    path = data_dir() / f"{note_id}.md"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return note_id


def load(note_id):
    return (data_dir() / f"{note_id}.md").read_text(encoding="utf-8")


def ids():
    return sorted(p.stem for p in data_dir().glob("*.md"))
EOF
cat > notes/index.py <<'EOF'
"""In-memory word index, refreshed from disk by modification time."""
import os

from . import store

_cache = {}  # note_id -> (mtime_ns, set of words)


def refresh():
    for note_id in store.ids():
        path = store.data_dir() / f"{note_id}.md"
        mtime = os.stat(path).st_mtime_ns
        if note_id not in _cache or _cache[note_id][0] != mtime:
            _cache[note_id] = (mtime, set(store.load(note_id).lower().split()))


def search(term):
    refresh()
    return sorted(note_id for note_id, (_, words) in _cache.items() if term.lower() in words)
EOF
cat > notes/links.py <<'EOF'
"""Notes link to each other with [[note-id]]."""
import re

from . import store

LINK = re.compile(r"\[\[([a-z0-9-]+)\]\]")


def backlinks(note_id):
    return [other for other in store.ids() if note_id in LINK.findall(store.load(other))]
EOF
cat > notes/sync.py <<'EOF'
"""Push notes to the team's remote store.

Production uses an S3-compatible bucket through RemoteStore; tests use FakeRemote.
Other team members' clients pull from the same bucket every few minutes and
treat every key as a note.
"""
from . import store


class FakeRemote:
    def __init__(self):
        self.objects = {}

    def put(self, key, body):
        self.objects[key] = body

    def keys(self):
        return sorted(self.objects)


def push(remote):
    for note_id in store.ids():
        remote.put(f"notes/{note_id}.md", store.load(note_id))
EOF
cat > tests/test_notes.py <<'EOF'
import os
import tempfile
import unittest


class NotesTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        os.environ["NOTES_DIR"] = self.dir.name

    def test_save_load_search_links_sync(self):
        from notes import index, links, store, sync
        a = store.save("Weekly Plan", "ship the parser")
        store.save("Retro", "see [[weekly-plan]] parser notes")
        self.assertEqual(store.load(a), "ship the parser")
        self.assertEqual(index.search("parser"), ["retro", "weekly-plan"])
        self.assertEqual(links.backlinks("weekly-plan"), ["retro"])
        remote = sync.FakeRemote()
        sync.push(remote)
        self.assertEqual(remote.keys(), ["notes/retro.md", "notes/weekly-plan.md"])


if __name__ == "__main__":
    unittest.main()
EOF
printf '# notes\n\nA small notes library: Markdown files named by title slug, a word index, [[links]], and push to a shared remote bucket.\n\nRun tests: `python3 -m unittest discover -s tests`\n' > README.md
git add -A && git commit -qm "Notes library"
