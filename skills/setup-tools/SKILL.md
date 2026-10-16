---
name: setup-tools
description: Discovers, checks, and prepares a project's tools (tests, search, symbol navigation, coverage, browser, report checker, the installed Matt Pocock and HumanLayer skills) before investigation or review work, and repairs a stale local tool record. Use when starting work in a new checkout, when a later skill's tool fails, or when the user asks to set up, verify, or fix tooling. Not for configuring project conventions or writing project files.
argument-hint: "Optional: the project directory, or the skills you plan to run here"
---

For helper loading, follow [package references](../REFERENCES.md). Write in
the shared [technical English](../TECHNICAL-ENGLISH.md), with results bounded
by their [evidence](../EVIDENCE.md).

# Set up tools

Prepare tools that will help the intended work, and leave practical usage
information for later sessions. Follow the host's normal execution and
permission model. Read [local tool setup](../TOOL-SETUP.md) for storage,
reuse, and the project-file rules; all setup output stays untracked and
project files stay as the user left them.

## 1. Discover what the work can use

Read the project instructions, manifests, existing scripts, CI, and any local
tool record. Identify the planned work from the request. Inspect the host's
available tools and relevant installed integrations. Prefer existing project
commands and native host capabilities.

Use the capability table in [CODE-TOOLS.md](../CODE-TOOLS.md) as a guide to
useful options. Select capabilities for this project and work; there is no
required tool stack or inventory of every installed plugin. Search, tests,
static checks, and history often suffice. Semantic navigation, coverage, a
browser, a profiler, or an index can help when the work needs them.

When the planned work can use an original Matt Pocock or HumanLayer skill
(plan-change's interview and drafting helpers, explain's extra views, the
implementation and PR handoffs), find the installed copies as
[original skills](references/upstream-skills.md) says. Each is a capability
like the others: usable now, needing installation, or unavailable.

Distinguish a tool exposed to this agent, an installed executable, and a
working project integration. Check a candidate's own help or documentation
for its installed version before proposing commands.

Done when each capability the planned work needs is named as usable now,
needing preparation, or unavailable, with the reason.

## 2. Try existing operations

Before the first check or preparation command that can write project files,
take the baseline in [local tool setup](../TOOL-SETUP.md#preserve-project-files).
Try a small relevant operation with the existing capability: one focused
test, navigation to a known definition, an actual index query, or a browser
operation against the intended application. Use the interface the next
skill will use. Keep the check proportional to the intended work. A recorded
operation that now fails is a gap. When PR review or an acceptance check is
planned, include the report checker among the operations to try, on that
skill's report template: `python3 <package>/skills/render_page.py <package>/skills/pr-review-guide/references/report-template.md --check --review --markdown-only`,
or for an acceptance check `<package>/skills/check-acceptance/references/report-template.md`
with `--acceptance` in place of `--review`.
It reports the template's unfilled prompts, which shows the checker and its
dependencies run; an import error names a missing dependency
([check mechanics](../HTML-PAGES.md#check-mechanics-and-meaning-separately)).

For an original skill, read its `SKILL.md` at the found path; a listing
entry without a readable file is a gap.

For a tool that can silently return incomplete output, compare against an
independently known example. Inspect exit status and output using the tool's
documented semantics. Distinguish a completed query with no matches, a test
reporting a product failure, and a tool that could not execute. Installation,
authentication, and a passing version command establish less than this check.

Done when each usable operation has an observed result with its scope, and
each gap names the capability the work needs.

## 3. Prepare gaps and verify

Reuse existing environments and configuration. Prefer project-local or
isolated installations and the tool's supported setup procedure. Choose
output locations using the local-state guidance before running commands.

Perform setup within the user's existing authorization. Ask only for a
missing consequential choice or permission, with the concrete command,
expected benefit, cost, and fallback. Continue independent work while a
choice is pending. Give short manual instructions for sign-in or activation.

Install a missing original skill only with the user's authorization, using
the command for their host from the same reference; otherwise record the gap
and that command.

Record a simple command or native operation. Reuse an existing script for
multi-step work; create a small local helper only when repeated complexity
warrants it. Each recorded operation carries the inputs it needs, rather
than a fixed interface shared by all tools.

After preparation, repeat the relevant operation from step 2. Reuse an
earlier successful check when its inputs and environment remain unchanged.
Resolve a cheap setup error when authorized; otherwise record the gap and
fallback. Compare project files with the baseline after commands that can
write and before reporting completion.

Done when prepared capabilities have observed operations and honest limits,
or their remaining setup and usable fallback are clear.

## 4. Save the local result

Save useful operations, setup details, observed results, and traps according
to [local tool setup](../TOOL-SETUP.md), including each original skill's
path and its version or install date. Keep detailed logs out of the brief
record. Later skills can rediscover ordinary commands cheaply from the
project; retain information that would otherwise be lost or expensive to
reconstruct.

Show the saved or reused record path, what is usable now, and any remaining
gap. If nothing useful needed saving or persistence was unavailable, say so;
continue with session-local knowledge and let later sessions rediscover it.
Available tools are options for later skills.

Done when useful preparation is saved for reuse or its persistence limit is
reported, and the project-file comparison is complete. Report unresolved
changes or unavailable comparison as a limitation, not successful preservation.
