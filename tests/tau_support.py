"""Scripted stand-ins for the retail benchmark's agent provider, customer and judges. Offline."""

import json
import threading
from typing import Any, Callable

from tests import support  # noqa: F401  (forbids network connections)

AGENT_KEY = "sk-test-AGENT-KEY-1"
CUSTOMER_KEY = "sk-test-CUSTOMER-KEY-2"
FINAL_TEXT = "All done, the change is made."


def environment(provider: str = "openai") -> dict[str, str]:
    env = {"OPENAI_API_KEY": CUSTOMER_KEY}
    if provider == "anthropic":
        env["ANTHROPIC_API_KEY"] = AGENT_KEY
    else:
        env["OPENAI_API_KEY"] = AGENT_KEY
    return env


def openai_reply(text: str | None = None, calls: list[tuple[str, dict]] = (), input_tokens: int = 100, cached: int = 0,
                 output_tokens: int = 10, status: str = "completed") -> dict[str, Any]:
    output: list[dict[str, Any]] = []
    if text is not None:
        output.append({"type": "message", "content": [{"type": "output_text", "text": text}]})
    for index, (name, arguments) in enumerate(calls):
        output.append({"type": "function_call", "call_id": f"call_{index}_{name}", "name": name, "arguments": json.dumps(arguments)})
    return {"model": "reported-openai-model", "status": status, "output": output,
            "usage": {"input_tokens": input_tokens, "input_tokens_details": {"cached_tokens": cached}, "output_tokens": output_tokens}}


def anthropic_reply(text: str | None = None, calls: list[tuple[str, dict]] = (), input_tokens: int = 20, written: int = 30,
                    read: int = 50, output_tokens: int = 10, stop_reason: str = "end_turn") -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": text}] if text is not None else []
    content += [{"type": "tool_use", "id": f"toolu_{index}_{name}", "name": name, "input": arguments} for index, (name, arguments) in enumerate(calls)]
    return {"model": "reported-anthropic-model", "stop_reason": stop_reason, "content": content,
            "usage": {"input_tokens": input_tokens, "cache_creation_input_tokens": written, "cache_read_input_tokens": read,
                      "output_tokens": output_tokens}}


class ScriptedAgent:
    """A ``Send`` that makes the golden writes of one task, one tool call per turn, and then says it is done.

    The turn is read from the request (how many tool calls the conversation holds), so one instance serves
    any number of conversations, in any order.
    """

    def __init__(self, task: Any, provider: str = "openai", only: Callable[[Any], bool] | None = None) -> None:
        self.provider = provider
        self.actions = [(a.name, dict(a.arguments)) for a in task.evaluation_criteria.actions or []
                        if only is None or only(a)]
        self.requests: list[dict[str, Any]] = []
        self.lock = threading.Lock()

    def __call__(self, provider: str, api_key: str, request: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            self.requests.append(request)
        if provider == "openai":
            step = sum(1 for item in request["input"] if item.get("type") == "function_call")
        else:
            step = sum(1 for m in request["messages"] for b in m["content"] if b["type"] == "tool_use")
        reply = openai_reply if provider == "openai" else anthropic_reply
        if step < len(self.actions):
            return reply(calls=[self.actions[step]])
        return reply(text=FINAL_TEXT)


def model_response(content: str, model: str = "gpt-4.1-2025-04-14", prompt: int = 11, completion: int = 7, cached: int = 3) -> Any:
    from litellm import ModelResponse
    from litellm.types.utils import Choices, CompletionTokensDetailsWrapper, Message, PromptTokensDetailsWrapper, Usage

    return ModelResponse(
        model=model, choices=[Choices(index=0, finish_reason="stop", message=Message(role="assistant", content=content))],
        usage=Usage(prompt_tokens=prompt, completion_tokens=completion, total_tokens=prompt + completion,
                    prompt_tokens_details=PromptTokensDetailsWrapper(cached_tokens=cached),
                    completion_tokens_details=CompletionTokensDetailsWrapper(reasoning_tokens=2)))


class ScriptedLitellm:
    """Stands in for ``litellm.completion``: the customer says hello and stops once the agent says it is done; judges say met."""

    def __init__(self, task: Any, fail_customer: bool = False, never_stop: bool = False) -> None:
        self.task, self.fail_customer, self.never_stop = task, fail_customer, never_stop
        self.calls: list[dict[str, Any]] = []
        self.lock = threading.Lock()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        model = kwargs["model"]
        with self.lock:
            self.calls.append(kwargs)
        messages = kwargs["messages"]
        if model.endswith("gpt-6-sol"):
            if self.fail_customer:
                raise RuntimeError("the customer's provider is down")
            last = messages[-1]["content"] or ""
            if not self.never_stop and FINAL_TEXT in last:
                return model_response("###STOP###")
            return model_response("Hello, I would like to change my order please.")
        if "gpt-5.4-mini" in model:  # the natural-language assertions judge
            assertions = self.task.evaluation_criteria.nl_assertions or []
            return model_response(json.dumps({"results": [{"expectedOutcome": a, "metExpectation": True, "reasoning": "yes"}
                                                          for a in assertions]}), model="gpt-4.1-mini-2025-04-14", prompt=40, completion=5, cached=0)
        return model_response(json.dumps({"reasoning": "said it", "met": True}), model="gpt-4.1-nano-2025-04-14", prompt=60, completion=6, cached=0)
