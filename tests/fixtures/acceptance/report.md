---
repository: acme/widgets
base: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
head: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
---
# Acceptance of CSV export and export permissions

**Bottom line:** CSV export works ([export.py:4](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/export.py#L4)), but nothing limits it to admins; decide whether to block the merge.

**Reviewed:** head bbbbbbb against base aaaaaaa. **Coverage:** `src/export.py` read at the line; one probe run; two intent sources.

## What was asked

Two sources asked for this: [Issue 41](intent/issue-41.md) asks to "export the table as CSV", and [Issue 42](intent/issue-42.md) asks that "only admins can export".

## What to look at

1. **Export has no permission check** — *you decide* · *we ran it* · [details](#1-export-ignores-the-caller-s-role).
2. **Empty tables may export a blank file** — *check it* · *reasoned, not run* · [details](#2-an-empty-table-may-export-a-blank-file).

## Requirements

### Issue 41: CSV export

| Requirement and intent | Status | Behavior and evidence | Next action |
| --- | --- | --- | --- |
| Export the table as CSV ([issue 41](intent/issue-41.md)) | Met | Rows are joined into CSV ([export.py:5](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/export.py#L5)); recorded in [the run record](runs/record.md) | None |
| Include a header row ([issue 41](intent/issue-41.md)) | Unmet | No header is written ([export.py:5](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/export.py#L5)) | Add the header |

### Issue 42: Export permissions

| Requirement and intent | Status | Behavior and evidence | Next action |
| --- | --- | --- | --- |
| Only admins can export ([issue 42](intent/issue-42.md)) | Not verified | not verified: the permission path was not run | Run it as a non-admin |
| Large exports are handled | Needs clarification | intent unclear: the sources give no size limit; unknown | Ask the spec owner |

## Nobody asked for this

- **A download filename with a timestamp** — *nobody asked for this* ([export.py:4](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/export.py#L4)); neither source names the file.

## Possible bugs

### 1. Export ignores the caller's role
*we ran it* · *new in this change*

**Where:** [export.py:4](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/export.py#L4)
**Trigger:** a non-admin calls the export.

| | Base | Head |
| --- | --- | --- |
| Non-admin export result | refused | file returned |

**Who / impact:** any signed-in user can download the table ([export.py:4](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/export.py#L4)).
**Fix direction:** *Suggestion:* check the role before building the file.
**Reproduce:**
```sh
python runs/bugs/1/probe.py
```
Output: `head alive after overrides.clear(): True` · [script](runs/bugs/1/probe.py)

### 2. An empty table may export a blank file
*suspected, not run* · *from an unrelated commit*

**Where:** [export.py:5](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/export.py#L5)
**Trigger:** the table has no rows.
**Introduced by:** 3f2a9c1 (rewrite of the row formatter)

| | Base | Head |
| --- | --- | --- |
| Empty export | predicted: no file | predicted: a zero-byte file |

**Who / impact:** users exporting an empty table; predicted: they get a file that opens as nothing.
**Fix direction:** *Suggestion:* return a header-only file.
**Probe that would settle it:** export an empty table at base and head.

## Questions for the author

**Spec owner:**

- Should a size limit apply to large exports? See [Issue 42: Export permissions](#issue-42-export-permissions).

**Author:**

- Was the missing role check deliberate? See [Export ignores the caller's role](#1-export-ignores-the-caller-s-role).

## Verification

Tests inspected: none. Recorded runs: one. Executed: one probe.

| Check or scenario | Result | Evidence origin | Revision and configuration | Scope and limits |
| --- | --- | --- | --- | --- |
| [Export tests](runs/record.md) | Passed | Recorded run | bbbbbbb; synthetic | Fixture only |
| [Bug probes](#possible-bugs) | Failed | Executed here | bbbbbbb against aaaaaaa; one probe | An empty table export stays suspected |

## Evidence and record

### Gaps

This synthetic fixture establishes report shape only.

### Provenance

Synthetic test fixture, not an actual acceptance check or execution result. Sources: [Issue 41](intent/issue-41.md) and [Issue 42](intent/issue-42.md), collected 2026-10-16.

### Feature scope

[export.py](https://github.com/acme/widgets/blob/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/export.py): the traced entry point is `export_csv`; linked PR and commits: none; interaction leads: none found.

## Status and label key

These labels describe separate judgments. Read each against its stated scope and evidence; no label alone establishes overall readiness or approval.

### Key: Requirement fulfillment

| Option | Meaning |
| --- | --- |
| Met | Evidence supports the whole stated requirement within its conditions. Remaining evidence gaps must still be named. |
| Partial | Some required conditions hold; the report names the remainder. |
| Unmet | Evidence shows that a required condition fails. |
| Not verified | Intent is clear, but evidence is insufficient to decide whether the requirement holds. |
| Needs clarification | Intent is missing, ambiguous, or conflicting. Retain conflicting statements and label any candidate interpretation as inferred. |
| Not applicable | A recorded, agreed scope decision excludes the requirement; the report links that decision and gives the reason. |

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

### Key: Review actions

| Option | Meaning |
| --- | --- |
| you decide | A behavior or tradeoff needs a choice from the reviewer or author. |
| check it | Confirm a specific claim at the code or with a scoped run. |
| ask the author | The author needs to supply information or confirm a choice the available evidence cannot settle. |
| read lightly | Evidence covers the whole named part and its relevant preservation claim, so a lighter read is justified within that boundary. |
| no action | The report records a known point that requires no action today. This is not approval of the whole change. |

### Key: Review evidence labels

| Option | Meaning |
| --- | --- |
| we ran it | An executed run produced the stated observation or measurement within its recorded conditions. A retained earlier result keeps its original provenance and is identified as Recorded run in Verification. |
| read at the line | The claim follows the inspected, pinned source lines; this is not a runtime result. |
| documented | Quoted documentation or a recorded statement establishes intent, not implemented behavior. |
| reasoned, not run | An inference from named evidence and reasoning; the predicted behavior was not executed. |
| not read | The relevant source was not inspected. No behavior claim is established for that boundary. |
| unknown | Available evidence does not settle the claim. The report states what would settle it. |

### Key: Bug evidence

| Option | Meaning |
| --- | --- |
| we ran it | A probe observed the Head result, and the Base result when it could run. The command and output identify that run and its conditions. A retained earlier card uses Recorded run in Verification; an unobserved Base value starts with predicted:. |
| suspected, not run | The code suggests the bug, but no probe ran. The card's Base and Head values are predictions, and the card names the probe that would settle it. |

### Key: Bug origin

| Option | Meaning |
| --- | --- |
| new in this change | The bug is absent at the base and present at the head, so this change introduces it. The evidence label says whether that was run or predicted. |
| pre-existing, made worse | The bug already exists at the base; this change makes it reach more callers or makes its effect worse. |
| from an unrelated commit | Absent at the base and present at the head, introduced by a commit outside the feature's work that touched feature code. The card names that commit under Introduced by. |
| no base pinned | No base is pinned, so the card does not attribute an origin. Base cells read no base pinned; the head result is observed or predicted as the evidence chip says. |

### Key: Intent alignment

| Option | Meaning |
| --- | --- |
| matches the stated intent | Evidence supports the behavior described by the recorded intent within the stated scope. |
| partly matches the stated intent | Evidence supports only part of the recorded intent; the report names the mismatch or remaining gap. |
| contradicts the stated intent | Evidence shows behavior that conflicts with the recorded intent. |
| intent unclear | The intended behavior cannot be settled from the available statements or their conflicts. |
| nobody asked for this | The inspected intent sources do not establish this consequential behavior as requested. This does not by itself prove scope creep. |
