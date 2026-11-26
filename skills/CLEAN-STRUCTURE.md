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
   that never touch each other, has two reasons. *Fails as:* needless link,
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
   raises *not supported* for a method of its interface. *Check:* search the
   callers for those tests. *Fails as:* scattered rule when the difference
   leaks into callers, fixed by moving it into the implementations; surplus
   when the members share no contract, fixed by dropping the shared type.
4. **Interface segregation.** A function receives what it uses. One that
   reads two fields of a large object, a request context, or a settings
   bundle takes those two. *Check:* for each parameter, the fields the body
   reads. *Fails as:* needless link; shapeless data when the object is a
   hash or dict.
5. **Dependency inversion.** Domain rules do not import details: a database
   driver, an HTTP client, a file format, a framework. The detail calls the
   rule, or is passed in. *Check:* the edges from rule modules to detail
   modules. *Fails as:* two-way flow or needless link. A direct call to the
   one detail that exists, which tests can reach, is fine: an interface with
   one implementation and no second user is surplus.
6. **YAGNI.** Every unit, parameter, option, branch, and extension point
   has a caller today. *Check:* a search for its callers, and the deletion
   test: if deleting it makes complexity vanish, it was not needed. *Fails
   as:* surplus, or unjustified special case. This holds for the target
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
     not a null a caller must remember to check.

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
     *handler*, *service*, *data*, *info*, *misc*.

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
    - an error that says only that something failed: an error names what
      failed with the values that identify it, keeps its cause, and is a
      type specific enough for a caller to catch.

    The ecosystem's own complexity or lint report, such as cyclomatic
    complexity per function, is a lead for where to read, not the finding.
    *Fails as:* hard-to-follow function, fixed by extracting a function,
    guard clauses, or a named condition, inside the function's own module.

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
- for each new or renamed unit, its name against its body.

Change a target that fails a check before you offer it, or name the failure
in its cost. In the plan, write one item per principle, labelled with its
name, with today's result and the proposed one and their evidence. Write
*not applicable* with the reason where the scope holds nothing the
principle covers, such as Liskov substitution with no subtypes. For readable
functions, name the functions read and the ones that fail. After the
rework, the same checks give the measures.
