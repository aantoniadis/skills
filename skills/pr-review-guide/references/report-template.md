---
base: {{merge_base_sha}}
head: {{head_sha}}
repository: {{owner}}/{{repo}}
---
# {{title}}

**Bottom line:** {{supported_conclusion_blockers_decisions_and_first_action}}

**Reviewed:** {{head_base_and_merge_base}}. **Coverage:** {{review_depth_and_consequential_gaps}}.

## What the change does

{{problem_intent_observable_change_contract_tradeoff_and_evidence}}

## Terms

{{terms_if_needed}}

## What to look at

1. **{{attention_consequence}}** — *{{what_to_do}}* · *{{how_we_know}}*
   {{change_consequence_and_decisive_evidence}}
   Look at: {{pinned_sources_and_comparison}}.
   Settle: {{question_that_decides_it}}
2. **{{bug_consequence}}** — *{{you_decide_or_check_it}}* · *{{we_ran_it_or_reasoned_not_run_matching_its_card}}* · [details](#{{card_heading_anchor}}).

## Possible bugs

{{not_run_or_no_bugs_found_paragraph_in_place_of_the_cards}}

### 1. {{bug_consequence}}
*we ran it* · *{{new_in_this_change_or_pre_existing_made_worse}}*

**Where:** {{pinned_lines}}
**Trigger:** {{input_configuration_or_caller_that_reaches_it}}

| | Base | Head |
| --- | --- | --- |
| {{compared_result}} | {{observed_at_base_or_predicted_when_the_base_could_not_run}} | {{observed_at_head}} |

**Who / impact:** {{affected_consumers_and_what_they_see_with_its_pinned_line_or_label}}
**Fix direction:** *Suggestion:* {{fix_direction}}
**Reproduce:**
```sh
{{exact_probe_command}}
```
Output: `{{output_excerpt}}` · {{link_to_the_probe_script_under_runs_bugs}}

### 2. {{suspected_bug_consequence}}
*suspected, not run* · *{{new_in_this_change_or_pre_existing_made_worse}}*

**Where:** {{pinned_lines}}
**Trigger:** {{input_configuration_or_caller_that_reaches_it}}

| | Base | Head |
| --- | --- | --- |
| {{compared_result}} | predicted: {{predicted_at_base}} | predicted: {{predicted_at_head}} |

**Who / impact:** {{affected_consumers_and_what_they_see_with_its_pinned_line_or_label}}
**Fix direction:** *Suggestion:* {{fix_direction}}
**Probe that would settle it:** {{probe_to_run_at_base_and_head}}

## Requirements

| Requirement and intent | Status | Behavior and evidence | Next action |
| --- | --- | --- | --- |
| {{quoted_requirement_and_source_or_explicitly_inferred_candidate}} | {{fulfillment_status}} | {{link_to_named_behavior_and_support_or_gap}} | {{action_or_none_with_reason}} |

{{consequential_delivered_behavior_with_unclear_or_conflicting_intent}}

## Reading plan

{{reading_priority_by_consequence_with_skip_reasons_when_more_than_eight_files_change}}

## Behavior changes

### {{part_name}}

{{fill_behavior_template_for_each_consequential_part_or_state_no_behavior_change_with_scope_and_evidence}}

## Questions for the author

{{questions_with_evidence_links_or_none_with_reason}}

## Verification

Tests inspected: {{assertions_and_limits_or_none}}. Recorded runs: {{applicability_or_none}}. Executed: {{checks_during_this_review_or_none}}.

| Check or scenario | Result | Evidence origin | Revision and configuration | Scope and limits |
| --- | --- | --- | --- | --- |
| {{check_and_link_to_run_record_or_named_behavior}} | {{result}} | {{origin}} | {{revision_configuration_or_explicit_unknown}} | {{what_this_establishes_and_leaves_open}} |
| [Bug probes](#possible-bugs) {{run_record_link_for_recorded_runs_or_executions_without_cards}} | {{result}} | {{origin}} | {{revision_and_configuration_inspected_or_probed}} | {{source_inspection_or_execution_scope_and_remaining_gaps}} |

## Evidence and record

### Gaps

{{unresolved_evidence_and_scope_limits_or_explicit_none}}

### Changed files

{{files_with_part_and_read_status_unless_reading_plan_covers_them}}

### Provenance

{{head_base_merge_base_times_sources_local_changes_and_prior_reviews}}

## Status and label key

{{generated_by_render_page_with_sync_labels}}
