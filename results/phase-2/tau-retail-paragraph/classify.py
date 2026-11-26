"""Class every failed conversation of the three runs per model (phase-1 run, control, treatment) by what the agent did
against the expected actions. Counted after the figures of Lab #258 were fixed.  python3 classify.py"""
import json, collections, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
P1 = HERE.parent.parent/"phase-1/tau-retail"
WRITE = {"cancel_pending_order","exchange_delivered_order_items","modify_pending_order_address","modify_pending_order_items",
         "modify_pending_order_payment","modify_user_address","return_delivered_order_items"}
def norm(a):
    return json.dumps({k:(sorted(v) if isinstance(v,list) else v) for k,v in (a or {}).items()}, sort_keys=True)
for model, dirs in {"haiku":[P1/"haiku",HERE/"control-haiku",HERE/"treatment-haiku"], "luna":[P1/"luna",HERE/"control-luna",HERE/"treatment-luna"]}.items():
    cls = collections.Counter(); by_task = collections.defaultdict(collections.Counter); argdiff = collections.Counter(); seen=set()
    for d in dirs:
        for l in open(pathlib.Path(d)/"conversations.jsonl"):
            c = json.loads(l)
            if c["outcome"] != "fail": continue
            calls = [(tc.get("name"), tc.get("arguments")) for m in c["messages"] if m.get("role")=="assistant" for tc in (m.get("tool_calls") or [])]
            seen |= {n for n,_ in calls}
            writes = [(n,a) for n,a in calls if n in WRITE]
            transfer = any(n=="transfer_to_human_agents" for n,_ in calls)
            exp = [(a["action"]["name"], a["action"]["arguments"]) for a in c["reward_info"]["action_checks"] if a["tool_type"]=="write"]
            missed = [(a["action"]["name"], a["action"]["arguments"]) for a in c["reward_info"]["action_checks"] if a["tool_type"]=="write" and not a["action_match"]]
            db_ok = c["reward_info"]["db_check"]["db_match"] if c["reward_info"].get("db_check") else None
            if db_ok: k = "database right, written assertion failed"
            elif not exp and writes: k = "changed something when no change was expected"
            elif not exp: k = "no change expected, none made, database still differs"
            elif not writes: k = "made no change at all" + (" (transferred to a human)" if transfer else "")
            elif not missed: k = "expected changes made, plus an extra or repeated change"
            else:
                names = {n for n,_ in writes}
                if all(n in names for n,_ in missed):
                    k = "right action, wrong details"
                    for n,a in missed:
                        got = [w for wn,w in writes if wn==n]
                        diff = sorted(key for key in a if all(norm({key:a[key]}) != norm({key:(g or {}).get(key)}) for g in got))
                        argdiff[(n, tuple(diff))] += 1
                elif len(writes) < len(exp): k = "made some of the expected changes, not all"
                else: k = "made a different kind of change"
            cls[k]+=1; by_task[c["task_id"]][k]+=1
    print(f"\n=== {model}: {sum(cls.values())} failed conversations")
    for k,v in cls.most_common(): print(f"  {v:3d}  {k}")
    print("  wrong details, by action and differing fields:", argdiff.most_common(6))
    for t in ("38","52","105","32"): print(f"  task {t}:", dict(by_task[t]))
