# Census of a feature

Read when listing the decision sites of a feature, breaking a decision on
purpose, or choosing how to get the edges for the dependency view. No single
kind of evidence finds every site, and each fails in a known way, so take
them together and read where they disagree. Label every result as
[evidence](../../EVIDENCE.md) says.

## Contents

- [Five kinds of evidence](#five-kinds-of-evidence)
- [Execution: which tests run a line](#execution-which-tests-run-a-line)
- [History](#history)
- [A deliberate break](#a-deliberate-break)
- [State and data that travels](#state-and-data-that-travels)
- [Read the disagreements](#read-the-disagreements)
- [Edges for the dependency view](#edges-for-the-dependency-view)

## Five kinds of evidence

| Kind | How to take it | What it misses |
| --- | --- | --- |
| Text | Search the scope and its callers for the feature's domain words and their synonyms, and for its discriminators: enum values, type fields, status strings, flags, configuration keys, table and column names. | Code that implements the feature under another name. |
| References | From each hit, follow callers, callees, references, and implementations in both directions with native symbol navigation, the language server, or a project index. With none of those, use search and the import edges, and say so. | Dependency injection, reflection, dynamic dispatch, and lookups by string. It also reports paths nothing takes. |
| Execution | Run the scenarios that exercise the feature and the scenarios that do not, and compare the code each set executes. | Every scenario nobody ran. Shared code that holds part of the rule looks unrelated, because both sets execute it. |
| History | Find the commits that introduced or changed a discriminator, and the files that change in the same commits. | Rules that have not changed inside the fetched history; work split across commits or squashed into one. |
| A deliberate break | In a scratch copy, change one decision and run the tests that should notice. | Nothing about reach: a red test shows the behavior is protected, a green suite shows it is not. |

Name the kinds taken for each feature. Mark a decision site that only one
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
2. Coverage of one focused run, such as the tests of one feature, compared
   with coverage of a run that leaves that feature out.
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
a=<package>/skills/untangle/scripts/function-names.gitattributes
git -c core.attributesFile="$a" log --oneline -L :<function>:<file>   # the history of one function or method
python3 <package>/skills/untangle/scripts/change_coupling.py --edges <edges.tsv> <scope>
python3 <package>/skills/untangle/scripts/change_coupling.py --functions <scope>
```

Without the attributes file, `git log -L :<name>:<file>` finds only
definitions that start a line, so it prints nothing, and no error, for a
method inside a class. With `--functions`, `change_coupling.py` counts
functions in place of files: one large file can hide a rule scattered over
its own functions, which file counts cannot show.

`change_coupling.py` lists the files in scope that change most, and the pairs
that change in the same commits. A pair of kind *code* with no dependency is
the lead to one rule in two places. A partner marked *one outside* lies
outside the scope: read it, because the other half of a rule often lives
there. Pairs of kind *test* and *document* are often expected; a document
that changes with the code and still disagrees with it is a finding.

## A deliberate break

A break answers "does any test protect this behavior?". List the breaks in a
file, one per line: a short name, the path, the line number, the text that
replaces the line, and the focused test command expected to catch it. Then
let the script make them, one at a time, in a disposable worktree of HEAD:

```bash
python3 <package>/skills/untangle/scripts/break_probe.py <runs>/breaks.tsv \
  --full "<the command that runs every test of the scope>" --setup "<install command, if the tests need one>" --out <runs>/breaks
```

Make one change per break: invert a condition, change a constant, remove a
check, alter a path. Choose the focused tests with `tests_for_line.py` or by
reading, but treat its *0 tests* as a lead, not a result: per-test coverage
misses some lines, such as `await` expressions. The script reruns every break
the focused tests miss under `--full`, and reports one of three results:

- *focused red*: the behavior is pinned, and those tests are its pin.
- *full red*: it is pinned only outside the focused selection. The pin
  exists; name the test that caught it from the log.
- *green*: no test protects the behavior. Record it in the map under
  *Behavior no test protects*; it is the first lock test a rework writes.

The worktree holds HEAD, so uncommitted changes in the checkout are not in
it; `--with-local-changes` brings them in, for lock tests not yet committed.
Each focused command runs once on the unbroken worktree first, and so does
the full command. One that already fails there is reported as *red before
the break* and pins nothing: its test is missing, the setup is incomplete,
or a test fails before any break and has to be left out of the command.

Break first what would hurt most if it changed silently: a check on who may
do what, a rule about money or data, a value another system reads.

## State and data that travels

Code is hard to follow when a reader cannot tell what a value holds without
knowing every piece of code that touched it. Two things cause that: state
several modules write, and data passed between modules as a hash, dict, or
untyped object. List both:

```bash
python3 <package>/skills/untangle/scripts/shared_data.py <scope>
```

The first table lists globals, class-level variables, module-level
collections, thread or request contexts, and memos. For each one that more
than one module writes, record every writer and reader.

The second table is a ledger of keys: the files that write each key, the
files that read it, and the reads that supply a default. Read it for these
signs that no one place declares the data's shape:

- a key written in more than one file: later writers change what earlier
  readers saw;
- a key read with a default: the reader does not know whether a writer set
  it;
- two reads of one key with different defaults: run one input through both,
  because they give different results for the same data;
- a key read and never written in scope: it comes from outside, or it is
  never set and every reader takes its default.

A key name is matched as text. Confirm at the sites that two rows concern the
same data.

The script reads keys written as `data[key] = ...` and read as `data[key]`
or with a default. It does not see keys set by a comprehension, passed as
keyword arguments into a store, or held in a database row. For those, start
from the other end: list every caller of the methods that write the state,
with the references search of the census, and read what each passes.

Then find out what changes the data after it is handed over. In a scratch
worktree, as for [a deliberate break](#a-deliberate-break), make the data
immutable at the point where one module hands it to the next. In Ruby, freeze
the hash and its nested values. In Python, replace the dict and its lists
with subclasses whose changing methods raise, because a read-only view such as
`MappingProxyType` fails `isinstance(x, dict)` checks and breaks the code for
the wrong reason. Run the baseline. Each test that fails with your raise names
a site that changes shared data. Record the sites; a suite that stays green
shows only that no test reaches a change.

State held in a database or a file is shared too, and a freeze cannot reach
it. Where two writers read a value, change it, and write it back, run them
interleaved in a probe: both read, then both write. A value one of them wrote
that is gone afterwards is a lost update, and it goes under behavior to decide.

Changing a value a function built itself is not a finding. The finding is a
change to data another module handed over, or to state another module also
writes.

## Read the disagreements

| The kinds disagree like this | Read it as a lead to |
| --- | --- |
| A scenario executes it; no search for the feature's words finds it | A hidden part of the feature: add the site, and name what it decides. |
| The words find it; no scenario executes it | Dead code, or a scenario nobody wrote. Find which before recording either. |
| Two code files change together; no dependency between them | One rule kept in two places, or an unwritten convention the two must follow. |
| A reference reaches it; no scenario does | A path nothing takes, or a caller outside the scope. Enumerate the callers. |
| The same condition on the same discriminator at several sites | A scattered rule: list every site, then check that they agree. |
| A test name states the behavior; no test fails when it is broken | Behavior no test protects. |
| A document states a count, a list, or a rule; the code or a run shows another | A broken stated rule: record both values. |
| Two reads of one key supply different defaults | Shapeless data, and behavior to decide: record what each reader does with the same input. |
| Data frozen where it is handed over makes a test fail | A site that changes shared data: shared mutable state. |

Sites that decide the same rule and disagree are the most valuable result of
the census: record the inputs on which they differ, and run one. The result
goes under *Behavior to decide*.

## Edges for the dependency view

Use the most exact source available, and say which one produced the edges:

1. The compiler or a dependency tool of the ecosystem, such as the JDK's
   `jdeps`, a module-graph command, or a bundler's graph output.
2. The language server or a project code index, queried per file.
3. [`import_edges.py`](../scripts/import_edges.py), which reads static
   imports in Python, JavaScript, TypeScript, and Java, and in Ruby
   `require_relative` and references to a constant one file defines, and
   leaves out edges that start in a test file. With `--rev <commit>` it reads
   the edges at that commit:

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
design forbids. A dependency that touches such a file is *not compared* in
the map and in its structure view.

A relationship reported as *not found* means no edge showed it. Before
recording it, check whether the dependency runs through something the edge
source cannot see, such as an injected object.
