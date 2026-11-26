"""The report of a retail run directory, built from ``run.json``, ``records.jsonl`` and a rates file only.

It imports nothing of upstream and makes no request, so it works wherever the records are.
A model with no rate, or tokens of a kind that has none for it, are "not priced": never zero,
never another kind's rate.
"""

import json
import math
from pathlib import Path
from typing import Any, Iterable

from ..dataset import DATA_DIR
from .batch import CONVERSATIONS_FILE, MANIFEST_FILE, RECORDS_FILE, SCORED, read_jsonl, read_manifest, recovered_records

RATES_FILE = DATA_DIR / "rates.json"
# token kind of a record -> the key of the rates file that prices it
RATE_KEYS = {"uncached_input": "input", "cache_write_input": "cache_write", "cache_read_input": "cache_read", "output": "output"}
COMPONENTS = ("agent", "customer", "judges")


def load_rates(path: Path) -> dict[str, dict[str, Any]]:
    return json.loads(path.read_text())["models"]


def usage_items(record: dict[str, Any], agent_model: str) -> list[tuple[str, str, dict[str, int]]]:
    """(component, model, tokens by kind) of one attempt: the agent's, then the customer's and the judges'."""
    items = [("agent", agent_model, dict(record["agent_tokens"]))]
    for component, key in (("customer", "customer_usage"), ("judges", "judges_usage")):
        for entry in record[key]["models"]:
            cached, written = entry["cached_tokens"], entry.get("cache_creation_tokens", 0)
            items.append((component, entry["model"], {
                "uncached_input": max(entry["prompt_tokens"] - cached - written, 0), "cache_write_input": written,
                "cache_read_input": cached, "output": entry["completion_tokens"]}))
    return items


def unknown_calls(record: dict[str, Any]) -> dict[str, int]:
    """Calls of one attempt whose reply carried no usage, by component: their tokens are unknown, not zero."""
    unknown = {"agent": record.get("agent_calls_without_usage", 0)}
    for component, key in (("customer", "customer_usage"), ("judges", "judges_usage")):
        unknown[component] = sum(entry.get("calls_without_usage", 0) for entry in record[key]["models"])
    return {component: count for component, count in unknown.items() if count}


def gaps_of(records: Iterable[dict[str, Any]], components: tuple[str, ...] = COMPONENTS) -> dict[str, int]:
    total: dict[str, int] = {}
    for record in records:
        for component, count in unknown_calls(record).items():
            if component in components:
                total[component] = total.get(component, 0) + count
    return total


def price(items: Iterable[tuple[str, str, dict[str, int]]], rates: dict[str, dict[str, Any]],
          components: tuple[str, ...] = COMPONENTS) -> tuple[float | None, list[str]]:
    """Dollars for the items of the given components, or None with what has no rate."""
    total, unpriced = 0.0, []
    for component, model, tokens in items:
        if component not in components:
            continue
        for kind, count in tokens.items():
            if not count:
                continue  # no tokens of this kind: nothing to price
            rate = (rates.get(model) or {}).get(RATE_KEYS[kind])
            if not isinstance(rate, (int, float)):
                label = f"{model} {kind.replace('_', ' ')}" + ("" if model in rates else " (no rate for the model)")
                if label not in unpriced:
                    unpriced.append(label)
                continue
            total += count * rate / 1_000_000
    return (None if unpriced else total), unpriced


def money(value: float | None, unpriced: list[str], items: Iterable[tuple[str, str, dict[str, int]]] = (), divisor: int = 1,
          components: tuple[str, ...] = COMPONENTS, gaps: dict[str, int] | None = None) -> str:
    """A dollar figure, "not priced" with what lacks a rate, or "none" when no tokens were used at all (nothing to price).

    ``gaps`` are the calls whose usage is unknown: a figure over them is a lower bound and says so.
    """
    note = ""
    if gaps:
        note = " (at least: usage unknown for " + ", ".join(f"{count} {component} call(s)" for component, count in gaps.items()) + ")"
    if value is None:
        return "not priced (no rate for: " + "; ".join(unpriced) + ")" + note
    if not any(count for component, _, tokens in items if component in components for count in tokens.values()):
        return "unknown" + note if gaps else "none (no tokens used)"
    return f"${value / divisor:.4f}" + note


def attempts(record: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """The attempt that gave the record's result, and each earlier unscored attempt."""
    return record, record.get("earlier_unscored_attempts", [])


def pass_hat_k(trials: int, successes: int, k: int) -> float:
    """Upstream's pass^k (``tau2.metrics.agent_metrics.pass_hat_k``): the chance that k trials drawn from the task's trials all pass."""
    return math.comb(successes, k) / math.comb(trials, k)


def tokens_table(records: list[dict[str, Any]]) -> list[str]:
    """Calls and tokens by component; ``calls`` include those whose usage was not reported, listed under the table."""
    agent = {kind: sum(r["agent_tokens"][kind] for r in records) for kind in RATE_KEYS}
    lines = ["| Component | Calls | Uncached input | Cache write | Cache read | Output |", "| --- | --- | --- | --- | --- | --- |",
             f"| agent | {sum(r['agent_calls'] for r in records)} | {agent['uncached_input']} | {agent['cache_write_input']} | "
             f"{agent['cache_read_input']} | {agent['output']} |"]
    for component, key in (("customer", "customer_usage"), ("judges", "judges_usage")):
        models: dict[str, dict[str, int]] = {}
        for record in records:
            for entry in record[key]["models"]:
                total = models.setdefault(entry["model"], {"calls": 0, "prompt_tokens": 0, "cached_tokens": 0, "cache_creation_tokens": 0,
                                                           "completion_tokens": 0})
                for name in total:
                    total[name] += entry.get(name, 0)
        for model, total in sorted(models.items()):
            lines.append(f"| {component} `{model}` | {total['calls']} | "
                         f"{max(total['prompt_tokens'] - total['cached_tokens'] - total['cache_creation_tokens'], 0)} | "
                         f"{total['cache_creation_tokens']} | {total['cached_tokens']} | {total['completion_tokens']} |")
        if not models:
            lines.append(f"| {component} | 0 | 0 | 0 | 0 | 0 |")
    gaps = gaps_of(records)
    if gaps:
        lines += ["", "Usage unknown or incomplete (the reply carried none, or lacked a token total), so the counts above are lower bounds: "
                  + ", ".join(f"{count} {component} call(s)" for component, count in gaps.items()) + "."]
    return lines


def build_report(directory: Path, rates_path: Path = RATES_FILE) -> str:
    manifest = read_manifest(directory)
    if manifest is None:
        raise ValueError(f"{directory / MANIFEST_FILE} not found: not a τ-bench run directory")
    parameters = manifest["parameters"]
    rates = load_rates(rates_path)
    agent_model, trials, task_ids = parameters["agent_model"], parameters["trials"], parameters["task_ids"]
    records, _ = recovered_records(directory)  # an interrupted run: the conversations file may be ahead of the index
    wanted = [(t, i) for t in task_ids for i in range(trials)]
    mine = [records[key] for key in wanted if key in records]
    scored = [r for r in mine if r["outcome"] in SCORED]
    unscored = [r for r in mine if r["outcome"] not in SCORED]
    passed = [r for r in scored if r["outcome"] == "pass"]
    upstream = parameters["upstream"]
    out = [f"# τ-bench {upstream['domain']} report: {parameters['provider']} `{agent_model}`", ""]
    instructions = parameters.get("instructions")
    out += [f"- upstream: `{upstream['repository']}` {upstream['release']} (`{upstream['commit']}`), benchmark `{upstream['benchmark']}`, "
            f"language `{upstream['language']}`, subset `{parameters['subset']['name']}` (SHA-256 `{parameters['subset']['sha256']}`)",
            f"- agent `{agent_model}` ({parameters['provider']}); customer `{parameters['user_model']}` with reasoning "
            f"`{parameters['customer_reasoning']['reasoning_effort']}`; judges: upstream's defaults",
            f"- trials {trials}, seed {parameters['seed']}",
            "- instructions: " + (f"SHA-256 `{instructions['sha256']}`, {instructions['bytes']} bytes" if instructions else "none (upstream's policy only)"),
            "", "## Conversations", "",
            f"- tasks: {len(task_ids)}; trials: {trials}; conversations asked for: {len(wanted)}",
            f"- scored: {len(scored)}; unscored: {len(unscored)}; no record yet: {len(wanted) - len(mine)}", ""]
    out += ["## Pass rate", "",
            (f"**{100 * len(passed) / len(scored):.1f}%** ({len(passed)} of {len(scored)} scored conversations)"
             if scored else "n/a (no scored conversation)"),
            "", "Unscored conversations are left out of this rate; they are listed below.", ""]
    if trials > 1:
        out += [f"## Tasks passed in all k trials", ""]
        complete, left_out = [], []
        for task in task_ids:
            runs = [records.get((task, i)) for i in range(trials)]
            if all(r is not None and r["outcome"] in SCORED for r in runs):
                complete.append(sum(1 for r in runs if r["outcome"] == "pass"))
            else:
                left_out.append(task)
        out += ["pass^k as upstream defines it (the chance that k of a task's trials, drawn together, all pass), averaged over the "
                f"tasks whose every trial is scored ({len(complete)} of {len(task_ids)} tasks).", ""]
        out += ["| k | pass^k |", "| --- | --- |"]
        for k in range(1, trials + 1):
            out.append(f"| {k} | " + (f"{100 * sum(pass_hat_k(trials, c, k) for c in complete) / len(complete):.1f}%" if complete else "n/a") + " |")
        out += ["", f"Tasks left out for an unscored or missing trial: {len(left_out)}" + (f" ({', '.join(left_out)})" if left_out else ""), ""]
    out += ["## Unscored", ""]
    if unscored:
        out += ["| Task | Trial | Attempt | Reason |", "| --- | --- | --- | --- |"]
        out += [f"| {r['task_id']} | {r['trial']} | {r['attempt']} | {(r.get('reason') or '').replace('|', '/')} |" for r in unscored]
    else:
        out.append("None.")
    earlier_attempts = [e for r in mine for e in attempts(r)[1]]
    out += ["", "## Tokens, from the attempts that gave the results", ""] + tokens_table(scored)
    out += ["", f"## Tokens, from unscored attempts ({len(unscored)} still unscored, {len(earlier_attempts)} earlier unscored attempt(s) "
            "of conversations since scored or retried)", ""] + tokens_table(unscored + earlier_attempts)
    out += ["", "## Cost", "", f"Rates: `{rates_path}` (US dollars per 1 million tokens).", ""]
    scored_items = [i for r in scored for i in usage_items(r, agent_model)]
    if scored:
        total, unpriced = price(scored_items, rates)
        out.append(f"- cost per scored conversation: {money(total, unpriced, scored_items, len(scored), gaps=gaps_of(scored))}")
        for component in COMPONENTS:
            c_total, c_unpriced = price(scored_items, rates, (component,))
            out.append(f"  - {component}: "
                       f"{money(c_total, c_unpriced, scored_items, len(scored), (component,), gaps_of(scored, (component,)))}")
    else:
        out.append("- cost per scored conversation: n/a (no scored conversation)")
    unscored_items = [i for r in unscored for i in usage_items(r, agent_model)]
    earlier = [i for e in earlier_attempts for i in usage_items(e, agent_model)]
    earlier_count = len(earlier_attempts)
    failed_items = unscored_items + earlier
    t_total, t_unpriced = price(scored_items + failed_items, rates)
    s_total, s_unpriced = price(scored_items, rates)
    u_total, u_unpriced = price(failed_items, rates)
    failed_gaps = gaps_of(unscored + earlier_attempts)
    out += ["", f"- total spent: {money(t_total, t_unpriced, scored_items + failed_items, gaps=gaps_of(scored + unscored + earlier_attempts))}",
            f"  - attempts that gave a result: {money(s_total, s_unpriced, scored_items, gaps=gaps_of(scored))}",
            f"  - unscored attempts, shown apart ({len(unscored)} still unscored, {earlier_count} earlier unscored attempt(s) of "
            f"conversations since scored or retried): {money(u_total, u_unpriced, failed_items, gaps=failed_gaps)}", ""]
    return "\n".join(out) + "\n"
