"""Tasks passed in all four trials, and the paired comparison of two runs (Lab #258).

  python3 compare.py RUN_A RUN_B     # W: all four in B and not in A; L: all four in A and not in B

Reads records.jsonl of each run directory. A task with an unscored trial in either run is left
out of the comparison and named. Reads no conversation.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path


def load(run):
    tasks = defaultdict(dict)
    for line in (Path(run) / "records.jsonl").read_text().splitlines():
        record = json.loads(line)
        tasks[record["task_id"]][record["trial"]] = record["outcome"]   # the last attempt of a trial stands
    return tasks


def summary(name, tasks):
    outcomes = [o for trials in tasks.values() for o in trials.values()]
    scored = [o for o in outcomes if o in ("pass", "fail")]
    at_least = {k: sum(1 for t in tasks.values() if sum(o == "pass" for o in t.values()) >= k) for k in (1, 2, 3, 4)}
    print(f"{name}: {len(tasks)} tasks, {len(outcomes)} conversations, {outcomes.count('pass')} pass, "
          f"{outcomes.count('fail')} fail, {len(outcomes) - len(scored)} unscored; "
          f"pass rate {outcomes.count('pass') / len(scored):.1%} of scored; passed in at least k trials: {at_least}")


a, b = load(sys.argv[1]), load(sys.argv[2])
summary(sys.argv[1], a)
summary(sys.argv[2], b)
complete = lambda t: len(t) == 4 and all(o in ("pass", "fail") for o in t.values())
left_out = sorted(k for k in set(a) | set(b) if not (complete(a.get(k, {})) and complete(b.get(k, {}))))
both = [k for k in a if k not in left_out]
all4 = lambda t: all(o == "pass" for o in t.values())
won = sorted((k for k in both if all4(b[k]) and not all4(a[k])), key=int)
lost = sorted((k for k in both if all4(a[k]) and not all4(b[k])), key=int)
print(f"compared tasks: {len(both)}; left out: {left_out}")
print(f"all four in A: {sum(all4(a[k]) for k in both)}; all four in B: {sum(all4(b[k]) for k in both)}")
print(f"W = {len(won)} {won}")
print(f"L = {len(lost)} {lost}")
print(f"W - L = {len(won) - len(lost)}")
