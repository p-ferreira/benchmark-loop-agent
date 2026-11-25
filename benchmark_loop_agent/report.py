"""One Markdown report per model, built from a finished run's files only.

Reads ``records.jsonl`` and ``run.json`` of the run directory and the rates
file. It never reads Phoenix or the network, so a report can be regenerated at
any time. Only the failure classes and ``--compare`` read the dataset: the
expected number of calls of a failed case, and which cases a run selected.

    python -m benchmark_loop_agent.report RUN_DIR [--rates FILE] [--output-dir DIR]
    python -m benchmark_loop_agent.report RUN_DIR RUN_DIR ... --output-dir DIR   # spread over repeated runs
    python -m benchmark_loop_agent.report --compare DIR_A DIR_B [--output-dir DIR]   # two runs, case by case
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from .comparison import OVERALL, UNAVAILABLE, comparison_counts, format_figure
from .compare import build_comparison
from .dataset import DATA_DIR
from .failures import FAILURE_CLASSES, UnknownCase, failure_class
from .repeats import render_spread, spreads
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


def comparison_section(manifest: dict[str, Any], provider: str, records: list[dict[str, Any]]) -> list[str]:
    """The comparison figure per category and overall, beside (not instead of) accuracy."""
    out = ["## Comparison figure", "",
           "Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and "
           "selected cases with no record stay in the denominator, so both count against the figure.", ""]
    counts = comparison_counts(manifest, records, provider)
    if counts is None:
        return out + [f"Comparison figure: {UNAVAILABLE}. This run's `run.json` does not record the cases it "
                      "selected, and a figure computed from the records present would leave out any missing case.", ""]
    mine = [r for r in records if r["provider"] == provider]
    out += ["| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |",
            "| --- | --- | --- | --- | --- | --- | --- |"]
    totals = [0, 0, 0]
    for key, (passed, selected) in counts.items():
        subset = mine if key == OVERALL else [r for r in mine if r["category"] == key]
        failed, unscored = (sum(1 for r in subset if r["outcome"] == o) for o in ("fail", "unscored"))
        missing = selected - passed - failed - unscored
        label, bold = ("Overall", "**") if key == OVERALL else (f"`{key}`", "")
        out.append(f"| {bold}{label}{bold} | "
                   f"{bold}{format_figure(passed, selected)}{bold} | {selected} | {passed} | {failed} | {unscored} | {missing} |")
    return out + [""]


def failure_section(provider: str, records: list[dict[str, Any]], categories: Sequence[str]) -> list[str]:
    """Failed cases by class, per category and overall; each failed case has exactly one class."""
    mine = [r for r in records if r["provider"] == provider and r["outcome"] == "fail"]
    try:
        classes = [(r["category"], failure_class(r)) for r in mine]
    except UnknownCase as error:
        raise ValueError(f"the expected answer of {error} cannot be found in the pinned data, so its failure "
                         "class is unknown; the report is not written") from None
    out = ["## Failure classes", "",
           "Each failed case has exactly one class, the first of these that applies: "
           "`called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a "
           "returned call could not be scored: arguments that are not a JSON object, or nested too deep); "
           "`no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number "
           "of calls differs from the expected answer's); `wrong-call` (the number is right and the checker "
           "rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.", "",
           "| Category | Failed | " + " | ".join(f"`{c}`" for c in FAILURE_CLASSES) + " |",
           "| --- | --- | " + " | ".join("---" for _ in FAILURE_CLASSES) + " |"]
    for key in [*categories, None]:
        subset = [c for category, c in classes if key is None or category == key]
        counts = Counter(subset)
        cells = " | ".join(str(counts[c]) for c in FAILURE_CLASSES)
        label, bold = ("Overall", "**") if key is None else (f"`{key}`", "")
        out.append(f"| {bold}{label}{bold} | {len(subset)} | {cells} |")
    return out + [""]


def instruction_line(manifest: dict[str, Any], provider: str) -> str:
    used = (manifest["parameters"].get("instructions") or {}).get(provider)
    if not used:
        return "* Instruction: none used"
    return f"* Instruction: SHA-256 `{used['sha256']}`, {used['bytes']} bytes"


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

    split = params.get("split")
    out = [f"# Benchmark report: `{requested or 'model not set'}` ({provider})", ""]
    if split:
        out += [f"> **Part: `{split}`.** This run selected only the cases of the {split} part of the split.", ""]
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

    out += comparison_section(manifest, provider, records)
    out += failure_section(provider, records, params["categories"])

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
            f"* Actual model (as the responses report it): {', '.join(f'`{m}`' for m in actual) or 'none, no actual model was reported'}",
            f"* Dataset revision: `{manifest.get('dataset_revision')}`",
            f"* Scorer revision: `{manifest.get('scorer_revision')}`",
            f"* Categories: {', '.join(f'`{c}`' for c in params['categories'])}",
            f"* Sample size per category: {f'at most {cap}' if sampled else 'all cases'}",
            f"* Seed: {params['seed']}",
            f"* Split part: {split or 'none, every case of the categories'}",
            instruction_line(manifest, provider),
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


def build_repeated_report(run_dirs: Sequence[Path], output_dir: Path) -> list[Path]:
    """One spread report per provider over runs of one configuration; refuses anything else."""
    manifests = []
    for run_dir in run_dirs:
        manifest = read_manifest(run_dir)
        if manifest is None:
            raise ValueError(f"{run_dir / MANIFEST_FILE} not found: not a run directory")
        manifests.append(manifest)
    names = [str(d) for d in run_dirs]
    table = spreads(names, manifests, [read_records(d / RECORDS_FILE) for d in run_dirs])
    params = manifests[0]["parameters"]
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for provider, rows in table.items():
        model = params["models"].get(provider)
        path = output_dir / file_name(provider, model).replace("report-", "repeated-", 1)
        path.write_text(render_spread(provider, model, params.get("split"), names, rows,
                                      instruction_line(manifests[0], provider)))
        written.append(path)
    return written


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="benchmark_loop_agent.report",
                                     description="Write one Markdown report per model from a run directory.")
    parser.add_argument("run_dirs", type=Path, nargs="*", metavar="RUN_DIR",
                        help="the --output-dir of a finished run; several of one configuration give the spread of the comparison figure")
    parser.add_argument("--rates", type=Path, default=RATES_FILE, help="rates file (default: data/rates.json)")
    parser.add_argument("--output-dir", type=Path, default=None, help="where the reports go (default: the run directory)")
    parser.add_argument("--compare", type=Path, nargs=2, default=None, metavar=("DIR_A", "DIR_B"),
                        help="compare two run directories case by case, one file per provider both hold (default destination: the current directory)")
    args = parser.parse_args(argv)
    if args.compare and args.run_dirs:
        parser.error("--compare takes its two run directories itself; give no RUN_DIR")
    if not args.compare and not args.run_dirs:
        parser.error("give a RUN_DIR, or --compare DIR_A DIR_B")
    try:
        if args.compare:
            paths = build_comparison(*args.compare, args.output_dir or Path.cwd())
        elif len(args.run_dirs) == 1:
            paths = build_reports(args.run_dirs[0], args.rates, args.output_dir or args.run_dirs[0])
        elif args.output_dir is None:
            parser.error("--output-dir is required with several run directories")
        else:
            paths = build_repeated_report(args.run_dirs, args.output_dir)
    except (ValueError, OSError, KeyError) as error:
        parser.error(f"{type(error).__name__}: {error}")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
