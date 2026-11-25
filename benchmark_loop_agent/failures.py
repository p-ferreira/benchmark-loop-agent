"""Why a failed case failed: one class per failed case, computed when a report is built.

The class comes from the record and the expected answer, never from a model
input, and it is not stored in the record. The first class in ``FAILURE_CLASSES``
that applies is the case's class.
"""

from typing import Any

from .categories import is_irrelevance
from .dataset import load_expected_answers

CALLED_WHEN_NONE_APPLIED = "called-when-none-applied"
MALFORMED_CALL = "malformed-call"
NO_CALL = "no-call"
TOO_FEW_CALLS = "too-few-calls"
TOO_MANY_CALLS = "too-many-calls"
WRONG_CALL = "wrong-call"
FAILURE_CLASSES = (CALLED_WHEN_NONE_APPLIED, MALFORMED_CALL, NO_CALL, TOO_FEW_CALLS, TOO_MANY_CALLS, WRONG_CALL)

# The reasons the runner gives when a returned call could not be scored (providers.py),
# before the checker saw it. A reason can be cut at 500 characters, so only its start is read.
_MALFORMED_STARTS = ("arguments for ", "input for ")
_MALFORMED_ENDS = ("are not valid JSON", "are not a JSON object", "is not a JSON object", "is nested too deeply")


class UnknownCase(Exception):
    """The expected number of calls for the case cannot be found."""


def _malformed(category: str, record: dict[str, Any]) -> bool:
    if any(isinstance(reason, str) and reason.startswith(_MALFORMED_STARTS)
           and (reason.endswith(_MALFORMED_ENDS) or len(reason) >= 500) for reason in record.get("reasons") or []):
        return True
    # live_relevance only says "no call", so its malformed calls are found in the record:
    # an entry whose arguments are not an object (a decoded deep object alone would have passed).
    if category == "live_relevance":
        # A non-finite number (1e400) is saved as {"unrepresentable_number": ...} (json_safe), which hides its type.
        return any(not isinstance(arguments, dict) or set(arguments) == {"unrepresentable_number"}
                   for call in record.get("returned_calls") or []
                   if isinstance(call, dict) for arguments in call.values())
    return False


def failure_class(record: dict[str, Any]) -> str:
    """The class of one failed record; raises ``UnknownCase`` when its expected answer is not in the data."""
    category, calls = record["category"], record.get("returned_calls") or []
    if is_irrelevance(category):
        return CALLED_WHEN_NONE_APPLIED
    if _malformed(category, record):
        return MALFORMED_CALL
    if category == "live_relevance":  # no expected answer: at least one call is wanted
        return NO_CALL
    try:
        expected = len(load_expected_answers(category)[record["case_id"]])
    except (KeyError, OSError, ValueError):
        raise UnknownCase(record["case_id"]) from None
    if not calls:
        return NO_CALL if expected >= 1 else WRONG_CALL
    if len(calls) < expected:
        return TOO_FEW_CALLS
    if len(calls) > expected:
        return TOO_MANY_CALLS
    return WRONG_CALL
