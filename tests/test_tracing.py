"""Offline tests of tracing: off by default, on against a local stand-in receiver, failures contained."""

import json
import contextlib
import io
import logging
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import httpx2
import requests

from benchmark_loop_agent import tracing
from benchmark_loop_agent.batch import RunParameters, run_batch
from benchmark_loop_agent.dataset import answer_path, load_cases, load_expected_answers
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

    def test_the_expected_size_of_each_category_is_saved(self) -> None:
        self.run_batch(FakeSend(wrong), environment("openai"), sample_size=0)
        self.assertEqual(read_manifest(self.directory)["selection"], {"simple_python": 0})
        other = Path(tempfile.mkdtemp()) / "other"
        self.run_batch(FakeSend(wrong), environment("openai"), directory=other)
        self.assertEqual(read_manifest(other)["selection"], {"simple_python": 2})

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
        self.assertEqual(set(self.receiver.paths), {"/v1/traces", "/v1/span_annotations"})  # base address plus each path
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


class CaseSpanContent(TracingTestCase):
    """The case span's input, output and status; the scoring span; the annotation of each verdict."""

    def by_case(self):
        return {s["attributes"]["benchmark.case_id"]: s for s in self.receiver.case_spans()}

    def test_a_pass_has_input_output_and_status_ok(self) -> None:
        self.run_batch(FakeSend(perfect), self.env(), sample_size=1)
        (span,) = self.receiver.case_spans()
        (record,) = read_records(self.directory / "records.jsonl")
        a = span["attributes"]
        question = next(c for c in load_cases("simple_python") if c.case_id == record["case_id"]).messages[0]["content"]
        self.assertEqual(a["input.value"], question)
        self.assertEqual(a["input.mime_type"], "text/plain")
        self.assertEqual(json.loads(a["output.value"]), record["returned_calls"])
        self.assertEqual(a["output.mime_type"], "application/json")
        self.assertEqual(span["status"], (1, ""))  # STATUS_CODE_OK

    def test_a_fail_is_a_completed_case_not_an_error(self) -> None:
        self.run_batch(FakeSend(wrong), self.env(), sample_size=1)
        (span,) = self.receiver.case_spans()
        self.assertEqual(span["status"], (1, ""))
        self.assertEqual(json.loads(span["attributes"]["output.value"]),
                         [{"calculate_triangle_area": {"base": 99, "height": 1}}])

    def test_an_unscored_case_is_an_error_with_the_reason(self) -> None:
        env = {"PHOENIX_COLLECTOR_ENDPOINT": self.receiver.url, "OPENAI_MODEL": "requested-model"}
        self.run_batch(FakeSend(perfect), env, sample_size=1)
        (span,) = self.receiver.case_spans()
        self.assertEqual(span["status"], (2, "OPENAI_API_KEY is not set"))
        self.assertIn("input.value", span["attributes"])
        self.assertNotIn("output.value", span["attributes"])  # no reply, no output
        self.assertEqual(self.receiver.scoring_spans(), [])  # scoring never ran

    def test_a_failed_request_has_no_scoring_span_and_still_an_annotation(self) -> None:
        self.run_batch(FakeSend(RuntimeError("down")), self.env(), sample_size=1)
        self.assertEqual(self.receiver.scoring_spans(), [])
        (annotation,) = self.receiver.annotations
        self.assertEqual(annotation["result"], {"label": "unscored", "explanation": "RuntimeError: down"})

    def test_scoring_span_with_an_expected_answer(self) -> None:
        self.run_batch(FakeSend(wrong), self.env(), sample_size=1)
        (case,), (scoring,) = self.receiver.case_spans(), self.receiver.scoring_spans()
        self.assertEqual((scoring["parent_id"], scoring["trace_id"]), (case["span_id"], case["trace_id"]))
        a = scoring["attributes"]
        self.assertEqual(a["openinference.span.kind"], "EVALUATOR")
        data = json.loads(a["input.value"])
        self.assertEqual(data["returned_calls"], [{"calculate_triangle_area": {"base": 99, "height": 1}}])
        self.assertEqual(data["expected_answer"],
                         load_expected_answers("simple_python")[case["attributes"]["benchmark.case_id"]])
        output = json.loads(a["output.value"])
        self.assertEqual(output["verdict"], "fail")
        self.assertEqual(output["reason"], case["attributes"]["benchmark.failure_reason"])

    def test_scoring_span_of_a_category_without_an_expected_answer(self) -> None:
        self.run_batch(FakeSend(wrong), self.env(), categories=("irrelevance",), sample_size=1)
        (scoring,) = self.receiver.scoring_spans()
        data = json.loads(scoring["attributes"]["input.value"])
        self.assertIsNone(data["expected_answer"])
        self.assertIn("BFCL's relevance rule", data["note"])
        self.assertIn("no expected answer", data["note"])
        self.assertEqual(json.loads(scoring["attributes"]["output.value"])["verdict"], "fail")

    def test_the_expected_answer_is_read_only_after_the_reply_and_never_sent_when_unscored(self) -> None:
        order: list[str] = []
        real = answer_path
        send = FakeSend(lambda p, r: order.append("request") or perfect(p, r))
        with mock.patch("benchmark_loop_agent.dataset.answer_path", lambda c: order.append("answer") or real(c)):
            load_expected_answers.cache_clear()
            self.run_batch(send, self.env(), sample_size=1)
        load_expected_answers.cache_clear()
        self.assertEqual(order[0], "request")
        self.assertIn("answer", order)
        other = Receiver()
        self.addCleanup(other.close)
        env = {"PHOENIX_COLLECTOR_ENDPOINT": other.url, "OPENAI_MODEL": "requested-model"}  # no key: no reply
        run_batch(Path(tempfile.mkdtemp()) / "o", parameters(sample_size=1), env, FakeSend(perfect),
                  sleep=lambda s: None, tracing_for=lambda run_id: tracing.configure(env, run_id))
        sent = json.dumps(other.spans)
        for answer in load_expected_answers("simple_python").values():
            self.assertNotIn(json.dumps(json.dumps(answer))[1:-1], sent)
        self.assertEqual(other.scoring_spans(), [])

    def test_each_verdict_is_one_annotation_on_its_case_span(self) -> None:
        for send, label, score in ((FakeSend(perfect), "pass", 1), (FakeSend(wrong), "fail", 0)):
            self.receiver.annotations.clear()
            self.receiver.spans.clear()
            self.run_batch(send, self.env(), directory=Path(tempfile.mkdtemp()) / "out")
            spans = self.receiver.case_spans()
            self.assertEqual(len(self.receiver.annotations), len(spans))
            self.assertEqual({a["span_id"] for a in self.receiver.annotations}, {s["span_id"] for s in spans})
            for annotation in self.receiver.annotations:
                self.assertEqual((annotation["name"], annotation["annotator_kind"]), ("bfcl", "CODE"))
                self.assertEqual(annotation["result"]["label"], label)
                self.assertEqual(annotation["result"]["score"], score)
                span = next(s for s in spans if s["span_id"] == annotation["span_id"])
                self.assertEqual(annotation["result"].get("explanation"),
                                 span["attributes"].get("benchmark.failure_reason"))

    def test_unscored_annotation_has_a_label_and_no_score(self) -> None:
        self.run_batch(FakeSend(RuntimeError("down")), self.env(), sample_size=1)
        (annotation,) = self.receiver.annotations
        self.assertEqual(annotation["result"]["label"], "unscored")
        self.assertNotIn("score", annotation["result"])

    def test_annotations_are_posted_to_the_configured_address_with_the_key(self) -> None:
        self.run_batch(FakeSend(wrong), self.env(PHOENIX_API_KEY=PHOENIX_KEY), sample_size=1)
        self.assertIn("/v1/span_annotations", self.receiver.paths)
        self.assertEqual(self.receiver.headers[-1]["authorization"], f"Bearer {PHOENIX_KEY}")
        self.assertNotIn(PHOENIX_KEY, json.dumps(self.receiver.annotations))

    def test_nothing_is_sent_with_the_endpoint_unset(self) -> None:
        self.run_batch(FakeSend(wrong), environment("openai"))
        self.assertEqual((self.receiver.paths, self.receiver.annotations), ([], []))

    def test_annotation_failures_change_nothing(self) -> None:
        expected, outcomes = ExportFailures.baseline(self, FakeSend(wrong))
        for status, delay in ((500, 0), (200, 3)):
            directory = Path(tempfile.mkdtemp()) / "out"
            self.receiver.annotation_status, self.receiver.annotation_delay = status, delay
            with mock.patch.object(tracing, "ANNOTATION_TIMEOUT_SECONDS", 1), contextlib.redirect_stderr(io.StringIO()):
                records = self.run_batch(FakeSend(wrong), self.env(), directory=directory)
            self.assertEqual(stable(read_records(directory / "records.jsonl")), expected)
            self.assertEqual([r.outcome for r in records], outcomes)
            self.assertEqual(sorted(p.name for p in directory.iterdir()), ["records.jsonl", "run.json"])
        with mock.patch("requests.adapters.HTTPAdapter.send", side_effect=requests.ConnectionError("refused")):
            records = self.run_batch(FakeSend(wrong), self.env(), directory=Path(tempfile.mkdtemp()) / "out")
        self.assertEqual([r.outcome for r in records], outcomes)

    def test_a_failed_annotation_send_is_not_repeated_on_resume(self) -> None:
        self.receiver.annotation_status = 500
        with contextlib.redirect_stderr(io.StringIO()):
            self.run_batch(FakeSend(wrong), self.env())
        self.receiver.annotation_status = 200
        self.run_batch(FakeSend(wrong), self.env())
        self.assertEqual(self.receiver.annotations, [])


class Redaction(TracingTestCase):
    def test_an_exporter_error_does_not_print_the_phoenix_key(self) -> None:
        self.receiver.status, self.receiver.reason = 401, f"bad key {PHOENIX_KEY}"
        stderr, captured = io.StringIO(), io.StringIO()
        handler = logging.StreamHandler(captured)
        logging.getLogger().addHandler(handler)
        self.addCleanup(logging.getLogger().removeHandler, handler)
        with contextlib.redirect_stderr(stderr), mock.patch.object(tracing, "FLUSH_TIMEOUT_MILLIS", 3000):
            self.run_batch(FakeSend(wrong), self.env(PHOENIX_API_KEY=PHOENIX_KEY), sample_size=1)
        self.assertTrue(self.receiver.headers, "the exporter never reached the receiver")
        self.assertNotIn(PHOENIX_KEY, stderr.getvalue() + captured.getvalue())
        self.assertIn("[redacted]", stderr.getvalue() + captured.getvalue())
        self.assertIs(logging.getLogRecordFactory(), logging.LogRecord)  # restored on shutdown

    def test_instrumented_responses_and_the_project_name_are_scrubbed_before_export(self) -> None:
        leaking = {**WIRE, "model": f"model-{PHOENIX_KEY}-{SECRET}"}

        def answer(request: httpx2.Request) -> httpx2.Response:
            return httpx2.Response(200, json=leaking)

        client = httpx2.Client(transport=httpx2.MockTransport(answer))
        send = lambda name, key, request: send_request(name, key, request, http_client=client)  # noqa: E731
        env = self.env(PHOENIX_API_KEY=PHOENIX_KEY, PHOENIX_PROJECT_NAME=f"project-{PHOENIX_KEY}")
        self.run_batch(send, env, sample_size=1)
        self.assertTrue([s for s in self.receiver.spans if s["name"] != "benchmark_case"])
        sent = json.dumps(self.receiver.spans)
        for secret in (PHOENIX_KEY, SECRET):
            self.assertNotIn(secret, sent)
        self.assertIn("[redacted]", sent)


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
        # Refuse the connection at the transport: the test never touches a port it does not own.
        with mock.patch("requests.adapters.HTTPAdapter.send", side_effect=requests.ConnectionError("refused")):
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
