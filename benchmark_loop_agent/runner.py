"""Run one case against one provider and build its record.

``run_provider`` never raises, and it shares nothing between calls, so one
case's or one provider's failure cannot prevent or change another's record.
"""

import time
from dataclasses import dataclass, fields
from typing import Any, Callable, Mapping, Sequence

from .dataset import DATASET_REVISION, Case
from .providers import ProviderError, ProviderResponse, Send, request_anthropic, request_openai
from .record import Record
from .scoring import SCORER_REVISION, score_calls

MAX_REASON_LENGTH = 500


@dataclass(frozen=True)
class Provider:
    """How to reach one provider: which environment variables configure it."""

    key_env: str
    model_env: str
    request: Callable[[str, str, Case, Send], ProviderResponse]


PROVIDERS: dict[str, Provider] = {
    "openai": Provider("OPENAI_API_KEY", "OPENAI_MODEL", request_openai),
    "anthropic": Provider("ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", request_anthropic),
}


def redact(value: Any, secrets: Sequence[str]) -> Any:
    """Return ``value`` with every secret removed from all strings inside it.

    Walks lists and dicts (keys included) because model-returned arguments can
    echo a key just as an exception message can.
    """
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, "[redacted]")
        return value
    if isinstance(value, list):
        return [redact(item, secrets) for item in value]
    if isinstance(value, dict):
        return {redact(k, secrets): redact(v, secrets) for k, v in value.items()}
    return value


def redact_record(record: Record, secrets: Sequence[str]) -> Record:
    """Redact every field of a record, since all of it is printed."""
    return Record(**{f.name: redact(getattr(record, f.name), secrets) for f in fields(Record)})


def run_provider(
    name: str, case: Case, environment: Mapping[str, str], send: Send
) -> Record:
    """Run the case against one provider and return its record. Never raises."""
    provider = PROVIDERS[name]
    api_key = environment.get(provider.key_env) or None
    model = environment.get(provider.model_env) or None
    # Every configured key, not just this provider's: nothing emitted may carry one.
    secrets = [key for p in PROVIDERS.values() if (key := environment.get(p.key_env))]

    def record(outcome, reasons, *, calls=None, response=None, latency=None) -> Record:
        return redact_record(Record(
            provider=name,
            requested_model=model,
            actual_model=response.actual_model if response else None,
            case_id=case.case_id,
            category=case.category,
            dataset_revision=DATASET_REVISION,
            scorer_revision=SCORER_REVISION,
            returned_calls=calls,
            outcome=outcome,
            # Redact first: truncating first could leave a key's first characters behind.
            reasons=[redact(reason, secrets)[:MAX_REASON_LENGTH] for reason in reasons],
            latency_seconds=latency,
            input_tokens=response.input_tokens if response else None,
            output_tokens=response.output_tokens if response else None,
        ), secrets)

    if api_key is None:
        return record("unscored", [f"{provider.key_env} is not set"])
    if model is None:
        return record("unscored", [f"{provider.model_env} is not set"])

    started = time.perf_counter()
    try:
        response = provider.request(api_key, model, case, send)
    except Exception as error:  # any failure of the call is "unscored", never a crash
        return record("unscored", [f"{type(error).__name__}: {error}"], latency=time.perf_counter() - started)
    latency = time.perf_counter() - started

    # Scoring is the only step that reads expected answers, and it runs after
    # the model has answered.
    try:
        verdict = score_calls(case, response.calls, response.malformed)
    except Exception as error:
        # The response arrived but the checker could not judge it (for example a
        # value of a type it does not expect), so it is a wrong answer, and the
        # reason says what happened. It must not stop the run.
        return record("fail", [f"scorer raised {type(error).__name__}: {error}"],
                      calls=response.calls + response.unscorable_calls, response=response, latency=latency)
    return record(
        "pass" if verdict.passed else "fail",
        verdict.reasons,
        calls=response.calls + response.unscorable_calls,
        response=response,
        latency=latency,
    )

