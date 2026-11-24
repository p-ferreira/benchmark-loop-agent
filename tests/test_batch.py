"""Offline tests: sampling, resume, retry, bounded failure, the manifest and the command line."""

import contextlib
import io
import json
import re
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from benchmark_loop_agent import __main__ as cli
from benchmark_loop_agent.batch import RunParameters, run_batch
from benchmark_loop_agent.categories import CATEGORIES
from benchmark_loop_agent.dataset import DATA_DIR, GORILLA_COMMIT, load_cases
from benchmark_loop_agent.retry import MAX_ATTEMPTS, is_transient, with_retries
from benchmark_loop_agent.sampling import sample_cases, select_cases
from benchmark_loop_agent.store import read_records
from tests.support import SECRET, FakeSend, anthropic_reply, environment, openai_reply, reply_for, right_calls


class Transient(Exception):
    status_code = 429


class BadKey(Exception):
    status_code = 401


def parameters(**changes) -> RunParameters:
    values = dict(categories=("simple_python", "irrelevance"), sample_size=3, seed=1,
                  providers=("openai", "anthropic"), models={"openai": "requested-model", "anthropic": "requested-model"},
                  concurrency=2)
    return RunParameters(**{**values, **changes})


ENV = environment("openai", "anthropic")


def perfect(provider: str, request: dict):
    """A reply that scores as a pass for whichever case the request is for."""
    prompt = json.dumps(request)
    for category in ("simple_python", "irrelevance"):
        for case in load_cases(category):
            if case.messages[0]["content"] in prompt:
                return reply_for(provider, right_calls(case) if category == "simple_python" else [])
    raise AssertionError("unknown case")


class SamplingTests(unittest.TestCase):
    def test_same_seed_same_cases_in_file_order(self) -> None:
        cases = load_cases("multiple")
        first = sample_cases(cases, 10, seed=7)
        self.assertEqual([c.case_id for c in first], [c.case_id for c in sample_cases(cases, 10, seed=7)])
        self.assertEqual(len(first), 10)
        order = [c.case_id for c in cases]
        self.assertEqual([c.case_id for c in first], sorted((c.case_id for c in first), key=order.index))
        self.assertNotEqual([c.case_id for c in first], [c.case_id for c in sample_cases(cases, 10, seed=8)])

    def test_default_is_every_case_and_a_big_size_keeps_every_case(self) -> None:
        cases = load_cases("live_parallel")
        self.assertEqual(sample_cases(cases, None, 0), cases)
        self.assertEqual(sample_cases(cases, 10_000, 0), cases)

    def test_a_category_keeps_its_sample_when_others_are_added(self) -> None:
        alone = [c.case_id for c in select_cases(["parallel"], 5, 3)]
        with_others = [c.case_id for c in select_cases(["simple_java", "parallel"], 5, 3) if c.category == "parallel"]
        self.assertEqual(alone, with_others)


class RetryTests(unittest.TestCase):
    def test_transient_errors_are_retried_with_growing_waits_then_succeed(self) -> None:
        waits: list[float] = []
        calls = []

        def flaky(provider, key, request):
            calls.append(1)
            if len(calls) < 3:
                raise Transient("slow down")
            return {"ok": True}

        send = with_retries(flaky, sleep=waits.append, jitter=lambda: 0.0)
        self.assertEqual(send("openai", "k", {}), {"ok": True})
        self.assertEqual((len(calls), waits), (3, [1.0, 2.0]))

    def test_retry_is_bounded(self) -> None:
        calls = []

        def always(provider, key, request):
            calls.append(1)
            raise Transient("rate limited")

        send = with_retries(always, sleep=lambda s: None)
        with self.assertRaises(Exception) as caught:
            send("openai", "k", {})
        self.assertEqual(len(calls), MAX_ATTEMPTS)
        self.assertIn(f"gave up after {MAX_ATTEMPTS} attempts", str(caught.exception))

    def test_a_permanent_error_is_not_retried(self) -> None:
        calls = []

        def bad(provider, key, request):
            calls.append(1)
            raise BadKey("no")

        with self.assertRaises(BadKey):
            with_retries(bad, sleep=lambda s: None)("openai", "k", {})
        self.assertEqual(len(calls), 1)

    def test_classification(self) -> None:
        import anthropic
        import openai

        self.assertTrue(is_transient(openai.APIConnectionError(request=mock.Mock())))
        self.assertTrue(is_transient(anthropic.APITimeoutError(request=mock.Mock())))
        for status in (408, 429, 500, 529):
            error = Exception()
            error.status_code = status  # type: ignore[attr-defined]
            self.assertTrue(is_transient(error))
        self.assertFalse(is_transient(BadKey()))
        self.assertFalse(is_transient(ValueError("x")))


class BatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp()) / "out"

    def records(self):
        return read_records(self.directory / "records.jsonl")

    def run_batch(self, send, **changes):
        return run_batch(self.directory, parameters(**changes), ENV, send, sleep=lambda s: None)

    def test_one_record_per_case_and_provider_with_category(self) -> None:
        records = self.run_batch(FakeSend(perfect))
        rows = self.records()
        self.assertEqual(len(rows), 12)  # 2 categories x 3 cases x 2 providers
        self.assertEqual({(r["provider"], r["case_id"]) for r in rows}.__len__(), 12)
        self.assertEqual({r["category"] for r in rows}, {"simple_python", "irrelevance"})
        self.assertEqual({r["outcome"] for r in rows}, {"pass"})
        self.assertEqual(len(records), 12)

    def test_manifest_holds_parameters_revisions_and_times(self) -> None:
        self.run_batch(FakeSend(perfect))
        manifest = json.loads((self.directory / "run.json").read_text())
        self.assertEqual(manifest["parameters"]["seed"], 1)
        self.assertEqual(manifest["parameters"]["sample_size"], 3)
        self.assertEqual(manifest["parameters"]["models"]["openai"], "requested-model")
        self.assertIn(GORILLA_COMMIT, manifest["dataset_revision"])
        self.assertIn(GORILLA_COMMIT, manifest["scorer_revision"])
        (session,) = manifest["sessions"]
        self.assertTrue(session["started_at"] and session["ended_at"])
        self.assertGreaterEqual(session["wall_seconds"], 0)
        self.assertNotIn(SECRET, (self.directory / "run.json").read_text())

    def test_resume_repeats_nothing_that_finished(self) -> None:
        self.run_batch(FakeSend(perfect))
        again = FakeSend(perfect)
        self.run_batch(again)
        self.assertEqual(again.requests, [])
        self.assertEqual(len(self.records()), 12)
        self.assertEqual(len(json.loads((self.directory / "run.json").read_text())["sessions"]), 2)

    def test_resume_after_an_interruption_runs_only_the_missing_cases(self) -> None:
        self.run_batch(FakeSend(perfect))
        path = self.directory / "records.jsonl"
        lines = path.read_text().splitlines()
        path.write_text("\n".join(lines[:8]) + "\n" + lines[8][:25])  # last line cut short
        again = FakeSend(perfect)
        self.run_batch(again)
        self.assertEqual(len(again.requests), 4)
        self.assertEqual(len(self.records()), 12)

    def test_resume_retries_unscored_and_keeps_pass_and_fail(self) -> None:
        wrong = lambda provider, request: reply_for(provider, [{"nothing": {}}])  # noqa: E731
        self.run_batch(FakeSend(wrong))  # every simple_python case fails, irrelevance cases fail too
        before = {(r["provider"], r["case_id"]): r["outcome"] for r in self.records()}
        self.assertEqual(set(before.values()), {"fail"})
        # Make three records unscored by hand, as an API outage would have.
        rows = self.records()
        for row in rows[:3]:
            row.update(outcome="unscored", returned_calls=None, reasons=["outage"])
        (self.directory / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        again = FakeSend(perfect)
        self.run_batch(again)
        self.assertEqual(len(again.requests), 3)
        after = {(r["provider"], r["case_id"]): r["outcome"] for r in self.records()}
        self.assertEqual(len(after), 12)
        for key in list(before)[3:]:
            self.assertEqual(after[key], "fail")  # finished records were not touched
        self.assertNotIn("unscored", after.values())

    def test_a_case_that_keeps_failing_is_unscored_after_bounded_attempts(self) -> None:
        send = FakeSend(lambda provider, request: Transient(f"busy {SECRET}"))
        self.run_batch(send, categories=("simple_python",), sample_size=1, providers=("openai",))
        (row,) = self.records()
        self.assertEqual(row["outcome"], "unscored")
        self.assertEqual(len(send.requests), MAX_ATTEMPTS)
        self.assertIn("gave up", row["reasons"][0])
        self.assertNotIn(SECRET, json.dumps(row))

    def test_one_providers_or_cases_failure_never_changes_another_record(self) -> None:
        def mixed(provider, request):
            if provider == "openai":
                return RuntimeError("boom")
            return perfect(provider, request)

        both = self.run_batch(FakeSend(mixed))
        self.assertEqual({r.outcome for r in both if r.provider == "openai"}, {"unscored"})
        self.assertEqual({r.outcome for r in both if r.provider == "anthropic"}, {"pass"})
        other = Path(tempfile.mkdtemp()) / "alone"
        run_batch(other, parameters(providers=("anthropic",)), ENV, FakeSend(perfect), sleep=lambda s: None)
        key = lambda r: r["case_id"]  # noqa: E731
        strip = lambda r: {k: v for k, v in r.items() if k != "latency_seconds"}  # noqa: E731
        together = sorted((r for r in self.records() if r["provider"] == "anthropic"), key=key)
        alone = sorted(read_records(other / "records.jsonl"), key=key)
        self.assertEqual([strip(r) for r in together], [strip(r) for r in alone])

    def test_one_failing_case_does_not_change_the_other_cases(self) -> None:
        first = select_cases(["simple_python"], 40, 1)[0]  # the sample parameters() uses below

        def one_bad(provider, request):
            if first.messages[0]["content"] in json.dumps(request):
                return RuntimeError("only this one")
            return perfect(provider, request)

        options = dict(categories=("simple_python",), sample_size=40, providers=("anthropic",), concurrency=4)
        baseline = Path(tempfile.mkdtemp()) / "baseline"
        run_batch(baseline, parameters(**options), ENV, FakeSend(perfect), sleep=lambda s: None)
        self.run_batch(FakeSend(one_bad), **options)
        expected = {r["case_id"]: r["outcome"] for r in read_records(baseline / "records.jsonl")}
        actual = {r["case_id"]: r["outcome"] for r in self.records()}
        self.assertEqual(actual.pop(first.case_id), "unscored")
        expected.pop(first.case_id)
        self.assertEqual(actual, expected)

    def test_changed_parameters_on_an_existing_directory_are_refused(self) -> None:
        self.run_batch(FakeSend(perfect))
        with self.assertRaises(ValueError):
            self.run_batch(FakeSend(perfect), seed=2)
        self.run_batch(FakeSend(perfect), concurrency=5)  # concurrency may change

    def test_requests_run_concurrently_up_to_the_limit(self) -> None:
        active, peak, lock = 0, 0, threading.Lock()
        barrier = threading.Barrier(2, timeout=5)

        def slow(provider, request):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            try:
                barrier.wait()
            except threading.BrokenBarrierError:
                pass
            with lock:
                active -= 1
            return perfect(provider, request)

        self.run_batch(FakeSend(slow), categories=("simple_python",), sample_size=2, providers=("openai",), concurrency=2)
        self.assertEqual(peak, 2)


class CliTests(unittest.TestCase):
    def run_cli(self, *argv: str, env=None, send=None):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict("os.environ", env if env is not None else ENV, clear=True), \
                mock.patch.object(cli, "send_request", send or FakeSend(perfect)), \
                mock.patch("benchmark_loop_agent.batch.time.sleep"), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_parameters_reach_the_run(self) -> None:
        directory = tempfile.mkdtemp()
        code, _, err = self.run_cli("--output-dir", directory, "--categories", "simple_python", "irrelevance",
                                    "--sample-size", "2", "--seed", "4", "--provider", "anthropic",
                                    "--anthropic-model", "claude-x", "--concurrency", "3")
        self.assertEqual(code, 0)
        manifest = json.loads((Path(directory) / "run.json").read_text())
        self.assertEqual(manifest["parameters"], {
            "categories": ["simple_python", "irrelevance"], "sample_size": 2, "seed": 4,
            "providers": ["anthropic"], "models": {"anthropic": "claude-x"}, "concurrency": 3})
        rows = read_records(Path(directory) / "records.jsonl")
        self.assertEqual({(r["provider"], r["requested_model"]) for r in rows}, {("anthropic", "claude-x")})
        self.assertEqual(len(rows), 4)
        self.assertIn("anthropic: pass 4", err)

    def test_defaults_are_all_thirteen_categories_and_every_case(self) -> None:
        args = cli.build_parser().parse_args(["--output-dir", "x"])
        self.assertEqual(tuple(args.categories), CATEGORIES)
        self.assertEqual(len(CATEGORIES), 13)
        self.assertIsNone(args.sample_size)

    def test_exit_codes_and_no_secret_in_output(self) -> None:
        directory = tempfile.mkdtemp()
        code, out, err = self.run_cli("--output-dir", directory, "--categories", "simple_python",
                                      "--sample-size", "1", send=FakeSend(RuntimeError(f"key {SECRET}")))
        self.assertEqual(code, 3)
        self.assertNotIn(SECRET, out + err + "".join(p.read_text() for p in Path(directory).iterdir()))

    def test_missing_models_are_unscored_not_defaulted(self) -> None:
        directory = tempfile.mkdtemp()
        env = {"OPENAI_API_KEY": SECRET, "ANTHROPIC_API_KEY": SECRET}
        code, _, _ = self.run_cli("--output-dir", directory, "--categories", "simple_python", "--sample-size", "1",
                                  env=env)
        rows = read_records(Path(directory) / "records.jsonl")
        self.assertEqual({r["outcome"] for r in rows}, {"unscored"})
        self.assertTrue(all("_MODEL is not set" in r["reasons"][0] for r in rows))
        self.assertEqual(code, 3)

    def test_changed_parameters_exit_with_a_usage_error(self) -> None:
        directory = tempfile.mkdtemp()
        self.run_cli("--output-dir", directory, "--categories", "simple_python", "--sample-size", "1")
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("--output-dir", directory, "--categories", "simple_python", "--sample-size", "2")
        self.assertEqual(caught.exception.code, 2)


class ReadmeCountTests(unittest.TestCase):
    def test_readme_states_the_number_of_cases_counted_from_the_files(self) -> None:
        readme = (DATA_DIR.parent / "README.md").read_text()
        for category in CATEGORIES:
            count = len(load_cases(category))
            self.assertRegex(readme, rf"\|\s*`{category}`\s*\|[^|\n]*\|\s*{count}\s*\|", category)
        total = sum(len(load_cases(c)) for c in CATEGORIES)
        self.assertIn(f"| **Total** | | {total} |", readme)

    def test_data_files_hold_no_extra_cases_and_ids_match_answers(self) -> None:
        for category in CATEGORIES:
            lines = (DATA_DIR / "questions" / f"BFCL_v4_{category}.json").read_text().splitlines()
            self.assertEqual(len(load_cases(category)), len([x for x in lines if x.strip()]))


if __name__ == "__main__":
    unittest.main()
