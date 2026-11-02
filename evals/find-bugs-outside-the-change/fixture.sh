#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/../notes-base.sh"
git checkout -q -b feature/search-terms
python3 - <<'PY'
from pathlib import Path
p = Path("notes/index.py"); s = p.read_text()
s = s.replace('''def search(term):
    refresh()
    return sorted(note_id for note_id, (_, words) in _cache.items() if term.lower() in words)''', '''def search(query):
    """Return ids of notes that contain every word of the query."""
    refresh()
    terms = query.split()
    first, rest = terms[0].lower(), terms[1:]
    return sorted(note_id for note_id, (_, words) in _cache.items()
                  if first in words and all(t in words for t in rest))''')
p.write_text(s)
t = Path("tests/test_notes.py"); s = t.read_text()
s = s.replace('''

if __name__''', '''
    def test_search_all_terms(self):
        from notes import index, store
        store.save("Plan", "ship the lexer")
        store.save("Other", "ship it")
        self.assertEqual(index.search("ship lexer"), ["plan"])


if __name__''')
t.write_text(s)
PY
git add -A && git commit -qm "Search by every word of the query"
