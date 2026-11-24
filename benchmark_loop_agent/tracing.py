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
from typing import Any, Iterator, Mapping

ENDPOINT_ENV = "PHOENIX_COLLECTOR_ENDPOINT"
API_KEY_ENV = "PHOENIX_API_KEY"
PROJECT_ENV = "PHOENIX_PROJECT_NAME"
DEFAULT_PROJECT = "benchmark-loop-agent"
OTLP_PATH = "/v1/traces"
EXPORT_TIMEOUT_SECONDS = 5
FLUSH_TIMEOUT_MILLIS = 10_000
SPAN_NAME = "benchmark_case"


class _Redact(logging.Filter):
    """Keep the Phoenix key out of anything the OpenTelemetry libraries log."""

    def __init__(self, secret: str) -> None:
        super().__init__()
        self.secret = secret

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            text = record.getMessage()
            if self.secret in text:
                record.msg, record.args = text.replace(self.secret, "[redacted]"), None
            if record.exc_info:  # a traceback could carry it too; keep the type only
                record.msg, record.args = f"{record.getMessage()} ({record.exc_info[0].__name__})", None
                record.exc_info = record.exc_text = None
        except Exception:
            return False
        return True


class Tracing:
    """A configured exporter. Build one with ``configure``; ``None`` means tracing is off."""

    def __init__(self, provider: Any, tracer: Any, run_id: str, instrumentors: tuple[Any, ...] = ()) -> None:
        self._instrumentors = instrumentors
        self._provider = provider
        self._tracer = tracer
        self.run_id = run_id

    @contextlib.contextmanager
    def case(self, *, provider: str, requested_model: str | None, case_id: str,
             category: str, invocation: int) -> Iterator["CaseSpan"]:
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
            span = self._tracer.start_span(SPAN_NAME, attributes=attributes)
            token = trace.use_span(span, end_on_exit=False)
            token.__enter__()
        except Exception:
            span = token = None
        handle = CaseSpan(span, {"run_id": self.run_id, "case_id": case_id, "category": category,
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

    def shutdown(self) -> None:
        """Send what is queued, within a time limit. A failure here is not reported as an error."""
        with contextlib.suppress(Exception):
            self._provider.force_flush(FLUSH_TIMEOUT_MILLIS)
        with contextlib.suppress(Exception):
            self._provider.shutdown()
        for instrumentor in self._instrumentors:
            with contextlib.suppress(Exception):
                instrumentor.uninstrument()


class CaseSpan:
    """What the runner tells the span once the case is judged."""

    def __init__(self, span: Any, metadata: dict[str, Any]) -> None:
        self._span = span
        self._metadata = metadata
        self._outcome: tuple[Any, ...] | None = None

    def outcome(self, record: Any) -> None:
        self._outcome = (record.outcome, record.actual_model, list(record.reasons))

    def finish(self) -> None:
        if self._span is None:
            return
        try:
            attributes: dict[str, Any] = {}
            metadata = dict(self._metadata)
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
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        api_key = environment.get(API_KEY_ENV) or None
        if api_key:
            for name in ("opentelemetry", "urllib3", "requests"):
                logging.getLogger(name).addFilter(_Redact(api_key))
            for handler in logging.getLogger().handlers:
                handler.addFilter(_Redact(api_key))
        headers = {"authorization": f"Bearer {api_key}"} if api_key else None
        exporter = OTLPSpanExporter(endpoint=endpoint.rstrip("/") + OTLP_PATH, headers=headers,
                                    timeout=EXPORT_TIMEOUT_SECONDS)
        provider = TracerProvider(resource=Resource.create({
            "openinference.project.name": environment.get(PROJECT_ENV) or DEFAULT_PROJECT,
            "service.name": "benchmark-loop-agent",
        }))
        provider.add_span_processor(BatchSpanProcessor(exporter))
        instrumentors = (OpenAIInstrumentor(), AnthropicInstrumentor())
        for instrumentor in instrumentors:
            instrumentor.instrument(tracer_provider=provider)
        return Tracing(provider, provider.get_tracer("benchmark_loop_agent"), run_id, instrumentors)
    except Exception as error:  # tracing must not stop the run
        print(f"tracing disabled: {type(error).__name__}", file=sys.stderr)
        return None
