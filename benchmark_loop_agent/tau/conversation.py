"""One attempt at one conversation: upstream's orchestrator, customer and evaluator around bla's agent.

``run_attempt`` never raises. It returns the record fields of the attempt and the full
conversation. The reward is whatever upstream's ``evaluate_simulation`` computes; this module
only decides whether a conversation was scored at all (see ``SCORED_TERMINATIONS``).
"""

import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from ..providers import Send
from ..runner import PROVIDERS, redact
from .agent import AgentCallError, AgentUsage, Attempt, attempting, register_agent
from .upstream import load
from .usage import CUSTOMER, JUDGES, ModelRefusal, UsageCollector, collecting

# Upstream scores a conversation that ended because someone stopped it, or because it reached its
# step limit (reward 0: a fail). Every other end is a premature termination by error: unscored.
SCORED_TERMINATIONS = ("agent_stop", "user_stop", "max_steps")
CUSTOMER_REASONING = {"reasoning_effort": "low"}  # upstream's setting for the benchmark's customer
MAX_REASON_LENGTH = 500


@dataclass(frozen=True)
class Settings:
    provider: str
    agent_model: str
    user_model: str
    instruction: str | None = None
    max_steps: int = 200  # upstream's defaults
    max_errors: int = 10


def customer_model_route(user_model: str) -> str:
    """The model name upstream's customer calls use: an id without a route is an OpenAI model."""
    return user_model if "/" in user_model else f"openai/{user_model}"


def run_attempt(config: Any, task: Any, seed: int, settings: Settings, environment: Mapping[str, str], send: Send) -> dict[str, Any]:
    """Run and score one conversation with upstream's ``run_single_task``. Returns ``{"fields", "conversation"}``; never raises."""
    secrets = [v for k, v in environment.items() if k.endswith("_API_KEY") and v]
    started = time.perf_counter()
    usage, collector = AgentUsage(), UsageCollector()
    outcome: dict[str, Any] = {"outcome": "unscored", "reward": None, "reward_components": None, "termination_reason": None,
                               "reason": None}
    simulation = None
    attempt = Attempt(settings.provider, settings.agent_model, environment.get(PROVIDERS[settings.provider].key_env, ""), send,
                      usage, settings.instruction)
    try:
        upstream = load()
        register_agent()
        with collecting(collector), attempting(attempt):
            simulation = upstream.run_single_task(config, task, seed=seed)
        reason = getattr(simulation.termination_reason, "value", simulation.termination_reason)
        info = simulation.reward_info
        outcome.update(termination_reason=reason)
        if reason not in SCORED_TERMINATIONS:
            outcome["reason"] = f"upstream ended the conversation prematurely: {reason}"
        else:
            outcome.update(outcome="pass" if info.reward >= 1 - 1e-6 else "fail", reward=info.reward,
                           reward_components=_components(info))
    except AgentCallError as error:
        outcome["reason"] = f"agent call failed: {error}"
    except ModelRefusal as error:
        outcome["reason"] = str(error)
    except Exception as error:  # a provider error of the customer or the judges, or anything upstream raises
        who = "judges" if collector.phase == JUDGES else "conversation (customer, tools or agent)"
        outcome["reason"] = f"{who}: {type(error).__name__}: {error}"
    if outcome["reason"]:
        outcome["reason"] = redact(outcome["reason"], secrets)[:MAX_REASON_LENGTH]
    totals = usage.totals()
    if simulation is None:
        simulation = collector.simulation  # the judges failed: keep the finished conversation they were given
    partial = simulation is None
    fields = {
        **outcome,
        "agent_calls": usage.dispatches,
        "agent_calls_without_usage": usage.calls_without_usage(),
        "agent_opening_user_turn_added": usage.opening_turn_added,
        "agent_models": usage.models(),
        "agent_tokens": {"uncached_input": totals["uncached_input_tokens"], "cache_write_input": totals["cache_write_input_tokens"],
                         "cache_read_input": totals["cache_read_input_tokens"], "output": totals["output_tokens"]},
        "customer_usage": collector.summary(CUSTOMER),
        "judges_usage": collector.summary(JUDGES),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    conversation = {"messages": _messages(simulation, usage), "partial": partial, "reward_info": _reward_info(simulation),
                    "agent_call_usage": [call.to_dict() for call in usage.calls]}
    return {"fields": redact(fields, secrets), "conversation": redact(conversation, secrets)}


def _components(info: Any) -> dict[str, Any]:
    """Each reward component upstream reports, as it reports it."""
    dump = info.model_dump(mode="json")
    return {"reward_breakdown": dump.get("reward_breakdown"), "reward_basis": dump.get("reward_basis"),
            "db_check": dump.get("db_check"), "action_checks": dump.get("action_checks"),
            "env_assertions": dump.get("env_assertions"), "communicate_checks": dump.get("communicate_checks"),
            "nl_assertions": dump.get("nl_assertions"), "info": dump.get("info")}


def _reward_info(simulation: Any) -> Any:
    return simulation.reward_info.model_dump(mode="json") if simulation is not None and simulation.reward_info else None


def _messages(simulation: Any, usage: AgentUsage) -> list[Any]:
    """The conversation; of an attempt that failed midway, what the agent had seen by then."""
    messages = simulation.messages if simulation is not None else usage.messages
    return [m.model_dump(mode="json", exclude={"raw_data"}) for m in messages]
