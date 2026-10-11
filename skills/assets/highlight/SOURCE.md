# highlight.js

highlight.js 11.11.1, BSD 3-Clause License (LICENSE in this folder).

Package: https://registry.npmjs.org/@highlightjs/cdn-assets/-/cdn-assets-11.11.1.tgz

Files: `es/core.min.js` → `core.min.js`; `es/languages/<name>.min.js` → `languages/`
for each language in `LANGUAGES` and `NAMES` of `skills/source_peek.py`;
`styles/intellij-light.min.css` → `intellij-light.min.css`.

The renderer inlines the core and only the grammars a page needs, turning each
module's `export` into a `return` so the page runs it with `new Function`
(`module_body` in `source_peek.py`). To re-vendor, copy the same files from a new
release and run `python3 tests/test_source_peek.py`, which rewrites each module's
`export` and checks the result's shape, and `node --test tests/peek.test.cjs`,
which loads the core with the Python and JavaScript grammars and highlights code.
