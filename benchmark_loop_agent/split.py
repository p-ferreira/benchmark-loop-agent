"""A seeded development, validation and held-out split of the single-turn cases.

Why it exists: an instruction tuned on some cases says nothing about those
cases, so a gain is only evidence on cases the tuning never saw. The split
file fixes which cases those are.

Why groups: BFCL repeats tool sets and questions across cases (and across
categories). Two cases that share either would leak one into the other, so they
are kept in one part. The builder reads the question files only, never the
expected answers, and the split file holds case identifiers and part names,
no question, tool or answer text.

    python -m benchmark_loop_agent.split [--seed S] [--development P] [--validation P] [--held-out P] [--output FILE]
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from .categories import CATEGORIES
from .dataset import DATA_DIR, DATASET_REVISION, Case, load_cases

PARTS = ("development", "validation", "held-out")
DEFAULT_PERCENTAGES = {"development": 50, "validation": 20, "held-out": 30}
DEFAULT_SEED = 0
SPLIT_FILE = DATA_DIR / "split.json"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def tool_set_key(case: Case) -> str:
    """The tool definitions as a set: key order and tool order do not matter."""
    return _canonical(sorted({_canonical(tool) for tool in case.functions}))


def question_key(case: Case) -> str:
    """The question as parsed from the question file."""
    return _canonical(case.messages)


def group_cases(cases: Sequence[Case]) -> tuple[list[list[Case]], Counter[str]]:
    """Group cases that share a tool set or a question, transitively.

    The case identifier plays no part. Returns the groups, each in input order and
    ordered by their first case, and how many cases each rule joined to an
    earlier case (``tools``, ``question``; a case joined by both counts for both).
    """
    parent = list(range(len(cases)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    joined: Counter[str] = Counter()
    for rule, key in (("tools", tool_set_key), ("question", question_key)):
        first: dict[str, int] = {}
        for index, case in enumerate(cases):
            seen = first.setdefault(key(case), index)
            if seen != index:
                joined[rule] += 1
                parent[find(index)] = find(seen)
    members: dict[int, list[Case]] = {}
    for index, case in enumerate(cases):
        members.setdefault(find(index), []).append(case)
    return sorted(members.values(), key=lambda group: cases.index(group[0])), joined


def assign_groups(groups: Sequence[Sequence[Case]], fractions: dict[str, float], seed: int) -> dict[str, str]:
    """Give each whole group to the part whose per-category shares it moves closest to the targets.

    Biggest groups go first, while there is room to place them; ties are broken
    by a generator seeded with ``seed``. A group that spans categories is placed once.
    """
    totals = Counter(case.category for group in groups for case in group)
    target = {(part, c): fractions[part] * n for part in fractions for c, n in totals.items()}
    held: Counter[tuple[str, str]] = Counter()
    rng = random.Random(seed)
    order = sorted(range(len(groups)), key=lambda i: (-len(groups[i]), rng.random()))
    part_of: dict[str, str] = {}
    for index in order:
        by_category = Counter(case.category for case in groups[index])

        def cost(part: str) -> tuple[float, float]:
            grown = sum((held[part, c] + n - target[part, c]) ** 2 - (held[part, c] - target[part, c]) ** 2
                        for c, n in by_category.items())
            return grown, rng.random()

        part = min(fractions, key=cost)
        for c, n in by_category.items():
            held[part, c] += n
        for case in groups[index]:
            part_of[case.case_id] = part
    return part_of


def build_split(seed: int, percentages: dict[str, float]) -> dict[str, Any]:
    """Build the split document from the question files alone."""
    if set(percentages) != set(PARTS) or any(p < 0 for p in percentages.values()):
        raise ValueError("give a non-negative percentage for each of " + ", ".join(PARTS))
    if abs(sum(percentages.values()) - 100) > 1e-9:
        raise ValueError(f"the percentages must add up to 100, not {sum(percentages.values())}")
    cases = [case for category in CATEGORIES for case in load_cases(category)]
    ids = [case.case_id for case in cases]
    if len(set(ids)) != len(ids):
        raise ValueError("case identifiers are not unique across the question files")
    groups, _ = group_cases(cases)
    part_of = assign_groups(groups, {p: v / 100 for p, v in percentages.items()}, seed)
    return {
        "dataset_revision": DATASET_REVISION,
        "seed": seed,
        "percentages": dict(percentages),
        "parts": {part: [i for i in ids if part_of[i] == part] for part in PARTS},
    }


def render_split(document: dict[str, Any]) -> str:
    """The exact bytes of the split file: one line per case identifier list."""
    parts = document["parts"]
    head = {k: v for k, v in document.items() if k != "parts"}
    body = ",\n".join(f"    {json.dumps(part)}: {json.dumps(parts[part])}" for part in PARTS)
    return json.dumps(head, indent=2)[:-2] + f',\n  "parts": {{\n{body}\n  }}\n}}\n'


def load_split(path: Path = SPLIT_FILE) -> dict[str, Any]:
    document = json.loads(path.read_text())
    if document.get("dataset_revision") != DATASET_REVISION:
        raise ValueError(f"{path} was built for dataset revision {document.get('dataset_revision')}, not {DATASET_REVISION}")
    return document


def part_case_ids(part: str, path: Path = SPLIT_FILE) -> frozenset[str]:
    if part not in PARTS:
        raise ValueError(f"unknown split part: {part}")
    return frozenset(load_split(path)["parts"][part])


def _number(text: str) -> float:
    value = float(text)
    return int(value) if value.is_integer() else value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="benchmark_loop_agent.split",
                                     description="Build the development, validation and held-out split file.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"seed (default: {DEFAULT_SEED})")
    for part in PARTS:
        parser.add_argument(f"--{part}", type=_number, default=DEFAULT_PERCENTAGES[part], metavar="PERCENT",
                            help=f"percentage of cases in the {part} part (default: {DEFAULT_PERCENTAGES[part]})")
    parser.add_argument("--output", type=Path, default=SPLIT_FILE, help="split file to write (default: data/split.json)")
    args = parser.parse_args(argv)
    try:
        document = build_split(args.seed, {part: getattr(args, part.replace("-", "_")) for part in PARTS})
    except ValueError as error:
        parser.error(str(error))
    args.output.write_text(render_split(document))
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
