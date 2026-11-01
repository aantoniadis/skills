# {{symptom_in_domain_terms}}

**Verdict:** {{symptom_contract_cause_and_fix_state_in_one_paragraph_with_the_deciding_pins_and_the_run_record_link}}

**Checked:** *{{reproduced_or_not_reproduced}}* · *{{fixed_fix_proposed_or_no_fix_proposed}}* · *{{test_red_then_green_test_not_verified_or_no_test_seam}}* · *{{origin_checked_or_origin_skipped}}*, {{reason_or_result}} · *{{reach_checked_or_reach_skipped}}*, {{reason_or_result}} · *{{consequence_checked_or_consequence_skipped}}*, {{reason_or_result}}. **Inspected source:** {{commit_or_saved_local_snapshot_and_configuration}}; see [evidence and record](#evidence-and-record).

## Symptom and contract

{{the_reported_symptom_quoted_from_its_source_then_what_should_happen_with_its_quoted_or_pinned_source_then_the_verdict_bug_or_works_as_specified_or_behavior_decision_open}}

## Reproduction

{{one_sentence_naming_the_loop_and_how_many_times_it_ran_with_the_run_record_link}}

```sh
{{exact_loop_command}}
```

Output: `{{output_excerpt}}` · {{link_to_the_saved_script_under_runs_bugs}}

| Criterion | Evidence |
| --- | --- |
| Red on the exact symptom | {{how_the_output_matches_the_reported_symptom_with_the_run_link}} |
| Deterministic | {{runs_and_rate_recorded_or_the_pinned_conditions}} |
| Fast | {{measured_duration}} |
| Runs unattended | {{how_it_ran_without_a_human_or_the_hitl_script_used}} |

{{what_was_cut_during_minimisation_and_what_stayed_load_bearing_with_the_run_link_or_the_artifacts_only_branch_with_what_was_tried}}

## Cause

{{one_sentence_saying_what_the_pinned_lines_do_wrong}}

```{{language}} url="{{pinned_source_link}}"
{{decisive_excerpt_exact_whitespace}}
```

### 1. {{cause_named_by_what_it_says}}
*{{we_ran_it_or_suspected_not_run}}* · *{{regression_always_broken_or_origin_not_checked}}*

**Where:** {{pinned_lines_and_the_symbol}}.

**Trigger:** {{input_timing_configuration_or_caller_that_reaches_it_with_its_observation_or_pin}}.

**Who / impact:** {{affected_consumers_and_what_they_see_with_the_quote_pin_or_label}}.

| | Before the fix | After the fix |
| --- | --- | --- |
| {{compared_result}} | {{observed_or_inferred_before}} | {{observed_after_or_proposed_when_no_fix_landed}} |

## Hypotheses

| Hypothesis | Prediction | Probe | Verdict |
| --- | --- | --- | --- |
| {{hypothesis_named_by_what_it_says}} | {{if_it_is_the_cause_then_this_changes_the_loop}} | {{probe_command_or_not_run}} | {{supported_contradicted_with_counterevidence_or_unresolved_with_the_missing_check}} |

## Origin

{{bisection_result_and_the_breaking_commit_with_its_quoted_intent_and_the_revert_or_forward_fix_choice_or_skipped_with_the_reason}}

## Reach

| Caller | Line | Result | Evidence |
| --- | --- | --- | --- |
| {{caller_or_path}} | {{pinned_line}} | {{fixed_affected_and_unfixed_or_cleared}} | {{counterevidence_pin_or_run_link}} |

{{or_skipped_with_the_reason_such_as_one_caller_and_no_copied_pattern}}

## Fix and regression test

{{applied_or_proposed_fix_with_its_pin_or_why_no_fix_was_attempted}}

```diff
{{unified_diff_when_available_otherwise_remove_this_fence}}
```

{{the_regression_test_its_seam_actual_runs_and_missing_checks_with_run_links_or_no_correct_seam_recorded_as_a_finding}}

## Verification

| Check or scenario | Result | Evidence origin | Revision and configuration | Scope and limits |
| --- | --- | --- | --- | --- |
| {{check_name_linked_to_its_run_record}} | {{Passed_Failed_Mixed_Not_run_or_Blocked}} | {{Executed_here_Recorded_run_Source_inspected_or_Proposed}} | {{revision_and_configuration}} | {{what_this_establishes_and_leaves_open}} |

## Consequence

{{other_consumers_of_what_the_fix_changed_compared_through_their_next_action_with_evidence_or_skipped_with_the_reason}}

## Limits and next steps

- {{consequential_unknown_and_the_check_that_would_settle_it}}
- {{instrumentation_and_throwaway_files_removed_or_what_remains_and_where}}

{{fix_state_then_the_next_command_or_the_evidence_or_authorization_needed_to_continue}}

## Evidence and record

- {{snapshot_or_commit_identity_and_capture_with_a_pin}}
- {{run_records_probe_scripts_issue_and_pr_quotes}}
- {{page_check_command_and_whether_the_page_was_opened_in_a_browser}}

## Status and label key

{{generated_by_render_page_with_sync_labels}}
