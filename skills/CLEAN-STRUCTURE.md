# Clean structure

Read when you propose a rework target, a reshape before a change, or a new
unit, and when you check that a rework landed. A correct refactoring keeps
the behavior and leaves code a reader can follow:

- each module has one responsibility;
- it follows SOLID where a second case exists today, and YAGNI everywhere;
- state is shared as little as possible;
- every name says what the unit is for, so a method whose body is complex
  still says what it does and why.

Each principle below has a check you run on the code today and on the
target as written, and the problem it is when it fails. A principle is met
when its check passes, not when a pattern is present.

## Contents

- [The principles](#the-principles)
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
   nothing else. *Check:* the last commit that added a variant, and the
   files it had to edit. *Fails as:* scattered rule.
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
   holds what an argument could carry. *Check:* the writers and readers of
   each piece of state, from the census. *Fails as:* shared mutable state,
   or shapeless data.
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
principle covers, such as Liskov substitution with no subtypes. After the
rework, the same checks give the measures.
