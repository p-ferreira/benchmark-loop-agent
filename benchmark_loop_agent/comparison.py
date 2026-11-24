"""The comparison figure: passes divided by the cases the run selected.

Accuracy leaves unscored cases out, so a run that failed to score half of its
cases can look perfect. This figure keeps every selected case in the
denominator, so an unscored case, or one with no record at all (an interrupted
run), counts against it. The selection is read from ``run.json`` only: when it
was not recorded, the denominator is unknown and no figure is given.
"""

from typing import Any, Sequence

OVERALL = "overall"
UNAVAILABLE = "unavailable"


def selected_counts(manifest: dict[str, Any]) -> dict[str, int] | None:
    """Cases selected per category as ``run.json`` recorded them, or ``None`` for an older run."""
    selection = manifest.get("selection")
    return dict(selection) if isinstance(selection, dict) else None


def comparison_counts(manifest: dict[str, Any], records: Sequence[dict[str, Any]],
                      provider: str) -> dict[str, tuple[int, int]] | None:
    """``(passes, selected)`` per category and overall for one provider, or ``None`` when unavailable."""
    selection = selected_counts(manifest)
    if selection is None:
        return None
    categories = manifest["parameters"]["categories"]
    mine = [r for r in records if r["provider"] == provider]
    counts = {c: (sum(1 for r in mine if r["category"] == c and r["outcome"] == "pass"), selection.get(c, 0))
              for c in categories}
    counts[OVERALL] = (sum(p for p, _ in counts.values()), sum(n for _, n in counts.values()))
    return counts


def format_figure(passed: int, selected: int) -> str:
    return f"{100 * passed / selected:.1f}% ({passed}/{selected})" if selected else "n/a (no cases selected)"
