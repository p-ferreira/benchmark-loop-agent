"""Score a returned tool call with BFCL's own AST checker, without running it.

The checker is BFCL's ``ast_checker.py`` copied unmodified into ``vendor/``
(see ``NOTICE``). We only import it and adapt our data to its input format; we
do not re-implement any comparison logic.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .case import GORILLA_COMMIT, PinnedCase

# BFCL's modules import each other as ``bfcl_eval.*``, so the vendored copy
# must be importable under that exact name. Importing it from ``vendor/`` keeps
# the copied files byte-for-byte identical to upstream.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))

from bfcl_eval.constants.enums import Language  # noqa: E402
from bfcl_eval.eval_checker.ast_eval.ast_checker import ast_checker  # noqa: E402

SCORER_REVISION = (
    f"ShishirPatil/gorilla@{GORILLA_COMMIT}"
    ":berkeley-function-call-leaderboard/bfcl_eval/eval_checker/ast_eval/ast_checker.py"
)

# BFCL picks the checker variant from the test category name. "simple_python"
# selects the single-function, Python-typed branch.
TEST_CATEGORY = "simple_python"

# One call in the shape BFCL's checker expects: {function_name: {parameter: value}}.
BfclCall = dict[str, dict[str, Any]]


@dataclass(frozen=True)
class Verdict:
    """Result of scoring: whether the call matched, and why not if it did not."""

    passed: bool
    reasons: list[str]


def score_calls(
    case: PinnedCase,
    calls: list[BfclCall],
    expected_answer: list[dict[str, Any]],
    model_name: str,
) -> Verdict:
    """Ask BFCL's AST checker whether ``calls`` match ``expected_answer``.

    ``model_name`` is part of the checker's signature; it only matters for
    function names containing ".", which the pinned case does not have.
    """
    result = ast_checker(case.functions, calls, expected_answer, Language.PYTHON, TEST_CATEGORY, model_name)
    return Verdict(passed=result["valid"], reasons=[] if result["valid"] else [str(e) for e in result["error"]])
