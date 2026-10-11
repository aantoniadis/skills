# Compare behavior and preservation

Use this reference with a concrete scenario, baseline, candidate, and evidence boundary. A planning candidate may be unimplemented; a review candidate is the selected head. The calling workflow owns the comparison and artifacts. Planning resolves desired behavior with the authorized decision maker. PR review compares delivered behavior with recorded intent and keeps unsupported author intent unresolved.

## Follow the consequence

Walk the same actor, request, or record through both flows. At each consequential difference trace **change → changed assumption or state → consumer interpretation → next action**. Follow shared producers and consumers past the modified function's return: how do callers recognize completion, refusal, partial success, or failure, and what do their checks, wrappers, or handlers do? When the change adds a **second consumer** of an existing producer, put the two consumers side by side: an output handled by one consumer but not another is a lead to inspect. Check the shared contract, effective behavior, and consequence. Intentional consumer-specific behavior can be valid; report a finding or ask for missing intent only when a material in-scope difference warrants it. Include relevant preparation, unchanged code, deferred work, asynchronous boundaries, and alternate entry points. For external callers, inspect the public contract and available usage examples; label inferred usage and its limits. Attach files, symbols, and inspected lines. Search hits alone do not establish impact.

Select scenarios from the consequential forks in the inspected flow: producer or wrapper mechanisms, consumer access patterns, input framing/timing/interruption, and existing state. Include the affected path's common configuration; a bare-component check cannot establish behavior through its usual wrappers. For example, pending authentication calls for inspecting consumers that equate a session with full authentication.

Expand combinations where their interaction can change the conclusion. Use a scenario matrix when it helps track those interactions, rather than crossing every axis by default. Record the evidence for each selected scenario: observed baseline, source-supported inference, demonstrated candidate, proposed outcome, or a named untested gap. An unimplemented planning candidate needs intended outcomes and remaining verification, not invented observations. Record changed and preserved behavior and the consumer's response. Distinguish a new defect, a pre-existing defect, and an old defect made consequential by the change using the same scenario at both snapshots.

For a propagation concern, establish the comparison set and shared expectation. Inspect effective behavior through inheritance, delegation, overrides, and configuration, including reasons for consumer-specific exceptions. An unchanged implementation that inherits the desired behavior is not an omission. Explain an actual effective-behavior difference and consequence before calling it a gap; unsettled desired behavior remains a question for the owner.

## Resolve factual uncertainty

State the predicted observable result, including the consumer's reaction, and what evidence would change the conclusion. Separate **baseline uncertainty** about today's behavior from **candidate uncertainty** about delivering the intended outcome. Inspect controlling code and reuse valid evidence first.

For remaining baseline uncertainty, use a focused existing test or isolated reproduction. For candidate uncertainty, exercise the relevant boundary with a focused test, isolated patch, or throwaway model within existing authorization. Identify unsettled choices assumed by the experiment. Choose fidelity for the question: a model cannot establish real-system integration. Tool setup earns its cost by resolving a named gap; use the caller's tool-recovery rules.

Tests are optional. Preserve necessary runs' runnable checks, original assumptions, results (including failure), revisions, configuration, and limits separately. Link later corrections rather than rewriting a run. Stop when the named question is answered; state the remaining gap and propose substantial experiments as further work.

Keep observed baseline, source-supported inference, demonstrated candidate behavior, model results, documented intent, and unverified assumptions distinct. A baseline failure is not proof of a candidate fix or a completed future acceptance test.

For negative or universal claims, identify the controlling invariant and relevant paths/configurations. A search with no matches or one passing case is insufficient. Narrow unsupported factual claims; retain any required broader guarantee with its evidence gap and verification work rather than narrowing the agreement.

Return the scenario's changed/preserved behavior, affected consumer's next action, supporting evidence and conditions, and open questions. Stop when these support an actionable explanation or explicit gap. A factual discovery does not settle desired behavior.
