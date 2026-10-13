# skills

Skills for coding agents, shipped as the **`aantoniadis-skills`** plugin for
Claude Code, Codex, and OpenCode. Five skills cover the work around a change:
set a project up for evidence, understand the code, plan the behavior, find
the defects, and review the PR. Matt Pocock's and HumanLayer's originals,
installed separately, carry a plan through spec, tickets, implementation, and
the PR.

```bash
claude plugin marketplace add aantoniadis/skills && claude plugin install aantoniadis-skills@aantoniadis
```

Invoke a skill as `/aantoniadis-skills:<name>` in Claude Code,
`$aantoniadis-skills:<name>` in Codex, and through the `/skills` menu or
`opencode run --command <name>` in OpenCode. Hosts also pick the skills up
through their normal model-driven selection.

## Install

```bash
# Claude Code
claude plugin marketplace add aantoniadis/skills
claude plugin install aantoniadis-skills@aantoniadis

# Codex
codex plugin marketplace add aantoniadis/skills
codex plugin add aantoniadis-skills@aantoniadis
```

The skills run Python 3 scripts. The page checker and renderer need two
packages; HTML pages with diagrams also use Node.js
([renderer options](skills/RENDERER.md)):

```bash
python3 -m pip install markdown-it-py beautifulsoup4
```

OpenCode loads the plugin from `opencode.json`, from Git or from a checkout:

```json
{ "plugin": ["@aantoniadis/skills@git+https://github.com/aantoniadis/skills.git"] }
```

```json
{ "plugin": ["/path/to/skills/opencode/skills.js"] }
```

Start a new session after an install or update.

**Updates.** Every merge to the default branch is a release. Codex reinstalls
the plugin when it starts on new commits. Claude Code updates by hand, or on
its own once auto-update is on for the `aantoniadis` marketplace under
`/plugin`:

```bash
claude plugin marketplace update aantoniadis && claude plugin update aantoniadis-skills@aantoniadis
```

OpenCode caches a Git-installed plugin; delete
`~/.cache/opencode/packages/@aantoniadis` to fetch the current version. A
checkout updates with `git pull`. For development, `claude --plugin-dir <checkout>`
runs the checkout directly.

### Original skills

Our skills work with six originals: Matt Pocock's `grilling`, `to-spec`,
`to-tickets`, and `implement`, and HumanLayer's `show-me` and `visual-pr`.
Install them once per machine, one route per host:

```bash
# Matt Pocock's skills: Claude Code
claude plugin install mattpocock-skills@claude-plugins-official
# Matt Pocock's skills: Codex
codex plugin marketplace add mattpocock/skills
codex plugin add mattpocock-skills@mattpocock
# Matt Pocock's skills: OpenCode and other hosts (-a <agent> selects the host)
npx skills@latest add mattpocock/skills -g
# HumanLayer's skills: every host
npx skills@latest add humanlayer/skills --skill show-me --skill visual-pr -g
```

`setup-tools` records where each copy is. Our skills name them
`mattpocock:implement` or `humanlayer:visual-pr`
([skills/REFERENCES.md](skills/REFERENCES.md)) and respect each author's
choice of who runs it: `plan-change` invokes `grilling` through the host; the
other five are user-invoked, so our skills finish their own deliverable and
hand you the command, such as `/mattpocock-skills:to-spec` in Claude Code or
`/to-spec` after an `npx skills` install. Each original then runs its own
workflow, unchanged.

## The skills

| Skill | Use it when | You get | How it works |
| --- | --- | --- | --- |
| [`setup-tools`](skills/setup-tools/SKILL.md) | Reusable preparation or repair would help the intended work | Useful tools checked, with a local untracked record when there is preparation to retain | [docs/setup-tools.md](docs/setup-tools.md) |
| [`explain`](skills/explain/SKILL.md) | You need to know how a flow works before touching it | A source-cited answer, with a reusable note or HTML page when selected | [docs/explain.md](docs/explain.md) |
| [`plan-change`](skills/plan-change/SKILL.md) | A ticket is vague and the change has consequences beyond its own function | A plan with named decisions, preserved behavior, evidence, and acceptance scenarios | [docs/plan-change.md](docs/plan-change.md) |
| [`find-bugs`](skills/find-bugs/SKILL.md) | You want the defects in a change before it merges, or before you review it | Ranked defects with evidence, material questions, and review limits | [docs/find-bugs.md](docs/find-bugs.md) |
| [`pr-review-guide`](skills/pr-review-guide/SKILL.md) | You have to review a PR you did not write | A guide to a pinned snapshot: what the change means, where to look, what to skim, what to ask the author | [docs/pr-review-guide.md](docs/pr-review-guide.md) |

The skills start from context and settled choices, and ask only about open
preferences or consequential decisions. Every claim sits next to its evidence:
a pinned line, an executed check, a quote, or a label such as inferred or not
inspected. `setup-tools` keeps what it learns in a
[local record](skills/TOOL-SETUP.md) outside the repository.

With the originals: `plan-change` hands agreed decisions to Matt's `to-spec`
and `to-tickets`, Matt's `implement` builds an unblocked ticket, `find-bugs`
runs before HumanLayer's `visual-pr` opens the PR, and `pr-review-guide`
serves the PR's human reviewer. An original invoked directly keeps its own
behavior, such as committing or pushing; one called by our skills follows our
task constraints.

- [Using the skills together](docs/workflow.md): copyable prompts, project
  setup, handoffs, and artifact locations
- [The light path](docs/light-path.md): a shorter workflow for contained
  changes in familiar code

## License

[MIT](LICENSE). Bundled third-party assets, the Manrope font and highlight.js, keep
their own licenses; [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) lists them.
