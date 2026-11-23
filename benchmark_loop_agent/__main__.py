"""Command line entry point: ``python -m benchmark_loop_agent``."""

import argparse
import json
import os
import sys
from typing import Sequence

from .case import load_case
from .providers import send_request
from .record import Record
from .runner import PROVIDERS, run_providers

EXIT_ALL_PASSED = 0
EXIT_SOME_FAILED = 1  # argparse uses 2 for bad usage, so 2 is skipped
EXIT_SOME_UNSCORED = 3


def exit_code(records: Sequence[Record]) -> int:
    """Unscored outranks fail: an unjudged provider means the run is incomplete."""
    outcomes = {record.outcome for record in records}
    if "unscored" in outcomes:
        return EXIT_SOME_UNSCORED
    if "fail" in outcomes:
        return EXIT_SOME_FAILED
    return EXIT_ALL_PASSED


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="benchmark_loop_agent",
        description="Run the pinned BFCL case and print one JSON record per provider.",
    )
    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDERS),
        help="run only this provider (default: all)",
    )
    args = parser.parse_args(argv)

    names = [args.provider] if args.provider else list(PROVIDERS)
    records = run_providers(names, load_case(), os.environ, send_request)
    for record in records:
        print(json.dumps(record.to_dict()))  # one record per line (JSON Lines)
        print(f"{record.provider}: {record.outcome}", file=sys.stderr)
    return exit_code(records)


if __name__ == "__main__":
    sys.exit(main())
