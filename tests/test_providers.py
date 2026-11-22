"""Offline tests: both adapters through pass, fail and error paths, with the HTTP boundary replaced."""

import json
import unittest
from typing import Any

from benchmark_loop_agent.case import load_case
from benchmark_loop_agent.providers import ProviderError
from benchmark_loop_agent.runner import run_provider

SECRET = "sk-test-SECRET-123"
RIGHT = {"base": 10, "height": 5}
WRONG = {"base": 11, "height": 5}
NAME = "calculate_triangle_area"


def openai_reply(arguments: Any) -> dict[str, Any]:
    return {
        "model": "gpt-actual",
        "choices": [{"message": {"tool_calls": [{"function": {"name": NAME, "arguments": arguments}}]}}],
        "usage": {"prompt_tokens": 7, "completion_tokens": 3},
    }


def anthropic_reply(arguments: dict[str, Any] | None) -> dict[str, Any]:
    content = [] if arguments is None else [{"type": "tool_use", "name": NAME, "input": arguments}]
    return {"model": "claude-actual", "content": content, "usage": {"input_tokens": 8, "output_tokens": 4}}


def environment(provider: str) -> dict[str, str]:
    prefix = provider.upper()
    return {f"{prefix}_API_KEY": SECRET, f"{prefix}_MODEL": "requested-model"}


class FakePost:
    """Stands in for the HTTP boundary and remembers what was sent."""

    def __init__(self, reply: dict[str, Any] | Exception) -> None:
        self.reply = reply
        self.requests: list[tuple[str, dict[str, str], dict[str, Any]]] = []

    def __call__(self, url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
        self.requests.append((url, headers, body))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


class AdapterTests(unittest.TestCase):
    def run_case(self, provider: str, reply: dict[str, Any] | Exception):
        post = FakePost(reply)
        return run_provider(provider, load_case(), environment(provider), post), post

    def test_openai_pass(self) -> None:
        record, post = self.run_case("openai", openai_reply(json.dumps(RIGHT)))
        self.assertEqual(record.outcome, "pass")
        self.assertEqual(record.returned_calls, [{NAME: RIGHT}])
        self.assertEqual((record.requested_model, record.actual_model), ("requested-model", "gpt-actual"))
        self.assertEqual((record.input_tokens, record.output_tokens), (7, 3))
        url, headers, body = post.requests[0]
        self.assertIn("openai.com", url)
        self.assertEqual(headers["authorization"], f"Bearer {SECRET}")
        self.assertEqual(body["tools"][0]["function"]["parameters"]["type"], "object")

    def test_openai_fail_wrong_value(self) -> None:
        record, _ = self.run_case("openai", openai_reply(json.dumps(WRONG)))
        self.assertEqual(record.outcome, "fail")
        self.assertTrue(record.reasons)

    def test_openai_fail_malformed_arguments(self) -> None:
        record, _ = self.run_case("openai", openai_reply("{not json"))
        self.assertEqual(record.outcome, "fail")

    def test_anthropic_pass(self) -> None:
        record, post = self.run_case("anthropic", anthropic_reply(RIGHT))
        self.assertEqual(record.outcome, "pass")
        self.assertEqual(record.actual_model, "claude-actual")
        self.assertEqual((record.input_tokens, record.output_tokens), (8, 4))
        url, headers, body = post.requests[0]
        self.assertIn("anthropic.com", url)
        self.assertEqual(headers["x-api-key"], SECRET)
        self.assertEqual(body["tools"][0]["input_schema"]["type"], "object")

    def test_anthropic_fail_wrong_value(self) -> None:
        record, _ = self.run_case("anthropic", anthropic_reply(WRONG))
        self.assertEqual(record.outcome, "fail")

    def test_anthropic_fail_no_tool_call(self) -> None:
        record, _ = self.run_case("anthropic", anthropic_reply(None))
        self.assertEqual(record.outcome, "fail")
        self.assertEqual(record.returned_calls, [])

    def test_provider_error_is_unscored_for_both(self) -> None:
        for provider in ("openai", "anthropic"):
            with self.subTest(provider=provider):
                record, _ = self.run_case(provider, ProviderError("HTTP 500: boom"))
                self.assertEqual(record.outcome, "unscored")
                self.assertIsNone(record.returned_calls)
                self.assertIn("boom", record.reasons[0])

    def test_unexpected_response_shape_is_unscored(self) -> None:
        for provider in ("openai", "anthropic"):
            with self.subTest(provider=provider):
                record, _ = self.run_case(provider, {"unexpected": True})
                self.assertEqual(record.outcome, "unscored")

    def test_missing_key_and_missing_model_are_unscored_without_a_request(self) -> None:
        for env, expected in (({"OPENAI_MODEL": "m"}, "OPENAI_API_KEY"), ({"OPENAI_API_KEY": "k"}, "OPENAI_MODEL")):
            post = FakePost(openai_reply(json.dumps(RIGHT)))
            record = run_provider("openai", load_case(), env, post)
            self.assertEqual(record.outcome, "unscored")
            self.assertIn(expected, record.reasons[0])
            self.assertEqual(post.requests, [])

    def test_key_in_exception_text_never_reaches_the_record(self) -> None:
        for provider in ("openai", "anthropic"):
            with self.subTest(provider=provider):
                record, _ = self.run_case(provider, RuntimeError(f"connection failed, key={SECRET}"))
                self.assertEqual(record.outcome, "unscored")
                self.assertNotIn(SECRET, json.dumps(record.to_dict()))
                self.assertIn("[redacted]", record.reasons[0])


if __name__ == "__main__":
    unittest.main()
