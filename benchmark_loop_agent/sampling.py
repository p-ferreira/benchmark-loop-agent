"""Choose which cases of each category to run."""

import random
from typing import Sequence

from .dataset import Case, load_cases


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


def select_cases(categories: Sequence[str], size: int | None, seed: int) -> list[Case]:
    """The cases of every requested category, in the order the categories were given."""
    return [case for category in categories for case in sample_cases(load_cases(category), size, seed)]
