# House rules

Read when a kind of structure finding, or a corner case handled by bending
the design, has appeared in a second change to the same project, or when the user asks how to stop it at the source. A session
that never invokes a skill still reads the project's instruction file, so a
rule that has to hold in every session goes there, or into a check the
project runs.

## Choose the form

- **A check, when the rule is mechanical:** a forbidden import between two
  parts, a banned construct, a file that must not be edited. Express it with
  the ecosystem's lint or dependency-rule tool, or with the stated design file
  and `design_conformance.py`, and write the failure message as the repair
  instruction. A check is followed every time; an instruction is not.
- **An instruction, when the rule needs judgment.** Write one behavior per
  line, concrete enough that a reviewer can check a commit against it. State
  where the rule applies and why: a bare "never" is applied too widely or
  dropped. Supply the fact the agent lacks, such as "this interface has no
  consumers outside the repository".
- **Nothing, when it happened once.** Each line in an instruction file costs
  attention in every session. Add a line for an observed, repeated behavior,
  and remove one that no longer changes anything.

## Lines to adapt

Offer only the lines that match a finding seen in this project, reworded with
its own names: its owner modules, its boundary, its design document.

```markdown
## Structure

- Before adding a condition on a concept, search for where that concept is
  already decided and change that place. One rule is decided in one module.
- When a change needs the same condition, constant, or list in a second file
  or layer, stop and say which restructuring would make it one place.
  Restructuring that the plan names is in scope; other restructuring is not.
- Validate where data enters: user input, external services, stored data,
  files. Inside, rely on the types and the callers. Add a check for a state
  only when you can name the caller or input that produces it.
- Add a fallback or catch an error only where the task says what the consumer
  should see on that failure. Otherwise let the error propagate.
- Pass data between modules as a value with declared fields, built once
  where the data enters. Do not add keys to a hash or dict another module
  built; return a result instead.
- Do not change an argument you were given, and do not write state another
  module owns. One module writes each piece of state.
- When you replace a path, move its callers and delete it in the same change,
  unless something outside this repository uses it.
- Search for existing code before writing a helper.
- Before handling a rare input or state with a parameter through layers, a
  branch in the general path, new stored state, or a new abstraction, stop.
  Say who meets the case and what handling it costs the design, offer the
  cheaper options (reject it at the boundary, isolate it at the edge, leave
  it), and let the developer choose.
```

Where the project states its design, add one line that points to it and names
the dependency directions it allows.

## After adding a rule

Note which finding it answers. If the same finding appears again with the
line in place, the instruction did not work: turn it into a check, or sharpen
it with the case it missed.
