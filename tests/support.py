"""Shared test helpers. Importing this module also forbids network connections."""

import json
import socket
from typing import Any

from benchmark_loop_agent.dataset import Case, load_cases, load_expected_answers

SECRET = "sk-test-SECRET-123"


# Ports of the stand-in receivers (tests/receiver.py) started by the running tests:
# the only place a test may connect to, and only on the loopback address.
ALLOWED_LOCAL_PORTS: set[int] = set()
_connect, _create_connection, _getaddrinfo = socket.socket.connect, socket.create_connection, socket.getaddrinfo


def _refuse(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("tests must not touch the network")


def _allowed(host: Any, port: Any) -> bool:
    return host == "127.0.0.1" and port in ALLOWED_LOCAL_PORTS


def _guarded_connect(self: socket.socket, address: Any) -> Any:
    if isinstance(address, tuple) and _allowed(address[0], address[1]):
        return _connect(self, address)
    _refuse()


def _guarded_create_connection(address: Any, *args: Any, **kwargs: Any) -> Any:
    if _allowed(address[0], address[1]):
        return _create_connection(address, *args, **kwargs)
    _refuse()


def _guarded_getaddrinfo(host: Any, port: Any, *args: Any, **kwargs: Any) -> Any:
    if _allowed(host, int(port) if port is not None else None):
        return _getaddrinfo(host, port, *args, **kwargs)
    _refuse()


# A test that tried a live call fails here instead of passing by luck.
socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
socket.create_connection = _guarded_create_connection  # type: ignore[assignment]
socket.getaddrinfo = _guarded_getaddrinfo  # type: ignore[assignment]


def environment(*providers: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for provider in providers:
        prefix = provider.upper()
        env.update({f"{prefix}_API_KEY": SECRET, f"{prefix}_MODEL": "requested-model"})
    return env


def case_by_id(category: str, case_id: str | None = None) -> Case:
    cases = load_cases(category)
    return cases[0] if case_id is None else next(c for c in cases if c.case_id == case_id)


def first_option(values: list[Any]) -> Any:
    """The first acceptable value; a nested dict answer holds option lists of its own."""
    value = values[0]
    if isinstance(value, dict):
        return {k: first_option(v) for k, v in value.items() if v[0] != ""}
    if isinstance(value, list):
        return [first_option([item]) for item in value]
    return value


def all_strings(case: Case) -> bool:
    """True if a perfect call has only string arguments (what Java and JavaScript cases need)."""
    return all(isinstance(v, str) for call in right_calls(case) for args in call.values() for v in args.values())


def right_calls(case: Case) -> list[dict[str, dict[str, Any]]]:
    """The calls a perfect model would return: the first acceptable value of each parameter.

    Names go out with "." as "_", as the tools sent to the providers do.
    """
    calls = []
    for call in load_expected_answers(case.category)[case.case_id]:
        (name, options), = call.items()
        arguments = {p: first_option(values) for p, values in options.items() if values[0] != ""}
        calls.append({name.replace(".", "_"): arguments})
    return calls


def openai_reply(calls: list[dict[str, Any]], *, raw: bool = False) -> dict[str, Any]:
    """A Responses API reply: tool calls among the other item types the API returns."""
    output: list[dict[str, Any]] = [{"type": "reasoning", "summary": []}]
    for index, call in enumerate(calls):
        (name, arguments), = call.items()
        output.append({"type": "function_call", "name": name, "call_id": f"call_{index}",
                       "arguments": arguments if raw else json.dumps(arguments)})
    output.append({"type": "message", "content": [{"type": "output_text", "text": "done"}]})
    return {"model": "gpt-actual", "output": output, "usage": {"input_tokens": 7, "output_tokens": 3}}


def anthropic_reply(calls: list[dict[str, Any]]) -> dict[str, Any]:
    content = [{"type": "tool_use", "name": n, "input": a} for call in calls for n, a in call.items()]
    return {"model": "claude-actual", "content": content, "usage": {"input_tokens": 8, "output_tokens": 4}}


def reply_for(provider: str, calls: list[dict[str, Any]]) -> dict[str, Any]:
    return openai_reply(calls) if provider == "openai" else anthropic_reply(calls)


class FakeSend:
    """Stands in for the call into the provider's library and remembers what was sent."""

    def __init__(self, reply: Any) -> None:
        self.reply = reply  # a reply dict, an Exception, or a function (provider, request) -> either
        self.requests: list[tuple[str, str, dict[str, Any]]] = []

    def __call__(self, provider: str, api_key: str, request: dict[str, Any]) -> dict[str, Any]:
        self.requests.append((provider, api_key, request))
        reply = self.reply(provider, request) if callable(self.reply) else self.reply
        if isinstance(reply, Exception):
            raise reply
        return reply
