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


class ProviderError(Exception):
    """The API call itself failed (network, HTTP error, unusable response)."""


@dataclass(frozen=True)
class ProviderResponse:
    """What a successful API response yielded, before scoring."""

    actual_model: str | None  # the model name as the response reports it
    calls: list[BfclCall]
    input_tokens: int | None
    output_tokens: int | None
    # Tool calls we could not turn into a BFCL call (e.g. arguments that are not
    # JSON). The response succeeded, so these count as a wrong answer, not an error.
    malformed: list[str] = field(default_factory=list)


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
        raise ProviderError(f"HTTP {error.code}: {error.read().decode(errors='replace')[:500]}") from None
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
    """Call OpenAI Chat Completions with the case's function as a tool."""
    # OpenAI wraps each tool as {"type": "function", "function": {...}} and takes
    # the schema under "parameters". Anthropic differs; see request_anthropic.
    tools = [
        {
            "type": "function",
            "function": {
                "name": f["name"],
                "description": f["description"],
                "parameters": json_schema_parameters(f["parameters"]),
            },
        }
        for f in case.functions
    ]
    body = {"model": model, "messages": [{"role": "user", "content": case.prompt}], "tools": tools}
    reply = post("https://api.openai.com/v1/chat/completions", {"authorization": f"Bearer {api_key}"}, body)

    try:
        message = reply["choices"][0]["message"]
        usage = reply.get("usage") or {}
        calls: list[BfclCall] = []
        malformed: list[str] = []
        for tool_call in message.get("tool_calls") or []:
            name = tool_call["function"]["name"]
            # OpenAI returns the arguments as a JSON *string*.
            try:
                arguments = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError:
                malformed.append(f"arguments for {name} are not valid JSON")
                continue
            calls.append({name: arguments})
        return ProviderResponse(
            reply.get("model"), calls, usage.get("prompt_tokens"), usage.get("completion_tokens"), malformed
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
        calls: list[BfclCall] = [
            {block["name"]: block["input"]} for block in reply["content"] if block["type"] == "tool_use"
        ]
        return ProviderResponse(reply.get("model"), calls, usage.get("input_tokens"), usage.get("output_tokens"))
    except (KeyError, TypeError) as error:
        raise ProviderError(f"unexpected Anthropic response shape: {type(error).__name__}: {error}") from None
