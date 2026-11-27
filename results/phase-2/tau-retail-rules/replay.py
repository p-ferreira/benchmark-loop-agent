"""Where each retail rule (``--rules``) would have stepped in, over the recorded gpt-6-luna conversations. No model call.

    uv run --locked python results/phase-2/tau-retail-rules/replay.py     # from the repository root

For every recorded conversation it walks the agent's replies in order and asks each rule's own test whether it
would have stepped in at that reply. For ``address`` the corrected call is also compared with the call the task
expects, which says whether the correction alone makes that call right. For the three other rules it says where
the rule steps in, not what the model would have done next: that takes a paid run. The expected calls are read
for grading only; no rule sees them.
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # the repository root, when run as a script

from benchmark_loop_agent.tau import rules
from benchmark_loop_agent.tau.agent import customer_asked_for_a_person

RESULTS = Path(__file__).resolve().parents[2]
RUNS = ["phase-1/tau-retail/luna", "phase-2/tau-retail-paragraph/control-luna", "phase-2/tau-retail-paragraph/treatment-luna",
        "phase-2/tau-retail-finish-check/luna", "phase-2/tau-retail-handover-rule/design-luna"]
NEVER_PASSED = {"38", "52", "105"}


def canon(arguments):
    return json.dumps({k: sorted(v) if isinstance(v, list) else v for k, v in arguments.items()}, sort_keys=True)


fired = collections.defaultdict(lambda: collections.Counter())   # rule -> outcome -> conversations
tasks = collections.defaultdict(lambda: collections.defaultdict(set))
detail = collections.Counter()
conversations = collections.Counter()
for run in RUNS:
    for line in open(RESULTS / run / "conversations.jsonl"):
        c = json.loads(line)
        if c["task_id"] in NEVER_PASSED or c["outcome"] not in ("pass", "fail"):
            continue
        outcome = c["outcome"]
        conversations[outcome] += 1
        expected = {(a["action"]["name"], canon(a["action"]["arguments"])) for a in c["reward_info"].get("action_checks") or []}
        items, hit, refused, paid = [], set(), False, False
        for m in c["messages"]:
            if m["role"] == "user":
                items.append({"role": "user", "text": m.get("content") or ""})
            elif m["role"] == "tool":
                items.append({"role": "tool", "id": m["id"], "text": m.get("content") or ""})
                if rules.product_table(m.get("content") or "") != (m.get("content") or ""):
                    hit.add("products")
            else:
                text = m.get("content") or ""
                calls = [{"id": t["id"], "name": t["name"], "arguments": t["arguments"]} for t in m.get("tool_calls") or []]
                for call in calls:
                    fixed = rules.fix_address(call)
                    if fixed is not call:
                        hit.add("address: call corrected")
                        was = (call["name"], canon(call["arguments"])) in expected
                        now = (fixed["name"], canon(fixed["arguments"])) in expected
                        detail[outcome, "address correction: " + ("expected call before and after" if was and now else
                               "makes the call the expected one" if now else "breaks an expected call" if was else "call still not the expected one")] += 1
                if rules.asks_for_country(text, calls):
                    hit.add("country: reply asking for the country held")
                if not paid and rules.payment_not_chosen(items, calls):
                    paid = True
                    hit.add("payment")
                    change = next(call for call in calls if call["name"] in rules.ITEM_CHANGES)
                    wanted = [json.loads(arguments).get("payment_method_id") for name, arguments in expected
                              if name == change["name"] and json.loads(arguments).get("order_id") == change["arguments"].get("order_id")]
                    detail[outcome, "payment held: the call's method " + ("is the expected one" if change["arguments"].get("payment_method_id") in wanted
                           else "is not the expected one" if wanted else "(no such expected call)")] += 1
                if not refused and rules.first_early_transfer(items, calls, customer_asked_for_a_person(items)):
                    refused = True
                    hit.add("handover-once")
                items.append({"role": "assistant", "text": text, "calls": calls})
        for rule in hit:
            fired[rule][outcome] += 1
            tasks[rule][outcome].add(c["task_id"])
print(f"{len(RUNS)} runs of gpt-6-luna, 47 tasks: {conversations['fail']} failed and {conversations['pass']} passed conversations")
print("conversations in which the rule steps in at least once:")
for rule in sorted(fired):
    print(f"  {rule:45s} failed {fired[rule]['fail']:3d}  passed {fired[rule]['pass']:3d}   tasks among the failed: "
          f"{' '.join(sorted(tasks[rule]['fail'], key=int))}")
for (outcome, what), number in sorted(detail.items()):
    print(f"  {outcome:5s} {number:4d}  {what}")
