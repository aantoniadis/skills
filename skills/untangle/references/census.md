# Census of a capability

Read when listing the decision sites of a capability, or when choosing how to
get the edges for the dependency view. No single kind of evidence finds every
site, and each fails in a known way, so take all four and read where they
disagree. Label every result as [evidence](../../EVIDENCE.md) says.

## Four kinds of evidence

| Kind | How to take it | What it misses |
| --- | --- | --- |
| Text | Search the scope and its callers for the capability's domain words and their synonyms, and for its discriminators: enum values, type fields, status strings, flags, configuration keys, table and column names. | Code that implements the capability under another name. |
| References | From each hit, follow callers, callees, references, and implementations in both directions with native symbol navigation, the language server, or a project index. | Dependency injection, reflection, dynamic dispatch, and lookups by string. It also reports paths nothing takes. |
| Execution | Run the scenarios that exercise the capability and the scenarios that do not, and compare the code each set executes. | Every scenario nobody ran. Shared code that holds part of the rule looks unrelated, because both sets execute it. |
| History | Find the commits that introduced or changed a discriminator, and the files that change in the same commits. | Rules that have not changed inside the fetched history; work split across commits or squashed into one. |

Execution is the kind the other three cannot replace. Take it in the cheapest
form the ecosystem has, in this order:

1. Coverage recorded per test, where the coverage tool supports it: it
   answers "which tests execute this line" and "which lines does this test
   execute" directly.
2. Coverage of one focused run, such as the tests of one capability, compared
   with coverage of a run that leaves that capability out.
3. A probe: a short script under `runs/` that drives one input through the
   public boundary, with logging at the boundaries it crosses, in a scratch
   worktree when it needs instrumentation.

Where the code uses dependency injection, reflection, dynamic dispatch,
lookups by string, or wiring from configuration, a static edge is a lead and
only an execution establishes it.

History commands, from the repository root:

```bash
git log -S'<discriminator>' --oneline -- <scope>      # commits that add or remove the string
git log -G'<regex>' --oneline -- <scope>              # commits whose diff matches
git log -L :<function>:<file>                         # the history of one function
python3 <package>/skills/untangle/scripts/change_coupling.py --edges <edges.tsv> <scope>
```

## Read the disagreements

| The kinds disagree like this | Read it as a lead to |
| --- | --- |
| A scenario executes it; no search for the capability's words finds it | A hidden part of the capability: add the site, and name what it decides. |
| The words find it; no scenario executes it | Dead code, or a scenario nobody wrote. Find which before recording either. |
| Two files change together; no dependency between them | One rule kept in two places, or an unwritten convention the two must follow. |
| A reference reaches it; no scenario does | A path nothing takes, or a caller outside the scope. Enumerate the callers. |
| The same condition on the same discriminator at several sites | A scattered rule: list every site, then check that they agree. |

Sites that decide the same rule and disagree are the most valuable result of
the census: record the inputs on which they differ, and run one.

Record each decision site once, with its pinned line, what it decides, and the
kinds of evidence that found it. A site found by one kind only says so.

## Edges for the dependency view

Use the most exact source available, and say which one produced the edges:

1. The compiler or a dependency tool of the ecosystem, such as the JDK's
   `jdeps`, a module-graph command, or a bundler's graph output.
2. The language server or a project code index, queried per file.
3. [`import_edges.py`](../scripts/import_edges.py), which reads static
   imports in Python, JavaScript, TypeScript, and Java:

```bash
python3 <package>/skills/untangle/scripts/import_edges.py <scope> > <investigation>/runs/edges.tsv
python3 <package>/skills/untangle/scripts/design_conformance.py <investigation>/runs/stated-design.json <investigation>/runs/edges.tsv
```

Any tool that writes `from<TAB>to` file paths, one edge per line, feeds both
`design_conformance.py` and `change_coupling.py --edges`. The stated design is
a JSON file of components, each a list of path patterns, and the allowed
dependencies between them:

```json
{"components": {"api": ["app/api/**"], "domain": ["app/domain/**"], "storage": ["app/db/**"]},
 "allowed": [["api", "domain"], ["domain", "storage"]]}
```

A relationship reported as *not found* means no edge showed it. Before
recording it, check whether the dependency runs through something the edge
source cannot see.
