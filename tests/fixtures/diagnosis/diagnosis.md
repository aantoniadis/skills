# Confirmation retries reserve stock twice

**Verdict:** A confirmed order held two reservations after one stock timeout. The contract is one reservation per confirmed order, pinned by [test_confirm.py:5](https://github.com/acme/shop/blob/cccccccccccccccccccccccccccccccccccccccc/tests/test_confirm.py#L5). The cause is the retry loop calling `reserve` with no idempotency key at [confirm.py:13](https://github.com/acme/shop/blob/cccccccccccccccccccccccccccccccccccccccc/orders/confirm.py#L13). Fixed by restoring the key at both callers; the regression test went red, then green ([run record](runs/bugs/1/run.md)).

**Checked:** *reproduced* · *fixed* · *test red then green* · *origin checked*, a regression from the gRPC move · *reach checked*, one more caller fixed · *consequence checked*, the single-attempt path unchanged. **Inspected source:** commit `ccccccc` of the fictional `acme/shop`; see [evidence and record](#evidence-and-record).

> **Fictional example.** This note demonstrates the diagnosis template. Its shop, files, and runs are invented.

## Symptom and contract

The issue says "order 42 shows two reservations in the warehouse view" after one stock timeout ([issue 1042](https://github.com/acme/shop/issues/1042)). The contract is one reservation per confirmed order: `test_confirm_reserves_once` pins it at [test_confirm.py:5](https://github.com/acme/shop/blob/cccccccccccccccccccccccccccccccccccccccc/tests/test_confirm.py#L5), and the issue states the same expectation ([issue 1042](https://github.com/acme/shop/issues/1042)). Verdict: a bug.

## Reproduction

The loop is one command that goes red on the exact symptom; it ran three times with the same output ([run record](runs/bugs/1/run.md)):

```sh
python runs/bugs/1/repro.py
```

Output: `reservations=2` · [repro.py](runs/bugs/1/repro.py)

| Criterion | Evidence |
| --- | --- |
| Red on the exact symptom | `reservations=2` matches the issue's two reservations ([run record](runs/bugs/1/run.md)) |
| Deterministic | three runs, same output, recorded in the [run record](runs/bugs/1/run.md) |
| Fast | 0.4 s per run, measured |
| Runs unattended | no prompts; ran as a plain script |

Minimised: the second order and the warehouse stub were cut one at a time, and the loop stayed red after each cut (observed, [run record](runs/bugs/1/run.md)). The one timeout and the retry are load-bearing.

## Cause

The retry re-enters `reserve` after a timeout that the stock service had already recorded, so the second attempt creates a second row; source at the pinned lines:

```python url="https://github.com/acme/shop/blob/cccccccccccccccccccccccccccccccccccccccc/orders/confirm.py#L10-L16"
def confirm(order, stock):
    for attempt in range(RETRIES):
        try:
            reserve(stock, order.id, order.quantity)
            break
        except StockTimeout:
            time.sleep(RETRY_SLEEP)
```

### 1. Retry without an idempotency key reserves twice
*we ran it* · *regression*

**Where:** [confirm.py:13](https://github.com/acme/shop/blob/cccccccccccccccccccccccccccccccccccccccc/orders/confirm.py#L13), `reserve(stock, order.id, order.quantity)` inside the retry loop, with no idempotency key.

**Trigger:** one `StockTimeout` after the stock service has recorded the reservation, so the retry reserves again; observed with the stub in [repro.py](runs/bugs/1/repro.py#L9).

**Who / impact:** the warehouse sees two reservations for one order and oversell protection fires wrongly, quoted from the issue ([issue 1042](https://github.com/acme/shop/issues/1042)).

| | Before the fix | After the fix |
| --- | --- | --- |
| Reservations after one timeout | 2, observed | 1, observed |

## Hypotheses

| Hypothesis | Prediction | Probe | Verdict |
| --- | --- | --- | --- |
| Retry without an idempotency key reserves twice | passing a key makes the loop go green | `repro.py --fixed` | supported, `reservations=1` ([run record](runs/bugs/1/run.md)) |
| The stock stub double-counts rows | a stub with no timeout also reports 2 | `StockStub(timeouts=0)` | contradicted, reports 1 ([run record](runs/bugs/1/run.md)) |
| The warehouse view counts cancelled rows | a cancelled order still shows a reservation | not run | unresolved; dropped after the first hypothesis was supported, not needed for the fix |

## Origin

The loop bisected between the last good tag and the head: the first bad commit is the gRPC move ([run record](runs/bugs/1/run.md)). Its PR says the change "drops the idempotency key to simplify the call" ([PR 980](https://github.com/acme/shop/pull/980)). A regression, so the fix is a forward fix that keeps the gRPC client and restores the key; the intent kept is the gRPC client.

## Reach

| Caller | Line | Result | Evidence |
| --- | --- | --- | --- |
| `cancel` | [cancel.py:11](https://github.com/acme/shop/blob/cccccccccccccccccccccccccccccccccccccccc/orders/cancel.py#L11) | affected; fixed, test added | the same loop releases through `reserve` without a key, [cancel.py:11](https://github.com/acme/shop/blob/cccccccccccccccccccccccccccccccccccccccc/orders/cancel.py#L11) |
| Other callers of `reserve` | none in `orders/` | cleared | symbol search recorded in the [run record](runs/bugs/1/run.md) |

## Fix and regression test

Both callers pass the order id as the idempotency key; the diff below is the whole change, starting at [confirm.py:13](https://github.com/acme/shop/blob/cccccccccccccccccccccccccccccccccccccccc/orders/confirm.py#L13):

```diff
--- a/orders/confirm.py
+++ b/orders/confirm.py
@@ -11,4 +11,4 @@ def confirm(order, stock):
     for attempt in range(RETRIES):
         try:
-            reserve(stock, order.id, order.quantity)
+            reserve(stock, order.id, order.quantity, key=order.id)
             break
--- a/orders/cancel.py
+++ b/orders/cancel.py
@@ -9,4 +9,4 @@ def cancel(order, stock):
     for attempt in range(RETRIES):
         try:
-            reserve(stock, order.id, -order.quantity)
+            reserve(stock, order.id, -order.quantity, key=f"cancel-{order.id}")
             break
```

The existing contract test exercises the real pattern, a timeout after the reservation was recorded, at the confirmation seam, so it served as the regression test: [test_confirm.py:5](https://github.com/acme/shop/blob/cccccccccccccccccccccccccccccccccccccccc/tests/test_confirm.py#L5). It failed before the fix and passed after it, and `test_cancel_releases_once` was added beside it for the second caller ([run record](runs/bugs/1/run.md)).

## Verification

| Check or scenario | Result | Evidence origin | Revision and configuration | Scope and limits |
| --- | --- | --- | --- | --- |
| [Reproduction loop before the fix](runs/bugs/1/run.md) | Failed | Executed here | commit `ccccccc`, default configuration | red on the exact symptom, as expected before the fix |
| [Regression test before the fix](runs/bugs/1/run.md) | Failed | Executed here | commit `ccccccc`, default configuration | `assert 2 == 1`; the test detects the bug |
| [Regression test after the fix](runs/bugs/1/run.md) | Passed | Executed here | fixed working tree, default configuration | both callers; the stub models the timeout, not the real service |
| [Reproduction loop after the fix](runs/bugs/1/run.md) | Passed | Executed here | fixed working tree, default configuration | `reservations=1` |
| [Consequence check, single attempt](runs/bugs/1/run.md) | Passed | Executed here | fixed working tree, no timeout | one reservation with the key and no retry |
| Full project suite | Not run | Proposed | fixed working tree | run `pytest` before the PR; this note covers the two confirmation tests |

## Consequence

The fix adds a key to a shared producer, `reserve`, so its other consumer was compared: a single attempt with the key reserves once, the same as before ([run record](runs/bugs/1/run.md)). A repeated confirmation of an already confirmed order now reserves nothing new, which the contract requires; inferred from the key check at [repro.py:10](runs/bugs/1/repro.py#L10) and not exercised against the real gRPC client.

## Limits and next steps

- The real gRPC client was not exercised; the stub models the timeout after the record. Run the suite against the staging stock service before release.
- The warehouse view hypothesis stays unresolved and is not needed for this fix.
- Instrumentation: none left; the loop needed no debug logging.

The fix and the test are in the working tree, uncommitted. Open the PR with HumanLayer's `visual-pr`:

```text
/visual-pr Create the PR for this branch. Use runs/bugs/1/run.md and diagnosis.md as context. Describe the restored idempotency key at both callers and the checks actually run.
```

## Evidence and record

- Source: commit `ccccccc` of the fictional `acme/shop`; the fixed files are the diff above, see [confirm.py:13](https://github.com/acme/shop/blob/cccccccccccccccccccccccccccccccccccccccc/orders/confirm.py#L13).
- Runs: [run record](runs/bugs/1/run.md), [repro.py](runs/bugs/1/repro.py), [issue 1042](https://github.com/acme/shop/issues/1042), [PR 980](https://github.com/acme/shop/pull/980).
- Page: checked with `render_page.py diagnosis.md --check --sync-labels` from source; not opened in a browser.

## Status and label key

These labels describe separate judgments. Read each against its stated scope and evidence; no label alone establishes overall readiness or approval.

### Key: Verification results

| Option | Meaning |
| --- | --- |
| Passed | The recorded check met its expected outcome under the stated revision and conditions. This does not prove correctness outside that scope. |
| Failed | The recorded check did not meet its expected outcome. The result alone does not establish the cause or whether this change introduced it. |
| Mixed | The recorded checks or scenarios include both passing and failing outcomes; the report identifies which are which. |
| Not run | No execution result is claimed for this entry. Reading source or proposing a check does not count as running it. |
| Blocked | An identified obstruction prevented completion of the check. The report names it and retains any partial evidence. |

### Key: Verification evidence origins

| Option | Meaning |
| --- | --- |
| Executed here | The check was executed in this session, including delegated execution. Its command, result, revision, conditions, and limits are recorded. |
| Recorded run | The report cites an existing run, such as CI or an earlier experiment. Its original revision and conditions determine applicability. |
| Source inspected | Relevant code or assertions were read. Execution is not established, so the result is Not run. |
| Proposed | No execution evidence is claimed. The result is Not run or Blocked; Blocked names the obstruction that prevented the planned check. |

### Key: Bug evidence

| Option | Meaning |
| --- | --- |
| we ran it | A probe observed the Head result, and the Base result when it could run. The command and output identify that run and its conditions. A retained earlier card uses Recorded run in Verification; an unobserved Base value starts with predicted:. |
| suspected, not run | The code suggests the bug, but no probe ran. The card's Base and Head values are predictions, and the card names the probe that would settle it. |

### Key: Cause origin

| Option | Meaning |
| --- | --- |
| regression | The loop went green at an earlier revision and red at the reported one; the note names the breaking commit and quotes its intent. |
| always broken | No earlier revision passes the loop, or the code was born with the cause; the fix is a forward fix. |
| origin not checked | Bisection was skipped; the note says why, such as one commit in history or no earlier working state. |

### Key: Diagnosis checks

| Option | Meaning |
| --- | --- |
| reproduced | One saved command went red on the exact symptom; the run record holds the command and output. When the loop ran against a stand-in for the component that carries the bug, the Checked line names that model. |
| not reproduced | No loop could be built after a real attempt; the cause is a ranked hypothesis labeled inferred. |
| fixed | The fix is in the working tree or committed, with its diff in the note. |
| fix proposed | A fix direction or diff is proposed but not applied; its assumptions and missing checks are stated. |
| no fix proposed | No application fix was applied or proposed; the note states why, such as diagnosis-only scope. |
| test red then green | The regression test failed before the fix and passed after it, both runs recorded. |
| test not verified | The regression test has no recorded red-to-green pair. The note states whether it is proposed, blocked, unrun, or still failing, and what remains to verify. |
| no test seam | No available seam exercises the real bug pattern; the note records the gap and any reproduction-loop evidence. |
| origin checked | Bisection ran and the breaking commit's intent is quoted, or the cause was traced to its first revision. |
| origin skipped | Origin was not investigated; the note gives the reason. |
| reach checked | Every caller and copied pattern that hits the cause is listed as fixed, affected and unfixed, or cleared with evidence. |
| reach skipped | Reach was not investigated; the note gives the reason, such as one caller and no copied pattern. |
| consequence checked | The fix's other consumers were compared through their next action, with evidence. |
| consequence skipped | Consequence was not investigated; the note gives the reason, such as no shared producer changed. |
