"""Possible bugs cards on the page and in --check --review: python3 tests/test_bug_cards.py."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/bug-cards"
spec = importlib.util.spec_from_file_location("bug_cards_page", ROOT / "skills/render_page.py")
page = importlib.util.module_from_spec(spec)
spec.loader.exec_module(page)

NOTE = FIXTURES / "report.md"
CARDS = NOTE.read_text()
NOT_RUN = (FIXTURES / "not-run.md").read_text()
NONE_FOUND = (FIXTURES / "none-found.md").read_text()


def line(source, prefix, occurrence=0):
    """The whole line (with its newline) that starts with prefix, counting from the first card."""
    return [text for text in source.splitlines(keepends=True) if text.startswith(prefix)][occurrence]


def section(source):
    start = source.index("## Possible bugs")
    return source[start:source.index("## Requirements")]


class BugCardTests(unittest.TestCase):
    def reject(self, source, message):
        with self.assertRaisesRegex(ValueError, message):
            page.check_review(source, NOTE)

    def test_each_form_passes_review_and_the_page_check(self):
        for name, source in (("cards", CARDS), ("not run", NOT_RUN), ("none found", NONE_FOUND)):
            with self.subTest(form=name):
                page.check_review(source, NOTE)
                page.check(source, page.render(source, NOTE.name), NOTE)

    def test_cards_render_chips_facts_table_and_reproduce(self):
        soup = page.parse(page.render(CARDS, NOTE.name))
        cards = soup.select("#possible-bugs article.bug-card")
        self.assertEqual([card.h3.get_text() for card in cards],
                         ["1. Overridden dependencies stay in memory", "2. An override with another kind of callable may be misread"])
        self.assertEqual([[chip.get_text() for chip in card.select(".bug-chips .chip")] for card in cards],
                         [["we ran it", "new in this change"], ["suspected, not run", "pre-existing, made worse"]])
        self.assertEqual([chip["class"][1] for chip in cards[1].select(".bug-chips .chip")], ["chip-suspected", "chip-made-worse"])
        self.assertEqual([fact.strong.get_text() for fact in cards[0].select(".behavior-fact")],
                         ["Where:", "Trigger:", "Who / impact:", "Fix direction:"])
        self.assertEqual([fact.strong.get_text() for fact in cards[1].select(".behavior-fact")],
                         ["Where:", "Trigger:", "Who / impact:", "Fix direction:", "Probe that would settle it:"])
        self.assertIn("1024 sessions reachable", cards[0].select(".behavior-fact .fact-copy")[2].get_text())
        for card in cards:
            table = card.select_one("table.base-head")
            self.assertEqual([th.get_text() for th in table.select("th")], ["", "Base", "Head"])
            self.assertEqual(table.parent["class"], ["table-scroll"])
        reproduce = cards[0].select_one("details.bug-reproduce")
        self.assertEqual(reproduce.summary.get_text(), "Reproduce")
        self.assertEqual(reproduce.select_one("figure.code-card pre").get_text().strip(), "python runs/bugs/probe.py")
        caption = reproduce.select_one("figure.code-card figcaption")
        self.assertIsNone(caption.a)
        self.assertIn("runs/bugs/probe.py", caption.get_text())
        self.assertEqual([a["href"] for a in reproduce.find_all("a")], ["runs/bugs/probe.py"])
        self.assertIn("Output:", reproduce.get_text())
        self.assertIsNone(cards[1].select_one("details.bug-reproduce"))
        self.assertEqual([a.get_text() for a in soup.select("#possible-bugs .label-help a")], ["bug evidence", "bug origin"])
        self.assertEqual([dt.get_text() for dt in soup.select("#key-bug-evidence + dl dt")], ["we ran it", "suspected, not run"])
        self.assertEqual(soup.select_one("#key-bug-origin + dl dt .chip")["class"], ["chip", "chip-new"])
        self.assertEqual(len(soup.select("ol.attention > li .chip")), 4)

    def test_sentence_forms_render_without_cards_or_bug_labels(self):
        for source in (NOT_RUN, NONE_FOUND):
            soup = page.parse(page.render(source, NOTE.name))
            self.assertIsNone(soup.select_one(".bug-card"))
            self.assertIsNotNone(soup.select_one("#possible-bugs p"))
            self.assertNotIn("bug-evidence", page.label_groups(source))
        self.assertEqual([group for group in page.label_groups(CARDS) if group.startswith("bug-")], ["bug-evidence", "bug-origin"])

    def test_label_catalog_defines_both_families(self):
        self.assertEqual(tuple(page.LABELS["bug-evidence"]["options"]), tuple(page.BUG_EVIDENCE))
        self.assertEqual(tuple(page.LABELS["bug-origin"]["options"]), tuple(page.BUG_ORIGIN))
        synced = page.with_label_key(CARDS)
        self.assertIn("### Key: Bug evidence", synced)
        self.assertIn("### Key: Bug origin", synced)
        self.assertEqual(page.reader_gaps(page.label_key_markdown(CARDS)), [])

    def test_section_is_required_and_has_one_of_three_forms(self):
        self.reject(NOT_RUN.replace(section(NOT_RUN), ""), "Possible bugs")
        self.reject(NOT_RUN.replace("The search for bugs has not run:", "The search for bugs did not run because"), "Possible bugs")
        self.reject(NOT_RUN.replace("The search for bugs has not run: the review stopped after the overview.", "The search for bugs has not run:"),
                    "Possible bugs")
        self.reject(NOT_RUN.replace("overview.\n", "overview.\n\nNo bugs found: none.\n"), "Possible bugs")
        moved = NOT_RUN.replace(section(NOT_RUN), "").replace("## What to look at", section(NOT_RUN) + "## What to look at")
        self.reject(moved, "after")
        self.reject(CARDS.replace("## Possible bugs\n", "## Possible bugs\n\nTwo bugs.\n"), "Possible bugs")
        self.reject(CARDS.replace("### 2. An override", "### 3. An override"), "numbered")
        self.reject(CARDS.replace("### 1. Overridden", "### Overridden"), "numbered")

    def test_a_report_without_the_section_still_renders_and_checks_without_review(self):
        old = NOT_RUN.replace(section(NOT_RUN), "").replace(line(NOT_RUN, "| [Bug probes]"), "")
        page.check(old, page.render(old, NOTE.name), NOTE)
        with self.assertRaisesRegex(ValueError, "'## Possible bugs'"):
            page.check_review(old, NOTE)

    def test_bug_origin_labels_cover_new_origins(self):
        self.assertEqual(tuple(page.LABELS["bug-origin"]["options"]),
                         ("new in this change", "pre-existing, made worse", "from an unrelated commit", "no base pinned"))

    def test_review_rejects_no_base_pinned_origin(self):
        source = CARDS.replace("*we ran it* · *new in this change*", "*we ran it* · *no base pinned*")
        source = source.replace("| freed |", "| no base pinned |")
        self.reject(source, "a base is pinned")

    def test_no_base_card_reads_no_base_pinned_in_base(self):
        origin = CARDS.replace("*suspected, not run* · *pre-existing, made worse*", "*suspected, not run* · *no base pinned*")
        with self.assertRaisesRegex(ValueError, "no base pinned"):
            page.check_bug_cards(origin, NOTE)
        source = origin.replace("| Flags for the override | predicted: computed for the override |",
                                "| Flags for the override | no base pinned |")
        page.check_bug_cards(source, NOTE)

    def test_unrelated_commit_card_names_the_commit(self):
        source = CARDS.replace("*suspected, not run* · *pre-existing, made worse*", "*suspected, not run* · *from an unrelated commit*")
        with self.assertRaisesRegex(ValueError, "Introduced by"):
            page.check_bug_cards(source, NOTE)
        trigger = line(source, "**Trigger:** an async")
        source = source.replace(trigger, trigger + "**Introduced by:** 3f2a9c1 (reformat of models.py)\n")
        page.check_bug_cards(source, NOTE)
        card = page.parse(page.render(source, NOTE.name)).select("#possible-bugs article.bug-card")[1]
        self.assertIn("Introduced by:", [fact.strong.get_text() for fact in card.select(".behavior-fact")])
        self.assertEqual(card.select(".bug-chips .chip")[1]["class"][1], "chip-unrelated")

    def test_bug_origin_gaps_without_base(self):
        self.assertEqual(len(page.bug_origin_gaps(CARDS, base=False)), 2)
        source = CARDS.replace("*new in this change*", "*no base pinned*").replace("*pre-existing, made worse*", "*no base pinned*")
        self.assertEqual(page.bug_origin_gaps(source, base=False), [])

    def test_removing_each_required_field_names_it(self):
        chips = line(CARDS, "*we ran it*")
        for label in ("Where", "Trigger", "Who / impact", "Fix direction"):
            with self.subTest(field=label):
                self.reject(CARDS.replace(line(CARDS, f"**{label}:**"), "", 1), label)
        self.reject(CARDS.replace(chips, ""), "chip")
        self.reject(CARDS.replace(line(CARDS, "**Who / impact:**") + line(CARDS, "1024 sessions"), ""), "Who / impact")
        start = CARDS.index("| | Base | Head |")
        table = CARDS[start:CARDS.index("\n\n", start) + 1]
        self.reject(CARDS.replace(table, "", 1), "Base")
        self.reject(CARDS.replace("| | Base | Head |", "| | Before | After |", 1), "Base")
        self.reject(CARDS.replace("| freed |", "|  |"), "Base")
        self.reject(CARDS.replace("*Suggestion:* store", "store"), "Fix direction")
        self.reject(CARDS.replace(line(CARDS, "**Where:**"), "**Where:** `src/models.py`, lines 57 to 67\n", 1), "Where")
        self.reject(CARDS.replace("```sh\npython runs/bugs/probe.py\n```\n", ""), "Reproduce")
        reproduce = CARDS[CARDS.index("**Reproduce:**"):CARDS.index("### 2.")]
        self.reject(CARDS.replace(reproduce, "\n"), "Reproduce")
        self.reject(CARDS.replace(" · [script](runs/bugs/probe.py)", ""), "runs/bugs/")
        self.reject(CARDS.replace(line(CARDS, "**Probe that would settle it:**"), ""), "Probe that would settle it")

    def test_chip_values_are_from_the_two_families(self):
        self.reject(CARDS.replace("*new in this change*", "*brand new*"), "chip")
        self.reject(CARDS.replace("*we ran it* · *new", "*observed* · *new"), "chip")
        self.reject(CARDS.replace("*we ran it* · *new in this change*", "*new in this change* · *we ran it*"), "chip")
        self.reject(CARDS.replace("*we ran it* · *new in this change*", "*we ran it*"), "chip")

    def test_reproduce_link_must_be_an_existing_file_under_runs_bugs(self):
        self.reject(CARDS.replace("[script](runs/bugs/probe.py)", "[script](runs/bugs/missing.py)"), "runs/bugs/")
        self.reject(CARDS.replace("[script](runs/bugs/probe.py)", "[script](report.md)"), "runs/bugs/")
        self.reject(CARDS.replace("[script](runs/bugs/probe.py)", "[script](runs/bugs/../../report.md)"), "runs/bugs/")

    def test_suspected_values_are_labeled_predicted_and_have_no_reproduce(self):
        self.reject(CARDS.replace("| predicted: computed for the override |", "| computed for the override |"), "predicted")
        self.reject(CARDS.replace("predicted: read from", "read from"), "predicted")
        probe = line(CARDS, "**Probe that would settle it:**")
        self.reject(CARDS.replace(probe, probe + "**Reproduce:**\n```sh\npython runs/bugs/probe.py\n```\n[script](runs/bugs/probe.py)\n"),
                    "Reproduce")

    def test_attention_item_linking_to_a_card_stays_one_line(self):
        self.assertEqual(page.attention_gaps(CARDS), [])
        longer = CARDS.replace("[details](#1-overridden-dependencies-stay-in-memory).",
                               "[details](#1-overridden-dependencies-stay-in-memory). Sessions stay reachable after the override is cleared.")
        self.assertEqual(page.attention_gaps(longer), [])
        continued = CARDS.replace("[details](#1-overridden-dependencies-stay-in-memory).",
                                  "[details](#1-overridden-dependencies-stay-in-memory).\n   Look at: the card.\n   Settle: is a weak cache wanted?")
        self.assertIn("one line", page.attention_gaps(continued)[0][1])
        unlinked = CARDS.replace(" · [details](#1-overridden-dependencies-stay-in-memory).", "")
        self.assertIn("reading route", page.attention_gaps(unlinked)[0][1])

    def test_card_shape_is_closed_in_both_modes(self):
        stray = "\nThis silently corrupts every customer's billing totals.\n"
        output = line(CARDS, "Output:")
        for where, source in (("after a table", CARDS.replace("| freed | still alive |\n", "| freed | still alive |\n" + stray, 1)),
                              ("after the Output line", CARDS.replace(output, output + stray)),
                              ("in a suspected card", CARDS.replace(line(CARDS, "**Probe that would settle it:**"),
                                                                    line(CARDS, "**Probe that would settle it:**") + stray)),
                              ("as a list", CARDS.replace(output, output + "\n- billing totals are wrong\n")),
                              ("twice", CARDS.replace(line(CARDS, "**Trigger:**"), line(CARDS, "**Trigger:**") * 2, 1))):
            with self.subTest(where=where):
                self.reject(source, "outside the card's fields|appears twice")
                with self.assertRaisesRegex(ValueError, "outside the card's fields|appears twice"):
                    page.check(source, page.render(source, NOTE.name), NOTE)

    def test_plain_check_runs_the_card_rules_when_the_section_exists(self):
        for source, message in ((CARDS.replace("| predicted: computed for the override |", "| computed for the override |"), "predicted"),
                                (CARDS.replace(" · [script](runs/bugs/probe.py)", ""), "runs/bugs/"),
                                (CARDS.replace(line(CARDS, "**Where:**"), "**Where:** `src/models.py`, lines 57 to 67\n", 1), "Where"),
                                (NOT_RUN.replace("The search for bugs has not run:", "Bugs:"), "Possible bugs")):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                page.check(source, page.render(source, NOTE.name), NOTE)
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "bug-cards"
            shutil.copytree(FIXTURES, copy)
            (copy / "report.md").write_text(page.with_label_key(CARDS.replace("predicted: read from", "read from")))
            checked = subprocess.run([sys.executable, str(ROOT / "skills/render_page.py"), str(copy / "report.md"), "--check"],
                                     capture_output=True, text=True)
            self.assertNotEqual(checked.returncode, 0)
            self.assertIn("predicted", checked.stderr)

    def test_we_ran_it_card_needs_its_output_line(self):
        self.reject(CARDS.replace(line(CARDS, "Output:"), "[script](runs/bugs/probe.py)\n"), "Output:")

    def test_output_line_and_fences_hold_nothing_else(self):
        output = line(CARDS, "Output:")
        fence = "```sh\npython runs/bugs/probe.py\n```\n"
        probe = line(CARDS, "**Probe that would settle it:**")
        for name, source, message in (
                ("continued", CARDS.replace(output, output + "This silently corrupts every customer's billing totals.\n"), "Output: line"),
                ("prose", CARDS.replace("Output: `head", "Output: billing totals are wrong; `head"), "Output: line"),
                ("no excerpt", CARDS.replace(output, "Output: [script](runs/bugs/probe.py)\n"), "Output: line"),
                ("twice", CARDS.replace(output, output + "\n" + output), "Output: line"),
                ("second fence", CARDS.replace(fence, fence + fence), "one code fence"),
                ("fence after probe text", CARDS.replace(probe, probe + fence), "one code fence"),
                ("two probe fences", CARDS.replace(probe, "**Probe that would settle it:**\n" + fence + fence), "one code fence")):
            with self.subTest(name=name):
                self.reject(source, message)
                with self.assertRaisesRegex(ValueError, message):
                    page.check(source, page.render(source, NOTE.name), NOTE)
        fenced_probe = CARDS.replace(probe, "**Probe that would settle it:**\n" + fence)
        page.check_review(fenced_probe, NOTE)

    def test_summary_forms_hold_one_paragraph_without_sentence_counting(self):
        for source, sentence in ((NOT_RUN, "the review stopped after the overview."),
                                 (NONE_FOUND, "an app built twice in one process.")):
            with self.subTest(form=sentence):
                prose = source.replace(sentence, sentence + " Limits include callers, e.g. a remote client.")
                page.check_review(prose, NOTE)
                page.check(prose, page.render(prose, NOTE.name), NOTE)
                self.reject(source.replace(sentence, sentence + "\n\nAnother paragraph."), "one paragraph")

    def test_attention_item_evidence_matches_its_card(self):
        ran = CARDS.replace("*you decide* · *we ran it*", "*you decide* · *read at the line*")
        self.assertIn("*we ran it*", page.attention_gaps(ran)[0][1])
        self.reject(ran, "item 1: its card says")
        suspected = CARDS.replace("*check it* · *reasoned, not run*", "*check it* · *we ran it*")
        self.assertIn("*reasoned, not run*", page.attention_gaps(suspected)[0][1])
        self.reject(suspected, "item 2: its card says")

    def test_we_ran_it_head_is_observed_and_base_may_be_predicted(self):
        page.check_review(CARDS.replace("| freed | still alive |", "| predicted: freed | still alive |"), NOTE)
        self.reject(CARDS.replace("| freed | still alive |", "| freed | predicted: still alive |"), "Head")

    def test_each_card_has_exactly_one_deciding_item(self):
        item = line(CARDS, "1. **Overridden")
        self.reject(CARDS.replace(item, ""), "exactly one")
        second = item.replace("1. ", "3. ", 1).replace("**Overridden dependencies stay in memory**", "**Sessions outlive overrides**")
        self.reject(CARDS.replace(line(CARDS, "2. **Cache"), line(CARDS, "2. **Cache") + second), "exactly one")
        for action in ("ask the author", "read lightly", "no action"):
            with self.subTest(action=action):
                self.reject(CARDS.replace("*you decide* · *we ran it*", f"*{action}* · *we ran it*"), "you decide.*check it")

    def test_bug_probes_row_preserves_execution_evidence(self):
        def probes(source, result, origin, record=False):
            rows = source.splitlines(keepends=True)
            link = "[Bug probes](#possible-bugs)" + (" ([record](runs/bugs/record.md))" if record else "")
            return "".join(f"| {link} | {result} | {origin} | bbbbbbb | Synthetic fixture |\n"
                           if row.startswith("| [Bug probes]") else row for row in rows)
        card_one = CARDS[CARDS.index("### 1."):CARDS.index("### 2.")]
        suspected = (CARDS.replace(card_one, "").replace(line(CARDS, "1. **Overridden"), "")
                     .replace("2. **Cache", "1. **Cache").replace("### 2.", "### 1.").replace("#2-an-override", "#1-an-override"))
        for source in (suspected, NONE_FOUND):
            for result, origin in (("Passed", "Executed here"), ("Mixed", "Recorded run"),
                                   ("Blocked", "Executed here"), ("Not run", "Source inspected")):
                with self.subTest(result=result, origin=origin):
                    page.check_review(probes(source, result, origin, record=True), NOTE)
            self.reject(probes(source, "Passed", "Executed here"), "run record")
            self.reject(probes(source, "Not run", "Recorded run", True), "actual result")
        for result in ("Passed", "Failed", "Mixed", "Blocked"):
            for origin in ("Executed here", "Recorded run"):
                page.check_review(probes(CARDS, result, origin, record=True), NOTE)
        for result, origin in (("Not run", "Executed here"), ("Not run", "Proposed"),
                               ("Not run", "Source inspected"), ("Passed", "Invented")):
            self.reject(probes(CARDS, result, origin), "Bug probes")
        page.check_review(probes(CARDS, "Failed", "Recorded run", True), NOTE)
        self.reject(probes(CARDS, "Failed", "Recorded run"), "run record")
        for result in ("Not run", "Blocked"):
            page.check_review(probes(NOT_RUN, result, "Proposed"), NOTE)
        self.reject(probes(NOT_RUN, "Passed", "Executed here", True), "has not run")
        self.reject(probes(NONE_FOUND, "Not run", "Proposed"), "Source inspected")
        row = line(CARDS, "| [Bug probes]")
        self.reject(CARDS.replace(row, ""), "Bug probes")
        self.reject(CARDS.replace(row, row + row), "Bug probes")

    def test_successful_diagnostic_can_observe_a_bug(self):
        source = CARDS.replace("| Failed | Executed here |", "| Passed | Executed here |")
        source = source.replace("An override with another kind of callable stays suspected",
                                "The diagnostic expected and observed retention; the application defect remains")
        page.check_review(source, NOTE)
        page.check(source, page.render(source, NOTE.name), NOTE)

    def test_who_impact_shows_its_basis(self):
        who = line(CARDS, "**Who / impact:**", 1)
        bare = "**Who / impact:** apps that override async dependencies with sync stubs; the stub may be awaited.\n"
        self.reject(CARDS.replace(who, bare), "Who / impact")
        with self.assertRaisesRegex(ValueError, "Who / impact"):
            page.check(CARDS.replace(who, bare), page.render(CARDS.replace(who, bare), NOTE.name), NOTE)
        for basis in ("**Who / impact:** *reasoned, not run*: apps that override async dependencies with sync stubs.\n",
                      "**Who / impact:** apps with sync stubs; predicted: the stub is awaited.\n",
                      "**Who / impact:** apps with sync stubs ([models.py:170](https://github.com/acme/widgets/blob/"
                      "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/src/models.py#L170)).\n"):
            with self.subTest(basis=basis[18:40]):
                page.check_review(CARDS.replace(who, basis), NOTE)
                page.check(CARDS.replace(who, basis), page.render(CARDS.replace(who, basis), NOTE.name), NOTE)

    def test_reproduce_fence_names_the_linked_script(self):
        self.reject(CARDS.replace("```sh\npython runs/bugs/probe.py\n```", "```sh\ncd runs/bugs && python probe.py\n```"),
                    "runs/bugs/probe.py")

    def test_review_example_passes_check_review(self):
        example = ROOT / "tests/fixtures/report-layout/report.md"
        checked = subprocess.run([sys.executable, str(ROOT / "skills/render_page.py"), str(example), "--check", "--review", "--markdown-only"],
                                 capture_output=True, text=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        with tempfile.TemporaryDirectory() as directory:  # the companion renders and checks from a copy
            copy = Path(directory) / "report-layout"
            shutil.copytree(example.parent, copy)
            command = [sys.executable, str(ROOT / "skills/render_page.py"), str(copy / "report.md"), "--review", "--sync-labels"]
            rendered = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            checked = subprocess.run(command + ["--check"], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            page.check_review_tables((copy / "report.md").read_text(), (copy / "report.html").read_text())

    def test_cli_review_check_passes_for_each_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "bug-cards"
            shutil.copytree(FIXTURES, copy)
            for name in ("report.md", "not-run.md", "none-found.md"):
                with self.subTest(fixture=name):
                    command = [sys.executable, str(ROOT / "skills/render_page.py"), str(copy / name), "--review"]
                    rendered = subprocess.run(command + ["--sync-labels"], capture_output=True, text=True)
                    self.assertEqual(rendered.returncode, 0, rendered.stderr)
                    checked = subprocess.run(command + ["--check"], capture_output=True, text=True)
                    self.assertEqual(checked.returncode, 0, checked.stderr)


if __name__ == "__main__":
    unittest.main()
