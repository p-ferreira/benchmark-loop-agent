"""Offline tests: every category's scoring path, using BFCL's own checker and rules."""

import unittest

from benchmark_loop_agent.categories import CATEGORIES
from benchmark_loop_agent.dataset import load_cases
from benchmark_loop_agent.scoring import score_calls
from tests.support import all_strings, case_by_id, right_calls

AST_CATEGORIES = [c for c in CATEGORIES if "relevance" not in c]


class AstScoringTests(unittest.TestCase):
    def test_a_correct_call_passes_and_an_empty_answer_fails_in_every_ast_category(self) -> None:
        for category in AST_CATEGORIES:
            with self.subTest(category=category):
                case = next(c for c in load_cases(category) if all_strings(c) or "java" not in category)
                self.assertTrue(score_calls(case, right_calls(case), []).passed)
                verdict = score_calls(case, [], [])
                self.assertFalse(verdict.passed)
                self.assertTrue(verdict.reasons)

    def test_the_first_and_last_case_of_each_ast_category_score_with_their_right_calls(self) -> None:
        for category in AST_CATEGORIES:
            cases = load_cases(category)
            picks = [cases[0], cases[-1]]
            if category in ("simple_java", "simple_javascript"):  # models send these as strings
                picks = [c for c in cases if all_strings(c)][:2]
            for case in picks:
                with self.subTest(case=case.case_id):
                    self.assertTrue(score_calls(case, right_calls(case), []).passed)

    def test_a_wrong_argument_fails(self) -> None:
        case = case_by_id("simple_python", "simple_python_0")
        calls = [{"calculate_triangle_area": {"base": 11, "height": 5}}]
        self.assertFalse(score_calls(case, calls, []).passed)

    def test_parallel_calls_may_come_in_any_order(self) -> None:
        case = case_by_id("parallel")
        calls = right_calls(case)
        self.assertGreater(len(calls), 1)
        self.assertTrue(score_calls(case, list(reversed(calls)), []).passed)
        self.assertFalse(score_calls(case, calls[:1], []).passed)

    def test_malformed_arguments_fail_an_ast_case(self) -> None:
        case = case_by_id("simple_python")
        verdict = score_calls(case, [], ["arguments for f are not valid JSON"])
        self.assertEqual((verdict.passed, verdict.reasons), (False, ["arguments for f are not valid JSON"]))

    def test_dotted_function_names_compare_in_their_underscore_form(self) -> None:
        # BFCL sends "math.factorial" to these providers as "math_factorial" and
        # the checker compares in that form (underscore_to_dot for native FC models).
        dotted = [c for c in load_cases("simple_python") if "." in c.functions[0]["name"]]
        self.assertTrue(dotted)
        case = dotted[0]
        self.assertTrue(score_calls(case, right_calls(case), []).passed)
        self.assertTrue(all("." not in name for call in right_calls(case) for name in call))
        wrong = [{"not_" + n: a for n, a in call.items()} for call in right_calls(case)]
        self.assertFalse(score_calls(case, wrong, []).passed)

    def test_java_and_javascript_values_are_strings_in_the_target_language(self) -> None:
        for category in ("simple_java", "simple_javascript"):
            with self.subTest(category=category):
                case = next(c for c in load_cases(category) if all_strings(c))
                self.assertTrue(score_calls(case, right_calls(case), []).passed)


class RelevanceScoringTests(unittest.TestCase):
    CALL = [{"f": {"x": 1}}]

    def test_irrelevance_passes_only_without_a_call(self) -> None:
        for category in ("irrelevance", "live_irrelevance"):
            with self.subTest(category=category):
                case = case_by_id(category)
                self.assertTrue(score_calls(case, [], []).passed)
                self.assertFalse(score_calls(case, self.CALL, []).passed)

    def test_live_relevance_passes_only_with_a_call(self) -> None:
        case = case_by_id("live_relevance")
        self.assertTrue(score_calls(case, self.CALL, []).passed)
        self.assertFalse(score_calls(case, [], []).passed)

    def test_undecodable_arguments_count_as_no_call_as_in_bfcl(self) -> None:
        bad = ["arguments for f are not valid JSON"]
        self.assertTrue(score_calls(case_by_id("irrelevance"), self.CALL, bad).passed)
        self.assertFalse(score_calls(case_by_id("live_relevance"), self.CALL, bad).passed)

    def test_no_expected_answer_file_exists_for_these_categories(self) -> None:
        from benchmark_loop_agent.dataset import answer_path

        for category in ("irrelevance", "live_irrelevance", "live_relevance"):
            self.assertFalse(answer_path(category).exists())


if __name__ == "__main__":
    unittest.main()
