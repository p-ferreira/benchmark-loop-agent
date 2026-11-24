"""Score returned tool calls with BFCL's own code, without running them.

The AST checker is BFCL's ``ast_checker.py`` copied unmodified into ``vendor/``
(see ``NOTICE``). We only import it and adapt our data to its input format; we
do not re-implement any comparison logic.

Relevance and irrelevance categories have no expected answers. BFCL's rule
(``eval_runner._evaluate_single_relevance_entry`` at the pinned commit) is
only whether the model made a function call, so that small rule is mirrored
here, including its messages:

* a call counts only if the output decodes and is a non-empty list of
  ``{name: {arguments}}``. Arguments that are not valid JSON make decoding
  fail, and arguments that are not an object make the output "empty"; both
  mean "no function call" (the provider adapters report both as malformed);
* ``irrelevance`` and ``live_irrelevance`` pass when there is no call;
* ``live_relevance`` passes when there is one.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .categories import is_irrelevance, is_java, is_js, is_relevance_or_irrelevance
from .dataset import GORILLA_COMMIT, Case, load_expected_answers

# BFCL's modules import each other as ``bfcl_eval.*``, so the vendored copy
# must be importable under that exact name. Importing it from ``vendor/`` keeps
# the copied files byte-for-byte identical to upstream.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))

from bfcl_eval.constants.enums import Language  # noqa: E402
from bfcl_eval.constants.model_config import NATIVE_FC_MODEL  # noqa: E402
from bfcl_eval.constants.type_mappings import GORILLA_TO_OPENAPI  # noqa: E402,F401
from bfcl_eval.eval_checker.ast_eval.ast_checker import ast_checker  # noqa: E402

SCORER_REVISION = (
    f"ShishirPatil/gorilla@{GORILLA_COMMIT}"
    ":berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)"
)

# One call in the shape BFCL's checker expects: {function_name: {parameter: value}}.
BfclCall = dict[str, dict[str, Any]]


@dataclass(frozen=True)
class Verdict:
    """Result of scoring: whether the response was right, and why not if it was not."""

    passed: bool
    reasons: list[str]


def language_of(category: str) -> Language:
    """BFCL's ``ast_file_runner`` picks the checker language from the category name."""
    if is_java(category):
        return Language.JAVA
    if is_js(category):
        return Language.JAVASCRIPT
    return Language.PYTHON


class ReferenceDataError(Exception):
    """The expected answers could not be read; says nothing about the model's response."""


def score_relevance(category: str, made_call: bool) -> Verdict:
    """BFCL's rule for (ir)relevance: irrelevance wants no call, relevance wants one."""
    if is_irrelevance(category):
        if made_call:
            return Verdict(False, ["Valid syntax. Successfully decode AST when it should not."])
        return Verdict(True, [])
    if made_call:
        return Verdict(True, [])
    return Verdict(False, ["Invalid syntax. Failed to decode AST when it should have."])


def score_calls(case: Case, calls: list[BfclCall], malformed: list[str], too_deep: Sequence[str] = ()) -> Verdict:
    """Judge a successful response for ``case``.

    ``malformed`` lists the returned calls whose arguments were not a JSON
    object. ``too_deep`` lists calls that decoded but nest beyond our safeguard:
    they are calls for the presence rule and unscorable for the AST checker.
    BFCL treats that as a decoding failure: a wrong answer for the AST
    categories and "no function call" for the (ir)relevance ones.
    """
    if is_relevance_or_irrelevance(case.category):
        return score_relevance(case.category, bool(calls or too_deep) and not malformed)
    if malformed or too_deep:
        return Verdict(False, [*malformed, *too_deep])
    # The expected answer is read here, after the model has answered, and goes
    # nowhere but the checker. BFCL checks against the schema as stored (without
    # the language note), so ``case.functions`` is passed, not the tools sent.
    try:
        expected = load_expected_answers(case.category)[case.case_id]
    except (OSError, ValueError, KeyError) as error:
        raise ReferenceDataError(f"{type(error).__name__} reading expected answers for {case.category}") from None
    result = ast_checker(case.functions, calls, expected, language_of(case.category), case.category, NATIVE_FC_MODEL)
    return Verdict(result["valid"], [] if result["valid"] else [str(e) for e in result["error"]])
