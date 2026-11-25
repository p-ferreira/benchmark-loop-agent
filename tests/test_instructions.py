"""Offline tests: the instruction file option, reply_text, failure classes and the two-run comparison."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from benchmark_loop_agent import __main__ as cli
from benchmark_loop_agent import report
from benchmark_loop_agent.batch import RunParameters, run_batch
from benchmark_loop_agent.categories import CATEGORIES
from benchmark_loop_agent.compare import Run, compare_runs
from benchmark_loop_agent.dataset import load_cases, load_expected_answers
from benchmark_loop_agent.failures import failure_class
from benchmark_loop_agent.instructions import digest
from benchmark_loop_agent.providers import anthropic_request, openai_request
from benchmark_loop_agent.runner import run_provider
from benchmark_loop_agent.store import read_manifest, read_records
from tests.support import SECRET, FakeSend, anthropic_reply, case_by_id, environment, openai_reply, right_calls

TEXT = "Call every function the request needs.\nÅ ünïcode ✓"
SYSTEM_CASE = next(c for c in load_cases("live_simple") if c.messages[0]["role"] == "system")
PLAIN_CASE = case_by_id("simple_python", "simple_python_0")


def params(**changes) -> RunParameters:
    values = dict(categories=("simple_python", "irrelevance"), sample_size=3, seed=1, providers=("openai", "anthropic"),
                  models={"openai": "m", "anthropic": "m"}, concurrency=2)
    return RunParameters(**{**values, **changes})


def silent(argv):
    with contextlib.redirect_stderr(io.StringIO()) as err:
        try:
            return cli.main(argv), err.getvalue()
        except SystemExit as stop:
            return stop.code, err.getvalue()


class RequestTests(unittest.TestCase):
    def test_openai_puts_a_developer_message_first_and_keeps_the_rest(self) -> None:
        for case in (PLAIN_CASE, SYSTEM_CASE):
            plain, given = openai_request("m", case), openai_request("m", case, TEXT)
            self.assertEqual(given["input"][0], {"role": "developer", "content": TEXT})
            self.assertEqual(given["input"][1:], plain["input"])
            self.assertEqual({k: v for k, v in given.items() if k != "input"}, {k: v for k, v in plain.items() if k != "input"})

    def test_anthropic_puts_the_instruction_before_the_cases_own_system_text(self) -> None:
        own = SYSTEM_CASE.messages[0]["content"]
        body = anthropic_request("m", SYSTEM_CASE, TEXT)
        self.assertEqual(body["system"], [{"type": "text", "text": TEXT}, {"type": "text", "text": own}])
        self.assertEqual(body["messages"], anthropic_request("m", SYSTEM_CASE)["messages"])
        self.assertEqual(anthropic_request("m", PLAIN_CASE, TEXT)["system"], [{"type": "text", "text": TEXT}])

    def test_without_an_instruction_the_request_is_what_it_was(self) -> None:
        self.assertNotIn("system", anthropic_request("m", PLAIN_CASE))
        self.assertEqual(anthropic_request("m", SYSTEM_CASE)["system"], [{"type": "text", "text": SYSTEM_CASE.messages[0]["content"]}])
        self.assertEqual(openai_request("m", PLAIN_CASE)["input"], PLAIN_CASE.messages)

    def test_no_answer_reaches_a_model_input_with_an_instruction(self) -> None:
        for category in CATEGORIES:
            answers = load_expected_answers(category)
            for case in load_cases(category):
                for build in (openai_request, anthropic_request):
                    body = json.dumps(build("m", case, TEXT))
                    self.assertNotIn("ground_truth", body)
                    if case.case_id in answers:
                        self.assertNotIn(json.dumps(answers[case.case_id]), body, case.case_id)


class ReplyTextTests(unittest.TestCase):
    def run_case(self, provider, reply, case=PLAIN_CASE):
        return run_provider(provider, case, environment(provider), FakeSend(reply))

    def test_text_parts_are_joined_in_order(self) -> None:
        reply = openai_reply(right_calls(PLAIN_CASE))
        reply["output"].insert(0, {"type": "message", "content": [{"type": "output_text", "text": "a"}, {"type": "output_text", "text": "b"}]})
        self.assertEqual(self.run_case("openai", reply).reply_text, "abdone")
        reply = anthropic_reply(right_calls(PLAIN_CASE))
        reply["content"] = [{"type": "text", "text": "x"}, *reply["content"], {"type": "text", "text": "y"}]
        self.assertEqual(self.run_case("anthropic", reply).reply_text, "xy")

    def test_empty_when_none_cut_and_redacted_and_none_when_unscored(self) -> None:
        self.assertEqual(self.run_case("anthropic", anthropic_reply(right_calls(PLAIN_CASE))).reply_text, "")
        long = anthropic_reply([])
        long["content"] = [{"type": "text", "text": "z" * 5000}]
        self.assertEqual(len(self.run_case("anthropic", long).reply_text), 4000)
        key = anthropic_reply([])
        key["content"] = [{"type": "text", "text": f"my key {SECRET}"}]
        self.assertNotIn(SECRET, self.run_case("anthropic", key).reply_text)
        self.assertIsNone(self.run_case("anthropic", RuntimeError("down")).reply_text)

    def test_an_earlier_record_without_the_field_still_loads_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            run_batch(out, params(providers=("openai",)), environment("openai"), FakeSend(lambda p, r: openai_reply([])), sleep=lambda s: None)
            rows = read_records(out / "records.jsonl")
            for row in rows:
                del row["reply_text"]
            (out / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
            records = run_batch(out, params(providers=("openai",)), environment("openai"), FakeSend(lambda p, r: 1 / 0), sleep=lambda s: None)
            self.assertTrue(all(r.reply_text is None for r in records))
            self.assertTrue(report.build_reports(out, report.RATES_FILE, out))


class FailureClassTests(unittest.TestCase):
    def record(self, case, calls, reasons=("x",), category=None):
        return {"category": category or case.category, "case_id": case.case_id, "returned_calls": calls, "reasons": list(reasons)}

    def test_each_class(self) -> None:
        one = PLAIN_CASE
        many = next(c for c in load_cases("parallel") if len(load_expected_answers("parallel")[c.case_id]) == 2)
        call = {"f": {}}
        self.assertEqual(failure_class(self.record(case_by_id("irrelevance"), [call])), "called-when-none-applied")
        self.assertEqual(failure_class(self.record(case_by_id("live_irrelevance"), [{"f": "raw"}], ["arguments for f are not a JSON object"])), "called-when-none-applied")
        self.assertEqual(failure_class(self.record(one, [{"f": "[1]"}], ["arguments for f are not a JSON object"])), "malformed-call")
        self.assertEqual(failure_class(self.record(one, [{"f": []}], ["input for f is nested too deeply"])), "malformed-call")
        self.assertEqual(failure_class(self.record(one, [])), "no-call")
        self.assertEqual(failure_class(self.record(many, [call])), "too-few-calls")
        self.assertEqual(failure_class(self.record(one, [call, call])), "too-many-calls")
        self.assertEqual(failure_class(self.record(one, [call])), "wrong-call")
        self.assertEqual(failure_class(self.record(many, [call, call])), "wrong-call")

    def test_live_relevance_failures_are_malformed_or_no_call(self) -> None:
        case = case_by_id("live_relevance")
        self.assertEqual(failure_class(self.record(case, [])), "no-call")
        self.assertEqual(failure_class(self.record(case, [{"f": "raw"}], ["Invalid syntax. Failed to decode AST when it should have."])), "malformed-call")

    def test_a_deep_object_the_checker_judged_is_not_malformed(self) -> None:
        self.assertEqual(failure_class(self.record(PLAIN_CASE, [{"f": "{...}"}], ["checker said no"])), "wrong-call")

    def test_the_report_counts_each_failed_case_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            run_batch(out, params(providers=("openai",)), environment("openai"), FakeSend(lambda p, r: openai_reply([{"f": {}}])), sleep=lambda s: None)
            text = report.build_reports(out, report.RATES_FILE, out)[0].read_text()
            self.assertIn("## Failure classes", text)
            self.assertIn("| `irrelevance` | 3 | 3 | 0 | 0 | 0 | 0 | 0 |", text)
            self.assertIn("| `simple_python` | 3 | 0 | 0 | 0 | 0 | 0 | 3 |", text)
            self.assertIn("| **Overall** | 6 | 3 | 0 | 0 | 0 | 0 | 3 |", text)


class CommandLineTests(unittest.TestCase):
    def run_cli(self, tmp, *extra, providers=("openai", "anthropic")):
        seen = []

        def fake_run_batch(directory, parameters, *rest, **kw):
            seen.append(parameters)
            return []

        argv = ["--output-dir", str(Path(tmp) / "out"), "--sample-size", "1"]
        for p in providers:
            argv += ["--provider", p]
        with mock.patch.object(cli, "run_batch", fake_run_batch):
            code, err = silent([*argv, *map(str, extra)])
        return code, err, seen

    def test_default_and_per_provider_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            default, own = Path(tmp, "d.txt"), Path(tmp, "o.txt")
            default.write_text("default")
            own.write_text("own")
            code, _, seen = self.run_cli(tmp, "--instructions", default, "--openai-instructions", own)
            self.assertEqual(seen[0].instructions, {"openai": "own", "anthropic": "default"})
            code, _, seen = self.run_cli(tmp, "--anthropic-instructions", own)
            self.assertEqual(seen[0].instructions, {"anthropic": "own"})
            code, _, seen = self.run_cli(tmp)
            self.assertEqual(seen[0].instructions, {})

    def test_refusals_happen_before_any_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cases = {"empty": b"", "big": b"a" * 8001, "latin": "é".encode("latin-1")}
            for name, data in cases.items():
                path = Path(tmp, name)
                path.write_bytes(data)
                for option in ("--instructions", "--openai-instructions", "--anthropic-instructions"):
                    code, err, seen = self.run_cli(tmp, option, path)
                    self.assertEqual((code, seen), (2, []), (name, option))
                    self.assertIn(str(path), err)
            exact = Path(tmp, "exact")
            exact.write_bytes(b"a" * 8000)
            self.assertEqual(self.run_cli(tmp, "--instructions", exact)[2][0].instructions["openai"], "a" * 8000)
            code, _, seen = self.run_cli(tmp, "--instructions", Path(tmp, "missing"))
            self.assertEqual((code, seen), (2, []))


class RunDirectoryTests(unittest.TestCase):
    def go(self, out, instructions, send=None, **changes):
        send = send or FakeSend(lambda p, r: openai_reply([]) if p == "openai" else anthropic_reply([]))
        run_batch(out, params(instructions=instructions, **changes), environment("openai", "anthropic"), send, sleep=lambda s: None)
        return send

    def test_the_digest_length_and_text_are_saved_and_sent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            send = self.go(out, {"openai": TEXT})
            manifest = read_manifest(out)
            self.assertEqual(manifest["parameters"]["instructions"], {"openai": digest(TEXT)})
            self.assertEqual(digest(TEXT)["bytes"], len(TEXT.encode()))
            self.assertEqual((out / "instruction-openai.txt").read_bytes(), TEXT.encode())
            self.assertFalse((out / "instruction-anthropic.txt").exists())
            for provider, _, request in send.requests:
                if provider == "openai":
                    self.assertEqual(request["input"][0], {"role": "developer", "content": TEXT})
                else:
                    self.assertNotIn(TEXT, json.dumps(request))

    def test_resume_with_other_text_or_none_is_refused_and_the_same_text_resumes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.go(out, {"openai": TEXT})
            for other in ({"openai": TEXT + "!"}, {}, {"anthropic": TEXT}):
                with self.assertRaises(ValueError):
                    self.go(out, other)
            self.assertEqual(self.go(out, {"openai": TEXT}).requests, [])

    def test_resume_with_an_instruction_where_there_was_none_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.go(out, {})
            self.assertNotIn("instructions", read_manifest(out)["parameters"])
            with self.assertRaises(ValueError):
                self.go(out, {"openai": TEXT})
            self.assertEqual(self.go(out, {}).requests, [])

    def test_an_instruction_for_a_provider_outside_the_run_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.go(out, {"anthropic": TEXT}, providers=("openai",))
            self.assertNotIn("instructions", read_manifest(out)["parameters"])

    def test_the_report_names_the_instruction_or_says_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with_text, without = Path(tmp, "a"), Path(tmp, "b")
            self.go(with_text, {"openai": TEXT})
            self.go(without, {})
            given = report.build_reports(with_text, report.RATES_FILE, with_text)
            names = {p.name: p.read_text() for p in given}
            self.assertIn(f"* Instruction: SHA-256 `{digest(TEXT)['sha256']}`, {digest(TEXT)['bytes']} bytes", names["report-openai-m.md"])
            self.assertIn("* Instruction: none used", names["report-anthropic-m.md"])
            self.assertIn("* Instruction: none used", report.build_reports(without, report.RATES_FILE, without)[0].read_text())

    def test_repeated_runs_with_different_digests_are_different_configurations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a, b, c = (Path(tmp, n) for n in "abc")
            self.go(a, {"openai": TEXT}, providers=("openai",))
            self.go(b, {"openai": TEXT}, providers=("openai",))
            self.go(c, {"openai": "other"}, providers=("openai",))
            self.assertTrue(report.build_repeated_report([a, b], Path(tmp, "o1")))
            with self.assertRaises(ValueError) as caught:
                report.build_repeated_report([a, c], Path(tmp, "o2"))
            self.assertIn("instructions", str(caught.exception))


def reply_by(outcomes):
    """A send that answers each case by an outcome name: pass, none, wrong, two."""
    def reply(provider, request):
        prompt = json.dumps(request, ensure_ascii=False)
        for category in ("simple_python", "irrelevance"):
            for case in load_cases(category):
                if case.messages[0]["content"] in prompt:
                    kind = outcomes(case)
                    calls = {"pass": right_calls(case) if category == "simple_python" else [], "none": [],
                             "wrong": [{"f": {}}], "two": [{"f": {}}, {"f": {}}]}[kind]
                    return openai_reply(calls)
        raise AssertionError("unknown case")
    return reply


class CompareTests(unittest.TestCase):
    def make(self, tmp, name, outcomes, **changes):
        out = Path(tmp, name)
        run_batch(out, params(providers=("openai",), **changes), environment("openai"), FakeSend(reply_by(outcomes)), sleep=lambda s: None)
        return out

    def test_counts_moves_and_accounting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = self.make(tmp, "a", lambda c: "pass" if c.category == "simple_python" else "wrong")
            b = self.make(tmp, "b", lambda c: "none" if c.category == "simple_python" else "pass")
            table = compare_runs(Run(a), Run(b))["openai"]
            rows = table["rows"]
            self.assertEqual((table["only_a"], table["only_b"], table["compared"]), (0, 0, 6))
            self.assertEqual(rows["simple_python"]["only_a"], 3)
            self.assertEqual(rows["simple_python"]["moves"], {("pass", "no-call"): 3})
            self.assertEqual(rows["irrelevance"]["only_b"], 3)
            self.assertEqual(rows["irrelevance"]["moves"], {("called-when-none-applied", "pass"): 3})
            o = rows["overall"]
            self.assertEqual((o["only_a"], o["only_b"], o["paired"], o["not_paired"]), (3, 3, 6, 0))

    def test_unscored_and_missing_cases_are_counted_apart_and_never_paired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = self.make(tmp, "a", lambda c: "pass")
            b = self.make(tmp, "b", lambda c: "pass")
            rows = read_records(b / "records.jsonl")
            rows[1].update(outcome="unscored", returned_calls=None, reply_text=None)
            (b / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows[1:]))  # the first has no record
            table = compare_runs(Run(a), Run(b))["openai"]["rows"]["overall"]
            self.assertEqual((table["no_record_b"], table["unscored_b"], table["not_paired"], table["paired"]), (1, 1, 2, 4))
            self.assertEqual(table["paired"] + table["not_paired"], table["compared"])

    def test_a_run_of_one_part_compares_with_a_full_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = self.make(tmp, "a", lambda c: "pass", sample_size=None, categories=("irrelevance",), split="validation")
            b = self.make(tmp, "b", lambda c: "pass", sample_size=None, categories=("irrelevance",))
            table = compare_runs(Run(a), Run(b))["openai"]
            self.assertEqual(table["only_a"], 0)
            self.assertGreater(table["only_b"], 0)
            self.assertEqual(table["compared"], table["rows"]["overall"]["paired"])

    def test_refusals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = self.make(tmp, "a", lambda c: "pass")
            other = Path(tmp, "x")
            run_batch(other, params(providers=("anthropic",)), environment("anthropic"),
                      FakeSend(lambda p, r: anthropic_reply([])), sleep=lambda s: None)
            with self.assertRaises(ValueError):
                compare_runs(Run(a), Run(other))
            c = self.make(tmp, "c", lambda c: "pass", categories=("simple_java",))
            with self.assertRaises(ValueError):
                compare_runs(Run(a), Run(c))

    def test_the_command_writes_one_file_per_provider_naming_model_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = self.make(tmp, "a", lambda c: "pass", instructions={"openai": TEXT})
            b = self.make(tmp, "b", lambda c: "none")
            out = Path(tmp, "out")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(report.main(["--compare", str(a), str(b), "--output-dir", str(out)]), 0)
            (path,) = out.iterdir()
            text = path.read_text()
            self.assertIn(digest(TEXT)["sha256"], text)
            self.assertIn("| B |", text)
            self.assertIn("`m`", text)
            code, _ = silent_report(["--compare", str(a), str(b)])
            self.assertEqual(code, 2)


def silent_report(argv):
    with contextlib.redirect_stderr(io.StringIO()) as err:
        try:
            return report.main(argv), err.getvalue()
        except SystemExit as stop:
            return stop.code, err.getvalue()


if __name__ == "__main__":
    unittest.main()
