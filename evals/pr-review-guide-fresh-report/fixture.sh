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
head=$(git rev-parse HEAD); base=$(git rev-parse main)
mkdir -p .scratch/feature-delete-review
cat > .scratch/feature-delete-review/report.md <<REPORT
---
head: $head
base: $base
---

# Review guide: note deletion

**Bottom line:** merge after one fix.

## What to look at

1. *you decide* · *we ran it* — \`sync.push\` now deletes every remote key that is missing locally, so a teammate's unpulled notes are erased from the bucket.
REPORT
