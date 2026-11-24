"""Optional tracing of a run in Arize Phoenix, over OTLP.

The ``openai`` and ``anthropic`` calls are recorded by the standard
OpenInference instrumentation. This module adds only what that cannot know:
one parent span per attempt at a case and provider, so the instrumentation's
spans for the request(s) become its children and the trace carries the run
identifier, the case, the category and, once it is known, the verdict.

Tracing is best effort and never changes a record, a verdict or the exit
code: every call into OpenTelemetry here is guarded, and an export that
fails is dropped, not kept for later.
"""

import contextlib
import json
import logging
import sys
import time
import traceback
from typing import Any, Callable, Iterator, Mapping, Sequence

import requests
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Event, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import Link
from opentelemetry.trace.status import Status, StatusCode

ENDPOINT_ENV = "PHOENIX_COLLECTOR_ENDPOINT"
API_KEY_ENV = "PHOENIX_API_KEY"
PROJECT_ENV = "PHOENIX_PROJECT_NAME"
DEFAULT_PROJECT = "benchmark-loop-agent"
OTLP_PATH = "/v1/traces"
EXPORT_TIMEOUT_SECONDS = 5
FLUSH_TIMEOUT_MILLIS = 10_000
SPAN_NAME = "benchmark_case"
SCORING_SPAN_NAME = "bfcl_scoring"
ANNOTATION_PATH = "/v1/span_annotations"
ANNOTATION_NAME = "bfcl"
ANNOTATION_TIMEOUT_SECONDS = 5
ANNOTATION_TOTAL_SECONDS = 10
ANNOTATION_BATCH = 100
RELEVANCE_NOTE = ("BFCL's relevance rule: the model passes by making (or not making) a function call; "
                  "this category holds no expected answer.")


def scrub(value: Any, secrets: Sequence[str]) -> Any:
    """``value`` with every secret removed from all strings inside it (lists, tuples, dicts too)."""
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, "[redacted]")
        return value
    if isinstance(value, list):
        return [scrub(item, secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(scrub(item, secrets) for item in value)
    if isinstance(value, Mapping):
        return {scrub(k, secrets): scrub(v, secrets) for k, v in value.items()}
    return value


class _Redact(logging.Filter):
    """Keep secrets out of a log record, whichever logger or handler it reaches."""

    def __init__(self, secrets: Sequence[str]) -> None:
        super().__init__()
        self.secrets = [s for s in secrets if s]

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            text = record.getMessage()
            if any(s in text for s in self.secrets):
                record.msg, record.args = scrub(text, self.secrets), None
            if record.exc_info and record.exc_info[0] is not None:  # a traceback could carry one; keep the type only
                trace = "".join(traceback.format_exception(*record.exc_info))
                if any(s in trace for s in self.secrets):
                    record.msg, record.args = f"{record.getMessage()} ({record.exc_info[0].__name__})", None
                    record.exc_info = record.exc_text = None
        except Exception:
            return False
        return True


def _redact_all_logging(secrets: Sequence[str]) -> Callable[[], None]:
    """Redact at the creation of every log record, so no logger, handler or fallback can print a secret.

    A filter on a logger does not see the events of its children, and the fallback
    handler has none, so the record factory is the one place all of them pass.
    Returns the function that puts the previous factory back.
    """
    previous = logging.getLogRecordFactory()
    redact = _Redact(secrets)

    def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = previous(*args, **kwargs)
        redact.filter(record)
        return record

    logging.setLogRecordFactory(factory)

    def restore() -> None:
        if logging.getLogRecordFactory() is factory:
            logging.setLogRecordFactory(previous)

    return restore


class _SanitizingExporter(SpanExporter):
    """Remove secrets from every span, standard instrumentation spans included, before it leaves."""

    def __init__(self, inner: SpanExporter, secrets: Sequence[str]) -> None:
        self._inner = inner
        self._secrets = [s for s in secrets if s]

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            clean = [self._clean(span) for span in spans]
        except Exception:  # never send what could not be checked
            return SpanExportResult.FAILURE
        return self._inner.export(clean)

    def _clean(self, span: ReadableSpan) -> ReadableSpan:
        secrets = self._secrets
        resource = span.resource
        events = [Event(scrub(e.name, secrets), scrub(dict(e.attributes or {}), secrets), e.timestamp)
                  for e in span.events]
        links = [Link(link.context, scrub(dict(link.attributes or {}), secrets)) for link in span.links]
        status = span.status
        if status is not None and status.description:
            status = Status(status.status_code, scrub(status.description, secrets))
        return ReadableSpan(
            name=scrub(span.name, secrets), context=span.context, parent=span.parent,
            resource=Resource(scrub(dict(resource.attributes), secrets), resource.schema_url),
            attributes=scrub(dict(span.attributes or {}), secrets), events=events, links=links,
            kind=span.kind, status=status, start_time=span.start_time, end_time=span.end_time,
            instrumentation_scope=span.instrumentation_scope)

    def shutdown(self) -> None:
        self._inner.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return self._inner.force_flush(timeout_millis)


class Tracing:
    """A configured exporter. Build one with ``configure``; ``None`` means tracing is off."""

    def __init__(self, provider: Any, tracer: Any, run_id: str, instrumentors: tuple[Any, ...] = (),
                 restore_logging: Callable[[], None] | None = None, endpoint: str | None = None,
                 api_key: str | None = None, secrets: Sequence[str] = ()) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._secrets = [s for s in secrets if s]
        self._annotations: list[dict[str, Any]] = []  # in memory only, never written to disk
        self._restore_logging = restore_logging
        self._instrumentors = instrumentors
        self._provider = provider
        self._tracer = tracer
        self.run_id = run_id

    @contextlib.contextmanager
    def case(self, *, provider: str, requested_model: str | None, case_id: str,
             category: str, invocation: int, question: str | None = None) -> Iterator["CaseSpan"]:
        """The span of one attempt. Only facts known before the model replies go in at the start."""
        span = None
        try:
            from opentelemetry import trace
            attributes = {
                "openinference.span.kind": "CHAIN",
                "session.id": self.run_id,
                "benchmark.run_id": self.run_id,
                "benchmark.invocation": invocation,
                "benchmark.case_id": case_id,
                "benchmark.category": category,
                "benchmark.provider": provider,
            }
            if requested_model is not None:
                attributes["benchmark.requested_model"] = requested_model
            if question is not None:
                attributes["input.value"] = question
                attributes["input.mime_type"] = "text/plain"
            span = self._tracer.start_span(SPAN_NAME, attributes=attributes)
            token = trace.use_span(span, end_on_exit=False)
            token.__enter__()
        except Exception:
            span = token = None
        handle = CaseSpan(span, self, {"run_id": self.run_id, "case_id": case_id, "category": category,
                                 "provider": provider, "requested_model": requested_model,
                                 "invocation": invocation})
        try:
            yield handle
        finally:
            handle.finish()
            if span is not None:
                with contextlib.suppress(Exception):
                    token.__exit__(None, None, None)
                with contextlib.suppress(Exception):
                    span.end()

    def add_annotation(self, annotation: dict[str, Any]) -> None:
        self._annotations.append(annotation)  # list.append is atomic: the runner's threads share it

    def send_annotations(self) -> None:
        """Send the ``bfcl`` annotations once, best effort, bounded in time; nothing is kept or retried."""
        if not self._endpoint or not self._annotations:
            return
        deadline = time.monotonic() + ANNOTATION_TOTAL_SECONDS
        headers = {"authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        url = self._endpoint.rstrip("/") + ANNOTATION_PATH
        try:
            for start in range(0, len(self._annotations), ANNOTATION_BATCH):
                left = deadline - time.monotonic()
                if left <= 0:
                    break
                batch = scrub(self._annotations[start:start + ANNOTATION_BATCH], self._secrets)
                requests.post(url, json={"data": batch}, headers=headers,
                              timeout=min(ANNOTATION_TIMEOUT_SECONDS, left))
        except Exception as error:  # the type only: a message could carry the address or a key
            print(f"annotations not sent: {type(error).__name__}", file=sys.stderr)
        finally:
            self._annotations = []

    def shutdown(self) -> None:
        """Send what is queued, within a time limit. A failure here is not reported as an error."""
        with contextlib.suppress(Exception):
            self._provider.force_flush(FLUSH_TIMEOUT_MILLIS)
        with contextlib.suppress(Exception):
            self.send_annotations()  # after the spans they belong to were exported
        with contextlib.suppress(Exception):
            self._provider.shutdown()
        for instrumentor in self._instrumentors:
            with contextlib.suppress(Exception):
                instrumentor.uninstrument()
        if self._restore_logging is not None:
            with contextlib.suppress(Exception):
                self._restore_logging()


class CaseSpan:
    """What the runner tells the span once the case is judged."""

    def __init__(self, span: Any, tracing: Tracing, metadata: dict[str, Any]) -> None:
        self._span = span
        self._tracing = tracing
        self._metadata = metadata
        self._outcome: tuple[Any, ...] | None = None
        self._output: str | None = None

    def outcome(self, record: Any, case: Any = None) -> None:
        """Called with the finished record: only now is the scoring span written and the expected answer read."""
        self._outcome = (record.outcome, record.actual_model, list(record.reasons))
        try:
            if record.returned_calls is not None:
                self._output = json.dumps(record.to_dict()["returned_calls"])
            if self._span is not None and record.outcome != "unscored":  # unscored: scoring never ran
                self._score(record)
        except Exception:
            pass

    def _score(self, record: Any) -> None:
        from opentelemetry import trace

        from .categories import is_relevance_or_irrelevance
        from .dataset import load_expected_answers

        payload: dict[str, Any] = {"returned_calls": record.to_dict()["returned_calls"]}
        if is_relevance_or_irrelevance(record.category):
            payload["expected_answer"] = None
            payload["note"] = RELEVANCE_NOTE
        else:
            try:
                payload["expected_answer"] = load_expected_answers(record.category).get(record.case_id)
            except Exception:
                payload["expected_answer"] = None
        reason = "; ".join(record.reasons)
        scoring = self._tracing._tracer.start_span(
            SCORING_SPAN_NAME, context=trace.set_span_in_context(self._span),
            attributes={"openinference.span.kind": "EVALUATOR",
                        "input.value": json.dumps(payload), "input.mime_type": "application/json",
                        "output.value": json.dumps({"verdict": record.outcome, "reason": reason}),
                        "output.mime_type": "application/json"})
        scoring.end()

    def finish(self) -> None:
        if self._span is None:
            return
        try:
            attributes: dict[str, Any] = {}
            metadata = dict(self._metadata)
            if self._output is not None:
                attributes["output.value"] = self._output
                attributes["output.mime_type"] = "application/json"
            if self._outcome is not None:
                verdict, actual_model, reasons = self._outcome
                attributes["benchmark.verdict"] = verdict
                metadata["verdict"] = verdict
                if reasons:
                    attributes["benchmark.failure_reason"] = "; ".join(reasons)
                    metadata["failure_reason"] = attributes["benchmark.failure_reason"]
                if actual_model is not None:  # absent, not invented, when no provider replied
                    attributes["benchmark.actual_model"] = actual_model
                    metadata["actual_model"] = actual_model
                if verdict == "unscored":
                    self._span.set_status(Status(StatusCode.ERROR, attributes.get("benchmark.failure_reason", "unscored")))
                else:
                    self._span.set_status(Status(StatusCode.OK))
                result: dict[str, Any] = {"label": verdict}
                if verdict != "unscored":
                    result["score"] = 1 if verdict == "pass" else 0
                if reasons:
                    result["explanation"] = attributes["benchmark.failure_reason"]
                self._tracing.add_annotation({
                    "span_id": format(self._span.get_span_context().span_id, "016x"),
                    "name": ANNOTATION_NAME, "annotator_kind": "CODE", "result": result})
            attributes["metadata"] = json.dumps(metadata)
            self._span.set_attributes(attributes)
        except Exception:
            pass


def configure(environment: Mapping[str, str], run_id: str) -> Tracing | None:
    """Set up export and instrumentation if ``PHOENIX_COLLECTOR_ENDPOINT`` is set; else do nothing."""
    endpoint = (environment.get(ENDPOINT_ENV) or "").strip()
    if not endpoint:
        return None
    try:
        from openinference.instrumentation.anthropic import AnthropicInstrumentor
        from openinference.instrumentation.openai import OpenAIInstrumentor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        from .runner import PROVIDERS  # here, not at the top: runner imports this module

        api_key = environment.get(API_KEY_ENV) or None
        secrets = [key for p in PROVIDERS.values() if (key := environment.get(p.key_env))]
        if api_key:
            secrets.append(api_key)
        restore_logging = _redact_all_logging(secrets) if secrets else None
        headers = {"authorization": f"Bearer {api_key}"} if api_key else None
        exporter = OTLPSpanExporter(endpoint=endpoint.rstrip("/") + OTLP_PATH, headers=headers,
                                    timeout=EXPORT_TIMEOUT_SECONDS)
        provider = TracerProvider(resource=Resource.create({
            "openinference.project.name": scrub(environment.get(PROJECT_ENV) or DEFAULT_PROJECT, secrets),
            "service.name": "benchmark-loop-agent",
        }))
        provider.add_span_processor(BatchSpanProcessor(_SanitizingExporter(exporter, secrets)))
        instrumentors = (OpenAIInstrumentor(), AnthropicInstrumentor())
        for instrumentor in instrumentors:
            instrumentor.instrument(tracer_provider=provider)
        return Tracing(provider, provider.get_tracer("benchmark_loop_agent"), run_id, instrumentors, restore_logging,
                       endpoint, api_key, secrets)
    except Exception as error:  # tracing must not stop the run
        for instrumentor in locals().get("instrumentors") or ():
            try:
                instrumentor.uninstrument()
            except Exception:
                pass
        if (provider := locals().get("provider")) is not None:
            try:
                provider.shutdown()
            except Exception:
                pass
        if (restore := locals().get("restore_logging")) is not None:
            restore()
        print(f"tracing disabled: {type(error).__name__}", file=sys.stderr)
        return None
