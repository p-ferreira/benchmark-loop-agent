"""Compare two run directories case by case, per provider.

Only cases both runs selected are compared, and a case is never paired across
providers. A case is paired when both runs hold a scored (pass or fail) record
for it; every other compared case is counted, per run, as unscored or without a
record, so the paired counts and those lines account for every compared case.
The cases a run selected are the ones its parameters select, checked against
the digest ``run.json`` recorded.
"""

from collections import Counter
from pathlib import Path
from typing import Any

from .categories import CATEGORIES
from .comparison import OVERALL
from .failures import FAILURE_CLASSES, UnknownCase, failure_class
from .sampling import select_cases
from .store import RECORDS_FILE, MANIFEST_FILE, read_manifest, read_records, selection_fingerprint

PASS = "pass"


class Run:
    """One run directory: its manifest, its records by provider and case, and the cases it selected."""

    def __init__(self, directory: Path) -> None:
        self.name = str(directory)
        manifest = read_manifest(directory)
        if manifest is None:
            raise ValueError(f"{directory / MANIFEST_FILE} not found: not a run directory")
        self.manifest = manifest
        params = manifest["parameters"]
        cases = select_cases(tuple(params["categories"]), params["sample_size"], params["seed"], params.get("split"))
        self.categories = {case.case_id: case.category for case in cases}
        recorded = manifest.get("selection_fingerprint")
        if recorded is not None and recorded != selection_fingerprint(self.categories):
            raise ValueError(f"{self.name} selected other cases than its parameters select now "
                             "(the split file or the dataset changed since)")
        rows = read_records(directory / RECORDS_FILE)
        if recorded is None and {r["case_id"] for r in rows} - set(self.categories):
            raise ValueError(f"{self.name} holds records for cases its parameters do not select")
        self.records = {(r["provider"], r["case_id"]): r for r in rows}

    @property
    def providers(self) -> list[str]:
        return list(self.manifest["parameters"]["providers"])

    def model(self, provider: str) -> str | None:
        return self.manifest["parameters"]["models"].get(provider)

    def instruction(self, provider: str) -> dict[str, Any] | None:
        return (self.manifest["parameters"].get("instructions") or {}).get(provider)


def _outcome(record: dict[str, Any] | None) -> str | None:
    """``pass``, a failure class, or ``None`` when the case is unscored or has no record."""
    if record is None or record["outcome"] not in ("pass", "fail"):
        return None
    return PASS if record["outcome"] == "pass" else failure_class(record)


def compare_provider(a: Run, b: Run, provider: str) -> dict[str, Any]:
    """Counts per category and overall for one provider shared by both runs."""
    both = sorted(set(a.categories) & set(b.categories))
    result: dict[str, Any] = {
        "only_a": len(set(a.categories) - set(b.categories)),
        "only_b": len(set(b.categories) - set(a.categories)),
        "compared": len(both),
        "rows": {},
    }
    categories = [c for c in CATEGORIES if any(a.categories[i] == c for i in both)]
    for key in [*categories, OVERALL]:
        ids = [i for i in both if key == OVERALL or a.categories[i] == key]
        row: dict[str, Any] = {"compared": len(ids), "paired": 0, "only_a": 0, "only_b": 0, "both_pass": 0, "both_fail": 0,
                               "unscored_a": 0, "unscored_b": 0, "no_record_a": 0, "no_record_b": 0, "not_paired": 0,
                               "moves": Counter()}
        for case_id in ids:
            ra, rb = a.records.get((provider, case_id)), b.records.get((provider, case_id))
            for side, record in (("a", ra), ("b", rb)):
                if record is None:
                    row[f"no_record_{side}"] += 1
                elif record["outcome"] not in ("pass", "fail"):
                    row[f"unscored_{side}"] += 1
            oa, ob = _outcome(ra), _outcome(rb)
            if oa is None or ob is None:
                row["not_paired"] += 1
                continue
            row["paired"] += 1
            if oa == PASS and ob == PASS:
                row["both_pass"] += 1
                continue
            if oa == PASS:  # A passed, B did not
                row["only_a"] += 1
            elif ob == PASS:
                row["only_b"] += 1
            else:
                row["both_fail"] += 1
            row["moves"][(oa, ob)] += 1
        result["rows"][key] = row
    return result


def compare_runs(a: Run, b: Run) -> dict[str, dict[str, Any]]:
    """One comparison per provider both runs hold; raises ``ValueError`` when nothing can be compared."""
    shared = [p for p in a.providers if p in b.providers]
    if not shared:
        raise ValueError(f"{a.name} and {b.name} share no provider")
    if not set(a.categories) & set(b.categories):
        raise ValueError(f"{a.name} and {b.name} selected no case in common")
    try:
        return {provider: compare_provider(a, b, provider) for provider in shared}
    except UnknownCase as error:
        raise ValueError(f"the expected answer of {error} cannot be found, so its failure class is unknown") from None


def _instruction_text(digest: dict[str, Any] | None) -> str:
    return f"sha256 `{digest['sha256']}`, {digest['bytes']} bytes" if digest else "none"


def render_comparison(a: Run, b: Run, provider: str, table: dict[str, Any]) -> str:
    """Markdown for one provider's comparison."""
    out = [f"# Comparison of two runs ({provider})", "",
           "Run A and run B are compared case by case on the cases both selected; a case is never paired "
           "with another provider's. A case is paired when both runs scored it (pass or fail).", "",
           "| Run | Directory | Model | Instruction |", "| --- | --- | --- | --- |"]
    for label, run in (("A", a), ("B", b)):
        out.append(f"| {label} | `{run.name}` | `{run.model(provider) or 'model not set'}` | {_instruction_text(run.instruction(provider))} |")
    out += ["", f"* Cases both runs selected (compared): {table['compared']}",
            f"* Cases only A selected: {table['only_a']}", f"* Cases only B selected: {table['only_b']}", "",
            "## Passes", "",
            "| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    label = lambda key: "**Overall**" if key == OVERALL else f"`{key}`"  # noqa: E731
    for key, r in table["rows"].items():
        out.append(f"| {label(key)} | {r['compared']} | {r['paired']} | {r['only_a']} | {r['only_b']} | "
                   f"{r['both_pass']} | {r['both_fail']} | {r['not_paired']} |")
    out += ["", "## Cases not paired", "",
            "A case that is unscored, or has no record, in a run is not paired. It is counted below for each "
            "run in which that is so; a case in this state in both runs is counted in both lines, and "
            "**Not paired** above counts it once, so Paired and Not paired add up to Compared.", "",
            "| Category | A unscored | A no record | B unscored | B no record | Not paired |",
            "| --- | --- | --- | --- | --- | --- |"]
    for key, r in table["rows"].items():
        out.append(f"| {label(key)} | {r['unscored_a']} | {r['no_record_a']} | {r['unscored_b']} | {r['no_record_b']} | {r['not_paired']} |")
    out += ["", "## Movement between failure classes", "",
            "Paired cases that failed in both runs or changed outcome, by A's class (or pass) and B's. "
            "The classes are " + ", ".join(f"`{c}`" for c in FAILURE_CLASSES) + ". Only counts above zero are listed.", "",
            "| Category | In A | In B | Cases |", "| --- | --- | --- | --- |"]
    order = [PASS, *FAILURE_CLASSES]
    for key, r in table["rows"].items():
        for (oa, ob), n in sorted(r["moves"].items(), key=lambda item: (order.index(item[0][0]), order.index(item[0][1]))):
            out.append(f"| {label(key)} | `{oa}` | `{ob}` | {n} |")
    if not any(r["moves"] for r in table["rows"].values()):
        out.append("| (none) | | | 0 |")
    return "\n".join(out) + "\n"


def build_comparison(dir_a: Path, dir_b: Path, output_dir: Path) -> list[Path]:
    """Write one comparison file per shared provider."""
    a, b = Run(dir_a), Run(dir_b)
    tables = compare_runs(a, b)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for provider, table in tables.items():
        path = output_dir / f"compare-{provider}.md"
        path.write_text(render_comparison(a, b, provider, table))
        written.append(path)
    return written
