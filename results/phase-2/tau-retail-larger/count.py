"""Tasks passed in all four trials, per run, and the tasks one run of a pair passes in all four and the other does not.

    python3 count.py            # from this directory
"""
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = {
    "claude-sonnet-5-5": HERE / "sonnet",
    "gpt-6-sol": HERE / "sol",
    "claude-haiku-5-5, phase 1": HERE.parents[1] / "phase-1/tau-retail/haiku",
    "claude-haiku-5-5, phase 2": HERE.parent / "tau-retail-paragraph/control-haiku",
    "gpt-6-luna, phase 1": HERE.parents[1] / "phase-1/tau-retail/luna",
    "gpt-6-luna, phase 2": HERE.parent / "tau-retail-paragraph/control-luna",
}
PAIRS = [("claude-sonnet-5-5", "claude-haiku-5-5"), ("gpt-6-sol", "gpt-6-luna")]


def all_four(directory):
    passed = defaultdict(dict)
    for line in open(directory / "records.jsonl"):
        record = json.loads(line)
        if record["outcome"] == "unscored":
            raise SystemExit(f"{directory}: unscored conversation, task {record['task_id']}")
        passed[str(record["task_id"])][record["trial"]] = record["reward"] == 1
    per_trial = [sum(trials[k] for trials in passed.values()) for k in sorted(next(iter(passed.values())))]
    return {task for task, trials in passed.items() if len(trials) == 4 and all(trials.values())}, per_trial


sets = {}
for name, directory in RUNS.items():
    sets[name], per_trial = all_four(directory)
    print(f"{name}: {len(sets[name])} of 50 tasks passed in all four trials; passes per trial {per_trial}")
for larger, cheaper in PAIRS:
    for phase in ("phase 1", "phase 2"):
        other = sets[f"{cheaper}, {phase}"]
        print(f"{larger} against {cheaper}, {phase}: only the larger {sorted(sets[larger] - other, key=int)}, "
              f"only the cheaper {sorted(other - sets[larger], key=int)}")
