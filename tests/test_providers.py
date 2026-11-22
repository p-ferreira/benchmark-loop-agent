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

    def test_openai_non_object_arguments_fail_and_keep_the_call(self) -> None:
        for raw in ("null", "1", "[1]"):
            with self.subTest(raw=raw):
                record, _ = self.run_case("openai", openai_reply(raw))
                self.assertEqual(record.outcome, "fail")
                self.assertEqual(record.returned_calls, [{NAME: raw}])

    def test_openai_malformed_arguments_are_retained_raw(self) -> None:
        record, _ = self.run_case("openai", openai_reply("{bad"))
        self.assertEqual(record.outcome, "fail")
        self.assertEqual(record.returned_calls, [{NAME: "{bad"}])

    def test_openai_undecodable_arguments_fail_and_keep_metadata(self) -> None:
        for raw in ('{"base": ' + "9" * 4301 + ', "height": 5}', "[" * 100000):
            with self.subTest(raw=raw[:10]):
                record, _ = self.run_case("openai", openai_reply(raw))
                self.assertEqual(record.outcome, "fail")
                self.assertEqual(record.actual_model, "gpt-actual")
                self.assertEqual(record.returned_calls, [{NAME: raw}])

    def test_anthropic_non_object_input_fails_and_keeps_the_call(self) -> None:
        reply = anthropic_reply({})
        reply["content"][0]["input"] = "oops"
        record, _ = self.run_case("anthropic", reply)
        self.assertEqual(record.outcome, "fail")
        self.assertEqual(record.returned_calls, [{NAME: "oops"}])

    def test_keys_echoed_in_a_successful_response_are_redacted_everywhere(self) -> None:
        other = "sk-ant-OTHER-456"
        arguments = json.dumps({**RIGHT, "unit": f"{SECRET} {other}"})
        post = FakePost(openai_reply(arguments))
        env = {**environment("openai"), "ANTHROPIC_API_KEY": other}
        record = run_provider("openai", load_case(), env, post)
        text = json.dumps(record.to_dict())
        self.assertNotIn(SECRET, text)
        self.assertNotIn(other, text)
        self.assertIn("[redacted]", text)

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

    def test_key_crossing_the_reason_cutoff_is_fully_redacted(self) -> None:
        from benchmark_loop_agent.runner import MAX_REASON_LENGTH

        for offset in range(len(SECRET) + 1):
            with self.subTest(offset=offset):
                prefix = "x" * (MAX_REASON_LENGTH - len("RuntimeError: ") - offset)
                record, _ = self.run_case("openai", RuntimeError(prefix + SECRET))
                reason = record.reasons[0]
                self.assertLessEqual(len(reason), MAX_REASON_LENGTH)
                for n in range(4, len(SECRET) + 1):
                    self.assertNotIn(SECRET[:n], reason)

    def test_long_http_error_body_is_not_truncated_before_redaction(self) -> None:
        import io
        import urllib.error
        from unittest import mock

        from benchmark_loop_agent.providers import post_json

        body = ("y" * 495 + SECRET).encode()
        error = urllib.error.HTTPError("https://example.invalid", 401, "x", {}, io.BytesIO(body))
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(ProviderError) as caught:
                post_json("https://example.invalid", {}, {})
        self.assertIn(SECRET, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
