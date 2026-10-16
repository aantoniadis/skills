---
head: {{head_sha}}
base: {{base_sha_or_remove_this_line_when_no_base_is_pinned}}
repository: {{owner}}/{{repo}}
---
# {{what_was_checked_as_a_short_statement}}

**Bottom line:** {{counts_by_status_blockers_and_first_action}}

**Reviewed:** {{head_base_or_no_base_and_collection_time}}. **Coverage:** {{sources_reached_and_missed_depth_and_material_gaps}}.

## What was asked

{{intent_sources_what_they_ask_for_and_the_feature_scope_each_cited}}

## What to look at

1. **{{attention_consequence}}** — *{{what_to_do}}* · *{{how_we_know}}*
   {{finding_and_decisive_evidence}}
   Look at: {{pinned_sources_and_comparison}}.
   Settle: {{question_that_decides_it}}
2. **{{bug_consequence}}** — *{{you_decide_or_check_it}}* · *{{we_ran_it_or_reasoned_not_run_matching_its_card}}* · [details](#{{card_heading_anchor}}).

## Requirements

### {{source_title}}

| Requirement and intent | Status | Behavior and evidence | Next action |
| --- | --- | --- | --- |
| {{quoted_requirement_with_its_source_link_or_labeled_inferred}} | {{fulfillment_status}} | {{pinned_source_run_record_or_bug_card_link_or_explicit_gap}} | {{action_or_none_with_reason}} |

## Nobody asked for this

- **{{delivered_behavior}}** — *nobody asked for this* ({{pinned_link}}); {{why_no_source_covers_it}}

{{or_none_found_paragraph_with_the_scope_inspected_in_place_of_the_list}}

## Possible bugs

{{not_run_or_no_bugs_found_paragraph_in_place_of_the_cards}}

### 1. {{bug_consequence}}
*we ran it* · *{{new_in_this_change_pre_existing_made_worse_from_an_unrelated_commit_or_no_base_pinned}}*

**Where:** {{pinned_lines}}
**Trigger:** {{input_configuration_or_caller_that_reaches_it}}
**Introduced by:** {{introducing_commit_sha_and_what_it_changed_for_an_unrelated_commit_else_remove_this_line}}

| | Base | Head |
| --- | --- | --- |
| {{compared_result}} | {{observed_at_base_or_predicted_when_the_base_could_not_run_or_exactly_no_base_pinned}} | {{observed_at_head}} |

**Who / impact:** {{affected_consumers_and_what_they_see_with_its_pinned_line_or_label}}
**Fix direction:** *Suggestion:* {{fix_direction}}
**Reproduce:**
```sh
{{exact_probe_command}}
```
Output: `{{output_excerpt}}` · {{link_to_the_probe_script_under_runs_bugs}}

### 2. {{suspected_bug_consequence}}
*suspected, not run* · *{{new_in_this_change_pre_existing_made_worse_from_an_unrelated_commit_or_no_base_pinned}}*

**Where:** {{pinned_lines}}
**Trigger:** {{input_configuration_or_caller_that_reaches_it}}
**Introduced by:** {{introducing_commit_sha_and_what_it_changed_for_an_unrelated_commit_else_remove_this_line}}

| | Base | Head |
| --- | --- | --- |
| {{compared_result}} | {{predicted_at_base_starting_with_predicted_or_exactly_no_base_pinned}} | predicted: {{predicted_at_head}} |

**Who / impact:** {{affected_consumers_and_what_they_see_with_its_pinned_line_or_label}}
**Fix direction:** *Suggestion:* {{fix_direction}}
**Probe that would settle it:** {{probe_to_run}}

## Questions for the author

**Spec owner:**

- {{question_for_the_spec_owner_with_its_evidence_link_or_none_with_reason}}

**Author:**

- {{question_for_the_feature_author_with_its_evidence_link_or_none_with_reason}}

## Verification

Tests inspected: {{assertions_and_limits_or_none}}. Recorded runs: {{applicability_or_none}}. Executed: {{checks_during_this_run_or_none}}.

| Check or scenario | Result | Evidence origin | Revision and configuration | Scope and limits |
| --- | --- | --- | --- | --- |
| {{check_and_link_to_run_record}} | {{result}} | {{origin}} | {{revision_configuration_or_explicit_unknown}} | {{what_this_establishes_and_leaves_open}} |
| [Bug probes](#possible-bugs) {{run_record_link_for_recorded_runs_or_executions_without_cards}} | {{result}} | {{origin}} | {{revision_and_configuration_inspected_or_probed}} | {{source_inspection_or_execution_scope_and_remaining_gaps}} |

## Evidence and record

### Gaps

{{unresolved_evidence_and_scope_limits_or_explicit_none}}

### Provenance

{{each_intent_source_with_its_collection_time_head_base_or_no_base_local_changes_and_configuration}}

### Feature scope

{{linked_prs_and_commits_traced_entry_points_interaction_leads_and_attribution_method}}

## Status and label key

{{generated_by_render_page_with_sync_labels}}
