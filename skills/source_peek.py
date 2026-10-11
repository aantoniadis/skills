"""Embed the files a reading page cites, pinned GitHub links and files beside the note, for its inline code peek (peek.js)."""
import base64
from dataclasses import dataclass
import difflib
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

MAX_LINES = 20_000  # ponytail: no peek past this; window the rows (like the native viewer) if bigger files matter
FOLD_MIN, FOLD_CONTEXT = 8, 3
BLOB = re.compile(r"^/([^/]+)/([^/]+)/blob/([0-9a-f]{40})/(.+)$")
SHA = re.compile(r"^[0-9a-f]{40}$")
FILE_KEY = re.compile(r"^([0-9a-f]{40}):(.+)$", re.S)
DIFF_KEY = re.compile(r"^([0-9a-f]{40})\.\.([0-9a-f]{40}):(.+)$", re.S)
LOCAL_KEY = re.compile(r"^local:(.+)$", re.S)
PAGES = (".md", ".html")  # local links to these open the page, not a peek
NO_REPOSITORY, NO_COMMIT = "no git repository to read", "commit not in the local clone"
OVERLONG = "binary, non-UTF-8, or over 20,000 lines"
LINES = re.compile(r"^L(\d+)(?:-L?(\d+))?$")
WORD = re.compile(r"\w+|\s+|[^\w\s]")
HIGHLIGHT = Path(__file__).resolve().parent / "assets/highlight"
CORE_EXPORT = re.compile(r"export\s*\{\s*(\w+)\s+as\s+default\s*\}\s*;?\s*$")
GRAMMAR_EXPORT = re.compile(r"export\s+default\s+(\w+)\s*;?\s*$")
LANGUAGES = {
    ".py": "python", ".pyi": "python", ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".mts": "typescript", ".cts": "typescript", ".rs": "rust", ".go": "go",
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin", ".scala": "scala", ".rb": "ruby", ".php": "php", ".cs": "csharp",
    ".c": "c", ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".hpp": "cpp", ".swift": "swift", ".sh": "bash", ".bash": "bash",
    ".zsh": "bash", ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "ini", ".ini": "ini", ".cfg": "ini",
    ".md": "markdown", ".html": "xml", ".xml": "xml", ".svg": "xml", ".css": "css", ".scss": "scss", ".sql": "sql",
    ".lua": "lua", ".dart": "dart", ".ex": "elixir", ".exs": "elixir", ".hs": "haskell", ".r": "r",
}
NAMES = {"Dockerfile": "dockerfile", "Makefile": "makefile"}
GRAMMARS = set(LANGUAGES.values()) | set(NAMES.values())  # the vendored grammars (assets/highlight/SOURCE.md)
# Fence info strings as reviewers spell them, mapped to the grammar that highlights them.
ALIASES = {"sh": "bash", "shell": "bash", "zsh": "bash", "py": "python", "ts": "typescript", "tsx": "typescript",
           "js": "javascript", "jsx": "javascript", "mjs": "javascript", "yml": "yaml", "html": "xml", "rb": "ruby",
           "kt": "kotlin", "cs": "csharp", "golang": "go", "shell-session": "bash", "console": "bash"}


@dataclass(frozen=True)
class Citation:
    href: str
    repository: str
    commit: str
    path: str
    start: int | None
    end: int | None


def citation(href):
    """The parts of a pinned GitHub blob link (full SHA, optional #Lx or #Lx-Ly in either order), or None for any other link."""
    url = urlsplit(href)
    match = BLOB.match(url.path) if url.scheme == "https" and url.netloc == "github.com" else None
    lines = LINES.match(url.fragment) if url.fragment else None
    if not match or (url.fragment and not lines):
        return None
    ends = sorted((int(lines[1]), int(lines[2] or lines[1]))) if lines else (None, None)
    if lines and ends[0] < 1:
        return None  # GitHub has no line 0
    return Citation(href, f"{match[1]}/{match[2]}", match[3], unquote(match[4]), *ends)


def local_citation(href, directory):
    """A relative link to a file beside the note (a run, probe output, or saved snapshot), with an optional #Lx-Ly;
    None for a page (.md, .html), an anchor, a remote link, a file outside the note's directory, or without a directory."""
    url = urlsplit(href)
    if directory is None or url.scheme or url.netloc or not url.path:
        return None
    lines = LINES.match(url.fragment) if url.fragment else None
    if url.fragment and not lines:
        return None
    path = os.path.normpath(unquote(url.path))
    root = Path(directory).resolve()
    target = (root / path).resolve()
    if os.path.isabs(path) or Path(path).suffix.lower() in PAGES or not target.is_file() or not target.is_relative_to(root):
        return None
    ends = sorted((int(lines[1]), int(lines[2] or lines[1]))) if lines else (None, None)
    if lines and ends[0] < 1:
        return None
    return Citation(href, None, None, path, *ends)


def git(repo, *args):
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                              env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")})
    except OSError:  # git not installed or not executable: callers treat it as "no repository"
        return subprocess.CompletedProcess(args, 127, b"", b"")


def repository_root(start):
    result = git(start, "rev-parse", "--show-toplevel")
    return Path(result.stdout.decode().strip()) if result.returncode == 0 else None


def resolve(repo, revision):
    """The full commit SHA for a revision, or None when the clone lacks it."""
    result = git(repo, "rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}")
    return result.stdout.decode().strip() if result.returncode == 0 else None


def blob(repo, commit, path):
    """The file's bytes at the commit, or None when the path is not a file there."""
    result = git(repo, "cat-file", "blob", f"{commit}:{path}")
    return result.stdout if result.returncode == 0 else None


def as_text(data):
    """Text for a peek, or None for binary, non-UTF-8, or overlong files."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return None if "\0" in text or len(split_lines(text)) > MAX_LINES else text


def split_lines(text):
    """Lines as peek.js splits them: on \\n only, without a trailing empty line."""
    lines = text.split("\n")
    return lines[:-1] if lines[-1] == "" else lines


def offsets(tokens):
    result = [0]
    for token in tokens:
        result.append(result[-1] + len(token))
    return result


def word_marks(left, right):
    """Character ranges [start, end) that differ between two paired lines, compared word by word."""
    a, b = WORD.findall(left), WORD.findall(right)
    at, bt = offsets(a), offsets(b)
    marks = ([], [])
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != "equal":
            if i2 > i1:
                marks[0].append([at[i1], at[i2]])
            if j2 > j1:
                marks[1].append([bt[j1], bt[j2]])
    return [marks[0], marks[1]]


def folds(rows):
    """Unchanged runs longer than FOLD_MIN rows, less FOLD_CONTEXT rows beside each change, as [from, to) row ranges."""
    result, start = [], None
    for index, row in enumerate(rows + [["~", None, None]]):  # the sentinel closes the last run
        if row[0] == "=":
            start = index if start is None else start
            continue
        if start is not None:
            low = start + (FOLD_CONTEXT if start > 0 else 0)
            high = index - (FOLD_CONTEXT if index < len(rows) else 0)
            if high - low > FOLD_MIN:
                result.append([low, high])
            start = None
    return result


def diff(base_text, head_text):
    """Aligned side-by-side rows: equal, changed (paired, with word marks), deleted, added.
    ponytail: SequenceMatcher without autojunk is quadratic in the worst case; fine to MAX_LINES in practice."""
    a = split_lines(base_text) if base_text is not None else []
    b = split_lines(head_text) if head_text is not None else []
    rows, marks = [], {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            rows += [["=", i + 1, j + 1] for i, j in zip(range(i1, i2), range(j1, j2))]
            continue
        pairs = min(i2 - i1, j2 - j1) if tag == "replace" else 0
        for k in range(pairs):
            marks[str(len(rows))] = word_marks(a[i1 + k], b[j1 + k])
            rows.append(["~", i1 + k + 1, j1 + k + 1])
        rows += [["-", i + 1, None] for i in range(i1 + pairs, i2)]
        rows += [["+", None, j + 1] for j in range(j1 + pairs, j2)]
    return {"rows": rows, "marks": marks, "folds": folds(rows),
            "added": sum(row[0] in "~+" for row in rows), "removed": sum(row[0] in "~-" for row in rows)}


def language(path):
    name = Path(path).name
    return NAMES.get(name) or LANGUAGES.get(Path(name).suffix.lower())


def module_body(path, pattern):
    """A vendored ES module as a function body returning its default export; the page runs it with new Function."""
    body, count = pattern.subn(r"return \1;", path.read_text())
    if count != 1:
        raise ValueError(f"Unexpected module shape in {path.name}; re-vendor highlight.js as assets/highlight/SOURCE.md says.")
    return body


def grammar(fence):
    """The vendored grammar for a fence's language name, or None when none ships."""
    name = ALIASES.get(fence.lower(), fence.lower())
    return name if name in GRAMMARS else None


def highlighter(files, fences=()):
    """The highlight.js core and the grammars of the payload files and the page's fences, as new Function bodies."""
    names = sorted({file["language"] for file in files.values() if file["language"]} | {g for g in map(grammar, fences) if g})
    return {"core": module_body(HIGHLIGHT / "core.min.js", CORE_EXPORT),
            "languages": {name: module_body(HIGHLIGHT / "languages" / f"{name}.min.js", GRAMMAR_EXPORT) for name in names}}


def markdown_line(source, href):
    """Where the Markdown first spells the link, as ' (Markdown line N)', or '' when it spells it otherwise."""
    at = source.find(href)
    return f" (Markdown line {source.count(chr(10), 0, at) + 1})" if at >= 0 else ""


def build(hrefs, front, repo, source="", directory=None, fences=()):
    """The peek payload for the page's links and the links left without a peek, as (href, reason) pairs.
    source is the Markdown, read only to name the line of a cited file that is missing at its commit; directory is
    the note's, where relative links find the files beside it; fences are the page's fence languages to highlight."""
    hrefs = list(dict.fromkeys(hrefs))
    files, diffs, links, skipped = {}, {}, {}, []
    for c in (local_citation(href, directory) for href in hrefs):
        if c is None:
            continue
        key = f"local:{c.path}"
        if key not in files:
            text = as_text((Path(directory) / c.path).read_bytes())
            if text is None:
                skipped.append((c.href, OVERLONG))
                continue
            files[key] = {"text": text, "language": language(c.path)}
        links[c.href] = {"file": key, "commit": None, "path": c.path, "start": c.start, "end": c.end, "side": None, "diff": None}
    cited = [c for c in map(citation, hrefs) if c]
    grammars = any(map(grammar, fences))
    if not cited:
        if not links and not grammars:
            return None, skipped  # no process starts for a page without pinned links
        return {"files": files, "diffs": diffs, "links": links, "hljs": highlighter(files, fences)}, skipped
    root = repository_root(repo or Path.cwd())
    if root is None:
        skipped += [(c.href, NO_REPOSITORY) for c in cited]
        if not links and not grammars:
            return None, skipped
        return {"files": files, "diffs": diffs, "links": links, "hljs": highlighter(files, fences)}, skipped
    base = head = None
    for key in ("base", "head"):
        if key in front:
            commit = resolve(root, front[key])
            if commit is None:
                raise ValueError(f"Front matter {key} does not resolve to a commit in {root}: {front[key]!r}")
            base, head = (commit, head) if key == "base" else (base, commit)
    texts = {}

    def text_at(commit, path):
        if (commit, path) not in texts:
            data = blob(root, commit, path)
            texts[commit, path] = None if data is None else as_text(data)
        return texts[commit, path]

    def add_file(commit, path):
        key = f"{commit}:{path}"
        files.setdefault(key, {"text": texts[commit, path], "language": language(path)})
        return key

    for c in cited:
        if resolve(root, c.commit) != c.commit:
            skipped.append((c.href, NO_COMMIT))
            continue
        if blob(root, c.commit, c.path) is None:
            raise ValueError(f"Cited file does not exist at its commit: {c.href}{markdown_line(source, c.href)}")
        if text_at(c.commit, c.path) is None:
            skipped.append((c.href, OVERLONG))
            continue
        link = {"file": add_file(c.commit, c.path), "commit": c.commit, "path": c.path,
                "start": c.start, "end": c.end, "side": None, "diff": None}
        if base and head and c.commit in (base, head):
            key = f"{base}..{head}:{c.path}"
            if key not in diffs:
                before, after = text_at(base, c.path), text_at(head, c.path)
                readable = all(t is not None or blob(root, s, c.path) is None for t, s in ((before, base), (after, head)))
                diffs[key] = None if before == after or not readable else {
                    "base": add_file(base, c.path) if before is not None else None,
                    "head": add_file(head, c.path) if after is not None else None,
                    "commits": [base, head], **diff(before, after)}
            if diffs[key]:
                link.update(side="base" if c.commit == base else "head", diff=key)
        links[c.href] = link
    diffs = {key: value for key, value in diffs.items() if value}
    if not links and not grammars:
        return None, skipped
    return {"files": files, "diffs": diffs, "links": links, "hljs": highlighter(files, fences)}, skipped


def encode(payload):
    return base64.b64encode(gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)).decode("ascii")


def decode(text):
    return json.loads(gzip.decompress(base64.b64decode(text.strip(), validate=True)))


def verify(payload, front, repo, directory=None):
    """Re-derive what the links, keys, and front matter imply, refuse any contradiction, and compare each embedded
    file with git where the clone has its commit, or with the file beside the note for a local link.
    Return the (file key, reason) pairs not compared with git."""
    files, diffs, links = payload["files"], payload["diffs"], payload["links"]
    # Files beside the note and fence grammars need no git; a page without pinned links starts no process.
    root = repository_root(repo or Path.cwd()) if any(not LOCAL_KEY.match(key) for key in files) else None
    local = {}

    def is_local(commit):
        if commit not in local:
            local[commit] = root is not None and resolve(root, commit) == commit
        return local[commit]

    for key, file in files.items():
        match = LOCAL_KEY.match(key) or FILE_KEY.match(key)
        if not match:
            raise ValueError(f"Embedded code key is not a full commit SHA and path: {key}; re-render the page.")
        if file["language"] != language(match[match.lastindex]):
            raise ValueError(f"Embedded code language differs from its path: {key}; re-render the page.")
    for key, stored in diffs.items():
        match = DIFF_KEY.match(key)
        names = (stored["base"], stored["head"])
        if not match or stored["commits"] != [match[1], match[2]] or names == (None, None) or any(
                name not in (None, f"{commit}:{match[3]}") or (name is not None and name not in files)
                for name, commit in zip(names, (match[1], match[2]))):
            raise ValueError(f"Embedded diff does not match its key: {key}; re-render the page.")
        texts = [files[name]["text"] if name else None for name in names]
        if texts[0] == texts[1] or {k: stored[k] for k in ("rows", "marks", "folds", "added", "removed")} != diff(*texts):
            raise ValueError(f"Embedded diff differs from its texts: {key}; re-render the page.")
        for name, commit in zip(names, (match[1], match[2])):
            if name is None and is_local(commit) and blob(root, commit, match[3]) is not None:
                raise ValueError(f"Embedded diff omits a file that exists at {commit}: {key}; re-render the page.")
    for href, link in links.items():
        c = citation(href) or local_citation(href, directory)
        key = f"{c.commit}:{c.path}" if c and c.commit else f"local:{c.path}" if c else None
        if c is None or link["file"] not in files or [link["file"], link["commit"], link["path"], link["start"], link["end"]] \
                != [key, c.commit, c.path, c.start, c.end]:
            raise ValueError(f"Code peek data contradicts its link: {href}; re-render the page.")
        if (link["diff"], link["side"]) != (None, None) and (
                link["diff"] not in diffs or link["side"] not in ("base", "head") or DIFF_KEY.match(link["diff"])[3] != c.path
                or diffs[link["diff"]]["commits"][link["side"] == "head"] != c.commit):
            raise ValueError(f"Code peek diff does not match its link: {href}; re-render the page.")
    if diffs.keys() - {link["diff"] for link in links.values()}:
        raise ValueError("Code peek data holds a diff that no link opens; re-render the page.")
    if files.keys() - {link["file"] for link in links.values()} - {d[side] for d in diffs.values() for side in ("base", "head")}:
        raise ValueError("Code peek data holds a file that no link or diff uses; re-render the page.")
    if diffs and not ("base" in front and "head" in front):
        raise ValueError("Code peek data holds a diff, but the front matter gives no base and head; re-render the page.")
    ends = []
    for name in ("base", "head"):
        value = front.get(name, "")
        commit = resolve(root, value) if root is not None and value else None
        ends.append(commit or (value if SHA.match(value) else None))
    if all(ends):  # base and head known: a link at either commit whose two embedded texts differ opens their diff
        for href, link in links.items():
            if link["diff"] not in (None, f"{ends[0]}..{ends[1]}:{link['path']}"):
                raise ValueError(f"Code peek diff does not compare the front matter's base and head: {href}; re-render the page.")
            texts = [files.get(f"{commit}:{link['path']}") for commit in ends]
            if link["commit"] in ends and all(texts) and texts[0]["text"] != texts[1]["text"] and link["diff"] is None:
                raise ValueError(f"Code peek lacks the base-to-head diff for {href}; re-render the page.")
    unverified = []
    for key, file in files.items():
        if LOCAL_KEY.match(key):  # its link was re-derived above, so the file exists beside the note
            if (Path(directory) / LOCAL_KEY.match(key)[1]).read_bytes().decode("utf-8", errors="replace") != file["text"]:
                raise ValueError(f"Embedded code differs from the file beside the note: {key}; re-render the page.")
            continue
        commit, path = FILE_KEY.match(key).groups()
        if not is_local(commit):
            unverified.append((key, NO_REPOSITORY if root is None else NO_COMMIT))
            continue
        data = blob(root, commit, path)
        if data is None:
            raise ValueError(f"Embedded code names a file missing at its commit: {key}; re-render the page.")
        if data.decode("utf-8", errors="replace") != file["text"]:
            raise ValueError(f"Embedded code differs from git at {key}; re-render the page.")
    return unverified
