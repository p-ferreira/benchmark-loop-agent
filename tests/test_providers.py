"""Offline tests: both adapters through pass, fail and error paths, with the provider call replaced."""

import json
import unittest
from typing import Any

import httpx2

from benchmark_loop_agent.case import load_case
from benchmark_loop_agent.providers import ProviderError, request_anthropic, request_openai, send_request
from benchmark_loop_agent.runner import run_provider

SECRET = "sk-test-SECRET-123"
RIGHT = {"base": 10, "height": 5}
WRONG = {"base": 11, "height": 5}
NAME = "calculate_triangle_area"


def openai_reply(arguments: Any) -> dict[str, Any]:
    """A Responses API reply: one tool call among the other item types the API returns."""
    return {
        "model": "gpt-actual",
        "output": [
            {"type": "reasoning", "summary": []},
            {"type": "function_call", "name": NAME, "arguments": arguments, "call_id": "call_1"},
            {"type": "message", "content": [{"type": "output_text", "text": "done"}]},
        ],
        "usage": {"input_tokens": 7, "output_tokens": 3},
    }


def anthropic_reply(arguments: dict[str, Any] | None) -> dict[str, Any]:
    content = [] if arguments is None else [{"type": "tool_use", "name": NAME, "input": arguments}]
    return {"model": "claude-actual", "content": content, "usage": {"input_tokens": 8, "output_tokens": 4}}


def environment(provider: str) -> dict[str, str]:
    prefix = provider.upper()
    return {f"{prefix}_API_KEY": SECRET, f"{prefix}_MODEL": "requested-model"}


class FakePost:
    """Stands in for the call into the provider's library and remembers what was sent."""

    def __init__(self, reply: dict[str, Any] | Exception) -> None:
        self.reply = reply
        self.requests: list[tuple[str, str, dict[str, Any]]] = []

    def __call__(self, provider: str, api_key: str, request: dict[str, Any]) -> dict[str, Any]:
        self.requests.append((provider, api_key, request))
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
        provider, api_key, body = post.requests[0]
        self.assertEqual((provider, api_key), ("openai", SECRET))
        tool = body["tools"][0]
        self.assertEqual((tool["type"], tool["name"], tool["parameters"]["type"]), ("function", NAME, "object"))
        # Optional BFCL parameters stay optional: strict mode would reject the schema.
        self.assertIs(tool["strict"], False)
        self.assertEqual(body["input"], [{"role": "user", "content": load_case().prompt}])

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
        provider, api_key, body = post.requests[0]
        self.assertEqual((provider, api_key), ("anthropic", SECRET))
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


class OfficialLibraryTests(unittest.TestCase):
    """The real ``send_request``, with the libraries' HTTP client answered locally."""

    def send_through_library(self, provider: str, status: int, reply: Any):
        seen: list[httpx2.Request] = []

        def answer(request: httpx2.Request) -> httpx2.Response:
            seen.append(request)
            return httpx2.Response(status, json=reply)

        client = httpx2.Client(transport=httpx2.MockTransport(answer))

        def send(name: str, api_key: str, request: dict[str, Any]) -> dict[str, Any]:
            return send_request(name, api_key, request, http_client=client)

        adapter = {"openai": request_openai, "anthropic": request_anthropic}[provider]
        return adapter, send, seen

    def test_openai_library_posts_to_responses_and_its_reply_is_understood(self) -> None:
        wire = {
            "id": "resp_1", "object": "response", "model": "gpt-actual", "status": "completed",
            "output": [{"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": NAME,
                        "arguments": json.dumps(RIGHT), "status": "completed"}],
            "usage": {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10},
        }
        adapter, send, seen = self.send_through_library("openai", 200, wire)
        response = adapter(SECRET, "requested-model", load_case(), send)
        self.assertEqual(response.calls, [{NAME: RIGHT}])
        self.assertEqual((response.actual_model, response.input_tokens, response.output_tokens), ("gpt-actual", 7, 3))
        self.assertEqual(seen[0].url.path, "/v1/responses")
        self.assertEqual(seen[0].headers["authorization"], f"Bearer {SECRET}")
        sent = json.loads(seen[0].content)
        self.assertEqual((sent["model"], sent["store"], sent["tools"][0]["name"]), ("requested-model", False, NAME))

    def test_anthropic_library_posts_to_messages_and_its_reply_is_understood(self) -> None:
        wire = {
            "id": "msg_1", "type": "message", "role": "assistant", "model": "claude-actual",
            "content": [{"type": "tool_use", "id": "toolu_1", "name": NAME, "input": RIGHT}],
            "stop_reason": "tool_use", "usage": {"input_tokens": 8, "output_tokens": 4},
        }
        adapter, send, seen = self.send_through_library("anthropic", 200, wire)
        response = adapter(SECRET, "requested-model", load_case(), send)
        self.assertEqual(response.calls, [{NAME: RIGHT}])
        self.assertEqual((response.actual_model, response.input_tokens, response.output_tokens), ("claude-actual", 8, 4))
        self.assertEqual(seen[0].url.path, "/v1/messages")
        # Which header carries the key is the library's business; it must be sent.
        self.assertIn(SECRET, " ".join(seen[0].headers.values()))
        sent = json.loads(seen[0].content)
        self.assertEqual((sent["model"], sent["tools"][0]["input_schema"]["type"]), ("requested-model", "object"))

    def test_a_refused_request_raises_with_the_provider_message(self) -> None:
        for provider in ("openai", "anthropic"):
            with self.subTest(provider=provider):
                adapter, send, _ = self.send_through_library(provider, 401, {"error": {"message": "bad key here"}})
                with self.assertRaises(Exception) as caught:
                    adapter(SECRET, "requested-model", load_case(), send)
                self.assertIn("bad key here", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
