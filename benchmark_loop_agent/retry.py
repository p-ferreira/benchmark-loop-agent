"""Bounded retry with exponential backoff for rate limits and transient API errors."""

import random
import time
from typing import Any, Callable

import anthropic
import openai

from .providers import Send

MAX_ATTEMPTS = 5  # total tries per request, the first one included
BASE_DELAY_SECONDS = 1.0
MAX_DELAY_SECONDS = 30.0

# HTTP statuses worth another try: timeout, conflict, rate limit and any server error.
RETRYABLE_STATUSES = {408, 409, 429}


def is_transient(error: BaseException) -> bool:
    """True for rate limits, server errors, timeouts and dropped connections.

    A bad key, an unknown model or a malformed request (4xx) would fail the same
    way again, so those are not retried. A library timeout is a kind of
    connection error in both SDKs.
    """
    if isinstance(error, (openai.APIConnectionError, anthropic.APIConnectionError)):
        return True
    status = getattr(error, "status_code", None)
    return isinstance(status, int) and (status in RETRYABLE_STATUSES or status >= 500)


class RetriesExhausted(Exception):
    """A transient error persisted through every attempt; the message names the last one."""


def with_retries(
    send: Send,
    *,
    attempts: int = MAX_ATTEMPTS,
    sleep: Callable[[float], Any] = time.sleep,
    jitter: Callable[[], float] = random.random,
) -> Send:
    """Wrap ``send`` so a transient error is retried up to ``attempts`` tries in all.

    The wait doubles each time (1 s, 2 s, 4 s, ... capped at 30 s) plus up to
    one second of jitter so concurrent workers do not retry in lockstep.
    """

    def retrying(provider: str, api_key: str, request: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(1, attempts + 1):
            try:
                return send(provider, api_key, request)
            except Exception as error:
                if not is_transient(error):
                    raise
                if attempt == attempts:
                    raise RetriesExhausted(
                        f"gave up after {attempts} attempts; last error {type(error).__name__}: {error}"
                    ) from None
                sleep(min(BASE_DELAY_SECONDS * 2 ** (attempt - 1), MAX_DELAY_SECONDS) + jitter())
        raise AssertionError("unreachable")  # pragma: no cover

    return retrying
