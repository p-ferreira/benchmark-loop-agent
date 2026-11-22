"""Offline tests: expected answer isolation, provider isolation, scorer pinning and exit codes."""

import contextlib
import io
import json
import unittest
from dataclasses import fields
from unittest import mock

from benchmark_loop_agent import __main__ as cli
from benchmark_loop_agent.case import DATA_DIR, GORILLA_COMMIT, PinnedCase, load_case, load_expected_answer
from benchmark_loop_agent.record import Record
from benchmark_loop_agent.runner import run_providers
from tests.test_providers import NAME, RIGHT, SECRET, FakePost, anthropic_reply, environment, openai_reply


class ExpectedAnswerIsolationTests(unittest.TestCase):
    def test_pinned_case_has_no_answer_field(self) -> None:
        self.assertEqual({f.name for f in fields(PinnedCase)}, {"case_id", "prompt", "functions"})

    def test_expected_answer_is_absent_from_every_model_input(self) -> None:
        # The answer's distinctive value "units" appears in the schema description, so
        # check the structure: the ground-truth key and its value lists must not be sent.
        answer_text = json.dumps(load_expected_answer())
        bodies = []
        for provider, reply in (("openai", openai_reply(json.dumps(RIGHT))), ("anthropic", anthropic_reply(RIGHT))):
            post = FakePost(reply)
            run_providers([provider], load_case(), environment(provider), post)
            bodies.append(json.dumps(post.requests[0][2]))
        for body in bodies:
            self.assertNotIn(answer_text, body)
            self.assertNotIn("ground_truth", body)
            self.assertNotIn('"base": [10]', body)

    def test_answer_is_not_read_until_after_the_model_answered(self) -> None:
        order: list[str] = []
        post = FakePost(anthropic_reply(RIGHT))

        def recording_post(*args):
            order.append("request")
            return post(*args)

        def recording_loader():
            order.append("answer")
            return load_expected_answer()

        with mock.patch("benchmark_loop_agent.runner.load_expected_answer", recording_loader):
            run_providers(["anthropic"], load_case(), environment("anthropic"), recording_post)
        self.assertEqual(order, ["request", "answer"])

    def test_case_file_does_not_contain_the_answer(self) -> None:
        self.assertNotIn("ground_truth", (DATA_DIR / "simple_python_0.case.json").read_text())


class ProviderIsolationTests(unittest.TestCase):
    def test_one_failing_provider_does_not_alter_the_other(self) -> None:
        env = {**environment("openai"), **environment("anthropic")}

        def post(url, headers, body):
            if "openai" in url:
                raise RuntimeError(SECRET)
            return anthropic_reply(RIGHT)

        both = run_providers(["openai", "anthropic"], load_case(), env, post)
        alone = run_providers(["anthropic"], load_case(), env, post)
        self.assertEqual([r.outcome for r in both], ["unscored", "pass"])
        for field_name in ("outcome", "returned_calls", "actual_model", "input_tokens", "reasons"):
            self.assertEqual(getattr(both[1], field_name), getattr(alone[0], field_name))

    def test_non_object_arguments_from_one_provider_do_not_stop_the_other(self) -> None:
        env = {**environment("openai"), **environment("anthropic")}

        def post(url, headers, body):
            return openai_reply("null") if "openai" in url else anthropic_reply(RIGHT)

        records = run_providers(["openai", "anthropic"], load_case(), env, post)
        self.assertEqual([r.outcome for r in records], ["fail", "pass"])

    def test_missing_credentials_for_both_still_yield_two_records(self) -> None:
        records = run_providers(["openai", "anthropic"], load_case(), {}, FakePost(RuntimeError("no")))
        self.assertEqual([r.outcome for r in records], ["unscored", "unscored"])


class ScorerPinTests(unittest.TestCase):
    def test_records_carry_the_pinned_revisions(self) -> None:
        record = run_providers(["anthropic"], load_case(), environment("anthropic"), FakePost(anthropic_reply(RIGHT)))[0]
        self.assertIn(GORILLA_COMMIT, record.dataset_revision)
        self.assertIn(GORILLA_COMMIT, record.scorer_revision)
        self.assertEqual(record.case_id, "simple_python_0")
        self.assertEqual(record.returned_calls, [{NAME: RIGHT}])


class CliTests(unittest.TestCase):
    def make_record(self, outcome: str) -> Record:
        return Record("p", "m", None, "c", "d", "s", None, outcome, [], None, None, None)  # type: ignore[arg-type]

    def test_exit_code_rule(self) -> None:
        make = self.make_record
        self.assertEqual(cli.exit_code([make("pass"), make("pass")]), 0)
        self.assertEqual(cli.exit_code([make("pass"), make("fail")]), 1)
        self.assertEqual(cli.exit_code([make("fail"), make("unscored")]), 3)

    def test_main_prints_one_json_line_per_provider_and_no_secret(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        env = {**environment("openai"), **environment("anthropic")}
        with mock.patch.dict("os.environ", env, clear=True), \
                mock.patch.object(cli, "post_json", FakePost(RuntimeError(f"key {SECRET}"))), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main([])
        lines = out.getvalue().splitlines()
        self.assertEqual([json.loads(line)["provider"] for line in lines], ["openai", "anthropic"])
        self.assertEqual(code, 3)
        self.assertNotIn(SECRET, out.getvalue() + err.getvalue())

    def test_non_finite_arguments_still_emit_strictly_valid_json(self) -> None:
        def reject_constant(token: str) -> None:
            raise AssertionError(f"non-JSON token {token}")

        replies = {"openai": openai_reply('{"base": 1e400, "height": -1e400}'),
                   "anthropic": anthropic_reply({"base": float("inf"), "height": float("nan")})}
        for provider, reply in replies.items():
            with self.subTest(provider=provider):
                out = io.StringIO()
                with mock.patch.dict("os.environ", environment(provider), clear=True), \
                        mock.patch.object(cli, "post_json", FakePost(reply)), \
                        contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                    code = cli.main(["--provider", provider])
                data = json.loads(out.getvalue(), parse_constant=reject_constant)
                self.assertEqual(data["outcome"], "fail")
                self.assertEqual(code, 1)
                self.assertIn("unrepresentable_number", json.dumps(data["returned_calls"]))

    def test_provider_flag_limits_the_run(self) -> None:
        out = io.StringIO()
        with mock.patch.dict("os.environ", {}, clear=True), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            cli.main(["--provider", "openai"])
        self.assertEqual(len(out.getvalue().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
