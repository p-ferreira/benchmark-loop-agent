"""Offline tests: both adapters through pass, fail and error paths, with the provider call replaced."""

import json
import unittest
from typing import Any

import httpx2

from benchmark_loop_agent.providers import ProviderError, request_anthropic, request_openai, send_request
from benchmark_loop_agent.runner import MAX_REASON_LENGTH, run_provider
from tests.support import (SECRET, FakeSend, anthropic_reply, case_by_id, environment, openai_reply,
                           reply_for, right_calls)

CASE = case_by_id("simple_python", "simple_python_0")
NAME = "calculate_triangle_area"
RIGHT = {"base": 10, "height": 5}
WRONG = {"base": 11, "height": 5}


def run(provider: str, reply: Any, case=CASE):
    post = FakeSend(reply)
    return run_provider(provider, case, environment(provider), post), post


class AdapterTests(unittest.TestCase):
    def test_openai_pass_and_request_shape(self) -> None:
        record, post = run("openai", openai_reply([{NAME: RIGHT}]))
        self.assertEqual(record.outcome, "pass")
        self.assertEqual(record.category, "simple_python")
        self.assertEqual(record.returned_calls, [{NAME: RIGHT}])
        self.assertEqual((record.requested_model, record.actual_model), ("requested-model", "gpt-actual"))
        self.assertEqual((record.input_tokens, record.output_tokens), (7, 3))
        provider, api_key, body = post.requests[0]
        self.assertEqual((provider, api_key), ("openai", SECRET))
        tool = body["tools"][0]
        self.assertEqual((tool["type"], tool["name"], tool["parameters"]["type"]), ("function", NAME, "object"))
        self.assertIs(tool["strict"], False)  # optional BFCL parameters stay optional
        self.assertEqual(body["input"], [{"role": "user", "content": CASE.messages[0]["content"]}])

    def test_anthropic_pass_and_request_shape(self) -> None:
        record, post = run("anthropic", anthropic_reply([{NAME: RIGHT}]))
        self.assertEqual(record.outcome, "pass")
        self.assertEqual((record.input_tokens, record.output_tokens), (8, 4))
        body = post.requests[0][2]
        self.assertEqual(body["tools"][0]["input_schema"]["type"], "object")
        self.assertNotIn("system", body)

    def test_wrong_value_and_missing_call_fail(self) -> None:
        for provider in ("openai", "anthropic"):
            with self.subTest(provider=provider):
                record, _ = run(provider, reply_for(provider, [{NAME: WRONG}]))
                self.assertEqual(record.outcome, "fail")
                self.assertTrue(record.reasons)
                record, _ = run(provider, reply_for(provider, []))
                self.assertEqual((record.outcome, record.returned_calls), ("fail", []))

    def test_malformed_openai_arguments_fail_and_are_kept_raw(self) -> None:
        for raw in ("{bad", "null", "1", "[1]", '{"base": ' + "9" * 4301 + "}", "[" * 100000):
            with self.subTest(raw=raw[:10]):
                record, _ = run("openai", openai_reply([{NAME: raw}], raw=True))
                self.assertEqual(record.outcome, "fail")
                self.assertEqual(record.actual_model, "gpt-actual")
                self.assertEqual(record.returned_calls, [{NAME: raw}])

    def test_non_object_anthropic_input_fails_and_is_kept(self) -> None:
        record, _ = run("anthropic", anthropic_reply([{NAME: "oops"}]))
        self.assertEqual((record.outcome, record.returned_calls), ("fail", [{NAME: "oops"}]))

    def test_provider_error_is_unscored_for_both(self) -> None:
        for provider in ("openai", "anthropic"):
            with self.subTest(provider=provider):
                record, _ = run(provider, ProviderError("HTTP 500: boom"))
                self.assertEqual(record.outcome, "unscored")
                self.assertIsNone(record.returned_calls)
                self.assertIn("boom", record.reasons[0])
                record, _ = run(provider, {"unexpected": True})
                self.assertEqual(record.outcome, "unscored")

    def test_missing_key_and_missing_model_are_unscored_without_a_request(self) -> None:
        for env, expected in (({"OPENAI_MODEL": "m"}, "OPENAI_API_KEY"), ({"OPENAI_API_KEY": "k"}, "OPENAI_MODEL")):
            post = FakeSend(openai_reply([{NAME: RIGHT}]))
            record = run_provider("openai", CASE, env, post)
            self.assertEqual(record.outcome, "unscored")
            self.assertIn(expected, record.reasons[0])
            self.assertEqual(post.requests, [])


class SecretTests(unittest.TestCase):
    def test_keys_echoed_in_a_successful_response_are_redacted_everywhere(self) -> None:
        other = "sk-ant-OTHER-456"
        reply = openai_reply([{NAME: {**RIGHT, "unit": f"{SECRET} {other}"}}])
        env = {**environment("openai"), "ANTHROPIC_API_KEY": other}
        record = run_provider("openai", CASE, env, FakeSend(reply))
        text = json.dumps(record.to_dict())
        self.assertNotIn(SECRET, text)
        self.assertNotIn(other, text)
        self.assertIn("[redacted]", text)

    def test_key_in_exception_text_never_reaches_the_record(self) -> None:
        for provider in ("openai", "anthropic"):
            with self.subTest(provider=provider):
                record, _ = run(provider, RuntimeError(f"connection failed, key={SECRET}"))
                self.assertNotIn(SECRET, json.dumps(record.to_dict()))
                self.assertIn("[redacted]", record.reasons[0])

    def test_key_crossing_the_reason_cutoff_is_fully_redacted(self) -> None:
        for offset in range(len(SECRET) + 1):
            with self.subTest(offset=offset):
                prefix = "x" * (MAX_REASON_LENGTH - len("RuntimeError: ") - offset)
                record, _ = run("openai", RuntimeError(prefix + SECRET))
                reason = record.reasons[0]
                self.assertLessEqual(len(reason), MAX_REASON_LENGTH)
                for n in range(4, len(SECRET) + 1):
                    self.assertNotIn(SECRET[:n], reason)


class OfficialLibraryTests(unittest.TestCase):
    """The real ``send_request``, with the libraries' HTTP client answered locally."""

    def through_library(self, status: int, reply: Any):
        seen: list[httpx2.Request] = []

        def answer(request: httpx2.Request) -> httpx2.Response:
            seen.append(request)
            return httpx2.Response(status, json=reply)

        client = httpx2.Client(transport=httpx2.MockTransport(answer))
        return (lambda name, key, request: send_request(name, key, request, http_client=client)), seen

    def test_openai_library_posts_to_responses(self) -> None:
        wire = {"id": "resp_1", "object": "response", "model": "gpt-actual", "status": "completed",
                "output": [{"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": NAME,
                            "arguments": json.dumps(RIGHT), "status": "completed"}],
                "usage": {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10}}
        send, seen = self.through_library(200, wire)
        response = request_openai(SECRET, "requested-model", CASE, send)
        self.assertEqual(response.calls, [{NAME: RIGHT}])
        self.assertEqual((response.actual_model, response.input_tokens, response.output_tokens), ("gpt-actual", 7, 3))
        self.assertEqual(seen[0].url.path, "/v1/responses")
        self.assertEqual(seen[0].headers["authorization"], f"Bearer {SECRET}")

    def test_anthropic_library_posts_to_messages(self) -> None:
        wire = {"id": "msg_1", "type": "message", "role": "assistant", "model": "claude-actual",
                "content": [{"type": "tool_use", "id": "toolu_1", "name": NAME, "input": RIGHT}],
                "stop_reason": "tool_use", "usage": {"input_tokens": 8, "output_tokens": 4}}
        send, seen = self.through_library(200, wire)
        response = request_anthropic(SECRET, "requested-model", CASE, send)
        self.assertEqual(response.calls, [{NAME: RIGHT}])
        self.assertEqual(seen[0].url.path, "/v1/messages")
        self.assertIn(SECRET, " ".join(seen[0].headers.values()))

    def test_a_refused_request_raises_with_the_provider_message(self) -> None:
        for provider, adapter in (("openai", request_openai), ("anthropic", request_anthropic)):
            with self.subTest(provider=provider):
                send, seen = self.through_library(401, {"error": {"message": "bad key here"}})
                with self.assertRaises(Exception) as caught:
                    adapter(SECRET, "requested-model", CASE, send)
                self.assertIn("bad key here", str(caught.exception))
                self.assertEqual(len(seen), 1)  # the libraries do not retry on their own

    def test_the_libraries_do_not_retry_a_server_error_themselves(self) -> None:
        send, seen = self.through_library(500, {"error": {"message": "down"}})
        with self.assertRaises(Exception):
            request_openai(SECRET, "requested-model", CASE, send)
        self.assertEqual(len(seen), 1)


class RightCallFixtureTests(unittest.TestCase):
    def test_the_fixture_builds_the_calls_the_pinned_case_expects(self) -> None:
        self.assertEqual(right_calls(CASE), [{NAME: {"base": 10, "height": 5, "unit": "units"}}])


if __name__ == "__main__":
    unittest.main()
