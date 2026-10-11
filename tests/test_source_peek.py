"""Check the code peek with python3 tests/test_source_peek.py."""
import base64
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills"))
spec = importlib.util.spec_from_file_location("reading_page", ROOT / "skills/render_page.py")
page = importlib.util.module_from_spec(spec)
spec.loader.exec_module(page)

REPORT = """---
base: {base}
head: {head}
repository: acme/widgets
---
# Widget counting

**Bottom line:** Duplicates no longer count; see [count](https://github.com/acme/widgets/blob/{head}/src/count.py#L2-L3).

## Details

The old code is [here](https://github.com/acme/widgets/blob/{base}/src/count.py#L2).
"""


def front_matter():
    source = REPORT.format(base="a" * 40, head="b" * 40)
    meta, body = page.split_front_matter(source)
    assert meta == {"base": "a" * 40, "head": "b" * 40, "repository": "acme/widgets"}, meta
    assert body.count("\n") == source.count("\n"), "line numbers must hold"
    assert body.startswith("\n" * 5 + "# Widget counting"), body[:40]
    assert page.split_front_matter(body) == ({}, body)
    assert page.with_front_matter(source, body + "\nextra\n") == source + "\nextra\n"
    # A note that opens with a thematic break is not front matter: its intro renders and nothing is blanked.
    ruled = "---\nIntro that matters.\n\n---\n# Plain\n\n**Bottom line:** none.\n"
    assert page.split_front_matter(ruled) == ({}, ruled)
    assert page.with_front_matter(ruled, ruled + "x\n") == ruled + "x\n"
    assert "Intro that matters." in page.render(ruled, "ruled.md")
    unfilled = REPORT.replace("{base}", "{{{{merge_base_sha}}}}").format(head="b" * 40)
    rejected(lambda: page.check_front_matter(page.split_front_matter(unfilled)[0]), "unfilled template prompts: base.")
    with tempfile.TemporaryDirectory() as directory:
        html = page.render(source, "report.md", repo=Path(directory))  # no repository: the links are only listed
        assert "base: " not in html and "<hr" not in html, "front matter must not render"
        rejected(lambda: page.check(unfilled, html, Path(directory) / "report.md", repo=Path(directory)),
                 "unfilled template prompts: base.")
        template = Path(directory) / "template.md"
        template.write_text(unfilled)  # no page beside it: the Markdown-only check path
        result = subprocess.run([sys.executable, str(ROOT / "skills/render_page.py"), str(template), "--check"],
                                capture_output=True, text=True)
        assert result.returncode == 1 and "Front matter contains unfilled template prompts: base." in result.stderr, result
        note = Path(directory) / "report.md"
        note.write_text(source)
        subprocess.run([sys.executable, str(ROOT / "skills/render_page.py"), str(note), "--sync-labels"], check=True,
                       capture_output=True)
        assert note.read_text().startswith(source.split("# Widget")[0]), "front matter must survive --sync-labels"


import source_peek  # noqa: E402


def git(repo, *args):
    """git without the user's global or system config (signing, hooks, templates)."""
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                          check=True, capture_output=True, text=True,
                          env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}).stdout.strip()


def commit(repo, files, message):
    """Write {path: text|bytes|None} (None deletes) and return the new commit SHA."""
    for path, content in files.items():
        target = repo / path
        if content is None:
            target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content if isinstance(content, bytes) else content.encode())
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def fixture(directory):
    repo = Path(directory) / "widgets"
    repo.mkdir()
    git(repo, "init", "-q")
    unchanged = "".join(f"x{n} = {n}\n" for n in range(20))
    base = commit(repo, {
        "src/count.py": "def count(keys):\n    n = len(keys)\n    return n\n" + unchanged + "def tail():\n    return 0\n",
        "src/gone.py": "old = 1\n",
        "docs/My File.md": "# Title\n",
        "crlf.txt": b"one\r\ntwo\r\nthree",
        "blob.bin": b"\x00\x01\x02",
    }, "base")
    head = commit(repo, {
        "src/count.py": "def count(keys):\n    n = len(set(keys))\n    return n\n" + unchanged + "def tail():\n    return 1\n",
        "src/gone.py": None,
        "src/new.py": "fresh = 2\n",
    }, "head")
    return repo, base, head


def url(sha, path, fragment=""):
    return f"https://github.com/acme/widgets/blob/{sha}/{path}{fragment}"


def citations():
    sha = "c" * 40
    assert source_peek.citation(url(sha, "a/b.py", "#L10-L24")).start == 10
    assert source_peek.citation(url(sha, "a/b.py", "#L10-L24")).end == 24
    assert source_peek.citation(url(sha, "a/b.py", "#L10-24")).end == 24
    assert (source_peek.citation(url(sha, "a/b.py", "#L7")).start, source_peek.citation(url(sha, "a/b.py", "#L7")).end) == (7, 7)
    assert source_peek.citation(url(sha, "a/b.py")).start is None
    reversed_range = source_peek.citation(url(sha, "a/b.py", "#L24-L10"))
    assert (reversed_range.start, reversed_range.end) == (10, 24), "a reversed range is normalised"
    assert source_peek.citation(url(sha, "a/b.py", "#L0")) is None, "GitHub has no line 0: a plain link"
    assert source_peek.citation(url(sha, "a/b.py", "#L0-L3")) is None
    assert source_peek.citation(url(sha, "a/b.md") + "?plain=1#L3").start == 3
    assert source_peek.citation(url(sha, "a/b.md", "#readme")) is None
    assert source_peek.citation(url(sha, "docs/My%20File.md")).path == "docs/My File.md"
    assert source_peek.citation(url("abc123", "a.py")) is None, "short SHAs are not pinned"
    assert source_peek.citation("https://github.com/acme/widgets/pull/3") is None
    assert source_peek.citation("https://example.com/acme/widgets/blob/" + sha + "/a.py") is None


def diffs():
    result = source_peek.diff("a\nb\nc\n", "a\nB\nc\nd\n")
    assert result["rows"] == [["=", 1, 1], ["~", 2, 2], ["=", 3, 3], ["+", None, 4]], result["rows"]
    assert result["marks"] == {"1": [[[0, 1]], [[0, 1]]]}, result["marks"]
    assert (result["added"], result["removed"]) == (2, 1)
    words = source_peek.diff("    n = len(keys)\n", "    n = len(set(keys))\n")
    left, right = words["marks"]["0"]
    assert left == [] or all(e > s for s, e in left)
    assert "".join("    n = len(set(keys))"[s:e] for s, e in right) == "set()", right
    long = "".join(f"{n}\n" for n in range(30))
    folded = source_peek.diff("start\n" + long + "end\n", "START\n" + long + "END\n")
    assert folded["folds"] == [[4, 28]], folded["folds"]  # 30 equal rows (1..30) minus 3 context rows each side
    assert source_peek.diff(None, "a\n")["rows"] == [["+", None, 1]]
    assert source_peek.diff("a\n", None)["rows"] == [["-", 1, None]]


def line_endings():
    assert source_peek.split_lines("one\r\ntwo\r\nthree") == ["one\r", "two\r", "three"]
    assert source_peek.split_lines("a\n") == ["a"]
    assert source_peek.split_lines("a\n\n") == ["a", ""]
    assert source_peek.split_lines("") == []


def building():
    with tempfile.TemporaryDirectory() as directory:
        repo, base, head = fixture(directory)
        front = {"base": base[:10], "head": "HEAD"}  # short and symbolic revisions resolve
        missing = "f" * 40
        hrefs = [url(head, "src/count.py", "#L2"), url(head, "src/count.py", "#L2"), url(base, "src/count.py", "#L24-L25"),
                 url(head, "src/new.py"), url(base, "src/gone.py", "#L1"), url(base, "docs/My%20File.md"),
                 url(base, "crlf.txt", "#L3"), url(base, "blob.bin"), url(missing, "src/count.py"),
                 "https://example.com/elsewhere"]
        payload, skipped = source_peek.build(hrefs, front, repo)
        links = payload["links"]
        assert set(links) == set(hrefs[:8]) - {url(base, "blob.bin")}, sorted(links)
        assert dict(skipped) == {url(base, "blob.bin"): "binary, non-UTF-8, or over 20,000 lines",
                                 url(missing, "src/count.py"): "commit not in the local clone"}, skipped
        # same_file_two_ranges: one file entry per (commit, path), one diff per path
        diff_key = links[url(head, "src/count.py", "#L2")]["diff"]
        assert diff_key == links[url(base, "src/count.py", "#L24-L25")]["diff"] == f"{base}..{head}:src/count.py"
        assert links[url(base, "src/count.py", "#L24-L25")]["side"] == "base"
        assert (links[url(base, "src/count.py", "#L24-L25")]["start"], links[url(base, "src/count.py", "#L24-L25")]["end"]) == (24, 25)
        assert sorted(payload["diffs"]) == sorted({diff_key, f"{base}..{head}:src/new.py", f"{base}..{head}:src/gone.py"})
        assert payload["diffs"][f"{base}..{head}:src/new.py"]["base"] is None
        assert payload["diffs"][f"{base}..{head}:src/gone.py"]["head"] is None
        assert payload["diffs"][diff_key]["commits"] == [base, head]
        # encoded_path and line_endings
        assert payload["files"][f"{base}:docs/My File.md"]["text"] == "# Title\n"
        assert payload["files"][f"{base}:crlf.txt"]["text"] == "one\r\ntwo\r\nthree"
        assert links[url(base, "crlf.txt", "#L3")]["diff"] is None, "unchanged files peek as code only"
        assert payload["files"][f"{head}:src/count.py"]["language"] == "python"
        assert source_peek.decode(source_peek.encode(payload)) == payload
        assert source_peek.encode(payload) == source_peek.encode(payload), "deterministic output"
        try:
            source_peek.build([url(head, "src/nope.py")], {}, repo)
        except ValueError as error:
            assert "src/nope.py" in str(error), error
        else:
            raise AssertionError("A file missing at an existing commit must stop rendering")
        nope = url(head, "src/nope.py")
        rejected(lambda: page.render(f"# T\n\n**Bottom line:** x.\n\n[n]({nope})\n", "t.md", repo=repo),
                 f"Cited file does not exist at its commit: {nope} (Markdown line 5)")
        for front in ({"base": "nope", "head": "HEAD"}, {"base": base, "head": ""}):
            key = "base" if front["base"] == "nope" else "head"
            rejected(lambda: source_peek.build([url(head, "src/count.py")], front, repo), f"Front matter {key} does not resolve")
        assert source_peek.build(["https://example.com/x"], {}, repo) == (None, [])
        none, skipped = source_peek.build([url(head, "src/count.py")], {"base": "nope"}, Path(directory))  # not a repository
        assert none is None and skipped == [(url(head, "src/count.py"), "no git repository to read")], skipped


def inherited_git_environment():
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as directory:
        repo, base, head = fixture(directory)
        other = Path(directory) / "other"
        other.mkdir()
        git(other, "init", "-q")
        with patch.dict(os.environ, {"GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other)}):
            assert source_peek.repository_root(repo) == repo
            payload, skipped = source_peek.build([url(head, "src/count.py")], {"base": base, "head": head}, repo)
            assert payload and not skipped
            assert source_peek.verify(payload, {"base": base, "head": head}, repo) == []


def git_missing():
    from unittest import mock
    href = url("c" * 40, "a.py")
    with mock.patch.object(source_peek.subprocess, "run", side_effect=FileNotFoundError("git")):
        assert source_peek.build([href], {}, Path(".")) == (None, [(href, "no git repository to read")])


def highlighting():
    assert source_peek.language("src/a.py") == "python"
    assert source_peek.language("web/App.TSX") == "typescript"
    assert source_peek.language("deploy/Dockerfile") == "dockerfile"
    assert source_peek.language("notes.unknownext") is None
    for name in sorted(set(source_peek.LANGUAGES.values()) | set(source_peek.NAMES.values())):
        body = source_peek.module_body(source_peek.HIGHLIGHT / "languages" / f"{name}.min.js", source_peek.GRAMMAR_EXPORT)
        assert body.rstrip().endswith(";") and "export default" not in body[-80:], name
    assert "return" in source_peek.module_body(source_peek.HIGHLIGHT / "core.min.js", source_peek.CORE_EXPORT)[-40:]
    with tempfile.TemporaryDirectory() as directory:
        repo, base, head = fixture(directory)
        payload, _ = source_peek.build([url(head, "src/count.py"), url(base, "docs/My%20File.md"), url(base, "crlf.txt")], {}, repo)
        assert sorted(payload["hljs"]["languages"]) == ["markdown", "python"], sorted(payload["hljs"]["languages"])
        assert payload["hljs"]["core"]
    assert [source_peek.grammar(name) for name in ("sh", "Python", "ts", "diff", "console", "mermaid")] == \
        ["bash", "python", "typescript", None, "bash", None]
    assert sorted(source_peek.highlighter({}, ["sh", "py", "zsh"])["languages"]) == ["bash", "python"]


import contextlib  # noqa: E402
import io  # noqa: E402


def local_files():
    """Links to files beside the note open in the peek and are checked against the disk copy without git;
    pages, anchors, remote links, and files outside the note's directory stay plain links."""
    from unittest import mock
    no_git = mock.patch.object(source_peek.subprocess, "run", side_effect=AssertionError("started a process"))
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "review"
        (root / "runs").mkdir(parents=True)
        (root / "runs/probe.py").write_text("import x\nprint(x)\n")
        (root / "runs/out.txt").write_text("a\nb\nc\n")
        (root / "runs/blob.bin").write_bytes(b"\x00\x01")
        (root / "notes.md").write_text("# n\n")
        (root / "page.html").write_text("<p>x</p>")
        (Path(directory) / "outside.py").write_text("y = 1\n")
        hrefs = ["runs/probe.py", "runs/out.txt#L2-L3", "runs/blob.bin", "notes.md", "page.html", "../outside.py",
                 "runs/missing.py", "#details", "https://example.com/x", "runs/probe.py", "runs/out.txt#readme"]
        with no_git:
            payload, skipped = source_peek.build(hrefs, {}, root, directory=root, fences=["sh", "nope"])
        assert set(payload["links"]) == {"runs/probe.py", "runs/out.txt#L2-L3"}, sorted(payload["links"])
        assert skipped == [("runs/blob.bin", source_peek.OVERLONG)], skipped
        assert payload["links"]["runs/out.txt#L2-L3"] == {"file": "local:runs/out.txt", "commit": None, "path": "runs/out.txt",
                                                          "start": 2, "end": 3, "side": None, "diff": None}
        assert payload["files"]["local:runs/probe.py"] == {"text": "import x\nprint(x)\n", "language": "python"}
        assert sorted(payload["hljs"]["languages"]) == ["bash", "python"], "fence aliases join file languages; unknown fences drop"
        assert source_peek.local_citation("runs/probe.py", None) is None, "without a directory nothing is local"
        assert source_peek.build(["notes.md", "page.html"], {}, root, directory=root) == (None, [])
        only_fences, _ = source_peek.build([], {}, root, directory=root, fences=["py"])
        assert only_fences["links"] == {} and list(only_fences["hljs"]["languages"]) == ["python"], "a fence alone embeds its grammar"
        with no_git:
            assert source_peek.verify(payload, {}, root, root) == []
        edited = dict(payload, files=dict(payload["files"], **{"local:runs/probe.py": {"text": "changed\n", "language": "python"}}))
        rejected(lambda: source_peek.verify(edited, {}, root, root), "Embedded code differs from the file beside the note: local:runs/probe.py")
        # On a page: the local link and the fence that cites a local file peek; --check compares the embedded copy with the file.
        note = root / "report.md"
        source = ("# Probe\n\n**Bottom line:** x.\n\n## Details\n\nSee [probe](runs/probe.py) and [out](runs/out.txt#L2-L3).\n\n"
                  "```py url=\"runs/probe.py#L2\"\nprint(x)\n```\n\n```sh\necho hi\n```\n")
        note.write_text(source)
        with no_git:
            html = page.render(source, note.name, repo=root, directory=root)
            page.check(source, html, note, repo=root)
        soup = page.parse(html)
        assert {a["href"] for a in soup.main.select("a[data-peek]")} == {"runs/probe.py", "runs/out.txt#L2-L3", "runs/probe.py#L2"}
        assert [f.get("data-first") for f in soup.select("figure.code-card")] == ["2"], "a cited fence numbers its rows from the cited line"
        assert not soup.main.select("#peek-data") and soup.select_one("body > script#peek-data")
        assert page.fence_languages(soup) == ["py", "sh"]
        (root / "runs/probe.py").write_text("import x\nprint(y)\n")
        with no_git:
            rejected(lambda: page.check(source, html, note, repo=root), "Embedded code differs from the file beside the note")
        (root / "runs/out.txt").unlink()
        with no_git:
            rejected(lambda: page.check(source, html, note, repo=root), "Missing local file: runs/out.txt#L2-L3")


def rendering():
    with tempfile.TemporaryDirectory() as directory:
        repo, base, head = fixture(directory)
        source = REPORT.format(base=base, head=head).replace("src/count.py#L2-L3", "src/count.py#L2-L3) and [gone](https://github.com/acme/widgets/blob/" + "f" * 40 + "/a.py")
        (Path(directory) / "report.md").write_text(source)  # check() requires the page's Markdown link target
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            html = page.render(source, "report.md", repo=repo)
        soup = page.parse(html)
        assert soup.main.select("a[data-peek]") and not soup.main.select("#peek-data, .peek-script, .peek-style")
        data = soup.select_one("body > script#peek-data")
        assert data is not None and data["type"] == "application/octet-stream"
        assert soup.select_one("body > script.peek-script") and soup.select_one("body > style.peek-style")
        assert "[document]" not in html
        assert soup.select_one("script.peek-script").string == (ROOT / "skills/peek.js").read_text()
        payload = source_peek.decode(data.string)
        assert {a["href"] for a in soup.main.select("a[data-peek]")} == set(payload["links"])
        assert "No code peek for https://github.com/acme/widgets/blob/" + "f" * 40 + "/a.py: commit not in the local clone" in errors.getvalue()
        page.check(source, html, Path(directory) / "report.md", repo=repo)  # existing mechanical rules still pass
        plain = page.render("# Plain\n\n**Bottom line:** none.\n\n## Details\n\n[x](https://example.com)\n", "plain.md", repo=repo)
        assert "peek" not in plain and "hljs" not in plain, "a page without pinned links carries no peek assets"


def checking():
    with tempfile.TemporaryDirectory() as directory:
        repo, base, head = fixture(directory)
        note = Path(directory) / "report.md"
        source = REPORT.format(base=base, head=head)
        note.write_text(source)
        html = page.render(source, note.name, repo=repo)
        page.check(source, html, note, repo=repo)
        soup = page.parse(html)
        data = soup.select_one("#peek-data")
        payload = source_peek.decode(data.string)

        def tampered(change):
            altered = source_peek.decode(data.string)
            change(altered)
            copy = page.parse(html)
            copy.select_one("#peek-data").string = source_peek.encode(altered)
            return str(copy)

        extra = tampered(lambda p: p["links"].update({"https://github.com/acme/widgets/blob/" + head + "/src/x.py": next(iter(p["links"].values()))}))
        rejected(lambda: page.check(source, extra, note, repo=repo), "Code peek for a link the report does not have")
        key = next(iter(payload["files"]))
        def edit(p):  # the text changed and its diff re-derived, so only git can tell
            p["files"][key]["text"] = "changed\n"
            for stored in p["diffs"].values():
                texts = [p["files"][name]["text"] if name else None for name in (stored["base"], stored["head"])]
                stored.update(source_peek.diff(*texts))
        edited = tampered(edit)
        rejected(lambda: page.check(source, edited, note, repo=repo), "differs from git")
        unmarked = html.replace(" data-peek=\"\"", "", 1)
        rejected(lambda: page.check(source, unmarked, note, repo=repo), "Peekable link lacks data-peek")
        stray = html.replace('<footer><a href="report.md"', '<footer><a data-peek="" href="report.md"', 1)
        assert stray != html, "the footer's Markdown link is the stray target"
        rejected(lambda: page.check(source, stray, note, repo=repo), "data-peek on a link without peek data")
        swapped = tampered(lambda p: p["hljs"].update(core="return {};"))
        rejected(lambda: page.check(source, swapped, note, repo=repo), "Embedded highlighter differs")
        for garbage in ("", "not base64!"):
            broken = page.parse(html)
            broken.select_one("#peek-data").string = garbage
            rejected(lambda: page.check(source, str(broken), note, repo=repo), "Code peek data is malformed")
        malformed = "Code peek data is malformed"
        for change in (lambda p: p.pop("hljs"), lambda p: p.pop("links"), lambda p: p.update(links=[]),
                       lambda p: p["files"][key].pop("text")):
            broken = tampered(change)
            rejected(lambda: page.check(source, broken, note, repo=repo), malformed)
        cut = page.parse(html)
        cut.select_one("#peek-data").string = base64.b64encode(base64.b64decode(source_peek.encode(payload))[:30]).decode()
        rejected(lambda: page.check(source, str(cut), note, repo=repo), malformed)
        keyless = dict(payload, files={"nocolon": payload["files"][key]})
        rejected(lambda: source_peek.verify(keyless, {}, repo), "not a full commit SHA and path: nocolon")
        tampering(source, html, note, repo, base, head, tampered)
        inside = page.parse(html)
        inside.main.append(inside.select_one("#peek-data").extract())
        rejected(lambda: page.check(source, str(inside), note, repo=repo), "Keep the code peek data outside <main>")


def tampering(source, html, note, repo, base, head, tampered):
    """Peek data that contradicts its own links, keys, texts, or front matter is refused, with git or without."""
    def check(altered, text=source):
        return lambda: page.check(text, altered, note, repo=repo)

    def invent(p):  # every link repointed at a symbolic key holding invented code
        p["files"]["HEAD:src/count.py"] = {"text": "invented\n", "language": "python"}
        for link in p["links"].values():
            link["file"] = "HEAD:src/count.py"
    rejected(check(tampered(invent)), "Embedded code key is not a full commit SHA and path: HEAD:src/count.py")
    head_link = url(head, "src/count.py", "#L2-L3")
    rejected(check(tampered(lambda p: p["links"][head_link].update(start=1))), f"Code peek data contradicts its link: {head_link}")
    rejected(check(tampered(lambda p: p["links"][head_link].update(file=f"{base}:src/count.py"))), "contradicts its link")
    rejected(check(tampered(lambda p: p["links"][head_link].update(side="base"))), f"Code peek diff does not match its link: {head_link}")
    diff_key = f"{base}..{head}:src/count.py"

    def equalise(p):  # the changed rows relabelled as unchanged
        p["diffs"][diff_key]["rows"] = [["=", *row[1:]] if row[0] == "~" else row for row in p["diffs"][diff_key]["rows"]]
    rejected(check(tampered(equalise)), f"Embedded diff differs from its texts: {diff_key}")
    rejected(check(tampered(lambda p: p["diffs"][diff_key].update(commits=[head, base]))), f"Embedded diff does not match its key: {diff_key}")
    rejected(check(tampered(lambda p: p["diffs"][diff_key].update(base=f"{head}:src/count.py"))), "Embedded diff does not match its key")

    def added(p):  # the diff re-derived as if the file were new at head
        p["diffs"][diff_key].update(base=None, **source_peek.diff(None, p["files"][f"{head}:src/count.py"]["text"]))
    rejected(check(tampered(added)), f"Embedded diff omits a file that exists at {base}: {diff_key}")

    def undiff(p):  # every diff gone and every link left on Code
        p["diffs"].clear()
        for link in p["links"].values():
            link.update(diff=None, side=None)
    no_diff = tampered(undiff)
    rejected(check(no_diff), "Code peek lacks the base-to-head diff for")
    from unittest import mock
    with mock.patch.object(source_peek.subprocess, "run", side_effect=FileNotFoundError("git")):  # offline: no git
        rejected(check(no_diff), "Code peek lacks the base-to-head diff for")
    other = source.replace(f"base: {base}", "base: " + "c" * 40)
    rejected(check(html, other), "Code peek diff does not compare the front matter's base and head")
    rejected(check(html, source.replace(f"base: {base}\nhead: {head}\n", "")), "the front matter gives no base and head")
    rejected(check(tampered(lambda p: p["files"].update({f"{head}:src/new.py": {"text": "fresh = 2\n", "language": "python"}}))),
             "holds a file that no link or diff uses")
    invented = url(head, "src/invented.py")
    payload = {"files": {f"{head}:src/invented.py": {"text": "x\n", "language": "python"}}, "diffs": {},
               "links": {invented: {"file": f"{head}:src/invented.py", "commit": head, "path": "src/invented.py",
                                    "start": None, "end": None, "side": None, "diff": None}}}
    rejected(lambda: source_peek.verify(payload, {}, repo), f"Embedded code names a file missing at its commit: {head}:src/invented.py")
    unlisted = dict(payload, files={"f" * 40 + ":a.py": {"text": "x\n", "language": "python"}})
    unlisted["links"] = {url("f" * 40, "a.py"): dict(payload["links"][invented], file="f" * 40 + ":a.py", commit="f" * 40, path="a.py")}
    assert source_peek.verify(unlisted, {}, repo) == [("f" * 40 + ":a.py", "commit not in the local clone")]
    assert source_peek.verify(unlisted, {}, note.parent) == [("f" * 40 + ":a.py", "no git repository to read")]


def rejected(action, message):
    try:
        action()
    except ValueError as error:
        assert message in str(error), error
    else:
        raise AssertionError("Expected rejection: " + message)


if __name__ == "__main__":
    front_matter()
    citations()
    diffs()
    line_endings()
    building()
    inherited_git_environment()
    git_missing()
    highlighting()
    local_files()
    rendering()
    checking()
    print("source peek tests passed")
