---
kind: change-card
---
# Platinum tier: where it fits

**The change:** Add a platinum customer tier with a 15 percent loyalty discount.

**Fit:** It does not fit: the rate is decided in two files, so platinum would be added twice ([pricing.py:6](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/pricing.py#L6), [serializers.py:9](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/api/serializers.py#L9)).

**Choice:** Reshape first, then add the tier; the default, applied because nobody answered.

**Inspected source:** commit `eeeeeee` of the fictional `acme/shop`. **What ran:** `python3 -m unittest discover -s tests`, 3 passed.

> **Fictional example.** This card demonstrates the change-card template. Its shop, files, and runs are invented.

## Questions for the user

| Question | Why it matters | Default until answered | Answer |
| --- | --- | --- | --- |
| Reshape first, or add platinum in both places? | It decides the steps below. | Reshape first. | open |

## Corner cases

| Case | Reach and harm | What handling it bends | Options, cheapest first | Decision |
| --- | --- | --- | --- | --- |
| A customer upgraded to platinum while a quote is open: the quote showed the gold total, checkout charges the platinum total (seen in our probe). | Found by our probe; no known user meets it. The customer pays less than quoted, never more. | Storing the tier on each quote, a new stored field, and a branch at checkout. | Leave: checkout uses the tier at checkout, as for gold and silver today. Build in: store the tier with the quote, in `shop/quotes.py` and `shop/storage.py` (proposed). | open: leave (default) |

## Rules and owners

| Rule | Owner | Decided today in | After the change |
| --- | --- | --- | --- |
| Loyalty discount rate | [pricing.py:6](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/pricing.py#L6) | [pricing.py:6](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/pricing.py#L6), [serializers.py:9](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/api/serializers.py#L9) | proposed: `shop/pricing.py` only |

## Structure before and after

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

## Reshape first

1. Lock tests, proposed: record the discount the order JSON shows for gold and silver, and see each fail under a changed rate.
2. Gather, proposed, structural: make `serializers.py` call `loyalty_discount`; proof is the lock tests green.
3. The change, proposed: add `"platinum": Decimal("0.15")` to `RATES` in `pricing.py`.

## Placement

**Reuse:** `pricing.loyalty_discount` at [pricing.py:11](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/pricing.py#L11).

**Data and state:** none, proposed: the change adds a value to the existing rate table, which `pricing.py` alone writes.

**In scope:** proposed: `shop/pricing.py`, `shop/api/serializers.py`, and the tests. **Out of scope:** everything else.

**Failure behavior:** an unknown tier keeps getting no discount, as today at [pricing.py:13](https://github.com/acme/shop/blob/eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee/shop/pricing.py#L13).

## Limits

The quote path computes its own rate; it is behavior to decide in the rework map, not part of this change (not inspected here).

## Status and label key

These labels describe separate judgments. Read each against its stated scope and evidence; no label alone establishes overall readiness or approval.

### Key: Stated dependencies against the code

| Option | Meaning |
| --- | --- |
| as stated | The design allows the relationship and the extracted dependencies show it. The result is as complete as the dependency source named beside it. |
| not stated | The code has the relationship and the stated design does not allow it. It is drift or an intended relationship the design never recorded; the user's answer says which. |
| not found | The design names the relationship and no extracted dependency shows it. The dependency may run through something the source of the edges cannot see. |

### Key: Structure findings

| Option | Meaning |
| --- | --- |
| scattered rule | One rule is decided at more than one place, and nothing in the code says the places must change together. |
| misplaced logic | A decision is made away from the module that owns the state or rule it decides. |
| needless link | Pieces that change for different reasons are tied together. |
| surplus | Code with no reason of its own to exist, such as a wrapper that only delegates, an option nothing varies, or code nothing reaches. |
| shared mutable state | State that more than one module writes, or data a module changes after another module handed it over. What a value holds depends on every writer and the order they ran in. |
| shapeless data | Data passed between modules with no declared shape, such as a hash or dict, so each site that reads or writes a key decides part of it. |
| unjustified special case | Code for one situation with no caller, input, test, incident, or decision behind it. It stays until its removal has the evidence the map names. |
