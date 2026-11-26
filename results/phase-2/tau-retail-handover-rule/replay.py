"""Where the hand-over rule would have stepped in, over the recorded gpt-6-luna conversations. No model call.

    uv run --locked python results/phase-2/tau-retail-handover-rule/replay.py     # from the repository root

For each recorded conversation it finds the first call to the transfer tool and asks the rule's own test
(``customer_asked_for_a_person``) whether the customer had asked for a person by then. A transfer made before
the customer asked is one the rule would not have allowed: the tool would not have been sent. It says where
the rule steps in, not what the model would have done next.
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # the repository root, when run as a script

from benchmark_loop_agent.tau.agent import HANDOVER_TOOL, customer_asked_for_a_person

RESULTS = Path(__file__).resolve().parents[2]
RUNS = {"phase-1/tau-retail/luna": "no change", "phase-2/tau-retail-paragraph/control-luna": "no change",
        "phase-2/tau-retail-paragraph/treatment-luna": "reasoning paragraph", "phase-2/tau-retail-finish-check/luna": "finish check"}
NEVER_PASSED = {"38", "52", "105"}  # passed by no model in any trial; counted apart
WRITES = {"cancel_pending_order", "exchange_delivered_order_items", "modify_pending_order_address", "modify_pending_order_items",
          "modify_pending_order_payment", "modify_user_address", "return_delivered_order_items"}

counts = collections.Counter()
for run in RUNS:
    for line in open(RESULTS / run / "conversations.jsonl"):
        conversation = json.loads(line)
        group = ("tasks 38, 52, 105: " if conversation["task_id"] in NEVER_PASSED else "other tasks: ") + conversation["outcome"]
        counts[group, "conversations"] += 1
        items, written = [], 0
        for message in conversation["messages"]:
            if message.get("role") == "user":
                items.append({"role": "user", "text": message.get("content") or ""})
            calls = [call["name"] for call in message.get("tool_calls") or []] if message.get("role") == "assistant" else []
            if HANDOVER_TOOL in calls:
                expected = sum(1 for a in conversation["reward_info"]["action_checks"] if a["tool_type"] == "write")
                counts[group, "transfer the rule would allow" if customer_asked_for_a_person(items) else "transfer the rule would not allow"] += 1
                if not customer_asked_for_a_person(items):
                    counts[group, "  of those, made with as many changes as the task expects" if written >= expected else "  of those, made with fewer changes than the task expects"] += 1
                break
            written += sum(1 for name in calls if name in WRITES)
print(f"{len(RUNS)} runs of gpt-6-luna, 4 trials of 50 tasks each")
for (group, what), number in sorted(counts.items()):
    print(f"{group:32s} {number:4d}  {what}")
