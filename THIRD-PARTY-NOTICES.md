# Third-party notices

Matt Pocock's and HumanLayer's skills are installed separately through their
own routes, as [original skills](skills/setup-tools/references/upstream-skills.md)
describes. Nothing from them is bundled here; each install carries its own
license.

- Matt Pocock, https://github.com/mattpocock/skills, MIT, Copyright (c) 2026 Matt Pocock
- HumanLayer, https://github.com/humanlayer/skills, MIT, Copyright (c) 2026 HumanLayer

## Manrope font

The report renderer bundles the Latin variable font from [Google Fonts](https://github.com/google/fonts/tree/main/ofl/manrope). Copyright 2018 The Manrope Project Authors. Licensed under the [SIL Open Font License 1.1](skills/assets/OFL-Manrope.txt). [Source details](skills/assets/FONT-SOURCE.md). Generated HTML includes the font and license for offline use.

## Optional diagram renderer

[Beautiful Mermaid](https://github.com/lukilabs/beautiful-mermaid), version 1.1.3,
is an optional Node.js authoring dependency, licensed under MIT. Its locked
transitive dependencies are ELK.js 0.11.1 (EPL-2.0) and entities 7.0.1
(BSD-2-Clause). Their packages contain the license texts. The HTML report embeds
the generated SVG, not the renderer libraries. Versions and integrity hashes are
recorded in [the lockfile](skills/diagram-renderer/package-lock.json).

## highlight.js

Source: https://github.com/highlightjs/highlight.js (release 11.11.1, `@highlightjs/cdn-assets`)  
License: BSD 3-Clause — Copyright (c) 2006, Ivan Sagalaev  
Bundled: `skills/assets/highlight/` (core, 30 grammars, the `intellij-light` theme, and the license text); reading pages with a code peek inline parts of it.

