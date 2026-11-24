"""One Markdown report per model, built from a finished run's files only.

Reads ``records.jsonl`` and ``run.json`` of the run directory and the rates
file. It never reads Phoenix, the dataset or the network, so a report can be
regenerated at any time.

    python -m benchmark_loop_agent.report RUN_DIR [--rates FILE] [--output-dir DIR]
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from .dataset import DATA_DIR
from .store import MANIFEST_FILE, RECORDS_FILE, read_manifest, read_records

RATES_FILE = DATA_DIR / "rates.json"
OUTCOMES = ("pass", "fail", "unscored")


def load_rates(path: Path) -> dict[str, dict[str, Any]]:
    return json.loads(path.read_text())["models"]


def accuracy(passed: int, failed: int) -> str:
    judged = passed + failed
    return f"{100 * passed / judged:.1f}% ({passed}/{judged})" if judged else "n/a (nothing judged)"


def cost_of(rate: dict[str, Any], input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * rate["input"] + output_tokens * rate["output"]) / 1_000_000


def wall_time(sessions: list[dict[str, Any]], legacy_concurrency: Any = None) -> tuple[str, list[str]]:
    """Total wall time, or why it is unavailable. Never derived from case latencies."""
    lines, missing = [], []
    for s in sorted(sessions, key=lambda s: s["number"]):
        if s.get("ended_at") is None or s.get("wall_seconds") is None:
            missing.append(str(s["number"]))
            shown = "unavailable (no end time was saved; the invocation was interrupted)"
        else:
            shown = f"{s['wall_seconds']:.1f} s"
        concurrency = s.get("concurrency", legacy_concurrency)  # the earlier manifest kept one global value
        lines.append(f"| {s['number']} | {'n/a' if concurrency is None else concurrency} | {s['started_at']} | {s.get('ended_at') or '-'} | {shown} |")
    if missing:
        total = f"unavailable for invocation {', '.join(missing)}, so no total is given"
    else:
        total = f"{sum(s['wall_seconds'] for s in sessions):.1f} s over {len(sessions)} invocation(s)"
    return total, lines


def render(manifest: dict[str, Any], provider: str, records: list[dict[str, Any]],
           rates: dict[str, dict[str, Any]]) -> str:
    params = manifest["parameters"]
    requested = params["models"].get(provider)
    mine = [r for r in records if r["provider"] == provider]
    sessions = manifest.get("sessions", [])
    counts = Counter(r["outcome"] for r in mine)

    selection = manifest.get("selection")  # cases per category in this run, saved when it started
    cap = params["sample_size"]  # a maximum: a category with fewer cases is taken whole
    if selection is None and cap == 0:  # the saved cap alone proves nothing was selected in any category
        selection = {c: 0 for c in params["categories"]}
    sampled = cap is not None
    size = {c: sum(1 for r in mine if r["category"] == c) for c in params["categories"]}
    problems, notes = [], []
    if selection is None:  # a run saved before the counts were recorded
        absent = [f"`{c}`" for c in params["categories"] if not size[c]]
        notes.append("This run's files do not record how many cases each category held, so whether every "
                     "selected case has a record cannot be established" +
                     (f"; no record exists for {', '.join(absent)} (an empty category cannot be told from a lost one)"
                      if absent else "") + ".")
    else:
        short = [f"`{c}` ({size[c]} of {selection.get(c, 0)} case(s))"
                 for c in params["categories"] if size[c] < selection.get(c, 0)]
        if short:
            problems.append("records missing for " + ", ".join(short))
    if counts["unscored"]:
        problems.append(f"{counts['unscored']} case(s) are unscored")
    if sessions and max(sessions, key=lambda s: s["number"]).get("ended_at") is None:
        problems.append("the latest invocation has no saved end time")

    out = [f"# Benchmark report: `{requested or 'model not set'}` ({provider})", ""]
    if sampled:
        if selection is None:
            sizes = f"at most {cap} case(s) per category (actual sizes not recorded)"
            whole = False
        else:
            sizes = f"at most {cap} case(s) per category, selected: " + ", ".join(
                f"`{c}` {selection.get(c, 0)}" for c in params["categories"])
            whole = all(selection.get(c, 0) < cap for c in params["categories"])
        out += [f"> **Sampled run.** {sizes}, seed {params['seed']}; " + (
            "every category was smaller than the maximum, so the whole of each was taken." if whole
            else "the figures are not necessarily those of the full dataset."), ""]
    for note in notes:
        out += ["> **Completeness unknown.** " + note, ""]
    if problems:
        out += ["> **Incomplete run.** " + "; ".join(problems) + ".", ""]

    out += ["## Accuracy", "",
            "Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it "
            "(they are counted below). **Overall** pools every judged case of the model, so each case "
            "counts once and a larger category weighs more; it is not the mean of the category figures.", "",
            "| Category | Accuracy | Pass | Fail | Unscored |", "| --- | --- | --- | --- | --- |"]
    for category in params["categories"]:
        c = Counter(r["outcome"] for r in mine if r["category"] == category)
        out.append(f"| `{category}` | {accuracy(c['pass'], c['fail'])} | {c['pass']} | {c['fail']} | {c['unscored']} |")
    out += [f"| **Overall** | **{accuracy(counts['pass'], counts['fail'])}** | {counts['pass']} | {counts['fail']} | {counts['unscored']} |", ""]

    # Each known count is summed on its own; a record with only one of them still counts that one.
    in_tokens = sum(r["input_tokens"] for r in mine if r["input_tokens"] is not None)
    out_tokens = sum(r["output_tokens"] for r in mine if r["output_tokens"] is not None)
    full = sum(1 for r in mine if r["input_tokens"] is not None and r["output_tokens"] is not None)
    no_usage = [f"`{r['case_id']}` ({'input and output' if r['input_tokens'] is None and r['output_tokens'] is None else 'input' if r['input_tokens'] is None else 'output'})"
                for r in mine if r["input_tokens"] is None or r["output_tokens"] is None]
    out += ["## Tokens and cost", "",
            f"* Input tokens: {in_tokens:,}", f"* Output tokens: {out_tokens:,}",
            f"* Records with complete usage: {full} of {len(mine)}"]
    if no_usage:
        out.append(f"* {len(no_usage)} case(s) lack reported usage (the missing count is named); the counts "
                   "that were reported are included, nothing was estimated for the missing ones, so the "
                   f"tokens and the cost are a lower bound: {', '.join(no_usage)}")
    rate = rates.get(requested) if requested else None
    if rate is None:
        out.append(f"* Cost: not given, the rates file has no entry for `{requested}`.")
    else:
        out += [f"* Cost: **${cost_of(rate, in_tokens, out_tokens):.4f}** at {rate['input']:.2f} (input) and "
                f"{rate['output']:.2f} (output) US dollars per 1 million tokens, standard tier "
                f"([pricing page]({rate['page']}), read on {rate['read_on']}).",
                "* The cost counts all input tokens at the uncached input rate. The records do not separate "
                "cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it."]
    out.append("")

    total, rows = wall_time(sessions, params.get("concurrency"))
    out += ["## Time", "",
            "The wall time is that of the whole run, as saved in `run.json`; all providers of the run "
            "share its invocations.", "", f"* Wall time: {total}", "",
            "| Invocation | Concurrency | Started | Ended | Wall time |", "| --- | --- | --- | --- | --- |", *rows, ""]

    actual = sorted({r["actual_model"] for r in mine if r["actual_model"]})
    out += ["## Run", "",
            f"* Run identifier: `{manifest.get('run_id', 'n/a')}`",
            f"* Requested model: `{requested}`",
            f"* Actual model (as the responses report it): {', '.join(f'`{m}`' for m in actual) or 'none, no response arrived'}",
            f"* Dataset revision: `{manifest.get('dataset_revision')}`",
            f"* Scorer revision: `{manifest.get('scorer_revision')}`",
            f"* Categories: {', '.join(f'`{c}`' for c in params['categories'])}",
            f"* Sample size per category: {f'at most {cap}' if sampled else 'all cases'}",
            f"* Seed: {params['seed']}",
            f"* Providers in the run: {', '.join(params['providers'])}", ""]
    return "\n".join(out)


def file_name(provider: str, model: str | None) -> str:
    return "report-" + re.sub(r"[^A-Za-z0-9._-]+", "_", f"{provider}-{model or 'unset'}") + ".md"


def build_reports(run_dir: Path, rates_path: Path, output_dir: Path) -> list[Path]:
    manifest = read_manifest(run_dir)
    if manifest is None:
        raise ValueError(f"{run_dir / MANIFEST_FILE} not found: not a run directory")
    records = read_records(run_dir / RECORDS_FILE)
    rates = load_rates(rates_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for provider in manifest["parameters"]["providers"]:
        path = output_dir / file_name(provider, manifest["parameters"]["models"].get(provider))
        path.write_text(render(manifest, provider, records, rates))
        written.append(path)
    return written


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="benchmark_loop_agent.report",
                                     description="Write one Markdown report per model from a run directory.")
    parser.add_argument("run_dir", type=Path, help="the --output-dir of a finished run")
    parser.add_argument("--rates", type=Path, default=RATES_FILE, help="rates file (default: data/rates.json)")
    parser.add_argument("--output-dir", type=Path, default=None, help="where the reports go (default: the run directory)")
    args = parser.parse_args(argv)
    try:
        paths = build_reports(args.run_dir, args.rates, args.output_dir or args.run_dir)
    except (ValueError, OSError, KeyError) as error:
        parser.error(f"{type(error).__name__}: {error}")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
