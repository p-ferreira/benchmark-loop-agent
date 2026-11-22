"""The pinned BFCL case, split so the expected answer cannot reach a model.

The prompt and function schema (what a model may see) and the expected answer
(what only the scorer may see) live in separate files and are loaded by
separate functions. ``PinnedCase`` has no field for the answer, so anything
that receives a case cannot pass the answer on by accident.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CASE_ID = "simple_python_0"

# gorilla commit that the case, its answer and the scorer files were taken from.
GORILLA_COMMIT = "6ea57973c7a6097fd7c5915698c54c17c5b1b6c8"
DATASET_REVISION = f"ShishirPatil/gorilla@{GORILLA_COMMIT}"


@dataclass(frozen=True)
class PinnedCase:
    """Everything a model is allowed to see for one case."""

    case_id: str
    prompt: str
    functions: list[dict[str, Any]]  # BFCL function schemas, as stored in the dataset


def load_case() -> PinnedCase:
    """Load the model-visible half of the pinned case."""
    raw = json.loads((DATA_DIR / f"{CASE_ID}.case.json").read_text())
    # BFCL stores questions as a list of turns, each a list of messages.
    # Single-turn categories have exactly one turn with one user message.
    (turn,) = raw["question"]
    (message,) = turn
    return PinnedCase(case_id=raw["id"], prompt=message["content"], functions=raw["function"])


def load_expected_answer() -> list[dict[str, Any]]:
    """Load BFCL's ``ground_truth`` for the case. Only the scoring step calls this.

    BFCL's format is unusual: each parameter maps to a *list of acceptable
    values*, and an empty string in that list means the parameter may be omitted.
    """
    return json.loads((DATA_DIR / f"{CASE_ID}.answer.json").read_text())["ground_truth"]
