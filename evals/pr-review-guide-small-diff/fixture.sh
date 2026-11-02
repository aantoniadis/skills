#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/../notes-base.sh"
git checkout -q -b feature/delete
cat >> notes/store.py <<'PY'


def delete(note_id):
    """Remove a note. Returns True when a file was removed."""
    path = data_dir() / f"{note_id}.md"
    if path.exists():
        path.unlink()
        return True
    return False
PY
git add -A && git commit -qm "Add note deletion"
