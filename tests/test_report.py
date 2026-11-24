"""The report's figures, checked against a small fixed set of records."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from benchmark_loop_agent import report
from benchmark_loop_agent.dataset import DATA_DIR

RATES = {"gpt-known": {"input": 2.0, "output": 10.0, "page": "https://example.test/pricing", "read_on": "2026-11-23"}}


def record(provider, case_id, category, outcome, tokens=(100, 10), model="gpt-known", actual="gpt-known-2026"):
    return {"provider": provider, "requested_model": model, "actual_model": actual if tokens or outcome != "unscored" else None,
            "case_id": case_id, "category": category, "outcome": outcome, "reasons": [],
            "latency_seconds": 1.0, "input_tokens": tokens[0] if tokens else None,
            "output_tokens": tokens[1] if tokens else None, "returned_calls": []}


RECORDS = [
    record("openai", "a1", "simple_python", "pass", (1000, 100)),
    record("openai", "a2", "simple_python", "fail", (2000, 200)),
    record("openai", "b1", "irrelevance", "pass", (3000, 300)),
    record("openai", "b2", "irrelevance", "pass", None),  # response without usage
    record("openai", "b3", "irrelevance", "unscored", None),
    record("anthropic", "a1", "simple_python", "pass", (500, 50), model="claude-unpriced", actual="claude-x"),
]


def manifest(sessions, sample_size=None, categories=("simple_python", "irrelevance"), selection="default", concurrency=None):
    if selection == "default":
        selection = {"simple_python": 2, "irrelevance": 3}
    m = {"run_id": "run123", "dataset_revision": "dsrev", "scorer_revision": "screv",
            "parameters": {"categories": list(categories), "sample_size": sample_size, "seed": 4,
                           "providers": ["openai", "anthropic"],
                           "models": {"openai": "gpt-known", "anthropic": "claude-unpriced"}},
            "sessions": sessions}
    if selection is not None:
        m["selection"] = selection
    if concurrency is not None:
        m["parameters"]["concurrency"] = concurrency
    return m


DONE = {"number": 1, "concurrency": 3, "started_at": "T0", "ended_at": "T1", "wall_seconds": 42.5}
CUT = {"number": 2, "concurrency": 5, "started_at": "T2", "ended_at": None, "wall_seconds": None}


class ReportTests(unittest.TestCase):
    def render(self, provider="openai", sessions=(DONE,), records=RECORDS, **kw):
        return report.render(manifest(list(sessions), **kw), provider, records, RATES)

    def test_figures(self) -> None:
        text = self.render()
        self.assertIn("| `simple_python` | 50.0% (1/2) | 1 | 1 | 0 |", text)
        self.assertIn("| `irrelevance` | 100.0% (2/2) | 2 | 0 | 1 |", text)
        self.assertIn("| **Overall** | **75.0% (3/4)** | 3 | 1 | 1 |", text)
        self.assertIn("pools every judged case", text)
        self.assertIn("Input tokens: 6,000", text)
        self.assertIn("Output tokens: 600", text)
        # (6000 * 2 + 600 * 10) / 1e6
        self.assertIn("**$0.0180**", text)
        self.assertIn("uncached input rate", text)
        self.assertIn("2 case(s) lack reported usage", text)
        self.assertIn("`b2` (input and output)", text)
        self.assertIn("`b3` (input and output)", text)
        self.assertIn("Wall time: 42.5 s over 1 invocation(s)", text)
        self.assertIn("| 1 | 3 | T0 | T1 | 42.5 s |", text)
        for item in ("`gpt-known`", "`gpt-known-2026`", "`dsrev`", "`screv`", "run123", "Seed: 4"):
            self.assertIn(item, text)
        self.assertIn("pricing page", text)
        self.assertNotIn("Sampled run", text)

    def test_partial_usage_keeps_the_known_component(self) -> None:
        records = [record("openai", "p1", "simple_python", "pass", (1000, None)),
                   record("openai", "p2", "simple_python", "pass", (None, 50))]
        text = report.render(manifest([DONE], selection={"simple_python": 2, "irrelevance": 0}), "openai", records, RATES)
        self.assertIn("Input tokens: 1,000", text)
        self.assertIn("Output tokens: 50", text)
        self.assertIn("**$0.0025**", text)  # (1000 * 2 + 50 * 10) / 1e6
        self.assertIn("`p1` (output)", text)
        self.assertIn("`p2` (input)", text)
        self.assertIn("Records with complete usage: 0 of 2", text)

    def test_every_case_without_usage_is_named(self) -> None:
        records = [record("openai", f"n{i:02}", "simple_python", "pass", None) for i in range(21)]
        text = report.render(manifest([DONE], selection={"simple_python": 21, "irrelevance": 0}), "openai", records, RATES)
        self.assertIn("21 case(s) lack reported usage", text)
        self.assertIn("`n20`", text)
        self.assertNotIn("more", text.split("lack reported usage")[1].split("\n")[0])

    def test_a_partial_category_is_incomplete_even_with_an_end_time(self) -> None:
        records = [record("openai", "a1", "simple_python", "pass")]
        text = report.render(manifest([DONE], selection={"simple_python": 2, "irrelevance": 0}), "openai", records, RATES)
        self.assertIn("**Incomplete run.** records missing for `simple_python` (1 of 2 case(s))", text)

    def test_an_empty_selection_is_complete(self) -> None:
        text = report.render(manifest([DONE], selection={"simple_python": 0, "irrelevance": 0}), "openai", [], RATES)
        self.assertNotIn("Incomplete run", text)

    def test_the_earlier_manifest_keeps_its_concurrency(self) -> None:
        old = {k: v for k, v in DONE.items() if k != "concurrency"}
        text = report.render(manifest([old], concurrency=7), "openai", RECORDS, RATES)
        self.assertIn("| 1 | 7 | T0 | T1 | 42.5 s |", text)

    def test_unscored_makes_the_run_incomplete(self) -> None:
        self.assertIn("**Incomplete run.** 1 case(s) are unscored", self.render())

    def test_a_missing_rate_leaves_cost_out_and_says_so(self) -> None:
        text = self.render("anthropic")
        self.assertIn("Cost: not given, the rates file has no entry for `claude-unpriced`", text)
        self.assertNotIn("$", text)
        self.assertIn("`irrelevance` (0 of 3 case(s))", text)  # also incomplete

    def test_an_interrupted_invocation_has_no_wall_time(self) -> None:
        text = self.render(sessions=(DONE, CUT))
        self.assertIn("unavailable for invocation 2, so no total is given", text)
        self.assertIn("| 2 | 5 | T2 | - | unavailable", text)
        self.assertIn("latest invocation has no saved end time", text)
        self.assertNotIn("Wall time: 42.5", text)

    def test_a_sampled_run_says_so_at_the_top(self) -> None:
        lines = self.render(sample_size=2).splitlines()
        self.assertTrue(lines[2].startswith("> **Sampled run.**"))
        self.assertIn("at most 2 case(s) per category", lines[2])

    def test_a_complete_full_run_has_no_warning(self) -> None:
        records = [r for r in RECORDS if r["outcome"] != "unscored"]
        text = self.render(records=records, selection={"simple_python": 2, "irrelevance": 2})
        self.assertNotIn("Incomplete run", text)
        self.assertNotIn("Sampled run", text)

    def test_a_cap_above_the_category_size_is_a_maximum(self) -> None:
        records = [record("openai", f"a{i}", "simple_python", "pass", (1, 1)) for i in range(400)]
        text = report.render(manifest([DONE], sample_size=401, categories=("simple_python",),
                                      selection={"simple_python": 400}), "openai", records, RATES)
        self.assertIn("at most 401 case(s) per category", text)
        self.assertIn("`simple_python` 400", text)
        self.assertIn("whole of each was taken", text)
        self.assertNotIn("Incomplete run", text)
        self.assertNotIn("not necessarily", text)

    def test_legacy_files_disclose_that_completeness_is_unknown(self) -> None:
        records = [record("openai", "a1", "simple_python", "pass", (1, 1))]
        text = report.render(manifest([DONE], sample_size=2, selection=None), "openai", records, RATES)
        self.assertIn("**Completeness unknown.**", text)
        self.assertIn("no record exists for `irrelevance`", text)
        self.assertNotIn("Incomplete run", text)

    def test_the_command_reads_only_the_run_directory_and_the_rates_file(self) -> None:
        directory = Path(tempfile.mkdtemp())
        (directory / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in RECORDS))
        (directory / "run.json").write_text(json.dumps(manifest([DONE])))
        rates = directory / "rates.json"
        rates.write_text(json.dumps({"models": RATES}))
        out = directory / "reports"
        with mock.patch("socket.socket.connect", side_effect=AssertionError("no network")):
            self.assertEqual(report.main([str(directory), "--rates", str(rates), "--output-dir", str(out)]), 0)
        self.assertEqual(sorted(p.name for p in out.iterdir()),
                         ["report-anthropic-claude-unpriced.md", "report-openai-gpt-known.md"])


class RatesFileTests(unittest.TestCase):
    def test_entries_are_those_of_the_brief(self) -> None:
        rates = report.load_rates(DATA_DIR / "rates.json")
        self.assertEqual(set(rates), {"gpt-6-sol", "claude-opus-5-5"})
        self.assertEqual((rates["gpt-6-sol"]["input"], rates["gpt-6-sol"]["output"]), (2.0, 10.0))
        self.assertEqual((rates["claude-opus-5-5"]["input"], rates["claude-opus-5-5"]["output"]), (4.0, 20.0))
        self.assertEqual(rates["gpt-6-sol"]["page"], "https://developers.openai.com/api/docs/pricing")
        self.assertEqual(rates["claude-opus-5-5"]["page"], "https://platform.claude.com/docs/en/about-claude/pricing")
        for rate in rates.values():
            self.assertEqual(rate["read_on"], "2026-11-23")


if __name__ == "__main__":
    unittest.main()
