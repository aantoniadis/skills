---
kind: change-card
---
# Platinum tier: where it fits

## In short

**The problem:** Adding a platinum tier at 15 percent means adding it twice, because the loyalty rate is decided in `pricing` and again in the API serializer ([pricing.py:6](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/pricing.py#L6), [serializers.py:9](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/api/serializers.py#L9)).

**What we propose:** Make the serializer call `pricing` first, then add platinum once, to the rate table. Two files change before the tier, and none of today's totals move (proposed).

**What you decide:** Reshape first, or add platinum in both places; reshape first is applied as the default. Whether a quote keeps the tier it was made with: open, and checkout keeps using the tier at checkout.

**Inspected source:** commit `eeeeeee` of the fictional `acme/shop`. **What ran:** `python3 -m unittest discover -s tests`, 3 passed.

> **Fictional example.** This card demonstrates the change-card template. Its shop, files, and runs are invented.

## Problems

### 1. The new tier would have to be added in two places

**Kind:** scattered rule · **How sure:** source, read at the lines · **Cost today:** 2 files for every rate change

**What is wrong:** The API serializer recomputes the discount for display with its own `if tier == ...` chain instead of asking `pricing`. Platinum added only to the rate table would charge 15 percent and display no discount (source, at the pinned lines).

```structure-focus
{"rules": ["Loyalty discount rate"]}
```

**Evidence:**

```python url="https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/pricing.py#L6"
RATES = {"gold": Decimal("0.10"), "silver": Decimal("0.05")}
```

```python url="https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/api/serializers.py#L9-L11"
if tier == "gold":
    discount = subtotal * Decimal("0.10")
elif tier == "silver":
```

**Proposed fix:** Reshape first: the serializer calls `pricing.loyalty_discount`, then platinum goes into the rate table once. The steps are in [the plan](#the-plan).

**Cost and risk:** 2 files and 1 call site before the tier; a lock test on the displayed discount comes first (proposed).

**What you get:** the tier, and every later rate, is one line in one file (proposed).

**Other options:**

- **Patch:** add platinum to the rate table and to the serializer's chain. The rule then has two places for every later change (proposed).

**Decision:** default applied: reshape first, because nobody answered. Say "patch" to add the tier in both places instead.

### 2. A customer upgraded while a quote is open pays less than quoted

**Kind:** corner case · **How sure:** observed, in our probe · **Cost today:** none known: found by our probe; no known user meets it

**What is wrong:** A customer upgraded to platinum while a quote is open is quoted the gold total and charged the platinum total. They pay less than quoted, never more (observed, in our probe).

**Proposed fix:** Leave it: checkout uses the tier at checkout, as it does for gold and silver today.

**Cost and risk:** none.

**Other options:**

- **Build in:** store the tier with each quote and branch on it at checkout: a new stored field in `shop/storage.py` and a branch in `shop/quotes.py` (proposed).

**Decision:** open. Recommended: leave it. Until you answer, checkout uses the tier at checkout.

## The plan

The display copy of the rate moves to its owner (source, at the pinned lines in the data; proposed after the change).

```structure-view
{
 "labels": {
  "today": "Before",
  "proposed": "After the change"
 },
 "parts": [
  {
   "id": "api",
   "label": "API",
   "said": "only translates requests"
  },
  {
   "id": "pricing",
   "label": "Pricing",
   "said": "every price is decided here"
  }
 ],
 "files": [
  {
   "id": "serializers",
   "path": "shop/api/serializers.py",
   "part": "api"
  },
  {
   "id": "pricing",
   "path": "shop/pricing.py",
   "part": "pricing"
  }
 ],
 "dependencies": [
  {
   "from": "serializers",
   "to": "pricing",
   "today": null,
   "proposed": "as stated",
   "at": "proposed: the serializer calls loyalty_discount",
   "why": "Gathers the display copy."
  }
 ],
 "rules": [
  {
   "name": "Loyalty discount rate",
   "owner": "pricing",
   "outcome": "moves",
   "note": "The platinum rate is added once, in pricing.",
   "sites": [
    {
     "file": "pricing",
     "at": "shop/pricing.py:6",
     "what": "RATES table"
    },
    {
     "file": "serializers",
     "at": "shop/api/serializers.py:9",
     "what": "its own if/elif on the tier"
    }
   ]
  }
 ]
}
```

**Rules and owners:** the loyalty rate is owned by [pricing.py:6](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/pricing.py#L6); it is decided there and at [serializers.py:9](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/api/serializers.py#L9) today, and only in `shop/pricing.py` after the change (proposed).

**Reuse:** `pricing.loyalty_discount` ([pricing.py:9](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/pricing.py#L9)).

**New units:** none.

**Data and state:** none added.

**In scope:** proposed: `shop/pricing.py`, `shop/api/serializers.py`, `tests/test_shop.py`. **Out of scope:** everything else.

**Failure behavior:** the change meets no new failure: an unknown customer still gets no discount ([pricing.py:11](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/pricing.py#L11)).

### Steps

1. Lock, proposed: a test that the order JSON shows a 4.00 discount for a gold 40.00 basket, seen failing with the serializer's rate changed.
2. Reshape, proposed: the serializer calls `pricing.loyalty_discount`; the lock test stays green.
3. Change, proposed: add `"platinum": Decimal("0.15")` to the rate table, with a test.

## Limits

Read: 3 of 3 files the change touches. The quote path computes its own rate; it is behavior to decide in the rework map, not part of this change (not inspected here).

## Status and label key

These labels describe separate judgments. Read each against its stated scope and evidence; no label alone establishes overall readiness or approval.

### Key: Stated dependencies against the code

| Option | Meaning |
| --- | --- |
| as stated | The design allows the relationship and the extracted dependencies show it. The result is as complete as the dependency source named beside it. |
| not stated | The code has the relationship and the stated design does not allow it. It is drift or an intended relationship the design never recorded; the user's answer says which. |
| not found | The design names the relationship and no extracted dependency shows it. The dependency may run through something the source of the edges cannot see. |

### Key: Kinds of problem

| Option | Meaning |
| --- | --- |
| scattered rule | One rule is decided at more than one place, and nothing in the code says the places must change together. |
| misplaced logic | A decision is made away from the module that owns the state or rule it decides. |
| needless link | Pieces that change for different reasons are tied together. |
| two-way flow | Calls or state move in both directions between parts: a cycle of dependencies, a call against the order of the parts, or a callback, event, or shared object through which a later step writes back into an earlier one. A reader can no longer follow the code in one direction. |
| surplus | Code with no reason of its own to exist, such as a wrapper that only delegates, an option nothing varies, or code nothing reaches. |
| shared mutable state | State that more than one module writes, or data a module changes after another module handed it over. What a value holds depends on every writer and the order they ran in. |
| shapeless data | Data passed between modules with no declared shape, such as a hash or dict, so each site that reads or writes a key decides part of it. |
| unjustified special case | Code for one situation with no caller, input, test, incident, or decision behind it. It stays until its removal has the evidence the map names. |
| corner case | A rare input or state whose handling would bend the design. Whether it is worth that complexity is the developer's decision, weighed on its reach, harm, and options. |
| behavior to decide | What the code does may be wrong or unwanted, such as two places that give different results for one input. It is not a structure problem; its fix is a behavior change that someone decides. |

### Key: How sure

| Option | Meaning |
| --- | --- |
| observed | A run showed it: a test, a probe, or a deliberate break, recorded with its command. |
| source | Read at the pinned lines, and in the history where the problem says so. No run showed it. |
| inferred | Concluded from the code's names, layout, or comments, or from evidence that does not settle it. A run or a read of the lines named would. |

### Key: Decisions

| Option | Meaning |
| --- | --- |
| open | Waits for your answer. The problem says what holds until then. |
| default applied | Nobody answered, so the recommended default was applied. Say otherwise and it changes. |
| decided | Settled by your answer, with its date, or by a policy you authorized. |
| none needed | The problem needs no decision from you; its fix follows from the evidence. |
