---
kind: rework-map
---
# {{component}}: what to fix, and how

## In short

**The problem:** {{the_structure_problem_that_costs_most_in_the_readers_terms_what_it_costs_and_its_evidence}}

**What we propose:** {{the_recommended_target_in_one_or_two_sentences_with_the_module_changes_and_what_protects_the_rework_proposed_or_leave_the_structure_as_it_is_with_the_reason}}

**What you decide:** {{each_decision_that_waits_for_the_user_in_one_line_with_its_default_or_none}}

**Scope:** {{paths_and_capabilities_included_and_excluded}}. **Inspected source:** {{revision_local_changes_and_configuration}}. **What ran:** {{baseline_command_result_and_run_record_link_or_the_obstruction}}.

{{when_nobody_answered_say_so_and_that_every_open_decision_is_marked_with_its_default}}

## What it does

{{one_sentence_this_is_the_behavior_the_rework_keeps_and_the_tests_that_verify_it}}

### {{feature_in_domain_words}}

- **{{behavior_as_a_short_name}}.** {{when_condition_then_result_as_a_consumer_sees_it_with_its_entry_point_pinned}} *Verified by:* {{tested_locked_or_untested_then_the_test_names_pinned_or_the_reason_none_protects_it}}

{{repeat_for_each_feature_and_behavior_in_the_users_order_of_importance}}

## How the code carries it

{{one_sentence_takeaway_how_many_behaviors_are_decided_in_more_than_one_file_then_a_behavior_map_fence_per_map_format}}

## Problems

### 1. {{the_problem_as_a_consequence_a_lead_understands}}

**Kind:** {{a_structure_kind_corner_case_or_behavior_to_decide}} · **How sure:** {{observed_source_or_inferred_with_what_ran_or_was_read}} · **Cost today:** {{what_it_costs_each_change_or_each_user_with_its_evidence}}

**What is wrong:** {{what_happens_and_why_it_hurts_with_pinned_lines_and_runs_in_as_many_paragraphs_as_it_needs}}

{{a_structure_focus_fence_naming_the_rules_and_files_of_this_problem_and_or_a_change_history_fence_when_history_shows_it}}

**Evidence:**

{{the_decisive_excerpts_as_fences_with_url_side_by_side_then_runs_and_searches_as_a_list}}

**Proposed fix:** {{what_changes_to_remove_it_proposed_or_the_handoff_for_behavior_to_decide}}

**Cost and risk:** {{files_call_sites_lock_tests_and_what_can_go_wrong_proposed}}

**What you get:** {{the_measure_before_and_after_such_as_decision_sites_for_the_rule_proposed}}

**Other options:**

- **Leave it:** {{what_the_problem_keeps_costing_at_its_present_rate_with_evidence}}
- **{{another_option}}:** {{what_it_changes_and_costs_and_why_it_is_not_recommended}}

**Decision:** {{open_default_applied_decided_or_none_needed_then_the_recommendation_and_what_holds_until_answered_or_the_answer_with_its_date}}

{{repeat_for_each_problem_in_rank_order_structure_problems_by_cost_first_and_behavior_to_decide_last}}

## The plan

**Recommended:** {{target_name_proposed_with_its_reason}}. **Chosen:** {{the_users_choice_with_its_date_or_open}}.

{{one_sentence_takeaway_with_its_evidence_kind_then_the_structure_view_fence_per_map_format}}

### {{recommended_target_name}}

**Owners:** {{proposed_one_module_per_rule_and_state}}.

**Interface:** {{proposed_signatures_or_types_callers_need}}.

**Guarantees at the boundary:** {{proposed_checks_made_once_and_the_inner_checks_by_line_that_become_unnecessary}}.

**Data and state:** {{proposed_named_value_with_its_fields_built_once_and_not_changed_the_one_writer_of_each_state_and_the_defaults_that_become_unnecessary}}.

**Flow:** {{proposed_the_one_direction_calls_and_state_move_in_the_order_of_the_parts_and_the_back_edges_the_target_removes}}.

**Failure behavior:** {{proposed_per_fallback_cannot_occur_fails_loudly_or_real_outcome}}.

**Measure:** {{decision_sites_per_rule_before_and_proposed_after_and_stated_dependencies_and_rules_that_become_true}}.

### Module changes

- **{{Rename_Remove_Merge_Split_or_Move}}** {{the_modules_and_what_they_become_proposed}}: {{the_reason_and_the_problems_it_removes}}

### Lock tests

{{one_list_item_per_lock_test_name_and_file_the_behavior_it_locks_marked_when_it_records_a_value_under_decision_the_break_it_failed_under_and_the_suite_run_that_passed}}

{{behaviors_on_the_list_without_a_lock_test_and_the_reason}}

### Steps

{{numbered_steps_for_the_chosen_or_recommended_target_each_proposed_structural_with_files_call_sites_pin_and_proof}}

{{steps_that_wait_for_an_open_answer_named_with_the_problem_that_decides_them}}

### Other questions

{{questions_only_a_person_can_answer_that_no_problem_holds_each_with_what_it_decides_its_default_and_the_answer_or_open}}

## What is sound

{{what_works_and_should_be_kept_with_its_evidence_and_what_looks_wrong_and_is_fine_with_the_reason_from_history_or_the_user}}

## How it works today

### Deliberate breaks

{{one_list_item_per_deliberate_break_what_was_changed_at_which_pinned_line_the_tests_run_whether_any_turned_red_and_the_run_record}}

### Stated design and the code

{{source_of_the_stated_design_with_links_or_inferred_from_layout}}

| Relationship | Result | Evidence | What the user said |
| --- | --- | --- | --- |
| {{from_component_to_component}} | {{as_stated_not_stated_or_not_found}} | {{edge_source_command_and_the_decisive_file_edges_pinned}} | {{intended_drift_or_open}} |

| Stated rule | Result | Evidence | What the user said |
| --- | --- | --- | --- |
| {{the_rule_quoted_with_its_link}} | {{holds_broken_or_not_checked}} | {{the_search_or_run_that_covers_it_or_the_pinned_line_or_run_that_breaks_it}} | {{intended_drift_or_open}} |

### State and data

{{each_piece_of_state_with_its_pinned_writers_and_readers_and_each_piece_of_shapeless_data_with_where_it_is_built_and_the_signs_in_prose_or_one_sentence_with_its_search_when_the_scope_keeps_none}}

### Main flows

{{one_diagram_per_main_flow_with_takeaway_evidence_label_and_source_map_per_EVIDENCE.md_and_which_steps_a_run_executed}}

### Special cases

| Special case | Kind | Reach | Why it exists | Points to |
| --- | --- | --- | --- | --- |
| {{pinned_line_and_what_it_handles}} | {{broad_handler_error_turned_into_a_value_default_early_return_retry_status_or_version_branch_compatibility_path_or_single_caller_parameter}} | {{reached_not_reached_or_unknown_with_the_caller_probe_or_run}} | {{commit_ticket_or_user_answer_or_no_reason_found}} | {{missing_requirement_wrong_producer_implicit_boundary_real_outcome_nothing_found_or_the_problem_that_holds_it}} |

{{counts_per_kind_and_file_of_the_leads_counted_and_not_inspected_one_by_one}}

## After the rework

{{only_in_a_follow_up_after_the_rework_landed_one_line_per_measure_before_now_and_met_or_not_met_with_the_run_else_remove}}

## Limits

{{capabilities_partly_or_not_inspected_scenarios_not_run_leads_not_followed_edge_source_limits_history_depth_and_the_check_that_would_settle_each}}

## Evidence and record

{{baseline_and_probe_commands_script_outputs_run_records_and_provenance}}

## Status and label key

{{generated_by_render_page_with_sync_labels}}
