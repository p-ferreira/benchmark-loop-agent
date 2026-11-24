"""Offline tests of tracing: off by default, on against a local stand-in receiver, failures contained."""

import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import httpx2

from benchmark_loop_agent import tracing
from benchmark_loop_agent.batch import RunParameters, run_batch
from benchmark_loop_agent.dataset import load_cases
from benchmark_loop_agent.providers import send_request
from benchmark_loop_agent.store import read_manifest, read_records
from tests.receiver import Receiver
from tests.support import SECRET, FakeSend, case_by_id, environment, openai_reply, right_calls

CASE = case_by_id("simple_python", "simple_python_0")
PHOENIX_KEY = "phoenix-test-KEY-456"
WIRE = {"id": "resp_1", "object": "response", "model": "gpt-actual", "status": "completed",
        "output": [{"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": "calculate_triangle_area",
                    "arguments": json.dumps({"base": 10, "height": 5}), "status": "completed"}],
        "usage": {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10}}


def parameters(**changes) -> RunParameters:
    values = dict(categories=("simple_python",), sample_size=2, seed=1, providers=("openai",),
                  models={"openai": "requested-model"}, concurrency=1)
    return RunParameters(**{**values, **changes})


def perfect(provider, request):
    prompt = json.dumps(request)
    case = next(c for c in load_cases("simple_python") if c.messages[0]["content"] in prompt)
    return openai_reply(right_calls(case))


def wrong(provider, request):
    return openai_reply([{"calculate_triangle_area": {"base": 99, "height": 1}}])


def stable(rows):
    return [{k: v for k, v in r.items() if k != "latency_seconds"} for r in rows]


class TracingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp()) / "out"
        self.receiver = Receiver()
        self.addCleanup(self.receiver.close)

    def run_batch(self, send, env, directory=None, **changes):
        directory = directory or self.directory
        return run_batch(directory, parameters(**changes), env, send, sleep=lambda s: None,
                         tracing_for=lambda run_id: tracing.configure(env, run_id))

    def env(self, **extra):
        return {**environment("openai"), "PHOENIX_COLLECTOR_ENDPOINT": self.receiver.url, **extra}


class OffByDefault(TracingTestCase):
    def test_nothing_is_sent_and_nothing_is_instrumented(self) -> None:
        env = environment("openai")
        with mock.patch.object(tracing, "_Redact", side_effect=AssertionError):
            self.assertIsNone(tracing.configure(env, "run"))
            records = self.run_batch(FakeSend(perfect), env)
        self.assertEqual(self.receiver.spans, [])
        self.assertEqual(self.receiver.paths, [])
        self.assertEqual(len(records), 2)

    def test_blank_endpoint_is_off(self) -> None:
        self.assertIsNone(tracing.configure({"PHOENIX_COLLECTOR_ENDPOINT": "  "}, "run"))

    def test_records_are_identical_with_and_without_tracing(self) -> None:
        plain = Path(tempfile.mkdtemp()) / "plain"
        run_batch(plain, parameters(), environment("openai"), FakeSend(wrong), sleep=lambda s: None)
        self.run_batch(FakeSend(wrong), self.env())
        self.assertEqual(stable(read_records(plain / "records.jsonl")),
                         stable(read_records(self.directory / "records.jsonl")))


class TracingOn(TracingTestCase):
    def test_one_trace_per_case_with_its_attributes(self) -> None:
        self.run_batch(FakeSend(wrong), self.env(PHOENIX_PROJECT_NAME="my-project"))
        spans = self.receiver.case_spans()
        records = read_records(self.directory / "records.jsonl")
        self.assertEqual(len(spans), len(records))
        self.assertEqual(set(self.receiver.paths), {"/v1/traces"})  # base address plus the OTLP path
        run_id = read_manifest(self.directory)["run_id"]
        for span in spans:
            a = span["attributes"]
            self.assertEqual(span["resource"]["openinference.project.name"], "my-project")
            self.assertEqual(a["benchmark.run_id"], run_id)
            self.assertEqual(a["benchmark.category"], "simple_python")
            self.assertEqual(a["benchmark.requested_model"], "requested-model")
            self.assertEqual(a["benchmark.actual_model"], "gpt-actual")
            self.assertEqual(a["benchmark.verdict"], "fail")
            self.assertTrue(a["benchmark.failure_reason"])
            metadata = json.loads(a["metadata"])
            self.assertEqual((metadata["category"], metadata["verdict"]), ("simple_python", "fail"))
        self.assertEqual({s["attributes"]["benchmark.case_id"] for s in spans}, {r["case_id"] for r in records})

    def test_pass_has_a_verdict_and_no_failure_reason(self) -> None:
        self.run_batch(FakeSend(perfect), self.env())
        for span in self.receiver.case_spans():
            self.assertEqual(span["attributes"]["benchmark.verdict"], "pass")
            self.assertNotIn("benchmark.failure_reason", span["attributes"])

    def test_instrumentation_spans_are_children_of_the_case_trace(self) -> None:
        def answer(request: httpx2.Request) -> httpx2.Response:
            return httpx2.Response(200, json=WIRE)

        client = httpx2.Client(transport=httpx2.MockTransport(answer))
        send = lambda name, key, request: send_request(name, key, request, http_client=client)  # noqa: E731
        self.run_batch(send, self.env(), sample_size=1)
        by_id = {s["span_id"]: s for s in self.receiver.spans}
        parents = [s for s in self.receiver.case_spans()]
        children = [s for s in self.receiver.spans if s["name"] != "benchmark_case"]
        self.assertEqual(len(parents), 1)
        self.assertTrue(children, "the OpenInference instrumentation recorded no span")
        for child in children:
            self.assertEqual(child["trace_id"], parents[0]["trace_id"])
            self.assertIn(child["parent_id"], by_id)
        self.assertEqual(children[0]["attributes"].get("openinference.span.kind"), "LLM")
        self.assertEqual(children[0]["attributes"].get("llm.token_count.prompt"), 7)

    def test_unscored_before_any_reply_has_a_trace_without_actual_model(self) -> None:
        env = {"PHOENIX_COLLECTOR_ENDPOINT": self.receiver.url, "OPENAI_MODEL": "requested-model"}
        self.run_batch(FakeSend(perfect), env, sample_size=1)
        (span,) = self.receiver.case_spans()
        a = span["attributes"]
        self.assertEqual((a["benchmark.verdict"], a["benchmark.requested_model"]), ("unscored", "requested-model"))
        self.assertIn("OPENAI_API_KEY is not set", a["benchmark.failure_reason"])
        self.assertNotIn("benchmark.actual_model", a)
        self.assertNotIn("actual_model", json.loads(a["metadata"]))
        self.assertFalse([k for k in a if "token" in k])

    def test_an_unscored_case_that_passes_on_resume_has_two_traces(self) -> None:
        env = self.env()
        self.run_batch(FakeSend(RuntimeError("down")), env, sample_size=1)
        first = self.receiver.case_spans()
        self.assertEqual([s["attributes"]["benchmark.verdict"] for s in first], ["unscored"])
        self.run_batch(FakeSend(perfect), env, sample_size=1)
        spans = self.receiver.case_spans()
        self.assertEqual(sorted(s["attributes"]["benchmark.verdict"] for s in spans), ["pass", "unscored"])
        self.assertEqual({s["attributes"]["benchmark.run_id"] for s in spans}, {read_manifest(self.directory)["run_id"]})
        self.assertEqual(sorted(s["attributes"]["benchmark.invocation"] for s in spans), [1, 2])
        self.assertEqual(len({s["trace_id"] for s in spans}), 2)

    def test_phoenix_key_is_sent_as_a_header_and_kept_out_of_records_and_traces(self) -> None:
        self.run_batch(FakeSend(wrong), self.env(PHOENIX_API_KEY=PHOENIX_KEY))
        self.assertEqual(self.receiver.headers[0]["authorization"], f"Bearer {PHOENIX_KEY}")
        everything = json.dumps(self.receiver.spans) + (self.directory / "records.jsonl").read_text() \
            + (self.directory / "run.json").read_text()
        self.assertNotIn(PHOENIX_KEY, everything)

    def test_phoenix_key_is_removed_from_library_logs(self) -> None:
        record = logging.LogRecord("opentelemetry", logging.ERROR, "", 0, "failed with %s", (PHOENIX_KEY,), None)
        self.assertTrue(tracing._Redact(PHOENIX_KEY).filter(record))
        self.assertNotIn(PHOENIX_KEY, record.getMessage())


class ExportFailures(TracingTestCase):
    def baseline(self, send):
        plain = Path(tempfile.mkdtemp()) / "plain"
        records = run_batch(plain, parameters(), environment("openai"), send, sleep=lambda s: None)
        return stable(read_records(plain / "records.jsonl")), [r.outcome for r in records]

    def check_unchanged(self, env) -> None:
        expected, outcomes = self.baseline(FakeSend(wrong))
        with mock.patch.object(tracing, "EXPORT_TIMEOUT_SECONDS", 1), mock.patch.object(tracing, "FLUSH_TIMEOUT_MILLIS", 2000):
            records = self.run_batch(FakeSend(wrong), env)
        self.assertEqual(stable(read_records(self.directory / "records.jsonl")), expected)
        self.assertEqual([r.outcome for r in records], outcomes)

    def test_a_receiver_that_answers_with_an_error(self) -> None:
        self.receiver.status = 500
        self.check_unchanged(self.env())

    def test_a_receiver_that_is_not_there(self) -> None:
        self.receiver.close()
        from tests.support import ALLOWED_LOCAL_PORTS
        ALLOWED_LOCAL_PORTS.add(self.receiver.port)  # connection refused, not a refused test
        self.addCleanup(ALLOWED_LOCAL_PORTS.discard, self.receiver.port)
        self.check_unchanged(self.env())

    def test_an_exception_inside_the_span_code_changes_nothing(self) -> None:
        expected, _ = self.baseline(FakeSend(wrong))
        with mock.patch("opentelemetry.trace.use_span", side_effect=RuntimeError("boom")):
            self.run_batch(FakeSend(wrong), self.env())
        self.assertEqual(stable(read_records(self.directory / "records.jsonl")), expected)

    def test_a_failed_export_is_not_sent_again_on_resume(self) -> None:
        self.receiver.status = 500
        with mock.patch.object(tracing, "EXPORT_TIMEOUT_SECONDS", 1), mock.patch.object(tracing, "FLUSH_TIMEOUT_MILLIS", 2000):
            self.run_batch(FakeSend(wrong), self.env())
        self.receiver.status = 200
        self.run_batch(FakeSend(wrong), self.env())  # every case finished: nothing runs, nothing is sent
        self.assertEqual(self.receiver.spans, [])
        self.assertEqual(sorted(p.name for p in self.directory.iterdir()), ["records.jsonl", "run.json"])


if __name__ == "__main__":
    unittest.main()
