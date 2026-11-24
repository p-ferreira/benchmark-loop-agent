"""The spread of the comparison figure over repeated runs of one configuration.

Model output varies from run to run, so one run's figure is one draw. Runs
are only combined when everything that decides what is run and by whom is the
same; a figure from a run with no recorded selection is refused, not guessed.
"""

from statistics import fmean
from typing import Any, Sequence

from .comparison import OVERALL, comparison_counts
from .store import selection_fingerprint

CONFIGURATION_KEYS = ("providers", "models", "split", "categories", "sample_size", "seed")


def configuration(manifest: dict[str, Any]) -> dict[str, Any]:
    """What must match between runs; ``split`` is ``None`` for a run without a part (or an older one)."""
    params = manifest["parameters"]
    return {key: params.get(key) for key in CONFIGURATION_KEYS}


# These lists name a set: sampling seeds each category on its own, so their order changes nothing.
UNORDERED_KEYS = ("providers", "categories")


def _comparable(key: str, value: Any) -> Any:
    return sorted(value) if key in UNORDERED_KEYS and isinstance(value, list) else value


def check_same_configuration(names: Sequence[str], manifests: Sequence[dict[str, Any]]) -> None:
    """Refuse runs whose configurations differ, naming the first difference found."""
    first = configuration(manifests[0])
    for name, manifest in zip(names[1:], manifests[1:]):
        other = configuration(manifest)
        for key in CONFIGURATION_KEYS:
            if _comparable(key, other[key]) != _comparable(key, first[key]):
                raise ValueError(f"{name} differs from {names[0]} in {key}: {other[key]!r} instead of {first[key]!r}")


def spread(runs: Sequence[dict[str, tuple[int, int]]]) -> dict[str, dict[str, Any]]:
    """Lowest, highest and mean figure and the number of runs, per category and overall."""
    result = {}
    for key in runs[0]:
        figures = [p / n if n else None for p, n in (run[key] for run in runs)]
        known = [f for f in figures if f is not None]
        result[key] = {"runs": len(runs), "scored_runs": len(known),
                       "lowest": min(known, default=None), "highest": max(known, default=None),
                       "mean": fmean(known) if known else None}
    return result


def _fingerprint(name: str, manifest: dict[str, Any], records: Sequence[dict[str, Any]]) -> str:
    """The recorded selection digest; for an older run, the recorded cases when they fill its whole selection."""
    if manifest.get("selection_fingerprint") is not None:
        return manifest["selection_fingerprint"]
    selection = manifest.get("selection")
    ids = {r["case_id"] for r in records}
    if isinstance(selection, dict) and len(ids) == sum(selection.values()):
        return selection_fingerprint(ids)
    raise ValueError(f"{name} does not record which cases it selected, so it cannot be compared with other runs")


def spreads(names: Sequence[str], manifests: Sequence[dict[str, Any]],
            records: Sequence[Sequence[dict[str, Any]]]) -> dict[str, dict[str, dict[str, Any]]]:
    """Per provider, the spread over the runs; raises ``ValueError`` for a refused set of runs."""
    check_same_configuration(names, manifests)
    prints = [_fingerprint(name, manifest, recs) for name, manifest, recs in zip(names, manifests, records)]
    for name, print_ in zip(names[1:], prints[1:]):
        if print_ != prints[0]:
            raise ValueError(f"{name} differs from {names[0]} in the cases selected (the split file or dataset changed)")
    result = {}
    for provider in manifests[0]["parameters"]["providers"]:
        runs = []
        for name, manifest, recs in zip(names, manifests, records):
            counts = comparison_counts(manifest, recs, provider)
            if counts is None:
                raise ValueError(f"{name} does not record the cases it selected, so its comparison figure is unavailable")
            runs.append(counts)
        if not runs[0][OVERALL][1]:
            raise ValueError(f"{names[0]} selected no cases, so the overall figure is undefined")
        result[provider] = spread(runs)
    return result


def _percent(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def render_spread(provider: str, model: str | None, split: str | None, names: Sequence[str],
                  table: dict[str, dict[str, Any]]) -> str:
    """Markdown for one provider's repeated-run figures."""
    out = [f"# Repeated runs: `{model or 'model not set'}` ({provider})", "",
           f"* Part: {split or 'every case (no --split)'}",
           f"* Runs: {len(names)} ({', '.join(f'`{n}`' for n in names)})", "",
           "The comparison figure is passes divided by the cases each run selected, so unscored and missing "
           "cases count against it. Lowest, highest and mean are over the runs; **Overall** is each run's pooled "
           "figure, not the mean of the category figures.", "",
           "| Category | Lowest | Highest | Mean | Runs |", "| --- | --- | --- | --- | --- |"]
    for key, row in table.items():
        label = "**Overall**" if key == OVERALL else f"`{key}`"
        out.append(f"| {label} | {_percent(row['lowest'])} | {_percent(row['highest'])} | {_percent(row['mean'])} | {row['runs']} |")
    return "\n".join(out) + "\n"
