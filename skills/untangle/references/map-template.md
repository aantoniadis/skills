---
kind: rework-map
---
# {{component}}: how it works today

**What it does:** {{capabilities_in_one_or_two_sentences_in_domain_words}}

**What differs from the stated design:** {{the_differences_that_matter_most_or_none_found_with_the_checked_scope}}

**Recommended rework:** {{recommended_target_and_its_reason_or_not_proposed_with_the_reason}}

**Scope:** {{paths_and_capabilities_included_and_excluded}}. **Inspected source:** {{revision_local_changes_and_configuration}}. **What ran:** {{baseline_command_result_and_run_record_link_or_the_obstruction}}.

## Questions for the user

| Question | Why it matters | Default until answered | Answer |
| --- | --- | --- | --- |
| {{question_only_a_person_can_answer}} | {{the_finding_target_or_step_it_decides}} | {{conservative_default_and_what_changes_under_the_other_answer}} | {{the_users_answer_with_its_date_or_not_answered}} |

## Capabilities

| Capability | Entry points | Decision sites | Evidence |
| --- | --- | --- | --- |
| {{capability_in_domain_words_linked_to_its_section_or_marked_not_stated_anywhere}} | {{pinned_entry_points}} | {{count_and_the_modules_that_hold_them_or_not_inspected_with_reason}} | {{kinds_of_evidence_taken_and_the_run_record}} |

### {{capability_name}}

{{what_it_does_for_which_consumer_with_evidence}}

{{one_list_item_per_decision_site_pinned_line_what_it_decides_and_the_kinds_of_evidence_that_found_it}}

{{where_two_sites_decide_the_same_rule_state_whether_they_agree_and_the_input_on_which_they_differ}}

{{repeat_for_each_inspected_capability}}

## Stated design and the code

{{source_of_the_stated_design_with_quotes_and_links_or_inferred_from_layout}}

| Relationship | Result | Evidence | What the user said |
| --- | --- | --- | --- |
| {{from_component_to_component}} | {{as_stated_not_stated_or_not_found}} | {{edge_source_command_and_the_decisive_file_edges_pinned}} | {{intended_drift_or_not_answered_default_applied}} |

## State and its writers

| State | Written by | Read by | Evidence |
| --- | --- | --- | --- |
| {{table_file_cache_global_or_field}} | {{pinned_writers}} | {{pinned_readers}} | {{search_command_or_run_and_its_limits}} |

## Main flows

{{one_diagram_per_main_flow_with_takeaway_evidence_label_and_source_map_per_EVIDENCE.md}}

## Special cases

| Special case | Kind | Reach | Why it exists | Points to |
| --- | --- | --- | --- | --- |
| {{pinned_line_and_what_it_handles}} | {{broad_handler_swallowed_error_default_early_return_retry_compatibility_path_or_single_caller_parameter}} | {{reached_not_reached_or_unknown_with_the_caller_probe_or_run}} | {{commit_ticket_or_user_answer_or_no_reason_found}} | {{missing_requirement_wrong_producer_implicit_boundary_real_outcome_or_nothing_found}} |

{{counts_per_file_of_defaults_and_early_returns_counted_and_not_inspected_one_by_one}}

## Findings

| Finding | Kind | Where | Cost today | Removed by |
| --- | --- | --- | --- | --- |
| {{consequence_as_a_short_name_linked_to_its_section}} | {{scattered_rule_misplaced_logic_needless_link_surplus_or_unjustified_special_case}} | {{pinned_lines}} | {{change_count_of_the_files_times_sites_one_change_touches_or_no_action_with_reason}} | {{link_to_the_target_or_kept_with_the_cost_that_decided_it}} |

### {{finding_name}}

{{what_is_decided_where_with_pinned_lines_the_evidence_that_confirms_it_and_what_it_costs_a_person_changing_this_code}}

{{short_decisive_excerpt_with_pinned_source_when_it_shows_the_problem}}

{{repeat_for_each_finding_in_rank_order}}

## Looks wrong, is fine

{{one_list_item_per_pattern_with_its_pinned_line_and_the_reason_from_history_or_the_user}}

## Targets

**Recommendation:** {{target_name_proposed_with_its_reason}}. **Chosen:** {{the_users_choice_with_its_date_or_open}}.

### {{target_name}}

**Owners:** {{proposed_one_module_per_rule_and_state}}.

**Interface:** {{proposed_signatures_or_types_callers_need}}.

**Guarantees at the boundary:** {{proposed_checks_made_once_and_the_inner_checks_by_line_that_become_unnecessary}}.

**Failure behavior:** {{proposed_per_fallback_cannot_occur_fails_loudly_or_real_outcome_and_the_questions_it_raises}}.

**Cost and risk:** {{proposed_files_call_sites_pins_to_write_and_what_can_go_wrong}}.

**Measure:** {{decision_sites_per_rule_before_and_proposed_after_and_relationships_that_become_as_stated}}.

### Leave it as it is

{{what_the_present_structure_costs_at_the_present_rate_of_change_with_evidence}}

{{repeat_for_each_target}}

## Rework steps

{{numbered_steps_for_the_chosen_or_recommended_target_each_proposed_structural_with_files_call_sites_pin_and_proof}}

{{behavior_changes_found_on_the_way_as_decisions_for_the_user_with_the_handoff}}

## Limits and open questions

{{capabilities_not_inspected_scenarios_not_run_edge_source_limits_history_depth_and_the_check_that_would_settle_each}}

## Evidence and record

{{baseline_and_probe_commands_script_outputs_run_records_and_provenance}}

## Status and label key

{{generated_by_render_page_with_sync_labels}}
