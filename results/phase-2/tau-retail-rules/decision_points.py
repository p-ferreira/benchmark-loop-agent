"""Decision points: one reply of gpt-6-luna re-asked at the moment an offer is made, plain and under the rules.

    uv run --locked python results/phase-2/tau-retail-rules/decision_points.py list            # no model call
    uv run --locked python results/phase-2/tau-retail-rules/decision_points.py run dev OUT     # paid: 2 arms x 24 points
    uv run --locked python results/phase-2/tau-retail-rules/decision_points.py run reserve OUT

A decision point is cut from a recorded conversation whose task expects an item change or exchange: the
conversation up to, and not including, the agent's first message to the customer after it read the product
of the expected new item. That message is where the offer is made. Each arm is asked for that one message
again: ``plain`` with one model call on the recorded conversation, ``rules`` with ``rules.turn`` (the product
shown as a summary, the search run in code). The reply is graded on the grading side only: it is ``right``
when it names the expected new item (by item id or by its price) and ``wrong`` when it names the price or id
of another variant of the product and not the expected one; anything else is ``unclear`` and is read by a
person. The expected item is never shown to the model. Points come from failed conversations (the recorded
agent did not make the expected change) and from passed ones (controls: what the rules must not break).
The tasks are split in two panels, ``dev`` and ``reserve``, with no task in both.
"""
import collections
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from benchmark_loop_agent.tau import rules  # noqa: E402

RESULTS = ROOT / "results"
RUNS = ["phase-1/tau-retail/luna", "phase-2/tau-retail-paragraph/control-luna", "phase-2/tau-retail-paragraph/treatment-luna",
        "phase-2/tau-retail-finish-check/luna", "phase-2/tau-retail-handover-rule/design-luna"]
NEVER_PASSED = {"38", "52", "105"}
PER_PANEL = 12  # failed points and as many passed ones


def kept(messages):
    """Recorded messages as the agent keeps them (role, text, calls)."""
    items = []
    for m in messages:
        if m["role"] == "user":
            items.append({"role": "user", "text": m.get("content") or ""})
        elif m["role"] == "tool":
            items.append({"role": "tool", "id": m["id"], "text": m.get("content") or ""})
        else:
            items.append({"role": "assistant", "text": m.get("content") or "",
                          "calls": [{"id": t["id"], "name": t["name"], "arguments": t["arguments"]} for t in m.get("tool_calls") or []]})
    return items


def points():
    """Every decision point of the recorded runs: (failed?, task, run, trial, prefix items, expected ids, other variants)."""
    found = []
    for run in RUNS:
        for line in open(RESULTS / run / "conversations.jsonl"):
            c = json.loads(line)
            if c["task_id"] in NEVER_PASSED or c["outcome"] not in ("pass", "fail"):
                continue
            expected = [a["action"] for a in c["reward_info"].get("action_checks") or [] if a["action"]["name"] in rules.ITEM_CHANGES]
            wanted = {str(i) for a in expected for i in a["arguments"]["new_item_ids"]}
            if not wanted:
                continue
            items = kept(c["messages"])
            made = {str(i) for item in items if item["role"] == "assistant" for call in item["calls"] if call["name"] in rules.ITEM_CHANGES
                    for i in call["arguments"].get("new_item_ids") or []}
            if c["outcome"] == "fail" and wanted <= made:
                continue  # it failed on something else: the expected items were all written
            for position, item in enumerate(items):
                if item["role"] != "assistant" or item["calls"] or not item["text"] or position == 0:
                    continue
                products = rules.products_read(items[:position])
                variants = {v["item_id"]: v for p in products.values() for v in p["variants"].values() if wanted & set(p["variants"])}
                here = wanted & set(variants)
                if not here:
                    continue
                if any(call["name"] in rules.ITEM_CHANGES for earlier in items[:position] if earlier["role"] == "assistant" for call in earlier["calls"]):
                    break  # an item change was already written by then: no offer is left to make
                found.append({"failed": c["outcome"] == "fail", "task": c["task_id"], "run": run, "trial": c["trial"], "items": items[:position],
                              "expected": sorted(here), "variants": variants, "recorded_reply": item["text"]})
                break
    return found


def panels():
    """``dev`` and ``reserve``: tasks alternate between them; in each, up to PER_PANEL failed and PER_PANEL passed points, spread over tasks."""
    by_task = collections.defaultdict(list)
    for point in points():
        by_task[point["task"]].append(point)
    chosen = {"dev": [], "reserve": []}
    failing_tasks = sorted((t for t, ps in by_task.items() if any(p["failed"] for p in ps)), key=int)
    other_tasks = sorted((t for t in by_task if t not in failing_tasks), key=int)
    for index, task in enumerate(failing_tasks + other_tasks):
        chosen["dev" if index % 2 == 0 else "reserve"].append(task)
    result = {}
    for name, tasks in chosen.items():
        picked = []
        for failed in (True, False):
            pools = [[p for p in by_task[t] if p["failed"] == failed] for t in tasks]
            taken, depth = [], 0
            while len(taken) < PER_PANEL and any(len(pool) > depth for pool in pools):
                for pool in pools:
                    if len(pool) > depth and len(taken) < PER_PANEL:
                        taken.append(pool[depth])
                depth += 1
            picked += taken
        result[name] = picked
    return result


def grade(point, text, calls):
    """``right``, ``wrong`` or ``unclear``, from what the reply names. Grading side only."""
    said = (text or "") + " " + json.dumps([c["arguments"] for c in calls])
    def names(item_id):
        return item_id in said or f"{point['variants'][item_id]['price']:.2f}" in said
    expected_prices = {f"{point['variants'][i]['price']:.2f}" for i in point["expected"]}
    if all(names(i) for i in point["expected"]):
        return "right"
    owned = {line.get("item_id") for _, text in rules.results_of(point["items"], rules.ORDER_TOOL) for line in ((json.loads(text).get("items") or [])
                                                                                                 if text.startswith("{") else [])}
    others = [i for i in point["variants"] if i not in point["expected"] and i not in owned  # naming an item the customer has is no offer
              and f"{point['variants'][i]['price']:.2f}" not in expected_prices]
    if any(names(i) for i in others):
        return "wrong"
    return "unclear"


def main():
    if sys.argv[1] == "list":
        for name, picked in panels().items():
            print(f"{name}: {sum(p['failed'] for p in picked)} failed and {sum(not p['failed'] for p in picked)} passed points; "
                  f"tasks {sorted({p['task'] for p in picked}, key=int)}")
            for p in picked:
                print(f"  {'failed' if p['failed'] else 'passed'} task {p['task']:>3} {p['run'].split('/')[-1]:15s} trial {p['trial']} "
                      f"prefix {len(p['items']):3d} items; recorded reply graded {grade(p, p['recorded_reply'], [])}")
        everything = points()
        print(f"all points: {sum(p['failed'] for p in everything)} failed, {sum(not p['failed'] for p in everything)} passed")
        return
    panel, out = sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    from benchmark_loop_agent.providers import send_request
    from benchmark_loop_agent.tau import agent as tau_agent
    from benchmark_loop_agent.tau.upstream import load
    registry = load().registry
    environment = registry.get_env_constructor("retail")()
    tools, policy = environment.get_tools(), environment.get_policy()
    agent_class = tau_agent.make_agent_class()
    done = {}
    record_file = out / f"{panel}.jsonl"
    if record_file.exists():
        done = {(r["task"], r["run"], r["trial"], r["arm"]): r for r in map(json.loads, open(record_file))}
    with open(record_file, "a") as records:
        for point in panels()[panel]:
            for arm in ("plain", "rules"):
                key = (point["task"], point["run"], point["trial"], arm)
                if key in done:
                    continue
                usage = tau_agent.AgentUsage()
                agent = agent_class(tools, policy, provider="openai", model="gpt-6-luna", api_key=os.environ["OPENAI_API_KEY"],
                                    send=send_request, usage=usage, rules=rules.RULES if arm == "rules" else ())
                definitions = tau_agent.tool_definitions(tools)
                try:
                    if arm == "plain":
                        text, calls = agent._ask(agent.system_prompt, point["items"], definitions)
                    else:
                        text, calls = rules.turn(rules.RULES, point["items"], definitions,
                                                 lambda shown, offered: agent._ask(agent.system_prompt, shown, offered), usage.rules,
                                                 tau_agent.customer_asked_for_a_person(point["items"]))
                    error = None
                except Exception as problem:  # noqa: BLE001  (a failed call is a result here, kept with its reason)
                    text, calls, error = "", [], f"{type(problem).__name__}: {str(problem)[:200]}"
                record = {"task": point["task"], "run": point["run"], "trial": point["trial"], "arm": arm, "failed_in_recording": point["failed"],
                          "expected": point["expected"], "grade": "error" if error else grade(point, text, calls), "error": error,
                          "reply": text, "calls": calls, "rules": usage.rules.record(), "model_calls": len(usage.calls), "tokens": usage.totals()}
                records.write(json.dumps(record) + "\n")
                records.flush()
                done[key] = record
    rows = list(done.values())
    for arm in ("plain", "rules"):
        for failed in (True, False):
            mine = [r for r in rows if r["arm"] == arm and r["failed_in_recording"] == failed]
            print(f"{arm:5s} on {'failed' if failed else 'passed'} points: " + ", ".join(f"{g} {sum(r['grade'] == g for r in mine)}" for g in ("right", "wrong", "unclear", "error")))
    totals = collections.Counter()
    for r in rows:
        totals.update(r["tokens"])
        totals["model_calls"] += r["model_calls"]
    print("tokens:", dict(totals))


if __name__ == "__main__":
    main()
