// Run with: node --test tests/peek.test.cjs
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const peek = require("../skills/peek.js");

const assets = path.join(__dirname, "../skills/assets/highlight");
const body = (file, pattern) => fs.readFileSync(path.join(assets, file), "utf8").replace(pattern, "return $1;");
const hljs = peek.loadHighlighter(body("core.min.js", /export\s*\{\s*(\w+)\s+as\s+default\s*\}\s*;?\s*$/), {
  python: body("languages/python.min.js", /export\s+default\s+(\w+)\s*;?\s*$/),
  javascript: body("languages/javascript.min.js", /export\s+default\s+(\w+)\s*;?\s*$/),
});
const highlight = (text, language) => peek.splitHighlighted(hljs.highlight(text, {language, ignoreIllegals: true}).value);
const balanced = line => (line.match(/<span /g) || []).length === (line.match(/<\/span>/g) || []).length;

test("split lines matches Python's split_lines", () => {
  assert.deepEqual(peek.splitLines("one\r\ntwo\r\nthree"), ["one\r", "two\r", "three"]);
  assert.deepEqual(peek.splitLines("a\n"), ["a"]);
  assert.deepEqual(peek.splitLines("a\n\n"), ["a", ""]);
  assert.deepEqual(peek.splitLines(""), []);
});

test("a multi-line string keeps its span on every line", () => {
  const lines = highlight('x = """one\ntwo\nthree"""\ny = 1\n', "python");
  assert.equal(lines.length, 5); // the trailing newline yields an empty fifth line the caller trims
  assert.ok(lines.every(balanced), lines.join("\n"));
  assert.match(lines[1], /^<span class="hljs-string">two<\/span>$/);
  assert.match(lines[3], /hljs-number/);
});

test("escaped text survives the split", () => {
  const lines = highlight('s = "<a & b>"\n', "python");
  assert.match(lines[0], /&lt;a &amp; b&gt;/);
  assert.equal(peek.escapeHtml('<a href="x">&</a>'), "&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;");
});

test("scopes follow definitions and indentation", () => {
  const text = "class A:\n    def f(self):\n        return g()\n\n    def h(self):\n        pass\nx = 1\n";
  const raw = peek.splitLines(text), html = highlight(text, "python").slice(0, raw.length);
  const found = peek.scopes(raw, html);
  assert.deepEqual(found.map(s => [s.name, s.start, s.end]), [["A", 1, 6], ["f", 2, 4], ["h", 5, 6]]);
  assert.deepEqual(peek.chainAt(found, 3), ["A", "f"]);
  assert.deepEqual(peek.chainAt(found, 7), []);
});

test("a closing brace stays inside its scope", () => {
  const text = "function f() {\n  return 1;\n}\nconst y = 2;\n";
  const raw = peek.splitLines(text), html = highlight(text, "javascript").slice(0, raw.length);
  assert.deepEqual(peek.scopes(raw, html).map(s => [s.name, s.start, s.end]), [["f", 1, 3]]);
});
