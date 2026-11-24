"""A stand-in OTLP/HTTP receiver on the loopback address, for the tracing tests."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

from tests.support import ALLOWED_LOCAL_PORTS


def _value(any_value: Any) -> Any:
    kind = any_value.WhichOneof("value")
    return getattr(any_value, kind) if kind else None


class Receiver:
    """Collects every span it is sent. ``status`` lets a test make it fail."""

    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.spans: list[dict[str, Any]] = []
        self.paths: list[str] = []
        self.headers: list[dict[str, str]] = []
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                receiver.paths.append(self.path)
                receiver.headers.append({k.lower(): v for k, v in self.headers.items()})
                if receiver.status == 200:
                    request = ExportTraceServiceRequest.FromString(body)
                    for resource in request.resource_spans:
                        resource_attributes = {a.key: _value(a.value) for a in resource.resource.attributes}
                        for scope in resource.scope_spans:
                            for span in scope.spans:
                                receiver.spans.append({
                                    "name": span.name,
                                    "trace_id": span.trace_id.hex(),
                                    "span_id": span.span_id.hex(),
                                    "parent_id": span.parent_span_id.hex(),
                                    "attributes": {a.key: _value(a.value) for a in span.attributes},
                                    "resource": resource_attributes,
                                })
                self.send_response(receiver.status)
                self.end_headers()

            def log_message(self, *args: Any) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        ALLOWED_LOCAL_PORTS.add(self.port)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        ALLOWED_LOCAL_PORTS.discard(self.port)

    def case_spans(self) -> list[dict[str, Any]]:
        return [s for s in self.spans if s["name"] == "benchmark_case"]
