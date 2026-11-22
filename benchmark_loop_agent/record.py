"""The machine-readable record emitted for each provider."""

import math
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
        """The record as strictly valid JSON data (see ``json_safe``)."""
        return json_safe(asdict(self))


def json_safe(value: Any) -> Any:
    """Replace floats JSON cannot express with a marker object.

    A model may return an argument such as ``1e400``: valid JSON on input, but
    Python reads it as ``inf``, which ``json.dumps`` would write as the invalid
    token ``Infinity``. The marker ``{"unrepresentable_number": "Infinity"}``
    keeps the record consumable by strict readers and still shows what came back.
    """
    if isinstance(value, float) and not math.isfinite(value):
        name = "NaN" if math.isnan(value) else "Infinity" if value > 0 else "-Infinity"
        return {"unrepresentable_number": name}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    return value
