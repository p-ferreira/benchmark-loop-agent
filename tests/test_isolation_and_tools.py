"""Offline tests: no expected answer reaches a model, and tools are built the way BFCL builds them."""

import json
import unittest
from dataclasses import fields
from unittest import mock

from benchmark_loop_agent.categories import CATEGORIES
from benchmark_loop_agent.dataset import Case, answer_path, load_cases, load_expected_answers, question_path
from benchmark_loop_agent.providers import anthropic_request, openai_request
from benchmark_loop_agent.runner import run_provider
from tests.support import FakeSend, case_by_id, environment, reply_for, right_calls


class IsolationTests(unittest.TestCase):
    def test_case_has_no_answer_field_and_question_files_hold_no_answer(self) -> None:
        self.assertEqual({f.name for f in fields(Case)}, {"case_id", "category", "messages", "functions"})
        for category in CATEGORIES:
            self.assertNotIn("ground_truth", question_path(category).read_text())

    def test_no_answer_reaches_a_model_input_in_any_category(self) -> None:
        for category in CATEGORIES:
            answers = load_expected_answers(category)
            for case in load_cases(category):
                for build in (openai_request, anthropic_request):
                    body = json.dumps(build("m", case))
                    self.assertNotIn("ground_truth", body)
                    if case.case_id in answers:
                        self.assertNotIn(json.dumps(answers[case.case_id]), body, case.case_id)

    def test_answers_are_read_only_after_the_model_answered(self) -> None:
        for category in ("simple_python", "irrelevance"):
            for provider in ("openai", "anthropic"):
                case = case_by_id(category)
                order: list[str] = []
                send = FakeSend(lambda p, r: order.append("request") or reply_for(p, []))
                real = answer_path
                with mock.patch("benchmark_loop_agent.dataset.answer_path",
                                lambda c: order.append("answer") or real(c)):
                    load_expected_answers.cache_clear()
                    run_provider(provider, case, environment(provider), send)
                self.assertEqual(order[0], "request")
                self.assertEqual(order.count("answer"), 0 if "irrelevance" in category else 1)
        load_expected_answers.cache_clear()

    def test_relevance_categories_have_no_answer_to_read(self) -> None:
        for category in ("irrelevance", "live_irrelevance", "live_relevance"):
            self.assertEqual(load_expected_answers(category), {})


class ToolConversionTests(unittest.TestCase):
    def tool(self, category: str, case_id: str | None = None, style=openai_request):
        request = style("m", case_by_id(category, case_id))
        return request["tools"][0]

    def test_every_case_of_every_category_converts_for_both_providers(self) -> None:
        for category in CATEGORIES:
            for case in load_cases(category):
                openai_request("m", case)
                anthropic_request("m", case)

    def test_dotted_names_are_sent_with_underscores(self) -> None:
        case = next(c for c in load_cases("simple_python") if "." in c.functions[0]["name"])
        for build in (openai_request, anthropic_request):
            for tool in build("m", case)["tools"]:
                self.assertNotIn(".", tool["name"])
        self.assertEqual(case.functions[0]["name"].replace(".", "_"), right_calls(case)[0].popitem()[0])

    def test_python_cases_get_the_python_note_and_json_schema_types(self) -> None:
        tool = self.tool("simple_python", "simple_python_0")
        self.assertTrue(tool["description"].endswith(" Note that the provided function is in Python 3 syntax."))
        self.assertEqual(tool["parameters"]["properties"]["base"]["type"], "integer")

    def test_java_parameters_become_strings_with_bfcl_notes(self) -> None:
        case = next(c for c in load_cases("simple_java") if any(
            p["type"] == "ArrayList" for p in c.functions[0]["parameters"]["properties"].values()))
        original = case.functions[0]["parameters"]["properties"]
        for style, key in ((openai_request, "parameters"), (anthropic_request, "input_schema")):
            tool = style("m", case)["tools"][0]
            self.assertIn(" Note that the provided function is in Java 8 SDK syntax.", tool["description"])
            for name, prop in tool[key]["properties"].items():
                self.assertEqual(prop["type"], "string")
                self.assertIn("in string representation.", prop["description"])
                if original[name]["type"] in ("ArrayList", "Array"):
                    self.assertNotIn("items", prop)
                    self.assertIn("The list elements are of type", prop["description"])
        self.assertEqual(original[next(iter(original))]["type"] != "string", True)  # inputs were not mutated

    def test_javascript_dict_and_array_parameters_become_strings_with_bfcl_notes(self) -> None:
        cases = load_cases("simple_javascript")
        kinds = {p["type"] for c in cases for p in c.functions[0]["parameters"]["properties"].values()}
        self.assertTrue({"array", "dict"} <= kinds)
        for case in cases:
            tool = openai_request("m", case)["tools"][0]
            self.assertIn("JavaScript syntax.", tool["description"])
            for name, prop in tool["parameters"]["properties"].items():
                self.assertEqual(prop["type"], "string")
                original = case.functions[0]["parameters"]["properties"][name]
                if original["type"] == "array":
                    self.assertNotIn("items", prop)
                if original["type"] == "dict" and "properties" in original:
                    self.assertIn("The dictionary entries have the following schema", prop["description"])
                    self.assertNotIn("properties", prop)

    def test_openai_maps_system_to_developer_and_anthropic_moves_it_to_system(self) -> None:
        case = next(c for c in load_cases("live_simple") if c.messages[0]["role"] == "system")
        self.assertEqual(openai_request("m", case)["input"][0]["role"], "developer")
        body = anthropic_request("m", case)
        self.assertEqual(body["system"], [{"type": "text", "text": case.messages[0]["content"]}])
        self.assertTrue(all(m["role"] != "system" for m in body["messages"]))

    def test_consecutive_user_messages_are_merged_for_anthropic(self) -> None:
        case = next(c for c in load_cases("live_irrelevance")
                    if [m["role"] for m in c.messages][:2] == ["user", "user"])
        body = anthropic_request("m", case)
        roles = [m["role"] for m in body["messages"]]
        self.assertFalse(any(a == b == "user" for a, b in zip(roles, roles[1:])))

    def test_a_case_without_functions_sends_no_tools(self) -> None:
        case = next(c for c in load_cases("live_irrelevance") if not c.functions)
        self.assertNotIn("tools", openai_request("m", case))
        self.assertNotIn("tools", anthropic_request("m", case))


if __name__ == "__main__":
    unittest.main()
