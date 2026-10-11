"""What a reader who was not there cannot decode (TECHNICAL-ENGLISH.md): bookkeeping IDs such as F2 or D1,
and the skills' own process words. Fenced code, inline code, link targets, and URLs are not prose."""

import re

BOOKKEEPING_ID = re.compile(r"(?<![\w#/.:-])[A-Z][0-9]{1,2}(?![\w/:-])")
# Product names shaped like an ID that replies name in prose: Cloudflare R2, AWS S3, Backblaze B2.
# Any other such name goes in a code span (TECHNICAL-ENGLISH.md).
PRODUCT_NAMES = {"R2", "S3", "B2"}
# Only phrasings that belong to these skills; "provisional" or "lower-tier" alone have domain meanings.
PROCESS = re.compile(r"\((?:provisional)\)|\b(?:defect pass|fresh review|lower-tier (?:review|model|check)"
                     r"|automatic depth|claim check)\b", re.I)


def reader_gaps(text):
    """(line, text) for each bookkeeping ID or process word in the prose of a Markdown text."""
    gaps = []
    fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if re.match(r"\s*(`{3,}|~{3,})", line):
            fenced = not fenced
            continue
        if fenced:
            continue
        prose = re.sub(r"`[^`]*`|\]\([^)]*\)|<[^>]*>|https?://\S+", " ", line)
        found = [*(match for match in BOOKKEEPING_ID.finditer(prose) if match.group(0) not in PRODUCT_NAMES),
                 *PROCESS.finditer(prose)]
        gaps.extend((number, match.group(0)) for match in sorted(found, key=lambda m: m.start()))
    return gaps
