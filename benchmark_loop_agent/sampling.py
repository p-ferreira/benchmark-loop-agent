"""Choose which cases of each category to run."""

import random
from typing import Sequence

from .dataset import Case, load_cases
from .split import part_case_ids


def sample_cases(cases: Sequence[Case], size: int | None, seed: int) -> list[Case]:
    """Pick ``size`` cases, the same ones for the same seed, kept in file order.

    ``None`` (or a size at least as large as the category) keeps every case.
    The generator is seeded per category, so adding a category to a run never
    changes the cases chosen for another.
    """
    if size is None or size >= len(cases):
        return list(cases)
    if size < 0:
        raise ValueError("sample size must not be negative")
    category = cases[0].category
    chosen = set(random.Random(f"{seed}:{category}").sample(range(len(cases)), size))
    return [case for index, case in enumerate(cases) if index in chosen]


def select_cases(categories: Sequence[str], size: int | None, seed: int, split: str | None = None) -> list[Case]:
    """The cases of every requested category, in the order the categories were given.

    With ``split`` only that part's cases are candidates, and a sample is drawn
    inside the part. Without it nothing changes.
    """
    allowed = part_case_ids(split) if split is not None else None
    chosen = []
    for category in categories:
        cases = load_cases(category)
        if allowed is not None:
            cases = [case for case in cases if case.case_id in allowed]
        chosen += sample_cases(cases, size, seed) if cases else []
    return chosen
