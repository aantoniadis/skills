"""The structure view of a rework map: the data check, a layout whose runs avoid every box, and a
figure that keeps today's picture readable without scripts."""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("structure_view", ROOT / "skills/structure_view.py")
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)
FIXTURE = ROOT / "tests/fixtures/rework-map/rework-map.md"


def fixture_data():
    (_, text), = view.fences(FIXTURE.read_text())
    return json.loads(text)


def segments(path):
    """The straight runs of a rounded path, as ((x1, y1), (x2, y2))."""
    points = [tuple(map(float, pair)) for pair in re.findall(r"[MLQ]\s*([\d.]+)\s+([\d.]+)", path)]
    return list(zip(points, points[1:]))


class StructureViewTests(unittest.TestCase):
    def test_fixture_data_passes_and_each_mistake_is_named(self):
        data = fixture_data()
        self.assertEqual(view.problems(data), [])
        broken = json.loads(json.dumps(data))
        broken["dependencies"][0]["today"] = "allowed"
        broken["dependencies"][1]["at"] = "see the code"
        broken["rules"][0]["owner"] = "nowhere"
        broken["rules"][0]["sites"][0]["at"] = ""
        broken["data"][0]["keys"][0]["reads"][0]["file"] = "ghost"
        found = " | ".join(view.problems(broken))
        for expected in ("`today` is one of", "`at` is the pinned line", "`owner` must be a file id",
                         "each site's `at` is its pinned line", "reads file 'ghost' is not a file id"):
            self.assertIn(expected, found)
        self.assertEqual(view.problems([]), ["the fence holds no JSON object"])

    def test_check_reports_invalid_json_with_its_line(self):
        with self.assertRaisesRegex(ValueError, r"Structure view at line 3: the fence is not valid JSON"):
            view.check("# Map\n\n```structure-view\n{not json\n```\n")
        view.check("# Map\n\nNo view here.\n")

    def test_no_run_crosses_a_box_it_does_not_start_or_end_at(self):
        data = fixture_data()
        plan = view.layout(data)
        for index, dependency in enumerate(data["dependencies"]):
            ends = {dependency["from"], dependency["to"]}
            for (x1, y1), (x2, y2) in segments(plan["edges"][index]):
                for file_id, box in plan["boxes"].items():
                    if file_id in ends:
                        continue
                    inside_x = box["x"] + 2 < max(x1, x2) and min(x1, x2) < box["x"] + box["w"] - 2
                    inside_y = box["y"] + 2 < max(y1, y2) and min(y1, y2) < box["y"] + box["h"] - 2
                    self.assertFalse(inside_x and inside_y, (dependency["from"], dependency["to"], file_id))

    def test_proposed_sites_move_to_the_owner_except_those_that_wait(self):
        data = fixture_data()
        homes = {(r, s): home for r, s, home in view.site_homes(data, "proposed")}
        self.assertEqual(homes[(0, 1)], "discounts", "the display copy moves to the owner")
        self.assertEqual(homes[(0, 2)], "builder", "the quote rate waits for the user's answer")
        self.assertEqual(homes[(1, 0)], "discounts")
        self.assertIn("<b>2 of 3</b>", view.facts({**data, "dependencies": data["dependencies"][0:3]}, "today"))
        self.assertIn("<b>4 of 4</b>", view.facts(data, "proposed"))

    def test_figure_draws_today_without_scripts_and_carries_both_views(self):
        html = view.figure(fixture_data(), 1)
        self.assertIn('class="sv-switch" role="group" aria-label="Which structure to show" hidden', html)
        self.assertIn('data-today="not stated" data-proposed=""', html)
        self.assertRegex(html, r'class="sv-dot waits" data-rule="0" data-today="[\d.]+,[\d.]+" data-proposed="[\d.]+,[\d.]+" transform="translate\(')
        self.assertIn("<th scope=\"row\"><span class=\"sv-code\">discount</span></th>", html)
        self.assertNotIn("<code>", html, "the page check counts code elements against the Markdown")


if __name__ == "__main__":
    unittest.main()
