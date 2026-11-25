"""Command line entry point: ``python -m benchmark_loop_agent``."""

import argparse
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

from .batch import RunParameters, run_batch
from .categories import CATEGORIES
from .instructions import read_instruction
from .providers import send_request
from .record import Record
from .runner import PROVIDERS
from .split import PARTS
from .tracing import configure

EXIT_ALL_PASSED = 0
EXIT_SOME_FAILED = 1  # argparse uses 2 for bad usage, so 2 is skipped
EXIT_SOME_UNSCORED = 3


def exit_code(records: Sequence[Record]) -> int:
    """Unscored outranks fail: an unjudged case means the run is incomplete."""
    outcomes = {record.outcome for record in records}
    if "unscored" in outcomes:
        return EXIT_SOME_UNSCORED
    if "fail" in outcomes:
        return EXIT_SOME_FAILED
    return EXIT_ALL_PASSED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="benchmark_loop_agent",
        description="Run single-turn BFCL cases through OpenAI and Anthropic and write one record per case and provider.",
    )
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="where records.jsonl and run.json go; rerun on the same directory to resume")
    parser.add_argument("--categories", nargs="+", choices=CATEGORIES, default=list(CATEGORIES), metavar="CATEGORY",
                        help="BFCL categories to run (default: all thirteen)")
    parser.add_argument("--sample-size", type=int, default=None, metavar="N",
                        help="cases per category, chosen with --seed (default: every case)")
    parser.add_argument("--seed", type=int, default=0, help="seed for --sample-size (default: 0)")
    parser.add_argument("--split", choices=PARTS, default=None, metavar="PART",
                        help="run only the cases of one part of data/split.json: " + ", ".join(PARTS) + " (default: every case)")
    parser.add_argument("--provider", action="append", choices=sorted(PROVIDERS),
                        help="provider to run; repeat for several (default: all)")
    parser.add_argument("--openai-model", help="OpenAI model ID (default: $OPENAI_MODEL)")
    parser.add_argument("--anthropic-model", help="Anthropic model ID (default: $ANTHROPIC_MODEL)")
    parser.add_argument("--instructions", type=Path, default=None, metavar="FILE",
                        help="UTF-8 text file (1 to 8,000 bytes) sent first in every request, for each provider without its own file")
    parser.add_argument("--openai-instructions", type=Path, default=None, metavar="FILE",
                        help="instruction file for OpenAI only (developer message); overrides --instructions")
    parser.add_argument("--anthropic-instructions", type=Path, default=None, metavar="FILE",
                        help="instruction file for Anthropic only (system field); overrides --instructions")
    parser.add_argument("--concurrency", type=int, default=4, help="requests in flight at once (default: 4)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.concurrency < 1:
        parser.error("--concurrency must be at least 1")
    if args.sample_size is not None and args.sample_size < 0:
        parser.error("--sample-size must not be negative")

    # Every file is checked before any request, even one for a provider this run leaves out.
    try:
        files = {"default": args.instructions, "openai": args.openai_instructions, "anthropic": args.anthropic_instructions}
        texts = {key: read_instruction(path) for key, path in files.items() if path is not None}
    except ValueError as error:
        parser.error(str(error))

    environment = dict(os.environ)
    for flag, variable in ((args.openai_model, "OPENAI_MODEL"), (args.anthropic_model, "ANTHROPIC_MODEL")):
        if flag:
            environment[variable] = flag
    names = tuple(dict.fromkeys(args.provider or sorted(PROVIDERS)))
    parameters = RunParameters(
        categories=tuple(dict.fromkeys(args.categories)),
        sample_size=args.sample_size,
        seed=args.seed,
        providers=names,
        models={n: environment.get(PROVIDERS[n].model_env) or None for n in names},
        concurrency=args.concurrency,
        split=args.split,
        instructions={n: texts[key] for n in names if (key := n if n in texts else "default") in texts},
    )
    try:
        records = run_batch(args.output_dir, parameters, environment, send_request,
                            tracing_for=lambda run_id: configure(environment, run_id))
    except ValueError as error:
        parser.error(str(error))

    counts = Counter((r.provider, r.outcome) for r in records)
    for name in names:
        summary = ", ".join(f"{outcome} {counts[(name, outcome)]}" for outcome in ("pass", "fail", "unscored"))
        print(f"{name}: {summary}", file=sys.stderr)
    return exit_code(records)


if __name__ == "__main__":
    sys.exit(main())
