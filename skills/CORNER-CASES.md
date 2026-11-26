# Corner cases

Read when a change, a plan, a fix, or a rework meets a corner case. A
**corner case** is an input or state that only some uses reach: an empty or
extreme value, a rare combination, a failure partway through an operation, a
race, a legacy record. Whether to handle it, and how, is a trade: the case's
reach and harm against the complexity its handling adds. The developer makes
that trade, with the price in front of them.

## When the developer decides

Handling a corner case **bends the design** when it needs any of these:

- a parameter, flag, or mode passed through layers that do not use it;
- a branch in a path that every input takes;
- a new stored field, state, or status;
- a new abstraction, interface, or extension point;
- a second path for a rule that already has one;
- an ordering constraint, a journal, a lock, or a retry.

A corner case that bends the design goes to the developer on a corner-case
card before its code is written, and every decision about it is recorded. A
check at the one site that meets the case, which adds none of these, does
not bend the design: place it as the calling skill places any change.

## The corner-case card

- **Case:** the input or state in domain words, and the probe or test that
  reaches it, with its result today.
- **Reach:** who meets it, from evidence: a test, a probe through the public
  boundary, stored data or logs that contain it, a ticket or report. When the
  only evidence is a probe written for this work, say "found by our probe; no
  known user meets it".
- **Harm if not handled:** what a user of the software gets: a wrong result,
  an error, lost or corrupted data, a security exposure. Take it from a run.
- **Options,** cheapest first. Give each one the design elements above that
  it needs, the files it touches, and what a user sees:
  1. **Reject:** refuse the case at the boundary with a clear error.
  2. **Isolate:** handle it in one place at the edge, such as normalizing the
     input before the general path, so the general path stays unchanged.
  3. **Build in:** handle it in the general design.
  4. **Leave:** keep today's behavior and record the case where the next
     developer reads it.

  Name only the options that exist for the case. An option that changes
  today's behavior says so.
- **Recommendation,** with the reason: the reach and the harm against the
  price.

Group cases with one answer, such as three empty inputs that one boundary
check rejects, into one card.

## When nobody answers

Keep the design, and list the card as an open question with its default:

- For behavior that exists today, the default is **leave**.
- For behavior the change adds, the default is **reject**; where no clear
  error can stand in for the case, such as a crash partway through, it is
  **leave**: the plain design, with the case recorded.
- When the harm is lost or corrupted data or a security exposure, the default
  is the cheapest option that prevents the harm, **reject** before
  **isolate**.
- When the request is to fix the case itself, as a bug report on it is, the
  default is **reject** when a clear error ends the harm, else **isolate**.

These defaults also apply under an autopilot policy that applies the agent's
recommendations. **Build in** needs the developer's own answer.

## Where the card goes

Write the card where the decision is read: the change card or the slice's
placement in [fit-change](fit-change/SKILL.md), the plan's decision record in
[plan-change](plan-change/SKILL.md), the diagnosis in
[fix-bug](fix-bug/SKILL.md), and the *Corner cases* table of a rework map in
[untangle](untangle/SKILL.md). Record the chosen option and its authority:
the developer's answer, or the default applied because nobody answered.
