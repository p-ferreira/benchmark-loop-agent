"""Thin native adapters for the OpenAI and Anthropic tool-calling APIs.

Each adapter sends the case prompt and function schema in that provider's own
format and returns the tool calls it got back in the form BFCL's scorer
expects. Nothing here executes a returned call.

The HTTP boundary is a plain function (``PostJson``) so tests can replace it;
the standard library is enough, so the project has no runtime dependencies.
"""

import json
import urllib.error
import urllib.request
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable

from .case import PinnedCase
from .scoring import BfclCall

# (url, headers, JSON body) -> parsed JSON response. Raises ProviderError on failure.
PostJson = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]

REQUEST_TIMEOUT_SECONDS = 120
ANTHROPIC_MAX_TOKENS = 1024  # required by the Messages API; ample for one tool call


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


def post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    """POST ``body`` as JSON using the standard library and parse the JSON reply."""
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        # Not truncated here: the runner redacts keys, then truncates, so a key
        # can never be cut in half and slip past redaction.
        raise ProviderError(f"HTTP {error.code}: {error.read().decode(errors='replace')}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ProviderError(f"{type(error).__name__}: {error}") from None


def json_schema_parameters(bfcl_parameters: dict[str, Any]) -> dict[str, Any]:
    """Turn a BFCL parameter schema into JSON Schema.

    BFCL writes the top-level type as "dict"; both providers require "object".
    The pinned case uses only JSON Schema types below that level, so nothing
    else needs translating.
    """
    schema = deepcopy(bfcl_parameters)
    if schema.get("type") == "dict":
        schema["type"] = "object"
    return schema


def request_openai(api_key: str, model: str, case: PinnedCase, post: PostJson) -> ProviderResponse:
    """Call the OpenAI Responses API with the case's function as a tool."""
    # The Responses API is used because OpenAI's current reasoning models refuse
    # function tools on the older Chat Completions endpoint. Its tools are flat
    # ({"type": "function", "name": ...}) with the schema under "parameters".
    # Anthropic differs; see request_anthropic.
    tools = [
        {
            "type": "function",
            "name": f["name"],
            "description": f["description"],
            "parameters": json_schema_parameters(f["parameters"]),
            # Strict mode would require every parameter to be listed as required.
            # BFCL schemas have optional parameters, so the schema is sent as written.
            "strict": False,
        }
        for f in case.functions
    ]
    body = {
        "model": model,
        "input": [{"role": "user", "content": case.prompt}],
        "tools": tools,
        "store": False,  # a benchmark request has no reason to be kept by the provider
    }
    reply = post("https://api.openai.com/v1/responses", {"authorization": f"Bearer {api_key}"}, body)

    try:
        usage = reply.get("usage") or {}
        calls: list[BfclCall] = []
        malformed: list[str] = []
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
                malformed.append(f"arguments for {name} are nested too deeply")
                unscorable.append({name: raw_arguments})
                continue
            calls.append({name: arguments})
        return ProviderResponse(
            reply.get("model"), calls, usage.get("input_tokens"), usage.get("output_tokens"), malformed, unscorable
        )
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderError(f"unexpected OpenAI response shape: {type(error).__name__}: {error}") from None


def request_anthropic(api_key: str, model: str, case: PinnedCase, post: PostJson) -> ProviderResponse:
    """Call Anthropic Messages with the case's function as a tool."""
    # Anthropic tools are flat, name the schema "input_schema", and require
    # max_tokens. The API key goes in "x-api-key", not a Bearer header.
    tools = [
        {
            "name": f["name"],
            "description": f["description"],
            "input_schema": json_schema_parameters(f["parameters"]),
        }
        for f in case.functions
    ]
    body = {
        "model": model,
        "max_tokens": ANTHROPIC_MAX_TOKENS,
        "messages": [{"role": "user", "content": case.prompt}],
        "tools": tools,
    }
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    reply = post("https://api.anthropic.com/v1/messages", headers, body)

    try:
        usage = reply.get("usage") or {}
        # Tool calls are "tool_use" blocks in the content list; "input" is already a dict.
        calls: list[BfclCall] = []
        malformed: list[str] = []
        unscorable: list[dict[str, Any]] = []
        for block in reply["content"]:
            if block["type"] != "tool_use":
                continue
            if too_deep(block["input"]):  # lists too: deep non-objects must not reach recursive redaction
                malformed.append(f"input for {block['name']} is nested too deeply")
                unscorable.append({block["name"]: printable_text(block["input"])})
            elif isinstance(block["input"], dict):
                calls.append({block["name"]: block["input"]})
            else:
                malformed.append(f"input for {block['name']} is not a JSON object")
                unscorable.append({block["name"]: block["input"]})
        return ProviderResponse(
            reply.get("model"), calls, usage.get("input_tokens"), usage.get("output_tokens"), malformed, unscorable
        )
    except (KeyError, TypeError) as error:
        raise ProviderError(f"unexpected Anthropic response shape: {type(error).__name__}: {error}") from None
