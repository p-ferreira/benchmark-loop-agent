"""Instruction files: text put in the system position of every request of a run."""

import hashlib
from pathlib import Path

MAX_INSTRUCTION_BYTES = 8000


def instruction_file_name(provider: str) -> str:
    """Where a run directory keeps the text its provider was given."""
    return f"instruction-{provider}.txt"


def digest(text: str) -> dict[str, str | int]:
    """The SHA-256 and byte length of the text as UTF-8, as ``run.json`` records them."""
    data = text.encode("utf-8")
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def read_instruction(path: Path) -> str:
    """The text of an instruction file; refuses an unreadable, empty, too large or non-UTF-8 file."""
    try:
        data = path.read_bytes()
    except OSError as error:
        raise ValueError(f"cannot read the instruction file {path}: {error.strerror or type(error).__name__}") from None
    if not data:
        raise ValueError(f"the instruction file {path} is empty")
    if len(data) > MAX_INSTRUCTION_BYTES:
        raise ValueError(f"the instruction file {path} is {len(data)} bytes; the limit is {MAX_INSTRUCTION_BYTES}")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"the instruction file {path} is not valid UTF-8") from None
