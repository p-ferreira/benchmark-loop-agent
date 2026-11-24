"""BFCL's question and expected-answer files, kept apart so no answer reaches a model.

``Case`` has no field for the expected answer, so nothing that receives a case
can pass the answer on by accident. Answers are loaded by a separate function
that only the scoring step calls.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .categories import CATEGORIES, is_relevance_or_irrelevance

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# gorilla commit that the data files and the scorer files were taken from.
GORILLA_COMMIT = "6ea57973c7a6097fd7c5915698c54c17c5b1b6c8"
DATASET_REVISION = f"ShishirPatil/gorilla@{GORILLA_COMMIT}"


@dataclass(frozen=True)
class Case:
    """Everything a model is allowed to see for one case."""

    case_id: str
    category: str
    messages: list[dict[str, str]]  # BFCL's single turn: role/content pairs
    functions: list[dict[str, Any]]  # BFCL function schemas exactly as stored


def _read_lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def question_path(category: str) -> Path:
    return DATA_DIR / "questions" / f"BFCL_v4_{category}.json"


def answer_path(category: str) -> Path:
    return DATA_DIR / "answers" / f"BFCL_v4_{category}.json"


def load_cases(category: str) -> list[Case]:
    """Load the model-visible half of every case in a category, in file order."""
    if category not in CATEGORIES:
        raise ValueError(f"unknown category: {category}")
    cases = []
    for raw in _read_lines(question_path(category)):
        (turn,) = raw["question"]  # single-turn categories have exactly one turn
        cases.append(Case(raw["id"], category, turn, raw["function"]))
    return cases


@lru_cache(maxsize=None)
def load_expected_answers(category: str) -> dict[str, list[dict[str, Any]]]:
    """Load BFCL's ``ground_truth`` per case id. Only the scoring step calls this.

    BFCL's format is unusual: each parameter maps to a *list of acceptable
    values*, and an empty string in that list means the parameter may be
    omitted. Relevance and irrelevance categories have no answer file at all.
    """
    if is_relevance_or_irrelevance(category):
        return {}
    return {row["id"]: row["ground_truth"] for row in _read_lines(answer_path(category))}
