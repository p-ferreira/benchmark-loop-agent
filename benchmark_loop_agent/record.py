"""The machine-readable record emitted for each provider."""

from dataclasses import asdict, dataclass
from typing import Any, Literal

from .scoring import BfclCall

# pass:     the response succeeded and the call matched the expected answer.
# fail:     the response succeeded and the call was wrong or missing.
# unscored: the API call did not succeed (including a missing key); nothing to judge.
Outcome = Literal["pass", "fail", "unscored"]


@dataclass(frozen=True)
class Record:
    """One provider's result for the pinned case."""

    provider: str
    requested_model: str | None
    actual_model: str | None  # as reported by the response; None if there was none
    case_id: str
    dataset_revision: str
    scorer_revision: str
    returned_calls: list[BfclCall] | None  # None when unscored
    outcome: Outcome
    reasons: list[str]  # why it failed or was not scored; empty on pass
    latency_seconds: float | None  # None when no request was made
    input_tokens: int | None  # None when the response did not report usage
    output_tokens: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
