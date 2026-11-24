"""Thin native adapters for the OpenAI and Anthropic tool-calling APIs.

Each adapter sends the case prompt and function schema in that provider's own
format and returns the tool calls it got back in the form BFCL's scorer
expects. Nothing here executes a returned call.

Requests go through each provider's official Python library, which owns the
endpoint, the authentication headers and the API version. The call into the
library is a plain function (``Send``) so tests can replace it.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Callable

import anthropic
import openai

from .dataset import Case
from .scoring import BfclCall
from .tools import convert_to_tool, with_language_handling

# (provider name, API key, request arguments) -> the reply as a plain dict.
Send = Callable[[str, str, dict[str, Any]], dict[str, Any]]

REQUEST_TIMEOUT_SECONDS = 120
ANTHROPIC_MAX_TOKENS = 4096  # required by the Messages API; room for several parallel calls


MAX_ARGUMENT_DEPTH = 50  # far deeper than any real function schema; bounds every later recursion


def too_deep(value: Any, limit: int = MAX_ARGUMENT_DEPTH) -> bool:
    """True if lists/dicts inside ``value`` nest deeper than ``limit``. Iterative, so it cannot recurse."""
    stack = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        if isinstance(item, (list, dict)):
            if depth > limit:
                return True
            children = item.values() if isinstance(item, dict) else item
            stack.extend((child, depth + 1) for child in children)
    return False


def printable_text(value: Any) -> str:
    """JSON text of ``value`` for the reader; placeholder only if it cannot be encoded."""
    try:
        return json.dumps(value)
    except (ValueError, RecursionError, TypeError):
        return "<input could not be encoded for printing>"


class ProviderError(Exception):
    """The API call itself failed (network, HTTP error, unusable response)."""


@dataclass(frozen=True)
class ProviderResponse:
    """What a successful API response yielded, before scoring."""

    actual_model: str | None  # the model name as the response reports it
    calls: list[BfclCall]
    input_tokens: int | None
    output_tokens: int | None
    # Tool calls we could not turn into a BFCL call (arguments that are not a JSON
    # object). The response succeeded, so these count as a wrong answer, not an
    # error. ``malformed`` says why; ``unscorable_calls`` keeps each call's name
    # and raw arguments for the reader. They never reach the BFCL checker.
    malformed: list[str] = field(default_factory=list)
    unscorable_calls: list[dict[str, Any]] = field(default_factory=list)
    # Calls whose arguments decode as a JSON object but nest deeper than our record
    # safeguard allows. Decoding succeeded, so BFCL's presence rule counts them as
    # calls; only the AST categories treat them as unscorable. Kept apart from
    # ``malformed`` so the safeguard never changes a relevance grade.
    too_deep: list[str] = field(default_factory=list)


def send_request(
    provider: str, api_key: str, request: dict[str, Any], http_client: Any = None
) -> dict[str, Any]:
    """Send ``request`` with the provider's official library and return the reply as a dict.

    A failed call raises the library's own exception. The runner turns any
    exception into an "unscored" record and redacts keys from its text.
    The libraries' own retrying is switched off: ``retry.py`` retries a bounded
    number of times, so the total number of attempts is known.
    ``http_client`` (the libraries' own HTTP client type) lets the tests answer
    the request without a network.
    """
    if provider == "openai":
        client = openai.OpenAI(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=0, http_client=http_client)
        return client.responses.create(**request).to_dict()
    if provider == "anthropic":
        client = anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS, max_retries=0, http_client=http_client)
        return client.messages.create(**request).to_dict()
    raise ProviderError(f"unknown provider: {provider}")


def openai_request(model: str, case: Case) -> dict[str, Any]:
    """The Responses API request for ``case``, built the way BFCL's OpenAI handler builds it."""
    # The Responses API is used because OpenAI's current reasoning models refuse
    # function tools on the older Chat Completions endpoint.
    tools = convert_to_tool(with_language_handling(case.functions, case.category), "openai-responses")
    for tool in tools:
        # Strict mode would require every parameter to be listed as required.
        # BFCL schemas have optional parameters, so the schema is sent as written.
        tool["strict"] = False
    # BFCL replaces the "system" role with "developer" for OpenAI.
    messages = [{**m, "role": "developer" if m["role"] == "system" else m["role"]} for m in case.messages]
    request: dict[str, Any] = {
        "model": model,
        "input": messages,
        "store": False,  # a benchmark request has no reason to be kept by the provider
    }
    if tools:  # BFCL leaves "tools" out when a case has no functions
        request["tools"] = tools
    return request


def request_openai(api_key: str, model: str, case: Case, send: Send) -> ProviderResponse:
    """Call the OpenAI Responses API with the case's functions as tools."""
    reply = send("openai", api_key, openai_request(model, case))

    try:
        usage = reply.get("usage") or {}
        calls: list[BfclCall] = []
        malformed: list[str] = []
        deep: list[str] = []
        unscorable: list[dict[str, Any]] = []
        # The reply's "output" list mixes item types (reasoning, text, tool calls).
        # Only "function_call" items are tool calls.
        for item in reply["output"]:
            if item["type"] != "function_call":
                continue
            name = item["name"]
            # OpenAI returns the arguments as a JSON *string*.
            raw_arguments = item["arguments"]
            try:
                arguments = json.loads(raw_arguments)
            except (ValueError, RecursionError, TypeError):
                # ValueError covers JSONDecodeError and also Python's integer-digit
                # limit; RecursionError covers absurdly deep nesting.
                malformed.append(f"arguments for {name} are not valid JSON")
                unscorable.append({name: raw_arguments})
                continue
            if not isinstance(arguments, dict):
                malformed.append(f"arguments for {name} are not a JSON object")
                unscorable.append({name: raw_arguments})
                continue
            if too_deep(arguments):
                deep.append(f"arguments for {name} are nested too deeply")
                unscorable.append({name: raw_arguments})
                continue
            calls.append({name: arguments})
        return ProviderResponse(
            reply.get("model"), calls, usage.get("input_tokens"), usage.get("output_tokens"), malformed, unscorable, deep
        )
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderError(f"unexpected OpenAI response shape: {type(error).__name__}: {error}") from None


def anthropic_request(model: str, case: Case) -> dict[str, Any]:
    """The Messages request for ``case``, built the way BFCL's Claude handler builds it."""
    # BFCL moves the system message into the "system" field and merges
    # consecutive user messages, which the Messages API requires.
    messages: list[dict[str, str]] = []
    system: str | None = None
    for message in case.messages:
        if message["role"] == "system" and system is None:
            system = message["content"]
        elif message["role"] == "user" and messages and messages[-1]["role"] == "user":
            messages[-1] = {**messages[-1], "content": messages[-1]["content"] + "\n\n" + message["content"]}
        else:
            messages.append(dict(message))
    request: dict[str, Any] = {"model": model, "max_tokens": ANTHROPIC_MAX_TOKENS, "messages": messages}
    tools = convert_to_tool(with_language_handling(case.functions, case.category), "claude")
    if tools:
        request["tools"] = tools
    if system is not None:
        request["system"] = [{"type": "text", "text": system}]
    return request


def request_anthropic(api_key: str, model: str, case: Case, send: Send) -> ProviderResponse:
    """Call Anthropic Messages with the case's functions as tools."""
    reply = send("anthropic", api_key, anthropic_request(model, case))

    try:
        usage = reply.get("usage") or {}
        # Tool calls are "tool_use" blocks in the content list; "input" is already a dict.
        calls: list[BfclCall] = []
        malformed: list[str] = []
        deep: list[str] = []
        unscorable: list[dict[str, Any]] = []
        for block in reply["content"]:
            if block["type"] != "tool_use":
                continue
            if too_deep(block["input"]):  # lists too: deep non-objects must not reach recursive redaction
                # A deep object still decoded (a call for BFCL's presence rule);
                # a deep non-object is not a call at all.
                (deep if isinstance(block["input"], dict) else malformed).append(
                    f"input for {block['name']} is nested too deeply")
                unscorable.append({block["name"]: printable_text(block["input"])})
            elif isinstance(block["input"], dict):
                calls.append({block["name"]: block["input"]})
            else:
                malformed.append(f"input for {block['name']} is not a JSON object")
                unscorable.append({block["name"]: block["input"]})
        return ProviderResponse(
            reply.get("model"), calls, usage.get("input_tokens"), usage.get("output_tokens"), malformed, unscorable, deep
        )
    except (KeyError, TypeError) as error:
        raise ProviderError(f"unexpected Anthropic response shape: {type(error).__name__}: {error}") from None
