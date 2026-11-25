"""What the customer and the judges used, read from upstream's own model calls.

Upstream makes every customer and judge call through ``tau2.utils.llm_utils.completion``
(litellm). ``recording`` wraps that one function for the length of a run; the wrapper
returns the reply untouched and notes the model and the usage the reply reports, for the
conversation whose thread made the call. Nothing else of upstream is changed.
"""

import contextvars
from contextlib import contextmanager
from typing import Any, Callable, Iterator

CUSTOMER = "customer"
JUDGES = "judges"


def normalise_model(name: str | None) -> str | None:
    """A model id as the rates file names it: without the route prefix upstream's calls add."""
    if name is None:
        return None
    for prefix in ("openai/", "responses/"):
        while name.startswith(prefix):
            name = name[len(prefix):]
    return name


class ModelRefusal(Exception):
    """A customer or judge model refused (an explicit signal in its reply); the conversation is unscored."""


def refusal_of(reply: Any) -> str | None:
    """The explicit refusal signal of a litellm reply, if it carries one: a refusal field or a content-filter finish."""
    for choice in _get(reply, "choices") or []:
        message = _get(choice, "message")
        refusal = _get(message, "refusal")
        if refusal:
            return f"refusal: {str(refusal)[:200]}"
        if _get(choice, "finish_reason") in ("content_filter", "refusal"):
            return f"finish_reason {_get(choice, 'finish_reason')}"
        content = _get(message, "content")
        if isinstance(content, list) and any(_get(part, "type") == "refusal" for part in content):
            return "refusal content part"
    return None


def _number(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


class UsageCollector:
    """The customer's and the judges' calls of one attempt at one conversation."""

    def __init__(self) -> None:
        self.phase = CUSTOMER  # the conversation runs first, then the judges score it
        self.calls: list[dict[str, Any]] = []
        self.simulation: Any = None  # the finished conversation handed to the judges, kept if they fail

    def add(self, requested: str | None, reply: Any) -> None:
        usage = _get(reply, "usage")
        details = _get(usage, "prompt_tokens_details")
        completion_details = _get(usage, "completion_tokens_details")
        self.calls.append({
            "phase": self.phase,
            "model": normalise_model(requested),
            "reported_model": _get(reply, "model"),
            "prompt_tokens": _number(_get(usage, "prompt_tokens")),
            "completion_tokens": _number(_get(usage, "completion_tokens")),
            "cached_tokens": _number(_get(details, "cached_tokens")),
            "cache_creation_tokens": _number(_get(details, "cache_creation_tokens")),
            "reasoning_tokens": _number(_get(completion_details, "reasoning_tokens")),
        })

    def summary(self, phase: str) -> dict[str, Any]:
        """Per requested model: calls and the tokens upstream's replies reported."""
        models: dict[str, dict[str, Any]] = {}
        for call in (c for c in self.calls if c["phase"] == phase):
            entry = models.setdefault(call["model"] or "unknown", {
                "model": call["model"], "reported_models": [], "calls": 0, "prompt_tokens": 0,
                "cached_tokens": 0, "cache_creation_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0,
                "calls_without_usage": 0})
            entry["calls"] += 1
            if call["reported_model"] and call["reported_model"] not in entry["reported_models"]:
                entry["reported_models"].append(call["reported_model"])
            if call["prompt_tokens"] is None and call["completion_tokens"] is None:
                entry["calls_without_usage"] += 1
            for key in ("prompt_tokens", "cached_tokens", "cache_creation_tokens", "completion_tokens", "reasoning_tokens"):
                entry[key] += call[key] or 0
        return {"calls": sum(m["calls"] for m in models.values()), "models": list(models.values())}


def _get(item: Any, name: str) -> Any:
    if item is None:
        return None
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name, None)


_current: contextvars.ContextVar[UsageCollector | None] = contextvars.ContextVar("tau_usage", default=None)


@contextmanager
def collecting(collector: UsageCollector) -> Iterator[UsageCollector]:
    """Make ``collector`` the one the calls of this thread are noted in."""
    token = _current.set(collector)
    try:
        yield collector
    finally:
        _current.reset(token)


@contextmanager
def recording(llm_utils: Any, simulation_module: Any) -> Iterator[None]:
    """Wrap ``llm_utils.completion`` so that calls made inside ``collecting`` are noted.

    ``simulation_module.evaluate_simulation`` is wrapped only to note that the judges' calls
    begin there: upstream's ``run_simulation`` runs the conversation, then calls it.
    """
    completion: Callable[..., Any] = llm_utils.completion
    evaluate: Callable[..., Any] = simulation_module.evaluate_simulation

    def noted(*args: Any, **kwargs: Any) -> Any:
        reply = completion(*args, **kwargs)
        collector = _current.get()
        if collector is not None:
            collector.add(kwargs.get("model", args[0] if args else None), reply)  # usage first: a refusal still cost tokens
            refusal = refusal_of(reply)
            if refusal:
                raise ModelRefusal(f"the {collector.phase} model refused ({refusal})")
        return reply

    def judged(*args: Any, **kwargs: Any) -> Any:
        collector = _current.get()
        if collector is not None:
            collector.phase = JUDGES
            collector.simulation = kwargs.get("simulation", args[0] if args else None)
        return evaluate(*args, **kwargs)

    llm_utils.completion, simulation_module.evaluate_simulation = noted, judged
    try:
        yield
    finally:
        llm_utils.completion, simulation_module.evaluate_simulation = completion, evaluate
