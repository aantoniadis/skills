# Local tool setup

Use this record when discovering tools for a project or reusing preparation
from an earlier session. The record is local to the user and checkout. It
offers useful operations; each skill chooses those relevant to its task.

## Contents

- [Locate the record](#locate-the-record)
- [Save useful preparation](#save-useful-preparation)
- [Preserve project files](#preserve-project-files)
- [Reuse and report](#reuse-and-report)

## Locate the record

Use the helper's physical package path and an explicit absolute project path;
the current directory can be anywhere:

```bash
python3 <package>/skills/tool_setup_path.py /absolute/project-directory
```

It prints a path without creating anything. In Git, directories within one
worktree resolve to the same record; separate worktrees have separate records.
Outside Git, pass the project root consistently. The path is
`$XDG_STATE_HOME/aantoniadis-skills/projects/<project-key>/tools.md`, with
`~/.local/state` as the default state directory. The key derives from the
canonical project path, so moving a checkout starts a new record.
The helper ignores inherited `GIT_*` overrides for these read-only queries.
It needs Git to distinguish a non-Git directory from a repository failure;
missing Git or failed discovery is reported instead of guessing a root.

Read the file if present. If absent, discover what the current task needs;
setup is optional. The host's current tool listing and the project's actual
configuration take precedence over a saved observation. Existing project
instructions can supply useful commands without becoming setup output.

## Save useful preparation

Create or update the record only when there is useful preparation or a
non-obvious discovery to retain. Keep it short: project path, verification
date and environment, useful commands or native tool operations, when to use
them, what worked, prerequisites, limitations, and any fallback. Link longer
procedures or helper scripts beside the record. Read the installed tool's
`--help` or version-matched documentation rather than copying its command
reference. Apply the shared [evidence rules](EVIDENCE.md) to recorded results.

Anchor an operation to its working directory and relevant host or environment.
For example, an entry could say:

> API tests: from `/work/example/services/api`, run
> `/work/example/.venv/bin/python -m pytest tests/test_health.py -q`.
> Checked on 2026-10-10 with Python 3.12: two tests passed. Any host with
> shell access can use this environment. This checked the health endpoint,
> not the full suite. Recheck after dependency or test configuration changes.

For native operations, name the host and exposed interface instead of a shell
command. This example illustrates useful context; it is not a record schema.

Immediately before creating or updating the record, resolve it again with:

```bash
python3 <package>/skills/tool_setup_path.py --for-write /absolute/project-directory
```

This also rejects a Git-tracked destination, including one in another checkout
or reached through a symlink, and project instruction filenames. It creates
nothing and does not establish filesystem write permission. If lookup,
validation, or saving fails, report that preparation was not saved.
Continue with session-local knowledge; do not create a project-file fallback.

## Preserve project files

Keep generated setup notes, probes, environments, and indexes in this local
state directory where the tool supports it. Reuse existing ignored project
artifacts when appropriate. Before running a preparation command, check its
output locations, including generated configuration and lockfiles. Setup
does not write `CLAUDE.md`, `AGENTS.md`, `AGENT.md`, tracked files, or new
files intended for Git. Do not edit `.gitignore` to make setup fit. If a tool
requires tracked changes, report that limitation and use an available
alternative; changing the project is a separate task.

Before the first check or preparation command that can write, take a baseline
of the working tree and the index from the project root. The snapshot is a Git
tree object built in a temporary index: content, mode, and symlink changes in
tracked and untracked files show in the diff, ignored output does not, and the
project's own index is untouched. The second command force-adds project
instruction files that the project ignores.

```bash
snap() { local i; i=$(mktemp -u); GIT_INDEX_FILE="$i" git add -A . && git ls-files -z --others --ignored --exclude-standard -- CLAUDE.md AGENTS.md AGENT.md | GIT_INDEX_FILE="$i" xargs -0r git add --force -- && GIT_INDEX_FILE="$i" git write-tree; rm -f "$i"; }
before=$(snap); staged=$(git write-tree)
```

After commands that can write, and before reporting completion:

```bash
git diff-tree -r --name-status "$before" "$(snap)"; [ "$staged" = "$(git write-tree)" ] || echo "index changed"
```

An empty diff and an unchanged index mean the project files are as the user
left them. A listed path changed after the baseline: report it, and undo only
your attributable change when safe. Preserve the user's starting edits; never
reset the checkout to erase pre-existing work. Outside Git, hash the project
files before and after instead. If comparison is unavailable, report that limit.

## Reuse and report

For updates from later skills, write only to the local record. Preserve
unrelated entries and user choices. Store credential requirements, never
credentials. A remembered executable path, connection, or index is evidence
about that environment at that time; refresh affected entries when the tool,
configuration, checkout, or host changes, or an operation fails. Ordinary
successful use can supply the current check.

Report the saved or reused record path and useful capabilities at the end of
setup. If no record was created or persistence failed, say so rather than
presenting a nonexistent artifact. Consuming skills locate saved records
through this reference.
