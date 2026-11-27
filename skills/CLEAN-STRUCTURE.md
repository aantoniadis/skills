# Clean structure

Read when you propose a rework target, a reshape before a change, or a new
unit, and when you check that a rework landed. A correct refactoring keeps
the behavior and leaves code a reader can follow:

- each module has one responsibility;
- it follows SOLID where a second case exists today, and YAGNI everywhere;
- state is shared as little as possible;
- every name says what the unit is for, so a method whose body is complex
  still says what it does and why;
- each function reads top to bottom as the steps of what its name says.

Each principle below has a check you run on the code today and on the
target as written, and the problem it is when it fails. A principle is met
when its check passes, not when a pattern is present.

## Contents

- [The principles](#the-principles)
- [Leads, not verdicts](#leads-not-verdicts)
- [Forms in common languages](#forms-in-common-languages)
- [When principles pull apart](#when-principles-pull-apart)
- [Applying them to a target](#applying-them-to-a-target)

## The principles

1. **Single responsibility.** A module's responsibility fits one sentence
   with no *and*, in the project's domain words, and the module has one
   reason to change: one feature, one source of requirements, one external
   system. *Check:* write the sentence. Read the module's rows in the
   behavior map, and its lines in the change history. A module that decides
   behaviors of two features, or whose lines change in two sets of commits
   that never touch each other, has two reasons. Leads for where to look:
   many collaborators, public functions that serve different callers,
   functions that share no fields (if you removed half of them, would the
   other half still make sense as a module?), imports from several unrelated
   areas, a high fan-out from `import_edges.py --coupling`, and a *util* or
   *common* directory that keeps growing. *Fails as:* needless link,
   fixed by **Split**. A module with no decision of its own is surplus,
   fixed by **Remove** or **Merge**.
2. **Open–closed.** Adding a variant that already has siblings, such as a
   tier, a provider, or a file format, adds one entry or one unit and edits
   nothing else. Where a set of variants is closed and several places must
   treat each variant, an exhaustive match over a closed type ties those
   places together: adding a variant fails to compile, or fails the type
   check, at every place that does not handle it. Those places are not a
   scattered rule, because the code says they change together. *Check:* the
   last commit that added a variant, and the files it had to edit; for each
   switch or chain of type tests over the variants, whether the compiler or
   type checker would flag a missing one. *Fails as:* scattered rule, fixed
   by one table of variants, or by a closed type with exhaustive matches.
3. **Liskov substitution.** Every implementation of an interface or
   subclass honors what callers rely on. No caller checks which one it holds,
   by a type test, a type switch, or a kind field, and no implementation
   raises *not supported* for a method of its interface or overrides it
   with an empty body. A subclass that extends a concrete class only to
   reuse its code, or overrides most of what it inherits, wants composition:
   it holds the other class and calls it. *Check:* search the callers for
   those tests, and the subclasses for empty and rejecting overrides. *Fails as:* scattered rule when the difference
   leaks into callers, fixed by moving it into the implementations; surplus
   when the members share no contract, fixed by dropping the shared type.
4. **Interface segregation.** A function receives what it uses. One that
   reads two fields of a large object, a request context, or a settings
   bundle takes those two. An interface whose implementers leave some of
   its methods empty, or whose callers each use a different part of it, is
   several interfaces. *Check:* for each parameter, the fields the body
   reads; for each interface, which callers use which methods. *Fails as:* needless link; shapeless data when the object is a
   hash or dict.
5. **Dependency inversion.** Domain rules do not import details: a database
   driver, an HTTP client, a file format, a framework. The detail calls the
   rule, or is passed in. A rule that constructs its own collaborator, such
   as a client or a repository, hides a dependency its callers cannot see or
   replace. A directory that many others depend on changes least easily, so
   it does not depend on a directory that changes more often. *Check:* the
   edges from rule modules to detail modules; the collaborators each rule
   constructs; the dependencies on a less stable directory that
   `import_edges.py --coupling` prints. *Fails as:* two-way flow or needless link. A direct call to the
   one detail that exists, which tests can reach, is fine: an interface with
   one implementation and no second user is surplus.
6. **YAGNI.** Every unit, parameter, option, branch, and extension point
   has a caller today. *Check:* a search for its callers, and the deletion
   test: if deleting it makes complexity vanish, it was not needed. Its
   shapes include an abstract class with one subclass and a type parameter
   used once. Repetition is a different question: two copies of the same
   knowledge, such as a rule or a rate, are a scattered rule however
   different they look; two blocks that look alike and mean different
   things are not, and merging them ties together what changes apart. Wait
   for the third copy of a shape before you abstract it. *Fails as:*
   surplus, or unjustified special case. This holds for the target
   too: each interface, registry, plugin point, or setting the target adds
   names its second user today, or it is left out.
7. **Minimal shared state.** A value is built once and not changed after it
   is handed over. Each piece of state has one writer, and readers get it
   through that writer. No global, class-level variable, or context field
   holds what an argument could carry. In the code that means:
   - data passed between modules is an immutable value type with declared
     fields, checked once where it is built;
   - a change makes a new value, through a copy with the field changed,
     instead of a setter on a shared object;
   - a collection handed out is read-only or a copy, and a collection taken
     in is copied before it is kept;
   - a value that may be absent says so in its type, and a function that
     finds nothing returns an empty collection or an explicit absent value,
     not a null a caller must remember to check;
   - a domain value, such as money, an identifier, or a currency, has its
     own type rather than a raw string or number, and values that always
     travel together are one value;
   - a status with fields that are valid only in some statuses becomes one
     type per state, each with only its fields, so a state that cannot
     occur cannot be built.

   *Check:* the writers and readers of each piece of state, from the census;
   each setter and each mutable field of a type passed between modules; each
   function that can return null without its type saying so. *Fails as:*
   shared mutable state, or shapeless data.
8. **One-way flow.** Calls and state move one way, from the entry points
   toward storage. There is no cycle, and a later step returns its result
   instead of writing into an earlier one's state. *Check:*
   `import_edges.py --cycles`, and the callbacks, events, and shared objects
   in the census. *Fails as:* two-way flow.
9. **Intention-revealing names.** A name says what the unit is for, and all of
   what it does:
   - a module or class is named for the decision it owns;
   - a function that returns a value is named for the value;
   - a function with an effect is named for the effect;
   - a boolean is named as a question, such as `is_expired`.

   *Check:* read each name, then its body and its callers. Three signs:
   - the name says less than the body does, such as a `get_` that writes or
     a `validate` that corrects;
   - the name describes the mechanism, not the purpose, such as
     `loop_items` or `process`;
   - the name is generic: *manager*, *helper*, *utils*, *common*, *base*,
     *handler*, *service*, *data*, *info*, *misc*;
   - one concept goes by several names, such as `find`, `get`, `fetch`, and
     `load` for the same kind of lookup.

   When the body must stay complex, the name still says what it does, and a
   short comment above it says why: the requirement, incident, or
   constraint it serves, with its link. A comment that retells the steps of
   the body means the name or the split is wrong. *Fails as:* unclear name,
   fixed by **Rename**, or by **Split** when no one name fits.
10. **Readable functions.** A function does what its name says at one level
    of detail, and a reader follows it top to bottom without holding state
    in their head. *Check:* read each function the census names, for these
    signs:
    - nesting deeper than two levels where guard clauses that return early
      would flatten it;
    - a condition of three or more clauses, or a negated compound, with no
      name: give it one as a well-named function or variable;
    - comments that work as headings over blocks of steps: each block is a
      function to extract, named by its comment;
    - steps at two levels of detail side by side, such as a domain decision
      next to string formatting or index arithmetic;
    - a loop that builds a collection by filtering and transforming, where
      the language's pipeline would read as the sentence; a loop with side
      effects or an early exit that carries state stays a loop;
    - a boolean argument that selects what the function does: it is two
      functions;
    - more than three parameters, or a group of them that travels together
      through several signatures: they are one value;
    - a function that both changes state and returns a result a caller
      depends on, where a command and a query would each say what they do;
    - an error that says only that something failed: an error names what
      failed with the values that identify it, keeps its cause, and is a
      type specific enough for a caller to catch; an error caught only to
      steer a loop, or caught broadly and logged, hides the outcome.

    The ecosystem's own complexity or lint report, such as cyclomatic
    complexity per function, is a lead for where to read, not the finding.
    *Fails as:* hard-to-follow function, fixed by extracting a function,
    guard clauses, or a named condition, inside the function's own module.
11. **Decisions with their data.** A decision lives with the data it
    reads: tell an object what to do rather than ask for its fields and
    decide for it. *Check:* three signs:
    - a function that reads several fields of another type, decides, and
      writes the result back into it: the decision belongs to that type;
    - a chain that reaches through objects, such as
      `order.customer().account().tier()`, couples the caller to every type
      on the way; builders and pipelines are not chains of this kind;
    - a type that carries fields while every rule about it lives elsewhere,
      when those rules are what the type means; a plain value passed across
      a boundary is fine.

    *Fails as:* misplaced logic, fixed by **Move**.

## Leads, not verdicts

Counts tell you where to read; the code tells you whether there is a
problem. Report a principle as broken only with the lines that break it.
These numbers are where to start reading:

- more than about seven collaborators in one module;
- more than about ten public functions;
- more than three parameters;
- nesting deeper than two;
- a cyclomatic complexity above about ten;
- an interface with more than about five methods;
- a directory of more than about twenty files.

`import_edges.py --coupling` gives fan-out, fan-in, and directory
instability; the ecosystem's own tools give finer numbers.

A shape a framework requires is not a finding: an ORM entity with setters,
dependency-injection annotations on domain classes, or a central error
handler. Name the framework rule that requires it. What the project's own
checks already enforce, such as a lint rule, a type checker, or an
architecture test, is not reported again. Read those checks first, build on
the patterns the project already uses, and propose a new rule where a
principle the target restores could be checked on every change.

## Forms in common languages

Use the form the language offers. Where the project already has a
convention, such as a style guide or a lint configuration, follow it.

- **An immutable value with declared fields:** a record in Java or C#; a
  `data class` with `val` fields in Kotlin; a frozen data class or
  `NamedTuple` in Python; a `readonly` type or `Readonly<T>` in TypeScript; a
  struct without `mut` in Rust; a frozen `Data` or `Struct` in Ruby.
- **A copy with one field changed:** `with` methods or a builder in Java;
  `copy(...)` in Kotlin; `with` expressions in C#; `dataclasses.replace` in
  Python; the spread `{...value, field}` in TypeScript; struct update syntax
  in Rust.
- **A read-only collection:** `List.copyOf` and `List.of` in Java;
  `tuple` or `frozenset` in Python; `ReadonlyArray` in TypeScript.
- **Absence in the type:** `Optional<T>` in Java, used through `map`,
  `orElse`, and `orElseThrow` rather than `get`; `T?` in Kotlin and C#;
  `T | None` in Python; `T | undefined` in TypeScript; `Option<T>` in Rust.
- **An exhaustive match over a closed type:** a sealed interface with a
  `switch` that has no `default` in Java; a sealed class with `when` in
  Kotlin; a `match` ending in `assert_never` in Python; a union with a
  `never` check in TypeScript; `match` on an enum in Rust.

## When principles pull apart

SOLID applied without a second case produces the indirection that YAGNI
forbids. Until the second case exists, YAGNI wins: the target says which
future case would earn the abstraction, and adds nothing for it. A
principle is not a count of patterns. A target that adds interfaces,
factories, or layers and removes no branch, state, or decision site is
surplus, whatever principle it cites.

A rename needs a reason: the name misleads a reader, names a mechanism, or
no longer matches the responsibility. Use the project's glossary words over
new ones. A rename of public API, a stored name, or a name outside the
repository has consumers the rework cannot see: it is a question for the
user, with its consumers listed.

## Applying them to a target

Before you recommend a target, run each check on the target as written:

- for each module, its responsibility sentence and its reason to change;
- for each abstraction it adds, its second user;
- for each piece of state, its one writer;
- for each new or renamed unit, its name against its body;
- for each function it adds or moves, the signs of a hard-to-follow
  function, and whether its decisions live with their data.

Change a target that fails a check before you offer it, or name the failure
in its cost. In the plan, write one item per principle, labelled with its
name, then today's result and the proposed one, each *broken*, *met*, or
*not applicable*, as `broken → met`, then their evidence. The page draws
the results as a scorecard. Write
*not applicable* with the reason where the scope holds nothing the
principle covers, such as Liskov substitution with no subtypes. For readable
functions, name the functions read and the ones that fail. After the
rework, the same checks give the measures.
