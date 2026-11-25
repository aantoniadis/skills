# Census of a capability

Read when listing the decision sites of a capability, breaking a decision on
purpose, or choosing how to get the edges for the dependency view. No single
kind of evidence finds every site, and each fails in a known way, so take
them together and read where they disagree. Label every result as
[evidence](../../EVIDENCE.md) says.

## Contents

- [Five kinds of evidence](#five-kinds-of-evidence)
- [Execution: which tests run a line](#execution-which-tests-run-a-line)
- [History](#history)
- [A deliberate break](#a-deliberate-break)
- [Read the disagreements](#read-the-disagreements)
- [Edges for the dependency view](#edges-for-the-dependency-view)

## Five kinds of evidence

| Kind | How to take it | What it misses |
| --- | --- | --- |
| Text | Search the scope and its callers for the capability's domain words and their synonyms, and for its discriminators: enum values, type fields, status strings, flags, configuration keys, table and column names. | Code that implements the capability under another name. |
| References | From each hit, follow callers, callees, references, and implementations in both directions with native symbol navigation, the language server, or a project index. With none of those, use search and the import edges, and say so. | Dependency injection, reflection, dynamic dispatch, and lookups by string. It also reports paths nothing takes. |
| Execution | Run the scenarios that exercise the capability and the scenarios that do not, and compare the code each set executes. | Every scenario nobody ran. Shared code that holds part of the rule looks unrelated, because both sets execute it. |
| History | Find the commits that introduced or changed a discriminator, and the files that change in the same commits. | Rules that have not changed inside the fetched history; work split across commits or squashed into one. |
| A deliberate break | In a scratch copy, change one decision and run the tests that should notice. | Nothing about reach: a red test shows the behavior is protected, a green suite shows it is not. |

Name the kinds taken for each capability. Mark a decision site that only one
kind found, because that is the site a reader is most likely to miss.

## Execution: which tests run a line

Execution is the kind the other four cannot replace. Take it in the cheapest
form the ecosystem has, in this order:

1. Coverage recorded per test. With coverage.py, record it and ask which
   tests execute a line:

   ```bash
   <test command> --cov=<package> --cov-context=test          # pytest with pytest-cov; keep the .coverage file under runs/
   python3 <package>/skills/untangle/scripts/tests_for_line.py <runs>/.coverage discounts.py:12 serializers.py:44
   ```

   Another ecosystem has its own per-test report; use it the same way.
2. Coverage of one focused run, such as the tests of one capability, compared
   with coverage of a run that leaves that capability out.
3. A probe: a short script under `runs/` that drives one input through the
   public boundary and prints what came back. Two entry points given the same
   input, side by side, is the probe that finds sites that disagree.

Where the code uses dependency injection, reflection, dynamic dispatch,
lookups by string, or wiring from configuration, a static edge is a lead and
only an execution establishes it.

## History

From the repository root:

```bash
git log -S'<discriminator>' --oneline -- <scope>      # commits that add or remove the string
git log -G'<regex>' --oneline -- <scope>              # commits whose diff matches
git log -L :<function>:<file>                         # the history of one function
python3 <package>/skills/untangle/scripts/change_coupling.py --edges <edges.tsv> <scope>
```

`change_coupling.py` lists the files in scope that change most, and the pairs
that change in the same commits. A pair of kind *code* with no dependency is
the lead to one rule in two places. A partner marked *one outside* lies
outside the scope: read it, because the other half of a rule often lives
there. Pairs of kind *test* and *document* are often expected; a document
that changes with the code and still disagrees with it is a finding.

## A deliberate break

A break answers "does any test protect this behavior?". Work in a disposable
worktree, never in the user's checkout, and remove it afterwards:

```bash
wt="$(mktemp -d)/probe" && git worktree add --detach "$wt" HEAD
# in "$wt": install what the tests need as the project's instructions say, change one decision,
# run the tests that should notice (the whole baseline when unsure), and keep the change and the output under runs/
git worktree remove --force "$wt"
```

Use the session's temporary directory when the host assigns one. Make one
change per break: invert a condition, change a constant, remove a check, alter
a path. Record each as one line: what was changed, where, the tests run, and
the result.

- A test turns red: the behavior is pinned, and that test is its pin.
- Every test stays green: no test protects the behavior. Record it in the map
  under *Behavior no test protects*; it is the first pin a rework writes.

Break first what would hurt most if it changed silently: a check on who may
do what, a rule about money or data, a value another system reads.

## Read the disagreements

| The kinds disagree like this | Read it as a lead to |
| --- | --- |
| A scenario executes it; no search for the capability's words finds it | A hidden part of the capability: add the site, and name what it decides. |
| The words find it; no scenario executes it | Dead code, or a scenario nobody wrote. Find which before recording either. |
| Two code files change together; no dependency between them | One rule kept in two places, or an unwritten convention the two must follow. |
| A reference reaches it; no scenario does | A path nothing takes, or a caller outside the scope. Enumerate the callers. |
| The same condition on the same discriminator at several sites | A scattered rule: list every site, then check that they agree. |
| A test name states the behavior; no test fails when it is broken | Behavior no test protects. |
| A document states a count, a list, or a rule; the code or a run shows another | A broken stated rule: record both values. |

Sites that decide the same rule and disagree are the most valuable result of
the census: record the inputs on which they differ, and run one. The result
goes under *Behavior to decide*.

## Edges for the dependency view

Use the most exact source available, and say which one produced the edges:

1. The compiler or a dependency tool of the ecosystem, such as the JDK's
   `jdeps`, a module-graph command, or a bundler's graph output.
2. The language server or a project code index, queried per file.
3. [`import_edges.py`](../scripts/import_edges.py), which reads static
   imports in Python, JavaScript, TypeScript, and Java, and leaves out edges
   that start in a test file:

```bash
python3 <package>/skills/untangle/scripts/import_edges.py <scope> > <runs>/edges.tsv
python3 <package>/skills/untangle/scripts/design_conformance.py <runs>/stated-design.json <runs>/edges.tsv
```

Any tool that writes `from<TAB>to` file paths, one edge per line, feeds both
`design_conformance.py` and `change_coupling.py --edges`. The stated design is
a JSON file of components, each a list of path patterns, and the allowed
dependencies between them. Keep the quote behind each allowed dependency under
`sources`, which the script ignores:

```json
{"components": {"api": ["app/api/**"], "domain": ["app/domain/**"], "storage": ["app/db/**"]},
 "allowed": [["api", "domain"], ["domain", "storage"]],
 "sources": {"api -> domain": "docs/architecture.md: 'handlers call the domain layer'"}}
```

Map only the components the design names. A file the design never mentions
stays unmapped; the script lists it, and the map reports it as a module the
design does not name, which is a different result from a dependency the
design forbids.

A relationship reported as *not found* means no edge showed it. Before
recording it, check whether the dependency runs through something the edge
source cannot see, such as an injected object.
