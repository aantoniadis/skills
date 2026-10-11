# Fictional order-confirmation record

Every fact, decision, and revision in this record is invented for presentation testing. It describes no application and records no real user agreement or execution.

Current snapshot: sample-current. A caller sends an order ID to the confirmation handler; the handler uses the order store and event bus. This model covers one nonempty order processed by one request at a time.

For a pending order with enough stock, the handler asks the store to reserve every line. The store reports successful reservation of all lines before the handler continues.

If stock is unavailable, the store rejects the reservation. In this model the order remains pending, the caller receives a stock error, and no confirmation event is published. Partial reservation rollback is not modeled.

After successful reservation, the handler changes the stored order to confirmed. It then asks the event bus to publish order.confirmed and returns the confirmed order ID to the caller after publication succeeds.

The current model has no already-confirmed guard: a later request for a confirmed order attempts reservation and event publication again. Whether that duplicate attempt succeeds against a real inventory system is unknown.

Publication failure after the state write, simultaneous requests, client timeouts, and downstream delivery are not modeled. The current trace establishes no atomicity, exactly-once delivery, or cleanup guarantee.

Fictional intent: "A repeated confirmation of a confirmed order returns its existing ID without another reservation or confirmation event."

Fictional decision record, iteration 1: Agreed, by the sample product owner — inspect stored confirmation state first; return the existing ID when already confirmed. Keep the pending-order successful path unchanged. This addresses sequential repeated requests only.

Fictional decision record, iteration 1: Agreed, by the sample product owner — preserve the stock-unavailable outcome for pending orders: pending state, stock error, no confirmation event. Partial reservation rollback remains outside this model and requires investigation before real implementation.

Fictional decision record, iteration 2: Open — simultaneous confirmations need a choice between locking and an atomic state transition. No choice, retry contract, or concurrency guarantee is agreed.

Fictional candidate, iteration 2: Proposed — use an outbox for publication recovery. No agreement or experiment supports this candidate yet; transaction boundaries and consumer deduplication remain unknown.

No implementation or tests exist for the planned change in this sample. Proposed checks: first confirmation reserves once and publishes once; a sequential repeat returns the same ID with no extra reserve or publish call; stock rejection leaves the order pending with no publish call.

Planning scope: a draft for repeat-safe confirmation. Production handoff is blocked by unresolved concurrency and publication-recovery behavior, and by uninspected partial reservation rollback. A local sequential model can be explored separately; it is not authorization for production work.
