"""Learn instruction lines from the failures of a development run: ``python -m benchmark_loop_agent.learn``.

A model (the writer) is shown the failed cases of a development run, with the failure class of each, and writes
short general rules. The rules are appended, one line each, to a copy of an instruction file. The writer is never
sent an expected answer: the request is built from the run's records and the question files only, and the code that
reads the expected answers (to refuse a rule that quotes one) runs after the writer has replied.

Exit codes: 0 done, 2 refused (bad usage or inputs, before any request), 3 a writer request failed.
"""

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import stat
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .dataset import Case, load_cases, load_expected_answers
from .failures import UnknownCase, failure_class
from .instructions import MAX_INSTRUCTION_BYTES, read_instruction
from .providers import ANTHROPIC_MAX_TOKENS, ProviderError, Send, anthropic_request, openai_request, send_request
from .retry import with_retries
from .runner import PROVIDERS, redact
from .split import part_case_ids
from .store import MANIFEST_FILE, RECORDS_FILE, read_manifest, read_records

EXIT_DONE = 0
EXIT_REFUSED = 2
EXIT_WRITER_FAILED = 3

MAX_RULE_CHARACTERS = 300
MIN_EXPECTED_STRING = 4  # an expected string value this long, found in a rule, refuses the rule
REQUEST_FILE = Path(__file__).with_name("learn_request.txt")
WRITER_PROVIDERS = ("openai", "anthropic")

KEPT = "kept"
REASONS = ("expected-value", "contains-key", "invalid-text", "not-single-line", "too-long", "duplicate",
           "over-max-bytes", "over-runner-limit")
SECRET_REASONS = ("expected-value", "contains-key")  # logged as a digest and a length, never as text


class Refused(Exception):
    """The command's inputs are refused; nothing was sent."""


class WriterFailed(Exception):
    """A writer request failed after the usual retries."""


def sha256(data: str | bytes) -> str:
    return hashlib.sha256(data.encode("utf-8", "surrogatepass") if isinstance(data, str) else data).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def request_template() -> str:
    return REQUEST_FILE.read_text(encoding="utf-8")


def fixed_request(lines_per_batch: int) -> str:
    return request_template().replace("{lines_per_batch}", str(lines_per_batch)).replace(
        "{max_characters}", str(MAX_RULE_CHARACTERS)).rstrip("\n")


# ---------------------------------------------------------------- what the writer is sent

def case_block(case: Case, record: Mapping[str, Any], provider: str, model: str, failure: str) -> dict[str, Any]:
    """What one failed case contributes to a request. No identifier, no category, no expected answer, no reasons.

    The functions are the ones the runner sent to the provider (its own request builder is used for them).
    """
    build = openai_request if provider == "openai" else anthropic_request
    block: dict[str, Any] = {
        "messages": case.messages,
        "functions": build(model, case).get("tools", []),
        "returned_calls": record.get("returned_calls"),
    }
    if record.get("reply_text") is not None:  # an older run has no reply text: the field is absent, not empty
        block["reply_text"] = record["reply_text"]
    block["failure_class"] = failure
    return block


def writer_prompt(lines_per_batch: int, current_text: str, blocks: Sequence[dict[str, Any]]) -> str:
    parts = [fixed_request(lines_per_batch), "Current instruction file:\n<<<\n" + current_text + "\n>>>"]
    parts.append("Failed cases:")
    parts += [f"Case {number}:\n" + json.dumps(block, ensure_ascii=False, indent=1) for number, block in enumerate(blocks, 1)]
    return "\n\n".join(parts)


def writer_request(provider: str, model: str, prompt: str) -> dict[str, Any]:
    if provider == "openai":
        return {"model": model, "input": [{"role": "user", "content": prompt}], "store": False}
    return {"model": model, "max_tokens": ANTHROPIC_MAX_TOKENS, "messages": [{"role": "user", "content": prompt}]}


def read_writer_reply(provider: str, reply: Mapping[str, Any]) -> tuple[str, str | None, int | None, int | None]:
    """The text, reported model and token counts of a writer reply."""
    try:
        usage = reply.get("usage") or {}
        if provider == "openai":
            texts = [part["text"] for item in reply["output"] if item["type"] == "message"
                     for part in item.get("content") or []
                     if isinstance(part, dict) and part.get("type") == "output_text" and isinstance(part.get("text"), str)]
        else:
            texts = [block["text"] for block in reply["content"]
                     if block["type"] == "text" and isinstance(block.get("text"), str)]
        return "".join(texts), reply.get("model"), usage.get("input_tokens"), usage.get("output_tokens")
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise ProviderError(f"unexpected writer response shape: {type(error).__name__}: {error}") from None


def parse_rules(text: str) -> list[Any] | None:
    """The rules in a writer reply (a JSON array, possibly in a code fence), or None when it is not one."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text[:text.rfind("```")] if "```" in text else text
    try:
        value = json.loads(text)
    except (ValueError, RecursionError):
        return None
    return value if isinstance(value, list) else None


# ---------------------------------------------------------------- what is kept

def expected_strings(cases: Sequence[Case]) -> set[str]:
    """Every expected string value in these cases (any length). Read only after the writer replied."""
    found: set[str] = set()
    stack: list[Any] = []
    for case in cases:
        stack.append(load_expected_answers(case.category).get(case.case_id, []))
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            if item:
                found.add(item)
        elif isinstance(item, list):
            stack.extend(item)
        elif isinstance(item, dict):
            stack.extend(item.values())
    return found


def judge_rule(rule: Any, text: str, *, max_bytes: int, batch_values: set[str], secrets: Sequence[str]) -> str | None:
    """The reason a rule is refused, or None, against the file as it stands (requirement 5)."""
    shown = rule if isinstance(rule, str) else canonical(rule)
    if any(len(value) >= MIN_EXPECTED_STRING and value in shown for value in batch_values):
        return "expected-value"
    if any(secret in shown for secret in secrets):
        return "contains-key"
    if not isinstance(rule, str):
        return "not-single-line"
    try:
        grow = len(rule.encode("utf-8")) + 1 + (0 if not text or text.endswith("\n") else 1)
    except UnicodeEncodeError:
        return "invalid-text"
    if rule.splitlines() != [rule] or not rule.strip():  # any line break, also a trailing or Unicode one
        return "not-single-line"
    if len(rule) > MAX_RULE_CHARACTERS:
        return "too-long"
    if rule in text.splitlines():
        return "duplicate"
    size = len(text.encode("utf-8")) + grow
    if size > max_bytes:
        return "over-max-bytes"
    if size > MAX_INSTRUCTION_BYTES:
        return "over-runner-limit"
    return None


def holds_expected(shown: str, run_values: set[str]) -> bool:
    """Whether a text holds an expected value of the run (two characters or more), so the log must not hold it."""
    return any(len(value) >= 2 and value in shown for value in run_values)


def append_rule(text: str, rule: str) -> str:
    return text + ("" if not text or text.endswith("\n") else "\n") + rule + "\n"


# ---------------------------------------------------------------- inputs

def load_failures(run_dir: Path) -> tuple[str, list[tuple[Case, dict[str, Any], str]]]:
    """The run's provider and its failed cases (case, record, failure class) in case-identifier order.

    Refuses anything but a development run of one provider, before any request.
    """
    try:
        manifest = read_manifest(run_dir) if (run_dir / MANIFEST_FILE).is_file() else None
        records = read_records(run_dir / RECORDS_FILE)
    except (OSError, ValueError):
        raise Refused(f"{run_dir} holds a {MANIFEST_FILE} or records file that cannot be read") from None
    if not isinstance(manifest, dict):
        raise Refused(f"{run_dir} holds no usable {MANIFEST_FILE}")
    parameters = manifest.get("parameters")
    if not isinstance(parameters, dict):
        raise Refused(f"{run_dir} holds a {MANIFEST_FILE} without parameters")
    if parameters.get("split") != "development":
        raise Refused(f"{run_dir} is not a development run (its split is {parameters.get('split')!r}); "
                      "only a run made with --split development can be learned from")
    providers = parameters.get("providers")
    if not isinstance(providers, list) or len(providers) != 1 or providers[0] not in PROVIDERS:
        raise Refused(f"{run_dir} must hold the run of exactly one provider; it records {providers!r}")
    provider = providers[0]
    development = part_case_ids("development")
    cases: dict[tuple[str, str], Case] = {}
    for record in records:
        if record["provider"] != provider:
            raise Refused(f"{run_dir} holds a record of provider {record['provider']!r}, not {provider!r}")
        if record["case_id"] not in development:
            raise Refused(f"{run_dir} holds a record whose case is not in the development part of the split")
    failed = sorted((r for r in records if r.get("outcome") == "fail"), key=lambda r: r["case_id"])
    result = []
    for record in failed:
        key = (record.get("category"), record["case_id"])
        if key not in cases:
            try:
                cases.update({(c.category, c.case_id): c for c in load_cases(key[0])})
            except ValueError:
                raise Refused(f"a record names an unknown category") from None
        if key not in cases:
            raise Refused("a record names a case that is not in the question files")
        try:
            result.append((cases[key], record, failure_class(record)))
        except UnknownCase:
            raise Refused("the failure class of a record cannot be found: its expected answer is missing") from None
    return provider, result


def identity_of(args: argparse.Namespace, file_bytes: bytes, run_dir: Path, provider: str,
                failures: Sequence[tuple[Case, dict[str, Any], str]]) -> dict[str, Any]:
    """Everything a logged batch depends on: the run, the file, the options, and the content of the cases.

    The cases enter as digests of what the request is built from (messages, functions) and of the expected answers
    the rules are filtered against, so a changed question or answer file is another input.
    """
    run_data = b"".join((run_dir / name).read_bytes() if (run_dir / name).is_file() else b"" for name in (MANIFEST_FILE, RECORDS_FILE))
    content = [[case.case_id, case_block(case, record, provider, "", failure),
                load_expected_answers(case.category).get(case.case_id)] for case, record, failure in failures]
    return {
        "run_sha256": sha256(run_data), "instructions_sha256": sha256(file_bytes), "cases_sha256": sha256(canonical(content)),
        "writer_provider": args.writer_provider, "writer_model": args.writer_model,
        "max_bytes": args.max_bytes, "batch_size": args.batch_size, "lines_per_batch": args.lines_per_batch,
        "request_text_sha256": sha256(fixed_request(args.lines_per_batch)),
    }


# ---------------------------------------------------------------- log

class Log:
    """The log file, owned exclusively for the run (a lock) and only ever appended to.

    The only thing ever cut off is a last line left unfinished by an interruption.
    """

    def __init__(self, path: Path, *, create: bool) -> None:
        self.path = path
        flags = os.O_RDWR | os.O_APPEND | (os.O_CREAT | os.O_EXCL if create else 0)
        try:
            self.fd = os.open(path, flags, 0o644)
        except FileExistsError:
            raise Refused(f"{path} was created by another run; use new files") from None
        except OSError as error:
            raise Refused(f"cannot open the log {path}: {error.strerror}") from None
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self.fd)
            raise Refused(f"{path} is in use by another run") from None

    def close(self) -> None:
        os.close(self.fd)

    def read(self, header_line: bytes, *, fresh: bool) -> tuple[dict[str, Any] | None, list[dict[str, Any]], bool, int]:
        """(header, batch entries, finished by totals, length of the complete lines). Anything unreadable is refused.

        ``header_line`` is the header this run would write. A log this run just created (``fresh``) must be empty.
        Any other log is accepted only if its first line is complete, ends with a newline and is exactly that line.
        """
        size = os.fstat(self.fd).st_size
        data = b""
        while len(data) < size:
            chunk = os.pread(self.fd, size - len(data), len(data))
            if not chunk:
                break
            data += chunk
        complete = data[:data.rfind(b"\n") + 1]  # a last line without its newline was cut short
        tail = data[len(complete):]
        if fresh:
            if data:
                raise Refused(f"{self.path} was created by another run; use new files")
            return None, [], False, 0
        if not data.startswith(header_line):
            raise Refused(f"the log {self.path} is not a log of this command for these inputs and options; use new files")
        if tail and not any(tail.startswith(mark) or mark.startswith(tail) for mark in (b'{"header": ', b'{"batch": ', b'{"totals": ')):
            raise Refused(f"the log {self.path} is not a log of this command")
        header, batches, finished = None, [], False
        for number, line in enumerate(complete.splitlines()):
            try:
                entry = json.loads(line)
            except ValueError:
                raise Refused(f"the log {self.path} is not valid JSON Lines") from None
            if not isinstance(entry, dict) or finished:
                raise Refused(f"the log {self.path} is not a log of this command")
            if number == 0:
                if not isinstance(entry.get("header"), dict):
                    raise Refused(f"the log {self.path} is not a log of this command")
                header = entry["header"]
            elif "totals" in entry:
                finished = True
            elif "batch" in entry and isinstance(entry.get("rules"), list):
                batches.append(entry)
            else:
                raise Refused(f"the log {self.path} is not a log of this command")
        return header, batches, finished, len(complete)

    def cut(self, length: int) -> None:
        if os.fstat(self.fd).st_size != length:
            os.ftruncate(self.fd, length)
            os.fsync(self.fd)

    def append(self, entry: Mapping[str, Any]) -> None:
        data = memoryview((json.dumps(entry, ensure_ascii=True) + "\n").encode("ascii"))
        while data:  # a short write is finished before anything else is done
            data = data[os.write(self.fd, data):]
        os.fsync(self.fd)


def write_output(path: Path, text: str) -> None:
    """Replace OUT atomically through a new, exclusively created temporary file in its directory."""
    try:
        mode = stat.S_IMODE(path.stat().st_mode)  # an existing file keeps its permissions
    except OSError:
        mask = os.umask(0)
        os.umask(mask)
        mode = 0o666 & ~mask
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(text.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(name)
        raise


# ---------------------------------------------------------------- the loop

def run_learning(args: argparse.Namespace, environment: Mapping[str, str], send: Send) -> int:
    """Run the command; raises ``Refused`` or ``WriterFailed``. Every refusal happens before anything is written."""
    provider, failures = load_failures(args.run_dir)
    try:
        file_bytes = args.instructions.read_bytes()
        original = read_instruction(args.instructions)
    except OSError as error:
        raise Refused(f"cannot read the instruction file {args.instructions}: {error.strerror}") from None
    except ValueError as error:
        raise Refused(str(error)) from None
    paths = [p.resolve() for p in (args.instructions, args.output, args.log)]
    if len(set(paths)) != 3:
        raise Refused("--output, --log and --instructions must be three different files")
    key_name = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}[args.writer_provider]
    api_key = environment.get(key_name)
    if not api_key:
        raise Refused(f"{key_name} is not set")
    secrets = [value for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") if (value := environment.get(name))]
    if any(secret in args.writer_model for secret in secrets):
        raise Refused("--writer-model contains an API key; it would be written to the log")
    if any(secret in original for secret in secrets):
        raise Refused(f"{args.instructions} contains an API key; it would be copied and sent to the writer")
    identity = identity_of(args, file_bytes, args.run_dir, provider, failures)
    batches = [failures[start:start + args.batch_size] for start in range(0, len(failures), args.batch_size)]

    if args.output.exists() and not args.output.is_file() or args.log.exists() and not args.log.is_file():
        raise Refused("--output and --log must be regular files")
    if args.output.exists() and not args.log.exists():
        raise Refused(f"{args.output} exists without a log; use new files")
    if not args.log.exists():
        for parent in {args.output.parent, args.log.parent}:
            parent.mkdir(parents=True, exist_ok=True)
    fresh = not args.log.exists()
    if not fresh and not args.output.exists():
        raise Refused(f"{args.log} exists without {args.output}; use new files")
    log = Log(args.log, create=fresh)
    try:
        return run_locked(args, log, fresh, send, provider, batches, identity, file_bytes, original, api_key, secrets)
    finally:
        log.close()


def kept_text(rule: dict[str, Any], lines: dict[str, str], where: Path) -> str:
    """The text of a kept rule: in the log, or, when the log withholds it, the line of OUT with that digest."""
    if isinstance(rule.get("text"), str):
        return rule["text"]
    line = lines.get(rule.get("sha256")) if isinstance(rule.get("sha256"), str) else None
    if line is None:
        raise Refused(f"{where} holds a kept rule whose text it withholds and the output does not hold; use new files")
    return line


def run_locked(args: argparse.Namespace, log: Log, fresh: bool, send: Send, provider: str,
               batches: list[list[tuple[Case, dict[str, Any], str]]], identity: dict[str, Any],
               file_bytes: bytes, original: str, api_key: str, secrets: Sequence[str]) -> int:
    header, logged, finished, length = log.read((json.dumps({"header": identity}, ensure_ascii=True) + "\n").encode("ascii"),
                                                fresh=fresh)
    # The log must belong to this exact run, and the output must be one of the two versions it can have after
    # an interruption: all logged batches applied, or all but the last.
    if header is not None and header != identity:
        raise Refused(f"{args.log} was written with other inputs or options; use new files")
    current = None
    if args.output.exists():
        try:
            current = args.output.read_bytes().decode("utf-8")
        except (OSError, ValueError):
            raise Refused(f"{args.output} cannot be read as text; use new files") from None
    lines = {sha256(line): line for line in (current or "").splitlines()}
    versions = [original]
    for number, entry in enumerate(logged):
        if entry.get("batch") != number or number >= len(batches) or \
                entry.get("case_sha256") != [sha256(c.case_id) for c, _, _ in batches[number]]:
            raise Refused(f"{args.log} does not match the batches of this run; use new files")
        text = versions[-1]
        for rule in entry["rules"]:
            if isinstance(rule, dict) and rule.get("kept"):
                text = append_rule(text, kept_text(rule, lines, args.log))
        versions.append(text)
    text = versions[-1]
    allowed = [versions[-1]] if finished else versions[-2:]
    if current is not None and current not in allowed:
        raise Refused(f"{args.output} is not what the log says it should hold; use new files")
    if current is None and logged:
        raise Refused(f"{args.output} is missing but the log holds finished batches; use new files")

    log.cut(length)  # first write: drops a last line cut short by an interruption
    if header is None:
        log.append({"header": identity})  # before the first request, so the inputs are on record from the start
    if current != text:
        write_output(args.output, text)
    if finished:
        return EXIT_DONE

    retrying = with_retries(send)
    run_values = set()
    for number in range(len(logged), len(batches)):
        if not run_values:
            run_values = expected_strings([case for batch in batches for case, _, _ in batch])
        entry, text = learn_batch(number, batches[number], text, provider, args, api_key, secrets, retrying, run_values)
        log.append(entry)  # the log first: a rule in the output is always in the log
        write_output(args.output, text)
        logged.append(entry)
    log.append(totals_entry(logged, file_bytes, text))
    return EXIT_DONE


def learn_batch(number: int, batch: Sequence[tuple[Case, dict[str, Any], str]], text: str, provider: str,
                args: argparse.Namespace, api_key: str, secrets: Sequence[str], send: Send,
                run_values: set[str]) -> tuple[dict[str, Any], str]:
    cases = [case for case, _, _ in batch]
    run_model = ""  # the functions are sent as the run sent them; the model name is not part of them
    blocks = [case_block(case, record, provider, run_model, failure) for case, record, failure in batch]
    request = writer_request(args.writer_provider, args.writer_model, writer_prompt(args.lines_per_batch, text, blocks))
    try:
        reply = send(args.writer_provider, api_key, request)
        reply_text, reported, input_tokens, output_tokens = read_writer_reply(args.writer_provider, reply)
    except Exception as error:  # a failed request stops the command, whatever the library raised
        raise WriterFailed(f"{type(error).__name__}: {redact(str(error), secrets)}"[:500]) from None
    reported_provider = reply.get("provider") if isinstance(reply.get("provider"), str) else None
    returned = parse_rules(reply_text)
    batch_values = expected_strings(cases)  # first read of the expected answers, after the writer has replied
    rules = []
    for rule in returned or []:
        reason = judge_rule(rule, text, max_bytes=args.max_bytes, batch_values=batch_values, secrets=secrets)
        shown = rule if isinstance(rule, str) else canonical(rule)
        if reason in SECRET_REASONS:
            rules.append({"sha256": sha256(shown), "length": len(shown), "kept": False, "refused": reason})
            continue
        if holds_expected(shown, run_values):  # not retention: the log never holds such a text, kept or not
            rules.append({"sha256": sha256(shown), "length": len(shown), "kept": reason is None, "refused": reason,
                          "text_withheld": True})
        else:
            rules.append({"text": shown, "kept": reason is None, "refused": reason})
        if reason is None:
            text = append_rule(text, rule)
    entry = {
        "batch": number,
        "case_sha256": [sha256(case.case_id) for case in cases],
        "writer": {"provider_requested": args.writer_provider, "provider_reported": reported_provider,  # null: not reported
                   "model_requested": args.writer_model, "model_reported": reported},
        "request_sha256": sha256(canonical(request)),
        "reply_was_a_json_array": returned is not None,
        "rules": rules,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    return redact(entry, secrets), text


def totals_entry(entries: Sequence[dict[str, Any]], file_bytes: bytes, text: str) -> dict[str, Any]:
    rules = [rule for entry in entries for rule in entry["rules"]]
    output = text.encode("utf-8")
    return {"totals": {
        "batches": len(entries),
        "rules_returned": len(rules),
        "kept": sum(1 for rule in rules if rule["kept"]),
        "refused": dict(Counter(rule["refused"] for rule in rules if rule["refused"])),
        "input_tokens": sum(e["input_tokens"] or 0 for e in entries),
        "output_tokens": sum(e["output_tokens"] or 0 for e in entries),
        "instructions": {"sha256": sha256(file_bytes), "bytes": len(file_bytes)},
        "output": {"sha256": sha256(output), "bytes": len(output)},
    }}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="benchmark_loop_agent.learn",
        description="Append general rules, written by a model from the failed cases of a development run, to a copy of an instruction file. "
                    "The writer is never sent an expected answer.")
    parser.add_argument("--run-dir", type=Path, required=True, metavar="DIR", help="a development run of one provider")
    parser.add_argument("--instructions", type=Path, required=True, metavar="FILE", help="the instruction file to start from")
    parser.add_argument("--output", type=Path, required=True, metavar="OUT", help="the learned file (a copy of FILE plus rules)")
    parser.add_argument("--writer-provider", choices=WRITER_PROVIDERS, required=True)
    parser.add_argument("--writer-model", required=True, metavar="ID")
    parser.add_argument("--max-bytes", type=int, default=4000, metavar="N", help="largest size of OUT in bytes (default: 4000)")
    parser.add_argument("--batch-size", type=int, default=20, metavar="N", help="failed cases per request (default: 20)")
    parser.add_argument("--lines-per-batch", type=int, default=3, metavar="N", help="most rules asked for per request (default: 3)")
    parser.add_argument("--log", type=Path, default=None, metavar="FILE", help="default: OUT with .log.jsonl appended")
    return parser


def main(argv: Sequence[str] | None = None, *, send: Send = send_request,
         environment: Mapping[str, str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    for name in ("max_bytes", "batch_size", "lines_per_batch"):
        if getattr(args, name) < 1:
            parser.error(f"--{name.replace('_', '-')} must be at least 1")
    if args.log is None:
        args.log = args.output.with_name(args.output.name + ".log.jsonl")
    try:
        return run_learning(args, os.environ if environment is None else environment, send)
    except Refused as error:
        print(f"refused: {error}", file=sys.stderr)
        return EXIT_REFUSED
    except WriterFailed as error:
        print(f"the writer request failed: {error}", file=sys.stderr)
        return EXIT_WRITER_FAILED


if __name__ == "__main__":
    sys.exit(main())
