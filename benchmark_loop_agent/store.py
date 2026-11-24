"""The output directory: one record per case and provider, plus the run manifest.

``records.jsonl`` holds JSON Lines, one record per (provider, case), appended
and flushed as each case finishes. ``run.json`` holds the run's parameters, the
dataset and scorer revisions, and the start and end time of every invocation.
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dataset import DATASET_REVISION
from .record import Record
from .scoring import SCORER_REVISION

RECORDS_FILE = "records.jsonl"
MANIFEST_FILE = "run.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_records(path: Path) -> list[dict[str, Any]]:
    """Records in a file; a line cut short by an interrupted write is skipped."""
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and "provider" in record and "case_id" in record:
            records.append(record)
    return records


class RecordStore:
    """Append-only record file that keeps at most one record per provider and case."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.path = directory / RECORDS_FILE
        self._lock = threading.Lock()
        directory.mkdir(parents=True, exist_ok=True)

    def open_for_resume(self) -> set[tuple[str, str]]:
        """Drop ``unscored`` records (those cases run again) and return the finished keys.

        The file is rewritten so a retried case ends up with one record, not two.
        """
        kept = [r for r in read_records(self.path) if r.get("outcome") in ("pass", "fail")]
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text("".join(json.dumps(r) + "\n" for r in kept))
        os.replace(temporary, self.path)
        return {(r["provider"], r["case_id"]) for r in kept}

    def append(self, record: Record) -> None:
        """Write one record and flush it, so an interruption loses at most the cases in flight."""
        line = json.dumps(record.to_dict()) + "\n"
        with self._lock, self.path.open("a") as file:
            file.write(line)
            file.flush()
            os.fsync(file.fileno())


def write_manifest(directory: Path, parameters: dict[str, Any], session: dict[str, Any], run_id: str | None = None) -> None:
    """Create or update ``run.json``; each invocation is one numbered entry in ``sessions``."""
    path = directory / MANIFEST_FILE
    manifest: dict[str, Any] = json.loads(path.read_text()) if path.exists() else {}
    manifest.update(
        parameters=parameters, dataset_revision=DATASET_REVISION, scorer_revision=SCORER_REVISION
    )
    if run_id and "run_id" not in manifest:  # one identifier for the run, kept across resumes
        manifest["run_id"] = run_id
    sessions = manifest.setdefault("sessions", [])
    sessions[:] = [s for s in sessions if s["number"] != session["number"]] + [session]
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n")
    os.replace(temporary, path)


def migrate_legacy_concurrency(directory: Path) -> None:
    """Move a global ``concurrency`` (the earlier manifest format) into the sessions that ran with it."""
    path = directory / MANIFEST_FILE
    manifest = json.loads(path.read_text())
    legacy = manifest["parameters"].pop("concurrency", None)
    if legacy is None:
        return
    for session in manifest.get("sessions", []):
        session.setdefault("concurrency", legacy)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n")
    os.replace(temporary, path)


def read_manifest(directory: Path) -> dict[str, Any] | None:
    path = directory / MANIFEST_FILE
    return json.loads(path.read_text()) if path.exists() else None
