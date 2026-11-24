"""The comparison figure, --split in the runner, and the repeated-run report."""

import json
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from benchmark_loop_agent import report
from benchmark_loop_agent.batch import run_batch
from benchmark_loop_agent.repeats import spreads
from benchmark_loop_agent.sampling import select_cases
from benchmark_loop_agent.split import PARTS, part_case_ids
from tests.support import FakeSend, environment
from tests.test_batch import ENV, parameters, perfect
from tests.test_report import RATES, manifest, record


def run(records, selection, **kw):
    m = manifest([], categories=("simple_python",), selection=selection, **kw)
    return report.render(m, "openai", records, RATES)


class FigureTests(unittest.TestCase):
    def test_a_pass_and_an_unscored_case_give_50_percent_but_accuracy_stays_100(self) -> None:
        text = run([record("openai", "a1", "simple_python", "pass"), record("openai", "a2", "simple_python", "unscored", None)],
                   {"simple_python": 2})
        self.assertIn("| `simple_python` | 100.0% (1/1) | 1 | 0 | 1 |", text)
        self.assertIn("| `simple_python` | 50.0% (1/2) | 2 | 1 | 0 | 1 | 0 |", text)
        self.assertIn("| **Overall** | **50.0% (1/2)** | 2 | 1 | 0 | 1 | 0 |", text)

    def test_a_selected_case_with_no_record_counts_against_the_figure(self) -> None:
        text = run([record("openai", "a1", "simple_python", "pass")], {"simple_python": 2})
        self.assertIn("| `simple_python` | 100.0% (1/1) | 1 | 0 | 0 |", text)
        self.assertIn("| `simple_python` | 50.0% (1/2) | 2 | 1 | 0 | 0 | 1 |", text)

    def test_a_run_without_the_recorded_selection_has_no_figure(self) -> None:
        text = run([record("openai", "a1", "simple_python", "pass")], None)
        self.assertIn("Comparison figure: unavailable", text)
        self.assertNotIn("50.0%", text)
        self.assertNotIn("100.0% (1/1) | 1 | 0 | 0 | 0 |", text)
        self.assertIn("| `simple_python` | 100.0% (1/1) | 1 | 0 | 0 |", text)  # accuracy unchanged

    def test_a_split_run_names_its_part_and_one_without_does_not(self) -> None:
        m = manifest([], categories=("simple_python",))
        m["parameters"]["split"] = "held-out"
        self.assertIn("Part: `held-out`", report.render(m, "openai", [], RATES))
        self.assertNotIn("Part:", run([], {"simple_python": 0}))


class SplitRunTests(unittest.TestCase):
    def test_split_selects_only_that_parts_cases(self) -> None:
        for part in PARTS:
            ids = part_case_ids(part)
            chosen = select_cases(("simple_python", "irrelevance"), 5, 3, part)
            self.assertEqual(len(chosen), 10)
            self.assertTrue(all(c.case_id in ids for c in chosen))
        self.assertEqual(len(select_cases(("simple_java",), None, 0, "validation")), 20)
        self.assertEqual(len(select_cases(("simple_java",), None, 0)), 100)

    def test_part_is_recorded_and_a_resume_with_another_part_is_refused(self) -> None:
        directory = Path(tempfile.mkdtemp()) / "out"
        run_batch(directory, parameters(split="validation", sample_size=2), ENV, FakeSend(perfect), sleep=lambda s: None)
        saved = json.loads((directory / "run.json").read_text())
        self.assertEqual(saved["parameters"]["split"], "validation")
        ids = part_case_ids("validation")
        self.assertTrue(all(json.loads(l)["case_id"] in ids for l in (directory / "records.jsonl").read_text().splitlines()))
        run_batch(directory, parameters(split="validation", sample_size=2), ENV, FakeSend(perfect), sleep=lambda s: None)
        for other in ("held-out", None):
            with self.assertRaises(ValueError):
                run_batch(directory, parameters(split=other, sample_size=2), ENV, FakeSend(perfect), sleep=lambda s: None)

    def test_a_resume_after_the_selection_changed_is_refused_before_anything_changes(self) -> None:
        directory = Path(tempfile.mkdtemp()) / "out"
        params = parameters(sample_size=1, categories=("simple_python",), providers=("openai",))
        run_batch(directory, params, ENV, FakeSend(perfect), sleep=lambda s: None)
        before = {n: (directory / n).read_bytes() for n in ("run.json", "records.jsonl")}
        other = [c for c in select_cases(("simple_python",), None, 0) if c.case_id not in before["records.jsonl"].decode()][:1]
        with unittest.mock.patch("benchmark_loop_agent.batch.select_cases", return_value=other):
            with self.assertRaisesRegex(ValueError, "other cases"):
                run_batch(directory, params, ENV, FakeSend(perfect), sleep=lambda s: None)
        self.assertEqual(before, {n: (directory / n).read_bytes() for n in before})

    def test_a_count_only_manifest_with_records_of_other_cases_is_refused_before_anything_changes(self) -> None:
        directory = Path(tempfile.mkdtemp()) / "out"
        params = parameters(sample_size=1, categories=("simple_python",), providers=("openai",))
        run_batch(directory, params, ENV, FakeSend(perfect), sleep=lambda s: None)
        saved = json.loads((directory / "run.json").read_text())
        del saved["selection_fingerprint"]  # the shape the preceding commit wrote
        (directory / "run.json").write_text(json.dumps(saved, indent=2) + "\n")
        before = {n: (directory / n).read_bytes() for n in ("run.json", "records.jsonl")}
        other = [c for c in select_cases(("simple_python",), None, 0) if c.case_id not in before["records.jsonl"].decode()][:1]
        with unittest.mock.patch("benchmark_loop_agent.batch.select_cases", return_value=other):
            with self.assertRaisesRegex(ValueError, "no longer select"):
                run_batch(directory, params, ENV, FakeSend(perfect), sleep=lambda s: None)
        self.assertEqual(before, {n: (directory / n).read_bytes() for n in before})
        run_batch(directory, params, ENV, FakeSend(perfect), sleep=lambda s: None)  # unchanged selection still resumes

    def test_a_run_without_split_saves_no_split_key(self) -> None:
        directory = Path(tempfile.mkdtemp()) / "out"
        run_batch(directory, parameters(sample_size=1), ENV, FakeSend(perfect), sleep=lambda s: None)
        self.assertNotIn("split", json.loads((directory / "run.json").read_text())["parameters"])


def fixture_run(passes, selected=("a1", "a2", "a3", "a4"), model="gpt-known", split=None, selection="default", ids="fp"):
    records = [record("openai", c, "simple_python", "pass" if c in passes else "fail") for c in selected]
    m = manifest([], categories=("simple_python",), selection={"simple_python": len(selected)} if selection == "default" else selection)
    m["parameters"]["providers"] = ["openai"]
    m["selection_fingerprint"] = ids
    m["parameters"]["models"] = {"openai": model}
    if split:
        m["parameters"]["split"] = split
    return m, records


class RepeatTests(unittest.TestCase):
    def test_lowest_highest_and_mean_over_the_runs(self) -> None:
        runs = [fixture_run({"a1"}), fixture_run({"a1", "a2", "a3"}), fixture_run({"a1", "a2"})]
        table = spreads(["r1", "r2", "r3"], [m for m, _ in runs], [r for _, r in runs])["openai"]
        for key in ("simple_python", "overall"):
            self.assertEqual((table[key]["lowest"], table[key]["highest"], table[key]["runs"]), (0.25, 0.75, 3))
            self.assertAlmostEqual(table[key]["mean"], 0.5)

    def test_command_writes_the_spread_report(self) -> None:
        directory = Path(tempfile.mkdtemp())
        dirs = []
        for i, passes in enumerate(({"a1"}, {"a1", "a2", "a3"})):
            m, recs = fixture_run(passes)
            (directory / f"r{i}").mkdir()
            (directory / f"r{i}" / "run.json").write_text(json.dumps(m))
            (directory / f"r{i}" / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs))
            dirs.append(str(directory / f"r{i}"))
        self.assertEqual(report.main([*dirs, "--output-dir", str(directory / "out")]), 0)
        text = next((directory / "out").glob("repeated-*.md")).read_text()
        self.assertIn("| **Overall** | 25.0% | 75.0% | 50.0% | 2 |", text)

    def test_runs_of_different_configurations_are_refused_naming_the_difference(self) -> None:
        a, b = fixture_run({"a1"}), fixture_run({"a1"}, model="other-model")
        with self.assertRaisesRegex(ValueError, "models"):
            spreads(["r1", "r2"], [a[0], b[0]], [a[1], b[1]])
        c = fixture_run({"a1"}, split="held-out")
        with self.assertRaisesRegex(ValueError, "split"):
            spreads(["r1", "r2"], [a[0], c[0]], [a[1], c[1]])

    def test_runs_that_selected_other_cases_are_refused(self) -> None:
        a, b = fixture_run({"a1"}), fixture_run({"a1"}, ids="other")
        with self.assertRaisesRegex(ValueError, "cases selected"):
            spreads(["r1", "r2"], [a[0], b[0]], [a[1], b[1]])

    def test_a_reordered_category_or_provider_list_is_the_same_configuration(self) -> None:
        a, b = fixture_run({"a1"}), fixture_run({"a1"})
        a[0]["parameters"]["categories"] = ["simple_python", "irrelevance"]
        b[0]["parameters"]["categories"] = ["irrelevance", "simple_python"]
        for m, _ in (a, b):
            m["selection"]["irrelevance"] = 0
        self.assertEqual(spreads(["r1", "r2"], [a[0], b[0]], [a[1], b[1]])["openai"]["overall"]["runs"], 2)

    def test_runs_with_no_selected_cases_are_refused(self) -> None:
        a, b = fixture_run(set(), selected=()), fixture_run(set(), selected=())
        with self.assertRaisesRegex(ValueError, "r1.*undefined"):
            spreads(["r1", "r2"], [a[0], b[0]], [a[1], b[1]])

    def test_complete_older_runs_are_compared_by_their_recorded_cases(self) -> None:
        a, b = fixture_run({"a1"}), fixture_run({"a1", "a2"})
        for m, _ in (a, b):
            del m["selection_fingerprint"]
        self.assertEqual(spreads(["r1", "r2"], [a[0], b[0]], [a[1], b[1]])["openai"]["overall"]["runs"], 2)
        c = fixture_run({"a1"}, selected=("a1", "a2", "a3", "x9"))
        del c[0]["selection_fingerprint"]
        with self.assertRaisesRegex(ValueError, "cases selected"):
            spreads(["r1", "r2"], [a[0], c[0]], [a[1], c[1]])
        d = fixture_run({"a1"}, selected=("a1", "a2"))  # incomplete: two records for four selected
        d[0]["selection"] = {"simple_python": 4}
        del d[0]["selection_fingerprint"]
        with self.assertRaisesRegex(ValueError, "does not record which cases"):
            spreads(["r1", "r2"], [a[0], d[0]], [a[1], d[1]])

    def test_a_run_with_an_unavailable_figure_is_refused(self) -> None:
        a, b = fixture_run({"a1"}), fixture_run({"a1"}, selection=None)
        with self.assertRaisesRegex(ValueError, "unavailable"):
            spreads(["r1", "r2"], [a[0], b[0]], [a[1], b[1]])


if __name__ == "__main__":
    unittest.main()
