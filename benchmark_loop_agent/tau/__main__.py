"""Command line entry point: ``python -m benchmark_loop_agent.tau``."""

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from ..instructions import read_instruction
from ..providers import send_request
from ..runner import PROVIDERS
from . import upstream
from .batch import RunParameters, run_retail
from .report import RATES_FILE, build_report

EXIT_DONE = 0
EXIT_SOME_UNSCORED = 3  # argparse uses 2 for bad usage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="benchmark_loop_agent.tau",
        description="Run the 50 retail tasks of tau2-bench's text benchmark: an agent model called by bla, upstream's simulated "
                    "customer and tools, scored by upstream's evaluator. One record per conversation.")
    parser.add_argument("--output-dir", type=Path, help="where run.json, records.jsonl and conversations.jsonl go; "
                        "run again on the same directory to run what is missing or unscored")
    parser.add_argument("--provider", choices=sorted(PROVIDERS), help="the agent's provider")
    parser.add_argument("--openai-model", help="OpenAI model ID of the agent (default: $OPENAI_MODEL)")
    parser.add_argument("--anthropic-model", help="Anthropic model ID of the agent (default: $ANTHROPIC_MODEL)")
    parser.add_argument("--trials", type=int, default=1, help="conversations per task (default: 1)")
    parser.add_argument("--concurrency", type=int, default=4, help="conversations in flight at once (default: 4)")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--tasks", nargs="+", metavar="ID", help="run only these tasks of retail_50 (a partial run)")
    selection.add_argument("--limit", type=int, metavar="N", help="run only the first N tasks of retail_50 (a partial run)")
    parser.add_argument("--user-model", default="gpt-6-sol", help="model of upstream's simulated customer (default: gpt-6-sol)")
    parser.add_argument("--instructions", type=Path, metavar="FILE",
                        help="UTF-8 text file (1 to 8,000 bytes) appended to the policy part of the system prompt")
    parser.add_argument("--finish-check", action="store_true",
                        help="hold a reply once and ask the agent again before it hands the customer to a human, and before its "
                             "reply after a call that changed something (off by default)")
    parser.add_argument("--handover-rule", action="store_true",
                        help="do not send the model the transfer tool until the customer has asked for a person (off by default)")
    parser.add_argument("--seed", type=int, default=300, help="seed of the trial seeds, as upstream's runner (default: 300)")
    parser.add_argument("--report", type=Path, metavar="DIR", help="write the report of a finished or partial run directory and stop")
    parser.add_argument("--rates", type=Path, default=RATES_FILE, metavar="FILE",
                        help="rates file for --report (default: data/rates.json)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.report is not None:
        try:
            print(build_report(args.report, args.rates), end="")
        except (OSError, ValueError) as error:
            parser.error(str(error))
        return EXIT_DONE
    if args.output_dir is None or args.provider is None:
        parser.error("--output-dir and --provider are required")
    if args.trials < 1 or args.concurrency < 1:
        parser.error("--trials and --concurrency must be at least 1")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    environment = dict(os.environ)
    flag = args.openai_model if args.provider == "openai" else args.anthropic_model
    model = flag or environment.get(PROVIDERS[args.provider].model_env)
    if not model:
        parser.error(f"no model for {args.provider}: give --{args.provider}-model or set {PROVIDERS[args.provider].model_env}")
    try:
        instruction = read_instruction(args.instructions) if args.instructions else None
        ids = upstream.pinned_task_ids()  # the digest check, before any request
        if args.tasks is not None:
            unknown = [t for t in args.tasks if t not in ids]
            if unknown or len(set(args.tasks)) != len(args.tasks):
                parser.error(f"--tasks must be distinct tasks of {upstream.SUBSET_NAME}; not accepted: {', '.join(unknown) or 'repeats'}")
            ids = list(args.tasks)
        elif args.limit is not None:
            ids = ids[:args.limit]
        parameters = RunParameters(args.provider, model, args.user_model, tuple(ids), args.trials, args.seed, instruction, args.concurrency, args.finish_check, args.handover_rule)
        records = run_retail(args.output_dir, parameters, environment, send_request)
    except (ValueError, RuntimeError) as error:
        parser.error(str(error))
    scored = [r for r in records if r["outcome"] in ("pass", "fail")]
    passed = sum(1 for r in scored if r["outcome"] == "pass")
    print(f"{args.provider}: pass {passed}, fail {len(scored) - passed}, unscored {len(records) - len(scored)}", file=sys.stderr)
    return EXIT_SOME_UNSCORED if len(scored) < len(ids) * args.trials else EXIT_DONE


if __name__ == "__main__":
    sys.exit(main())
