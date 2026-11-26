"""Failed conversations by what the agent did, for the runs without the check (Lab #258's control) and with it.

    python3 classes.py          # from this directory

The classes are those of ../tau-retail-paragraph/classify.py, grouped. Counted from conversations.jsonl by
tool calls and upstream's reward information; no conversation is read by a person or an agent.
"""
import collections
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
CONTROL = HERE.parent / "tau-retail-paragraph"
WRITE = {"cancel_pending_order", "exchange_delivered_order_items", "modify_pending_order_address", "modify_pending_order_items",
         "modify_pending_order_payment", "modify_user_address", "return_delivered_order_items"}


def classes(directory):
    found = collections.Counter()
    for line in open(directory / "conversations.jsonl"):
        c = json.loads(line)
        if c["outcome"] != "fail":
            continue
        calls = [tc.get("name") for m in c["messages"] if m.get("role") == "assistant" for tc in (m.get("tool_calls") or [])]
        writes = [n for n in calls if n in WRITE]
        checks = [a for a in c["reward_info"]["action_checks"] if a["tool_type"] == "write"]
        missed = [a["action"]["name"] for a in checks if not a["action_match"]]
        database = c["reward_info"]["db_check"]["db_match"] if c["reward_info"].get("db_check") else None
        if database:
            kind = "changed the order correctly and failed a written check"
        elif checks and not writes:
            kind = "changed nothing" + (", handed to a human" if "transfer_to_human_agents" in calls else "")
        elif checks and missed and all(n in writes for n in missed):
            kind = "right action, wrong detail"
        elif checks and missed and len(writes) < len(checks):
            kind = "some of the requested changes, not all"
        else:
            kind = "other"
        found[kind] += 1
    return found


for model in ("haiku", "luna"):
    without, with_check = classes(CONTROL / f"control-{model}"), classes(HERE / model)
    print(f"\n{model}: {sum(without.values())} failed conversations without the check, {sum(with_check.values())} with it")
    for kind in sorted(set(without) | set(with_check)):
        print(f"  {without[kind]:3d} -> {with_check[kind]:3d}  {kind}")
