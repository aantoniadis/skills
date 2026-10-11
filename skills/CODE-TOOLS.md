# Tools for a code question

Choose tools for the uncertainty the task needs to resolve. Read the
[local tool record](TOOL-SETUP.md) if present, then use the host's
current capabilities and the project's scripts and configuration. A missing
record does not prevent investigation. Use [setup-tools](setup-tools/SKILL.md)
when reusable preparation or repair would materially help.

| Need | Useful options |
| --- | --- |
| Locate entry points, configuration, or literal uses | File search and reads; `rg` when available. |
| Follow symbols across aliases, overloads, or callers | Native definitions/references or call hierarchy; structural and text search. |
| Observe dispatch, state, or ordering | Focused tests or CLI probes; tracing or a debugger for unresolved runtime behavior. |
| Explain a contract or past decision | Git history, dependency source, relevant official documentation, PR or issue tools. |
| Measure time or allocations | A profiler or trace on a representative scenario. |
| Map code structure | Native symbol navigation or an available graph/index whose scope and freshness fit the question. |
| Find untested changed behavior | Existing test and coverage commands; per-test contexts when supported and useful. |
| Check compatibility with a declared dependency range | An isolated environment at the relevant versions and a focused operation through the changed path. |
| Check or render a report | The shared renderer and its dependencies; a diagram backend only for a selected diagram. See [HTML-PAGES.md](HTML-PAGES.md). |
| Use an original Matt Pocock or HumanLayer skill | The installed copy that setup-tools recorded; see [original skills](setup-tools/references/upstream-skills.md). |

## Use a prepared operation

Read the recorded operation for its intended question, working directory, inputs, host,
environment, and limits.
Use it when applicable, or choose another suitable tool. Reuse an existing
result only when its source revision, inputs, environment, and scope still
match. A native tool can serve the same purpose as a shell command.

Check the installed tool's help when its interface is uncertain. Establish
usability with the relevant operation; repeat a small known-answer probe when
an integration is new, stale, or can fail silently. Ordinary successful use
can serve as the check. A version command establishes presence, and an MCP
configuration establishes intent; neither proves the agent can execute the
needed operation. Refresh an index when relevant source or configuration
has changed.

Inspect exit status, output, and completion using the tool's documented
semantics. An empty completed search differs from an interrupted command.
A failing test can establish a defect while its runner works correctly.
Record consequential results with their command or tool call, revision,
conditions, and limitations under the shared [evidence rules](EVIDENCE.md).

## Bound the evidence

- Search installed dependencies with ignore rules accounted for, for example
  `rg -uu` on a virtual environment or `node_modules` when ordinary search
  excludes them.
- Resolve ambiguous definitions with semantic navigation when available.
  Check aliases, re-exports, overrides, and dynamic dispatch when relevant;
  no single caller tool proves completeness. Cross-check consequential
  missing callers with another method.
- Graph edges are leads to inspect. Index scope, resolution heuristics, and
  stale inputs can omit or misidentify relationships. Confirm relationships
  that control the conclusion against source or runtime evidence.
- Coverage shows code executed by the selected tests. Shared test contexts
  do not prove a directed call chain, and unexecuted scenarios remain unknown.
- A successful setup check establishes that operation in that environment;
  it does not validate all future outputs or all project behavior.

## Recover only what the task needs

Identify the failure with a focused check. Reuse authorization for a routine
repair, such as activating the correct environment. Follow
[setup-tools](setup-tools/SKILL.md) when preparation or installation is
needed. Ask only for missing choices or permissions; continue independent
work and use an adequate fallback with its evidence limits stated.

Update useful discoveries after the `tool_setup_path.py --for-write` check; if persistence
is unavailable, retain them for this session and report that limit. A missing
optional tool narrows the evidence available. When an essential operation
cannot run, identify the affected work.
