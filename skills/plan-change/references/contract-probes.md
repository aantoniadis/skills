# Contract probes

Use this reference at the tested-contract depth. It turns the agreed
decisions into a contract at each seam the change crosses, then tries to break
each clause against the real code and systems before implementation starts.
The contract is ready when it survives the probes.

## 1. Draft the contract

A **seam** is a boundary where the change meets code or a system it does not
own: a neighboring feature that reads or writes the same state; a shared
protocol, queue, file, cache, or database; an external system; the platform or
runtime lifecycle. Find the seams through the consumers that behavior
comparison traced and through every shared state the change writes.

For each seam, check these aspects. Write a clause for each aspect the change
depends on:

- inputs and outputs: shapes, types, units, encodings, and size limits;
- outcomes: success, refusal, partial result, and failure, and how the other
  side recognizes each one;
- cancellation, timeouts, and retries;
- ordering, concurrency, and stale versions or results;
- lifecycle: open, close, reopen, reload, quit, and restart;
- resources at peak load: memory, storage, rate, and quotas.

Add a `## Contract` section after Decisions in the plan, with one row per
clause:

| Clause | Seam | Status | Evidence |
| --- | --- | --- | --- |

A clause names its consumer and the behavior that consumer relies on. Its
status is one of these:

- **Assumed:** no probe or decision supports it yet. A new clause starts here.
- **Proven:** a probe that crossed the real seam held. Evidence links the run
  and states the conditions it covered.
- **Decided:** the user, or an authorized autopilot policy, chose this behavior
  after a probe or comparison. Evidence links the decision.
- **Accepted risk:** the user accepted the clause without proof, or after a
  probe broke it. Evidence names the gap or the failed probe, and the
  acceptance.

## 2. Rank and probe

Rank the Assumed clauses by the cost of a wrong assumption after implementation
starts. A clause that would change an interface, a data format, a stored
record, or another feature's behavior ranks above one that changes a local
detail. Probe the highest-ranked clause first.

A **probe** is the smallest throwaway code that crosses the real seam: the
neighboring feature's actual code, the real external system or a local
sandbox of it such as a container or a test account, and the real platform
when lifecycle matters. A mock or model shows only how the mock or model
behaves. Run the candidate next to its neighbors, because a feature that
works alone can still conflict at a shared seam.

Write each probe to **break** its clause. Aim the inputs, timing, concurrency,
and lifecycle events from the aspect list at the edges of the clause, such as
a non-ASCII character before the caret, a cancel during the request, a reopen
after release, or the limit plus one.

Keep probes in the investigation location or on a throwaway branch, outside
production code. Record each run in Verification with origin Executed here, as
[evidence](../../EVIDENCE.md) says. Ask before material cost, side effects on
shared or external systems, or credentials beyond existing authorization.
Continue other probes while you wait.

## 3. Return each result to the decision maker

- **The probe holds:** mark the clause Proven, then probe the next clause.
- **The probe breaks the clause:** the contract must change. Bring the
  clause, the probe output, the viable options, and a recommendation to the
  user through the plan's tradeoff step. The answer marks the revised clause
  Decided and links the decision. An authorized autopilot policy settles the
  change only within the policy's scope; record it as a policy decision. Then
  probe the revised clause.
- **The clause cannot be probed within authorization or cost:** it stays
  Assumed until the user authorizes the probe or accepts the named risk.

Probes report facts. The user, or the user's authorized policy, decides what
the contract becomes.

## 4. Stop and hand on

The loop is complete when every clause on a consequential seam is Proven,
Decided, or Accepted risk, and every seam has at least one probe that crossed
it or a recorded reason it has none. When the user stops earlier, the
remaining Assumed clauses block the slices that rely on them.

The spec and each ticket state the clauses their slices rely on, with status
and evidence. When implementation finds that a clause does not hold, the
feedback reopens that clause and its decision through the same loop.
