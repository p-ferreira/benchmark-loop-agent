"""Offline tests of the learning command: what the writer is sent, what is kept, the log, resuming and the refusals."""

import contextlib
import hashlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from benchmark_loop_agent import dataset, learn
from benchmark_loop_agent.dataset import DATA_DIR, load_cases
from benchmark_loop_agent.split import part_case_ids
from tests.support import SECRET, FakeSend

WRITER_KEY = "sk-writer-KEY-456"
ENV = {"OPENAI_API_KEY": WRITER_KEY, "ANTHROPIC_API_KEY": "sk-ant-KEY-789"}
START = "Answer in the language of the request.\nCall a function only when one applies.\n"
REASON_MARKER = "REASONMARKERzq9"


def writer_reply(rules, provider="openai"):
    text = rules if isinstance(rules, str) else json.dumps(rules)
    usage = {"input_tokens": 11, "output_tokens": 5}
    if provider == "openai":
        return {"model": "writer-actual", "output": [{"type": "reasoning"}, {"type": "message", "content": [{"type": "output_text", "text": text}]}], "usage": usage}
    return {"model": "writer-actual", "content": [{"type": "text", "text": text}], "usage": usage}


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class LearnTest(unittest.TestCase):
    N = 5  # failed cases

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        # A data directory whose answer files hold markers that appear nowhere else.
        data = self.tmp / "data"
        (data / "answers").mkdir(parents=True)
        (data / "questions").symlink_to(DATA_DIR / "questions")
        development = part_case_ids("development")
        self.cases = sorted((c for c in load_cases("simple_python") if c.case_id in development), key=lambda c: c.case_id)[:self.N + 2]
        self.markers = {}
        rows = [json.loads(line) for line in (DATA_DIR / "answers" / "BFCL_v4_simple_python.json").read_text().splitlines() if line.strip()]
        for row in rows:
            if row["id"] in {c.case_id for c in self.cases}:
                (name, options), = row["ground_truth"][0].items()
                parameter = next(iter(options))
                marker = f"MARKER{len(self.markers)}x{row['id'].replace('_', '')}Q"
                options[parameter] = [marker] + options[parameter]
                self.markers[row["id"]] = marker
        (data / "answers" / "BFCL_v4_simple_python.json").write_text("".join(json.dumps(r) + "\n" for r in rows))
        patcher = mock.patch.object(dataset, "DATA_DIR", data)
        patcher.start()
        self.addCleanup(patcher.stop)
        dataset.load_expected_answers.cache_clear()
        self.addCleanup(dataset.load_expected_answers.cache_clear)
        self.failed = self.cases[:self.N]
        self.run_dir = self.make_run(self.failed + self.cases[self.N:], failed=len(self.failed))
        self.instructions = self.tmp / "start.txt"
        self.instructions.write_text(START)
        self.out = self.tmp / "out" / "learned.txt"

    def make_run(self, cases, *, failed, providers=("openai",), split="development", name="run", reply_text=True):
        directory = self.tmp / name
        directory.mkdir()
        (directory / "run.json").write_text(json.dumps({"parameters": {"providers": list(providers), "split": split}}))
        lines = []
        for index, case in enumerate(cases):
            record = {"provider": providers[0], "case_id": case.case_id, "category": case.category,
                      "outcome": "fail" if index < failed else "pass", "returned_calls": [{"some_fn": {"x": 1}}],
                      "reasons": [f"expected {REASON_MARKER}"] if index < failed else []}
            if reply_text:
                record["reply_text"] = f"reply {index}"
            lines.append(json.dumps(record))
        (directory / "records.jsonl").write_text("\n".join(lines) + "\n")
        return directory

    def argv(self, **changes):
        values = {"--run-dir": self.run_dir, "--instructions": self.instructions, "--output": self.out,
                  "--writer-provider": "openai", "--writer-model": "writer-model", "--batch-size": 2}
        values.update({f"--{k.replace('_', '-')}": v for k, v in changes.items()})
        return [str(x) for pair in values.items() for x in pair]

    def run_cli(self, replies, send=None, argv=None, env=None):
        send = send or FakeSend(replies if callable(replies) else (lambda provider, request: writer_reply(replies, provider)))
        with contextlib.redirect_stderr(io.StringIO()) as err, mock.patch("benchmark_loop_agent.retry.time.sleep"):
            code = learn.main(argv or self.argv(), send=send, environment=ENV if env is None else env)
        return code, send, err.getvalue()

    def log_lines(self):
        return [json.loads(line) for line in Path(str(self.out) + ".log.jsonl").read_text().splitlines()]

    def log(self):
        return self.log_lines()[1:]  # after the header line

    def header(self):
        return self.log_lines()[0]["header"]


class RequestContentTests(LearnTest):
    def assert_nothing_secret(self, send):
        every = json.dumps(send.requests)
        for case in self.cases:
            self.assertNotIn(case.case_id, every)
        for marker in list(self.markers.values()) + [REASON_MARKER]:
            self.assertNotIn(marker, every)
        self.assertNotIn("simple_python", every)

    def test_no_expected_answer_reason_identifier_or_category_reaches_the_writer(self) -> None:
        code, send, _ = self.run_cli([])
        self.assertEqual(code, 0)
        self.assertEqual(len(send.requests), 3)  # 5 cases, 2 per batch
        self.assert_nothing_secret(send)

    def test_the_marker_check_catches_a_leak(self) -> None:
        real = learn.case_block

        def leaking(case, record, provider, model, failure):
            return {**real(case, record, provider, model, failure), "expected": learn.load_expected_answers(case.category)[case.case_id]}

        with mock.patch.object(learn, "case_block", leaking):
            _, send, _ = self.run_cli([])
        with self.assertRaises(AssertionError):
            self.assert_nothing_secret(send)

    def test_what_is_sent_for_a_case_and_how_the_batches_run(self) -> None:
        code, send, _ = self.run_cli(["Prefer one call."])
        prompts = [r[2]["input"][0]["content"] for r in send.requests]
        self.assertIn("at most 3 new rules", prompts[0])
        self.assertIn("300 characters", prompts[0])
        self.assertIn(self.failed[0].messages[0]["content"], prompts[0])
        self.assertIn(self.failed[1].messages[0]["content"], prompts[0])
        self.assertIn(self.failed[2].messages[0]["content"], prompts[1])
        self.assertNotIn(self.failed[2].messages[0]["content"], prompts[0])
        self.assertIn("reply 0", prompts[0])
        self.assertIn('"failure_class": "wrong-call"', prompts[0])
        self.assertIn(json.dumps(self.failed[0].functions[0]["name"].replace(".", "_")), prompts[0])
        self.assertIn("some_fn", prompts[0])
        self.assertEqual(send.requests[0][1], WRITER_KEY)
        # each batch sees the file as it stands: the rule kept in batch 0 is in batch 1's request, not in batch 0's
        self.assertNotIn("Prefer one call.", prompts[0])
        self.assertIn("Prefer one call.", prompts[1])

    def test_the_fixed_request_is_a_text_of_the_repository(self) -> None:
        self.assertTrue(learn.REQUEST_FILE.is_file())
        self.assertIn("{lines_per_batch}", learn.request_template())

    def test_a_record_without_reply_text_is_sent_without_the_field(self) -> None:
        old = self.make_run(self.failed, failed=len(self.failed), name="old", reply_text=False)
        _, send, _ = self.run_cli([], argv=self.argv(run_dir=old))
        prompt = send.requests[0][2]["input"][0]["content"]
        self.assertNotIn("reply_text", prompt)
        _, send, _ = self.run_cli([], argv=self.argv(output=self.tmp / "other.txt"))
        self.assertIn('"reply_text"', send.requests[0][2]["input"][0]["content"])

    def test_an_empty_reply_is_sent_as_empty(self) -> None:
        directory = self.make_run(self.failed, failed=len(self.failed), name="empty")
        rows = [json.loads(line) for line in (directory / "records.jsonl").read_text().splitlines()]
        rows[0]["reply_text"] = ""
        (directory / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        _, send, _ = self.run_cli([], argv=self.argv(run_dir=directory))
        self.assertIn('"reply_text": ""', send.requests[0][2]["input"][0]["content"])

    def test_the_anthropic_writer_request(self) -> None:
        _, send, _ = self.run_cli(lambda p, r: writer_reply(["Be brief."], p), argv=self.argv(writer_provider="anthropic"))
        provider, key, request = send.requests[0]
        self.assertEqual((provider, key), ("anthropic", ENV["ANTHROPIC_API_KEY"]))
        self.assertEqual(request["messages"][0]["role"], "user")
        self.assertIn("Be brief.", self.out.read_text())


class KeepingTests(LearnTest):
    def test_rules_are_kept_as_written_and_refusals_have_reasons(self) -> None:
        marker = self.markers[self.failed[0].case_id]
        long = "x" * 301
        rules = ["  Keep it short. ", "two\nlines", long, START.splitlines()[0], f"Say {marker} first", f"Use {WRITER_KEY}", "Ask when unsure."]
        code, _, _ = self.run_cli(rules, argv=self.argv(batch_size=10))
        self.assertEqual(code, 0)
        entry = self.log()[0]
        reasons = [r["refused"] for r in entry["rules"]]
        self.assertEqual(reasons, [None, "not-single-line", "too-long", "duplicate", "expected-value", "contains-key", None])
        self.assertEqual(self.out.read_text(), START + "  Keep it short. \nAsk when unsure.\n")
        self.assertNotIn("text", entry["rules"][4])
        self.assertEqual(entry["rules"][4]["sha256"], sha(f"Say {marker} first"))
        self.assertEqual(entry["rules"][4]["length"], len(f"Say {marker} first"))
        logtext = Path(str(self.out) + ".log.jsonl").read_text()
        self.assertNotIn(marker, logtext)
        self.assertNotIn(WRITER_KEY, logtext)
        self.assertNotIn(ENV["ANTHROPIC_API_KEY"], logtext)

    def test_an_expected_value_of_another_batch_is_not_a_reason_to_refuse_but_is_never_logged(self) -> None:
        other = self.markers[self.failed[4].case_id]  # a case of batch 2 of 3, returned in batch 0
        self.run_cli([f"Mention {other}"], argv=self.argv(batch_size=2))
        rule = self.log()[0]["rules"][0]
        self.assertEqual((rule["kept"], rule["refused"], rule["text_withheld"]), (True, None, True))
        self.assertNotIn("text", rule)
        self.assertNotIn(other, Path(str(self.out) + ".log.jsonl").read_text())

    def test_a_short_expected_value_inside_a_rule_is_kept_but_never_logged(self) -> None:
        rows = [json.loads(line) for line in (dataset.DATA_DIR / "answers" / "BFCL_v4_simple_python.json").read_text().splitlines()]
        for row in rows:
            if row["id"] == self.failed[0].case_id:
                (name, options), = row["ground_truth"][0].items()
                options[next(iter(options))].append("zq9")
        (dataset.DATA_DIR / "answers" / "BFCL_v4_simple_python.json").write_text("".join(json.dumps(r) + "\n" for r in rows))
        dataset.load_expected_answers.cache_clear()
        self.run_cli(["Use zq9 consistently."], argv=self.argv(batch_size=2))
        self.assertNotIn("zq9", Path(str(self.out) + ".log.jsonl").read_text())
        self.assertIn("Use zq9 consistently.", self.out.read_text())
        self.assertEqual(self.log()[0]["rules"][0]["refused"], None)

    def test_a_withheld_kept_rule_is_replayed_from_the_output_on_resume(self) -> None:
        other = self.markers[self.failed[4].case_id]
        replies = [f"Mention {other}"]
        self.run_cli(replies, argv=self.argv(batch_size=2))
        code, send, _ = self.run_cli(replies, argv=self.argv(batch_size=2))
        self.assertEqual((code, len(send.requests)), (0, 0))

    def test_a_log_that_is_not_ours_is_refused_and_left_alone(self) -> None:
        log = Path(str(self.out) + ".log.jsonl")
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("my notes without a newline")
        code, send, _ = self.run_cli([])
        self.assertEqual((code, len(send.requests)), (2, 0))
        self.assertEqual(log.read_text(), "my notes without a newline")

    def test_a_file_that_only_starts_like_a_header_is_refused_and_left_alone(self) -> None:
        for content in ('{"header": "personal notes"}', '{"header": {"x": 1}}\n'):
            with self.subTest(content=content):
                log = Path(str(self.out) + ".log.jsonl")
                log.parent.mkdir(parents=True, exist_ok=True)
                log.write_text(content)
                code, send, _ = self.run_cli([])
                self.assertEqual((code, len(send.requests)), (2, 0))
                self.assertEqual(log.read_text(), content)
                self.assertFalse(self.out.exists())
                log.unlink()

    def test_a_secret_in_the_writer_model_is_refused_before_the_log_exists(self) -> None:
        code, send, _ = self.run_cli([], argv=self.argv(writer_model=WRITER_KEY))
        self.assertEqual((code, len(send.requests)), (2, 0))
        self.assertFalse(Path(str(self.out) + ".log.jsonl").exists())

    def test_a_short_write_is_finished(self) -> None:
        real = os.write

        def short(fd, data):
            return real(fd, bytes(data)[:7])

        with mock.patch("benchmark_loop_agent.learn.os.write", short):
            code, _, _ = self.run_cli(["Rule one."])
        self.assertEqual(code, 0)
        self.assertEqual(len(self.log_lines()), 5)  # header, three batches, totals

    def test_unicode_line_breaks_make_a_rule_not_single_line(self) -> None:
        rules = ["Ends with a separator. ", "Ends with a paragraph. ", "Ends with form feed.\x0c", "Fine."]
        self.run_cli(rules, argv=self.argv(batch_size=10))
        self.assertEqual([r["refused"] for r in self.log()[0]["rules"]], ["not-single-line"] * 3 + [None])
        self.assertEqual(self.out.read_text(), START + "Fine.\n")

    def test_a_valid_rule_after_an_invalid_one_is_kept_whatever_the_limit(self) -> None:
        self.run_cli(["bad\nrule", "Good rule."], argv=self.argv(batch_size=10, lines_per_batch=1))
        self.assertEqual([r["refused"] for r in self.log()[0]["rules"]], ["not-single-line", None])

    def test_size_limits(self) -> None:
        code, _, _ = self.run_cli(["a" * 100, "b" * 100], argv=self.argv(max_bytes=len(START) + 101, batch_size=10))
        self.assertEqual([r["refused"] for r in self.log()[0]["rules"]], [None, "over-max-bytes"])
        self.assertEqual(len(self.out.read_bytes()), len(START) + 101)
        big = self.tmp / "big.txt"
        big.write_text("y" * 7950)
        self.run_cli(["z" * 100], argv=self.argv(instructions=big, max_bytes=20000, output=self.tmp / "o2.txt", batch_size=10))
        reasons = [r["refused"] for entry in json.loads("[" + ",".join(Path(str(self.tmp / "o2.txt") + ".log.jsonl").read_text().splitlines()) + "]") for r in entry.get("rules", [])]
        self.assertEqual(reasons[0], "over-runner-limit")
        self.assertEqual((self.tmp / "o2.txt").read_bytes(), big.read_bytes())

    def test_a_file_without_a_final_newline_gets_the_rule_on_its_own_line(self) -> None:
        self.instructions.write_text("No newline")
        self.run_cli(["Rule one."], argv=self.argv(batch_size=10))
        self.assertEqual(self.out.read_text(), "No newline\nRule one.\n")

    def test_an_unreadable_reply_returns_no_rules(self) -> None:
        self.run_cli("sorry, no")
        self.assertEqual(self.out.read_text(), START)
        self.assertFalse(self.log()[0]["reply_was_a_json_array"])

    def test_log_fields_and_totals(self) -> None:
        self.run_cli(["Rule A.", "Rule A."], argv=self.argv(batch_size=10))
        batch, totals = self.log()
        self.assertEqual(batch["case_sha256"], [sha(c.case_id) for c in self.failed])
        self.assertEqual(batch["writer"], {"provider_requested": "openai", "provider_reported": None, "model_requested": "writer-model", "model_reported": "writer-actual"})
        self.assertEqual(len(batch["request_sha256"]), 64)
        self.assertEqual((batch["input_tokens"], batch["output_tokens"]), (11, 5))
        self.assertEqual(totals["totals"], {
            "batches": 1, "rules_returned": 2, "kept": 1, "refused": {"duplicate": 1}, "input_tokens": 11, "output_tokens": 5,
            "instructions": {"sha256": sha(START), "bytes": len(START)},
            "output": {"sha256": sha(START + "Rule A.\n"), "bytes": len(START + "Rule A.\n")}})

    def test_the_default_log_name(self) -> None:
        self.run_cli([])
        self.assertTrue(Path(str(self.out) + ".log.jsonl").is_file())


class RefusalTests(LearnTest):
    def refused(self, **changes):
        code, send, err = self.run_cli([], **changes)
        self.assertEqual(code, 2, err)
        self.assertEqual(send.requests, [])
        self.assertFalse(self.out.exists())
        return err

    def test_not_a_development_run(self) -> None:
        for split in ("validation", "held-out", None):
            directory = self.make_run(self.failed, failed=5, split=split, name=f"r-{split}")
            self.refused(argv=self.argv(run_dir=directory))

    def test_several_providers(self) -> None:
        directory = self.make_run(self.failed, failed=5, providers=("openai", "anthropic"), name="two")
        self.refused(argv=self.argv(run_dir=directory))

    def test_a_record_outside_the_development_part(self) -> None:
        validation = sorted(part_case_ids("validation"))
        case = next(c for c in load_cases("simple_python") if c.case_id in validation)
        directory = self.make_run(self.failed + [case], failed=5, name="leaky")
        self.refused(argv=self.argv(run_dir=directory))

    def test_a_passing_record_outside_the_development_part_too(self) -> None:
        case = next(c for c in load_cases("simple_python") if c.case_id in part_case_ids("held-out"))
        directory = self.make_run(self.failed + [case], failed=5, name="leaky2")
        self.refused(argv=self.argv(run_dir=directory))

    def test_a_missing_run_or_key(self) -> None:
        self.refused(argv=self.argv(run_dir=self.tmp / "nothing"))
        code, send, _ = self.run_cli([], env={})
        self.assertEqual((code, send.requests), (2, []))

    def test_a_bad_instruction_file_and_bad_numbers(self) -> None:
        self.instructions.write_bytes(b"\xff\xfe")
        self.refused()
        for option in ("max_bytes", "batch_size", "lines_per_batch"):
            with self.assertRaises(SystemExit):
                self.run_cli([], argv=self.argv(**{option: 0}))


class ResumeTests(LearnTest):
    def test_a_second_run_sends_nothing_and_changes_nothing(self) -> None:
        self.run_cli(["Rule A."])
        before = (self.out.read_bytes(), Path(str(self.out) + ".log.jsonl").read_bytes())
        code, send, _ = self.run_cli(["Rule B."])
        self.assertEqual((code, send.requests), (0, []))
        self.assertEqual((self.out.read_bytes(), Path(str(self.out) + ".log.jsonl").read_bytes()), before)

    def test_it_continues_after_the_last_logged_batch(self) -> None:
        sent = FakeSend(lambda p, r: writer_reply([f"Rule {len(sent.requests)}."], p) if len(sent.requests) < 2 else OSError("down"))
        code, _, err = self.run_cli(None, send=sent)
        self.assertEqual(code, 3)
        self.assertNotIn(WRITER_KEY, err)
        self.assertEqual(self.out.read_text(), START + "Rule 1.\n")
        self.assertEqual(len(self.log()), 1)  # no totals, no half batch
        code, send, _ = self.run_cli(lambda p, r: writer_reply(["Rule next."], p))
        self.assertEqual(code, 0)
        self.assertEqual(len(send.requests), 2)  # batches 1 and 2 only
        self.assertEqual(self.out.read_text(), START + "Rule 1.\nRule next.\n")  # batch 2 repeats the rule
        self.assertEqual(self.out.read_text().splitlines()[:3], START.splitlines() + ["Rule 1."])
        self.assertEqual(len(self.log()), 4)

    def test_other_inputs_or_options_over_an_existing_output_are_refused(self) -> None:
        self.run_cli(["Rule A."])
        for change in ({"max_bytes": 3000}, {"batch_size": 3}, {"lines_per_batch": 2}, {"writer_model": "other"}):
            code, send, _ = self.run_cli([], argv=self.argv(**change))
            self.assertEqual((code, send.requests), (2, []), change)
        code, send, _ = self.run_cli([], argv=self.argv(writer_provider="anthropic"))
        self.assertEqual((code, send.requests), (2, []))
        self.instructions.write_text(START + "More\n")
        code, send, _ = self.run_cli([])
        self.assertEqual((code, send.requests), (2, []))
        self.instructions.write_text(START)
        with (self.run_dir / "records.jsonl").open("a") as handle:
            handle.write(json.dumps({"provider": "openai", "case_id": self.cases[-1].case_id, "category": "simple_python", "outcome": "pass"}) + "\n")
        code, send, _ = self.run_cli([])
        self.assertEqual((code, send.requests), (2, []))

    def test_an_output_changed_since_is_refused(self) -> None:
        self.run_cli(["Rule A."])
        self.out.write_text(START + "Edited\n")
        code, send, _ = self.run_cli([])
        self.assertEqual((code, send.requests), (2, []))

    def test_an_output_without_a_log_is_refused(self) -> None:
        self.out.parent.mkdir()
        self.out.write_text(START)
        code, send, _ = self.run_cli([])
        self.assertEqual((code, send.requests), (2, []))

    def test_a_first_batch_failure_leaves_an_unchanged_copy(self) -> None:
        code, _, _ = self.run_cli(None, send=FakeSend(RuntimeError("boom")))
        self.assertEqual(code, 3)
        self.assertEqual(self.out.read_text(), START)
        self.assertEqual(self.log(), [])

    def test_the_header_holds_the_identity_before_any_request(self) -> None:
        code, _, _ = self.run_cli(None, send=FakeSend(RuntimeError("boom")))
        self.assertEqual(code, 3)
        self.assertEqual(self.header()["writer_model"], "writer-model")
        code, send, _ = self.run_cli([], argv=self.argv(writer_model="other"))
        self.assertEqual((code, send.requests), (2, []))

    def test_a_refused_rerun_leaves_the_log_untouched(self) -> None:
        self.run_cli(["Rule A."])
        log = Path(str(self.out) + ".log.jsonl")
        before = (log.read_bytes(), self.out.read_bytes())
        code, send, _ = self.run_cli([], argv=self.argv(max_bytes=3000))
        self.assertEqual((code, send.requests), (2, []))
        self.assertEqual((log.read_bytes(), self.out.read_bytes()), before)

    def test_an_interruption_after_the_last_batch_is_finished_without_sending(self) -> None:
        self.run_cli([])
        log = Path(str(self.out) + ".log.jsonl")
        lines = log.read_bytes().splitlines(keepends=True)
        log.write_bytes(b"".join(lines[:-1]) + lines[-1][:10])  # totals cut short
        code, send, _ = self.run_cli([])
        self.assertEqual((code, send.requests), (0, []))
        self.assertIn("totals", self.log_lines()[-1])

    def test_an_output_one_version_behind_is_repaired_but_an_empty_one_is_refused(self) -> None:
        self.run_cli(["Rule A."], argv=self.argv(batch_size=10))
        log = Path(str(self.out) + ".log.jsonl")
        lines = log.read_bytes().splitlines(keepends=True)
        log.write_bytes(b"".join(lines[:-1]))  # no totals
        self.out.write_text(START)  # the version before the last batch
        code, send, _ = self.run_cli([], argv=self.argv(batch_size=10))
        self.assertEqual((code, send.requests), (0, []))
        self.assertEqual(self.out.read_text(), START + "Rule A.\n")
        log.write_bytes(b"".join(lines[:-1]))
        self.out.write_text("")
        code, send, _ = self.run_cli([], argv=self.argv(batch_size=10))
        self.assertEqual((code, send.requests), (2, []))

    def test_a_changed_question_is_another_input(self) -> None:
        self.run_cli(["Rule A."])
        original = dataset.load_cases

        def changed(category):
            return [dataset.Case(**{**c.__dict__, "messages": [{"role": "user", "content": "changed"}]}) if c.case_id == self.failed[0].case_id else c
                    for c in original(category)]

        with mock.patch.object(learn, "load_cases", changed):
            code, send, _ = self.run_cli([])
        self.assertEqual((code, send.requests), (2, []))

    def test_a_truncated_manifest_is_refused(self) -> None:
        (self.run_dir / "run.json").write_text('{"parameters": {"provid')
        code, send, _ = self.run_cli([])
        self.assertEqual((code, send.requests), (2, []))

    def test_a_key_in_the_instruction_file_is_refused_before_any_file_exists(self) -> None:
        self.instructions.write_text(START + f"key {WRITER_KEY}\n")
        code, send, _ = self.run_cli([])
        self.assertEqual((code, send.requests), (2, []))
        self.assertFalse(self.out.exists())

    def test_a_temporary_looking_input_is_never_replaced(self) -> None:
        start = self.tmp / "learned.txt.tmp"
        start.write_text(START)
        out = self.tmp / "learned.txt"
        code, _, _ = self.run_cli(["Rule A."], argv=self.argv(instructions=start, output=out))
        self.assertEqual(code, 0)
        self.assertEqual(start.read_text(), START)
        self.assertEqual(out.read_text(), START + "Rule A.\n")

    def test_a_log_in_use_is_refused(self) -> None:
        self.run_cli([])
        log = learn.Log(Path(str(self.out) + ".log.jsonl"), create=False)
        self.addCleanup(log.close)
        code, send, _ = self.run_cli([])
        self.assertEqual((code, send.requests), (2, []))


if __name__ == "__main__":
    unittest.main()
