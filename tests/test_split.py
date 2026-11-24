"""The split: disjoint, complete, grouped, reproducible, and the README's counts."""

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from benchmark_loop_agent import split
from benchmark_loop_agent.categories import CATEGORIES
from benchmark_loop_agent.dataset import DATA_DIR, load_cases
from benchmark_loop_agent.split import PARTS, SPLIT_FILE, group_cases, question_key, tool_set_key
import tests.support  # noqa: F401  (forbids network connections)

CASES = [case for category in CATEGORIES for case in load_cases(category)]
DOCUMENT = json.loads(SPLIT_FILE.read_text())
PART_OF = {case_id: part for part, ids in DOCUMENT["parts"].items() for case_id in ids}


class SplitTests(unittest.TestCase):
    def test_parts_are_disjoint_and_hold_every_case(self) -> None:
        self.assertEqual(tuple(DOCUMENT["parts"]), PARTS)
        listed = [i for part in PARTS for i in DOCUMENT["parts"][part]]
        self.assertEqual(len(listed), 3641)
        self.assertEqual(len(set(listed)), 3641)
        self.assertEqual(set(listed), {case.case_id for case in CASES})

    def test_no_tool_set_or_question_is_in_two_parts(self) -> None:
        for key in (tool_set_key, question_key):
            parts: dict[str, set[str]] = {}
            for case in CASES:
                parts.setdefault(key(case), set()).add(PART_OF[case.case_id])
            self.assertTrue(all(len(p) == 1 for p in parts.values()), key.__name__)

    def test_named_pairs_are_each_in_one_part(self) -> None:
        for pair in (("simple_python_4", "multiple_96"), ("multiple_2", "parallel_multiple_60"),
                     ("live_irrelevance_44-2-32", "live_multiple_23-5-0")):
            self.assertEqual(len({PART_OF[i] for i in pair}), 1, pair)

    def test_grouping_ignores_tool_order_and_key_order_and_the_identifier(self) -> None:
        by_id = {case.case_id: case for case in CASES}
        self.assertEqual(tool_set_key(by_id["multiple_2"]), tool_set_key(by_id["parallel_multiple_60"]))
        self.assertEqual(question_key(by_id["live_irrelevance_44-2-32"]), question_key(by_id["live_multiple_23-5-0"]))
        groups, joined = group_cases(CASES)
        self.assertEqual(sum(len(g) for g in groups), len(CASES))
        self.assertTrue(joined["tools"] and joined["question"])

    def test_rebuilding_with_the_committed_seed_and_proportions_reproduces_the_file(self) -> None:
        self.assertEqual(DOCUMENT["seed"], 0)
        self.assertEqual(DOCUMENT["percentages"], {"development": 50, "validation": 20, "held-out": 30})
        self.assertEqual(DOCUMENT["dataset_revision"], split.DATASET_REVISION)
        directory = Path(tempfile.mkdtemp())
        for _ in range(2):
            self.assertEqual(split.main(["--output", str(directory / "split.json")]), 0)
            self.assertEqual((directory / "split.json").read_bytes(), SPLIT_FILE.read_bytes())

    def test_another_seed_or_proportions_are_options(self) -> None:
        directory = Path(tempfile.mkdtemp()) / "s.json"
        split.main(["--seed", "1", "--development", "60", "--validation", "20", "--held-out", "20", "--output", str(directory)])
        other = json.loads(directory.read_text())
        self.assertEqual(other["seed"], 1)
        self.assertNotEqual(other["parts"], DOCUMENT["parts"])
        self.assertAlmostEqual(len(other["parts"]["development"]) / 3641, 0.6, delta=0.02)

    def test_each_category_is_close_to_the_proportions(self) -> None:
        for category in CATEGORIES:
            counts = Counter(PART_OF[c.case_id] for c in CASES if c.category == category)
            total = sum(counts.values())
            for part, share in zip(PARTS, (0.5, 0.2, 0.3)):
                self.assertAlmostEqual(counts[part] / total, share, delta=0.1, msg=(category, part))

    def test_the_file_holds_identifiers_only_and_the_builder_never_reads_answers(self) -> None:
        text = SPLIT_FILE.read_text()
        for case in CASES[:200]:
            self.assertNotIn(case.messages[0]["content"], text)
        source = Path(split.__file__).read_text()
        for name in ("load_expected_answers", "answer_path", "possible_answer"):
            self.assertNotIn(name, source)

class PercentageTests(unittest.TestCase):
    def test_nonfinite_or_negative_percentages_are_refused(self) -> None:
        for bad in (float("nan"), float("inf"), -1.0):
            with self.assertRaisesRegex(ValueError, "finite"):
                split.build_split(0, {"development": bad, "validation": 20.0, "held-out": 30.0})


class ReadmeSplitCountTests(unittest.TestCase):
    def test_readme_states_cases_and_groups_per_part(self) -> None:
        readme = (DATA_DIR.parent / "README.md").read_text()
        groups, _ = group_cases(CASES)
        for part in PARTS:
            cases = len(DOCUMENT["parts"][part])
            n_groups = sum(1 for g in groups if PART_OF[g[0].case_id] == part)
            self.assertRegex(readme, rf"\|\s*{part}\s*\|\s*{cases}\s*\|\s*{n_groups}\s*\|", part)
        self.assertIn(f"| **Total** | {len(CASES)} | {len(groups)} |", readme)


if __name__ == "__main__":
    unittest.main()
