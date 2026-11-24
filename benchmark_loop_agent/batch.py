"""Run a chosen set of cases through the chosen providers, resuming where a run stopped."""

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .dataset import Case
from .record import Record
from .retry import with_retries
from .runner import PROVIDERS, run_provider
from .sampling import select_cases
from .providers import Send
from .tracing import API_KEY_ENV, Tracing
from .store import RecordStore, migrate_legacy_concurrency, now, read_manifest, read_records, write_manifest


@dataclass(frozen=True)
class RunParameters:
    """Everything that decides which cases run and against which models."""

    categories: tuple[str, ...]
    sample_size: int | None  # per category; None means every case
    seed: int
    providers: tuple[str, ...]
    models: dict[str, str | None]  # requested model ID per provider (no default in code)
    concurrency: int

    def identity(self) -> dict[str, Any]:
        """The parameters a resumed run must repeat (concurrency may change; each session records its own)."""
        data = asdict(self)
        del data["concurrency"]
        return data


def run_batch(
    directory: Path,
    parameters: RunParameters,
    environment: Mapping[str, str],
    send: Send,
    sleep: Callable[[float], Any] = time.sleep,
    tracing_for: Callable[[str], Tracing | None] | None = None,
) -> list[Record]:
    """Run every unfinished (case, provider) pair and return this run's records.

    Cases with a ``pass`` or ``fail`` record in ``directory`` are skipped;
    ``unscored`` ones run again. Each record is written as soon as its case
    finishes. ``send`` is wrapped in bounded retries, per request; ``sleep``
    is the backoff wait (replaceable so tests do not wait). ``tracing_for``
    receives the run identifier and returns the tracing to use, or ``None``;
    tracing never changes a record or the result.
    """
    _refuse_credentials_as_models(parameters, environment)
    previous = read_manifest(directory)
    if previous is not None:
        saved = previous["parameters"]
        if "concurrency" in saved:  # earlier format: one global setting; keep it with the sessions that used it
            migrate_legacy_concurrency(directory)
            previous = read_manifest(directory)
            saved = previous["parameters"]
        if saved != _jsonable(parameters.identity()):
            raise ValueError(
                f"{directory} holds a run with different parameters; use a new --output-dir "
                "or repeat the original categories, sample size, seed, providers and models"
            )

    cases = select_cases(parameters.categories, parameters.sample_size, parameters.seed)
    store = RecordStore(directory)
    finished = store.open_for_resume()
    pending = [(name, case) for case in cases for name in parameters.providers
               if (name, case.case_id) not in finished]

    number = len(previous["sessions"]) + 1 if previous else 1
    run_id = (previous or {}).get("run_id") or uuid.uuid4().hex
    tracing = tracing_for(run_id) if tracing_for else None
    session: dict[str, Any] = {"number": number, "concurrency": parameters.concurrency, "started_at": now(), "ended_at": None, "wall_seconds": None}
    write_manifest(directory, parameters.identity(), session, run_id)
    started = time.perf_counter()
    retrying = with_retries(send, sleep=sleep)

    def work(job: tuple[str, Case]) -> Record:
        name, case = job
        if tracing is None:
            record = run_provider(name, case, environment, retrying)
        else:
            with tracing.case(provider=name, requested_model=parameters.models.get(name), case_id=case.case_id,
                              category=case.category, invocation=number) as span:
                record = run_provider(name, case, environment, retrying)
                span.outcome(record)
        store.append(record)
        return record

    pool = ThreadPoolExecutor(max_workers=max(1, parameters.concurrency))
    try:
        new_records = list(pool.map(work, pending))
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        session.update(ended_at=now(), wall_seconds=round(time.perf_counter() - started, 3))
        write_manifest(directory, parameters.identity(), session, run_id)
        if tracing is not None:
            tracing.shutdown()
    return new_records + _kept(directory, cases, parameters.providers, {(r.provider, r.case_id) for r in new_records})


def _refuse_credentials_as_models(parameters: RunParameters, environment: Mapping[str, str]) -> None:
    """Reject a model ID that contains a configured key, before anything is written.

    The manifest records the requested model IDs verbatim, so a key mistakenly
    given as a model ID would be persisted. The error names the provider only.
    """
    keys = [environment.get(p.key_env) for p in PROVIDERS.values()] + [environment.get(API_KEY_ENV)]
    for name, model in parameters.models.items():
        if model and any(key and key in model for key in keys):
            raise ValueError(f"the {name} model ID contains a configured API key; refusing to record it")


def _kept(directory: Path, cases: Sequence[Case], providers: Sequence[str], skip: set[tuple[str, str]]) -> list[Record]:
    """Records from earlier invocations for the selected cases, as ``Record`` objects."""
    wanted = {(p, c.case_id) for c in cases for p in providers} - skip
    rows = [r for r in read_records(directory / "records.jsonl") if (r["provider"], r["case_id"]) in wanted]
    return [Record(**row) for row in rows]


def _jsonable(data: dict[str, Any]) -> dict[str, Any]:
    """Tuples become lists, as they do in the manifest file."""
    return {k: list(v) if isinstance(v, tuple) else v for k, v in data.items()}
