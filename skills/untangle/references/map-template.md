---
kind: rework-map
---
# {{component}}: how it works today

**What it does:** {{capabilities_in_one_or_two_sentences_in_domain_words}}

**What differs from the stated design:** {{the_differences_that_matter_most_with_counts_of_dependencies_and_rules_checked_or_none_found}}

**Recommended rework:** {{recommended_target_proposed_with_its_reason_or_leave_the_structure_as_it_is_with_the_reason}}

**Scope:** {{paths_and_capabilities_included_and_excluded}}. **Inspected source:** {{revision_local_changes_and_configuration}}. **What ran:** {{baseline_command_result_and_run_record_link_or_the_obstruction}}.

{{when_nobody_answered_say_so_and_that_every_open_question_is_marked_with_its_default}}

## Behavior to decide

| What happens | Evidence | Handoff |
| --- | --- | --- |
| {{behavior_that_may_be_wrong_or_unwanted_in_the_consumers_terms}} | {{pinned_lines_and_the_run_that_shows_it}} | {{fix_bug_or_plan_change_and_the_question_that_decides_it}} |

## Questions for the user

| Question | Why it matters | Default until answered | Answer |
| --- | --- | --- | --- |
| {{question_only_a_person_can_answer}} | {{the_finding_target_or_step_it_decides}} | {{conservative_default_and_what_changes_under_the_other_answer}} | {{the_users_answer_with_its_date_or_open}} |

## Capabilities

| Capability | Entry points | Decision sites | Evidence |
| --- | --- | --- | --- |
| {{capability_in_domain_words_linked_to_its_section_or_marked_not_stated_anywhere}} | {{pinned_entry_points}} | {{count_and_the_modules_that_hold_them_or_partly_or_not_inspected_with_reason}} | {{kinds_of_evidence_taken_and_the_run_record}} |

### {{capability_name}}

{{what_it_does_for_which_consumer_with_evidence}}

{{one_list_item_per_decision_site_pinned_line_what_it_decides_and_a_mark_when_only_one_kind_of_evidence_found_it}}

{{where_two_sites_decide_the_same_rule_state_whether_they_agree_and_the_input_on_which_they_differ}}

{{repeat_for_each_inspected_capability}}

## Behavior no test protects

{{one_list_item_per_deliberate_break_that_left_every_test_green_what_was_changed_at_which_pinned_line_the_tests_run_and_the_run_record}}

{{the_breaks_that_turned_a_test_red_in_one_sentence_with_the_run_record}}

## Stated design and the code

{{source_of_the_stated_design_with_links_or_inferred_from_layout}}

| Relationship | Result | Evidence | What the user said |
| --- | --- | --- | --- |
| {{from_component_to_component}} | {{as_stated_not_stated_or_not_found}} | {{edge_source_command_and_the_decisive_file_edges_pinned}} | {{intended_drift_or_open}} |

{{modules_the_design_does_not_name_with_their_edges}}

| Stated rule | Result | Evidence | What the user said |
| --- | --- | --- | --- |
| {{the_rule_quoted_with_its_link}} | {{holds_broken_or_not_checked}} | {{the_search_or_run_that_covers_it_or_the_pinned_line_or_run_that_breaks_it}} | {{intended_drift_or_open}} |

## State and data

{{one_sentence_with_its_search_when_the_scope_keeps_no_state_of_its_own_and_passes_only_declared_values_else_the_tables}}

| State | Written by | Read by | Evidence |
| --- | --- | --- | --- |
| {{table_file_cache_global_class_variable_or_field}} | {{pinned_writers}} | {{pinned_readers}} | {{search_command_or_run_and_its_limits}} |

| Data and key | Built or written at | Read at | Signs |
| --- | --- | --- | --- |
| {{the_hash_dict_or_object_and_one_key_of_it}} | {{pinned_sites_that_build_it_or_write_the_key}} | {{pinned_readers_and_the_default_each_supplies}} | {{written_in_several_files_read_with_a_default_defaults_differ_or_changed_after_handover_with_the_freeze_run}} |

## Structure today and proposed

{{one_sentence_takeaway_with_its_evidence_kind_then_a_structure_view_fence_per_map_format}}

## Main flows

{{one_diagram_per_main_flow_with_takeaway_evidence_label_and_source_map_per_EVIDENCE.md_and_which_steps_a_run_executed}}

## Special cases

| Special case | Kind | Reach | Why it exists | Points to |
| --- | --- | --- | --- | --- |
| {{pinned_line_and_what_it_handles}} | {{broad_handler_error_turned_into_a_value_default_early_return_retry_status_or_version_branch_compatibility_path_or_single_caller_parameter}} | {{reached_not_reached_or_unknown_with_the_caller_probe_or_run}} | {{commit_ticket_or_user_answer_or_no_reason_found}} | {{missing_requirement_wrong_producer_implicit_boundary_real_outcome_or_nothing_found}} |

{{counts_per_kind_and_file_of_the_leads_counted_and_not_inspected_one_by_one}}

## Findings

| Finding | Kind | Where | Cost today | Removed by |
| --- | --- | --- | --- | --- |
| {{consequence_as_a_short_name_linked_to_its_section}} | {{scattered_rule_misplaced_logic_needless_link_surplus_shared_mutable_state_shapeless_data_or_unjustified_special_case}} | {{pinned_lines}} | {{sites_one_change_to_the_rule_touches_and_how_often_the_rule_changed_or_no_action_with_reason}} | {{link_to_the_target_or_kept_with_the_cost_that_decided_it}} |

### {{finding_name}}

{{what_is_decided_where_with_pinned_lines_the_evidence_that_confirms_it_and_what_it_costs_a_person_changing_this_code}}

{{short_decisive_excerpt_with_pinned_source_when_it_shows_the_problem}}

{{repeat_for_each_finding_in_rank_order}}

## Looks wrong, is fine

{{one_list_item_per_pattern_with_its_pinned_line_and_the_reason_from_history_or_the_user}}

## Targets

**Recommendation:** {{target_name_proposed_with_its_reason}}. **Chosen:** {{the_users_choice_with_its_date_or_open}}.

### {{recommended_target_name}}

**Owners:** {{proposed_one_module_per_rule_and_state}}.

**Interface:** {{proposed_signatures_or_types_callers_need}}.

**Guarantees at the boundary:** {{proposed_checks_made_once_and_the_inner_checks_by_line_that_become_unnecessary}}.

**Data and state:** {{proposed_named_value_with_its_fields_built_once_and_not_changed_the_one_writer_of_each_state_and_the_defaults_that_become_unnecessary}}.

**Failure behavior:** {{proposed_per_fallback_cannot_occur_fails_loudly_or_real_outcome}}.

**Cost and risk:** {{proposed_files_call_sites_pins_to_write_and_what_can_go_wrong}}.

**Measure:** {{decision_sites_per_rule_before_and_proposed_after_and_stated_dependencies_and_rules_that_become_true}}.

### Leave it as it is

{{what_the_present_structure_costs_at_the_present_rate_of_change_with_evidence_and_what_is_still_worth_doing}}

{{each_further_alternative_in_a_few_sentences_what_it_changes_what_it_costs_and_why_it_is_not_recommended}}

## Lock tests

| Lock test | Behavior it locks | Failed under | Suite |
| --- | --- | --- | --- |
| {{test_name_and_file}} | {{behavior_in_domain_words_and_marked_when_it_records_a_value_under_decision}} | {{the_break_and_the_run_record_that_showed_it_red}} | {{the_suite_run_that_passed_on_the_code_as_it_is}} |

{{behaviors_on_the_list_without_a_lock_test_and_the_reason}}

## Rework steps

{{numbered_steps_for_the_chosen_or_recommended_target_each_proposed_structural_with_files_call_sites_pin_and_proof}}

{{steps_that_wait_for_an_open_answer_named_with_the_question}}

## After the rework

{{only_in_a_follow_up_after_the_rework_landed_one_line_per_measure_before_now_and_met_or_not_met_with_the_run_else_remove}}

## Limits and open questions

{{capabilities_partly_or_not_inspected_scenarios_not_run_leads_not_followed_edge_source_limits_history_depth_and_the_check_that_would_settle_each}}

## Evidence and record

{{baseline_and_probe_commands_script_outputs_run_records_and_provenance}}

## Status and label key

{{generated_by_render_page_with_sync_labels}}
