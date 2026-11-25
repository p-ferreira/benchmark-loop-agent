"""A run of the retail benchmark: which conversations, their records, resume.

The output directory holds ``run.json`` (the parameters, the pinned upstream and the
invocations), ``records.jsonl`` (one record per task and trial) and ``conversations.jsonl``
(every attempt's full conversation, appended as it ends).
"""

import json
import os
import random
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..instructions import digest
from ..providers import Send
from ..retry import with_retries
from ..runner import PROVIDERS
from . import upstream
from .agent import counting, register_agent
from .conversation import Settings, customer_model_route, run_attempt
from .usage import recording

RECORDS_FILE = "records.jsonl"
CONVERSATIONS_FILE = "conversations.jsonl"
MANIFEST_FILE = "run.json"
INSTRUCTION_FILE = "instructions.txt"
BENCHMARK = "tau2-bench retail (text, English)"
SCORED = ("pass", "fail")
CUSTOMER_KEY_ENV = "OPENAI_API_KEY"  # the customer's default route and upstream's judges are OpenAI models


@dataclass(frozen=True)
class RunParameters:
    provider: str
    agent_model: str
    user_model: str
    task_ids: tuple[str, ...]
    trials: int = 1
    seed: int = 300  # upstream's default seed
    instruction: str | None = None
    concurrency: int = 4

    def identity(self) -> dict[str, Any]:
        """Everything that decides which conversations a directory holds and how they were run."""
        return {
            "benchmark": BENCHMARK,
            "upstream": upstream.identity(),
            "subset": {"name": upstream.SUBSET_NAME, "sha256": upstream.SUBSET_SHA256},
            "task_ids": list(self.task_ids),
            "provider": self.provider,
            "agent_model": self.agent_model,
            "user_model": self.user_model,
            "customer_reasoning": {"reasoning_effort": "low"},
            "trials": self.trials,
            "concurrency": self.concurrency,
            "seed": self.seed,
            "trial_seeds": trial_seeds(self.seed, self.trials),
            "instructions": digest(self.instruction) if self.instruction is not None else None,
        }


def trial_seeds(seed: int, trials: int) -> list[int]:
    """One seed per trial, drawn as upstream's runner draws them (same generator, same range)."""
    generator = random.Random(seed)
    return [generator.randint(0, 1000000) for _ in range(trials)]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Lines of a JSON-lines file; one cut short by an interrupted write is skipped."""
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def read_manifest(directory: Path) -> dict[str, Any] | None:
    path = directory / MANIFEST_FILE
    return json.loads(path.read_text()) if path.exists() else None


def _write_atomically(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w") as file:
        file.write(text)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary, path)


def recovered_records(directory: Path) -> tuple[dict[tuple[str, int], dict[str, Any]], bool]:
    """The records of a directory, and whether the conversations file was ahead of records.jsonl.

    conversations.jsonl is the authoritative commit: each line holds the attempt's whole record.
    An interruption between that append and the replacement of records.jsonl leaves a record that
    the conversations file is ahead of; it is restored from the file, never scheduled again.
    """
    records = {(r["task_id"], r["trial"]): r for r in read_jsonl(directory / RECORDS_FILE) if "task_id" in r and "trial" in r}
    changed = False
    for line in read_jsonl(directory / CONVERSATIONS_FILE):
        record = line.get("record")
        if not isinstance(record, dict) or "task_id" not in record or "trial" not in record:
            continue
        key = (record["task_id"], record["trial"])
        if key not in records or record.get("attempt", 0) > records[key].get("attempt", 0):
            records[key] = record
            changed = True
    return records, changed


class Store:
    """The records of a directory, one per (task, trial); thread safe."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._isolate_torn_tail()
        self.records, changed = recovered_records(directory)
        if changed:
            self._write_records()

    def _isolate_torn_tail(self) -> None:
        """A stop in the middle of an append leaves a last line without its newline.

        The next append would join it, and the joined line would be unreadable: the new entry lost.
        A whole entry that lacked only the newline gets its newline; an unreadable fragment is
        truncated, so the journal stays valid JSON lines (nothing in it was committed).
        """
        path = self.directory / CONVERSATIONS_FILE
        if path.exists() and path.stat().st_size:
            with path.open("rb+") as file:
                data = file.read()
                if data.endswith(b"\n"):
                    return
                start = data.rfind(b"\n") + 1
                try:
                    json.loads(data[start:])
                    file.write(b"\n")
                except ValueError:
                    file.truncate(start)
                file.flush()
                os.fsync(file.fileno())

    def _write_records(self) -> None:
        _write_atomically(self.directory / RECORDS_FILE, "".join(json.dumps(r) + "\n" for r in self.records.values()))

    def pending(self, task_ids: Sequence[str], trials: int) -> list[tuple[str, int]]:
        """Conversations that are missing or unscored; a scored one is never repeated."""
        return [(task, trial) for trial in range(trials) for task in task_ids
                if self.records.get((task, trial), {}).get("outcome") not in SCORED]

    def put(self, fields: dict[str, Any], conversation: dict[str, Any], task_id: str, trial: int, seed: int) -> dict[str, Any]:
        """Keep the attempt's record. The usage of an earlier unscored attempt moves into the new record."""
        with self._lock:
            previous = self.records.get((task_id, trial))
            earlier: list[dict[str, Any]] = []
            attempt = 1
            if previous is not None:
                earlier = list(previous.get("earlier_unscored_attempts", []))
                earlier.append({k: v for k, v in previous.items() if k not in ("earlier_unscored_attempts", "task_id", "trial")})
                attempt = len(earlier) + 1
            record = {"task_id": task_id, "trial": trial, "seed": seed, "attempt": attempt, **fields,
                      "earlier_unscored_attempts": earlier}
            line = json.dumps({"task_id": task_id, "trial": trial, "attempt": attempt, "outcome": fields["outcome"],
                               "reason": fields.get("reason"), **conversation, "record": record}) + "\n"
            with (self.directory / CONVERSATIONS_FILE).open("a") as file:  # the one commit: it holds the record too
                file.write(line)
                file.flush()
                os.fsync(file.fileno())
            self.records[(task_id, trial)] = record
            self._write_records()
            return record


def write_manifest(directory: Path, parameters: dict[str, Any], session: dict[str, Any], run_id: str) -> None:
    path = directory / MANIFEST_FILE
    manifest = json.loads(path.read_text()) if path.exists() else {}
    manifest.update(parameters=parameters)
    manifest.setdefault("run_id", run_id)
    sessions = manifest.setdefault("sessions", [])
    sessions[:] = [s for s in sessions if s["number"] != session["number"]] + [session]
    _write_atomically(path, json.dumps(manifest, indent=2) + "\n")


def check_environment(parameters: RunParameters, environment: Mapping[str, str]) -> None:
    """Refuse, before any request, a run that lacks a key it needs or records a key as a model id."""
    key_env = PROVIDERS[parameters.provider].key_env
    for variable in dict.fromkeys((key_env, CUSTOMER_KEY_ENV)):
        if not environment.get(variable):
            raise ValueError(f"{variable} is not set (the agent, the customer and the judges need "
                             f"{key_env} and {CUSTOMER_KEY_ENV})")
    keys = [environment.get(p.key_env) for p in PROVIDERS.values()]
    if parameters.instruction is not None and any(key and key in parameters.instruction for key in keys):
        raise ValueError("the instruction text contains a configured API key; refusing to record it")
    for model in (parameters.agent_model, parameters.user_model):
        if any(key and key in model for key in keys):
            raise ValueError("a model ID contains a configured API key; refusing to record it")


def run_retail(directory: Path, parameters: RunParameters, environment: Mapping[str, str], send: Send,
               sleep: Callable[[float], Any] = time.sleep) -> list[dict[str, Any]]:
    """Run the conversations of ``parameters`` that are missing or unscored; return every record of the run."""
    check_environment(parameters, environment)
    allowed = upstream.pinned_task_ids()  # the digest check: before the directory is touched and before any request
    unknown = [t for t in parameters.task_ids if t not in allowed]
    if unknown or len(set(parameters.task_ids)) != len(parameters.task_ids):
        raise ValueError(f"tasks outside {upstream.SUBSET_NAME} or repeated: {', '.join(unknown) or 'duplicates'}")
    identity = parameters.identity()
    previous = read_manifest(directory)
    if previous is not None and previous["parameters"] != identity:
        raise ValueError(f"{directory} holds a run with different options; use a new --output-dir or repeat the "
                         "original provider, models, tasks, trials, concurrency, seed and instruction text")
    config, tasks = upstream.prepare(list(parameters.task_ids), parameters.agent_model, customer_model_route(parameters.user_model),
                                     parameters.trials, parameters.seed)
    store = Store(directory)
    if parameters.instruction is not None:
        (directory / INSTRUCTION_FILE).write_bytes(parameters.instruction.encode("utf-8"))
    pending = store.pending(parameters.task_ids, parameters.trials)
    seeds = trial_seeds(parameters.seed, parameters.trials)
    settings = Settings(parameters.provider, parameters.agent_model, parameters.user_model, parameters.instruction)

    number = len(previous["sessions"]) + 1 if previous else 1
    run_id = (previous or {}).get("run_id") or uuid.uuid4().hex
    session: dict[str, Any] = {"number": number, "concurrency": parameters.concurrency, "started_at": now(),
                               "ended_at": None, "wall_seconds": None}
    write_manifest(directory, identity, session, run_id)
    started = time.perf_counter()
    retrying = with_retries(counting(send), sleep=sleep)  # counted beneath the retries: every dispatch is a call
    register_agent()  # once, before any worker starts

    def work(job: tuple[str, int]) -> None:
        task_id, trial = job
        attempt = run_attempt(config, tasks[task_id], seeds[trial], settings, environment, retrying)
        store.put(attempt["fields"], attempt["conversation"], task_id, trial, seeds[trial])

    pool = ThreadPoolExecutor(max_workers=max(1, parameters.concurrency))
    try:
        # The usage wrapper stays installed until the workers have stopped: on an interrupt the running
        # conversations still call the customer and the judges, and those calls must be recorded.
        with recording(upstream.load().llm_utils, upstream.load().simulation_module):
            try:
                list(pool.map(work, pending))
            finally:
                pool.shutdown(wait=True, cancel_futures=True)
    finally:
        session.update(ended_at=now(), wall_seconds=round(time.perf_counter() - started, 3))
        write_manifest(directory, identity, session, run_id)
    return [store.records[key] for key in sorted(store.records) if key[0] in parameters.task_ids and key[1] < parameters.trials]
