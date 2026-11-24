"""The thirteen single-turn BFCL categories and how each one is judged."""

# BFCL's SINGLE_TURN_CATEGORY at the pinned commit
# (bfcl_eval/constants/category_mapping.py), in BFCL's order.
CATEGORIES: tuple[str, ...] = (
    "simple_python",
    "simple_java",
    "simple_javascript",
    "multiple",
    "parallel",
    "parallel_multiple",
    "irrelevance",
    "live_simple",
    "live_multiple",
    "live_parallel",
    "live_parallel_multiple",
    "live_irrelevance",
    "live_relevance",
)


def is_js(category: str) -> bool:
    """BFCL's ``is_js``: the name contains "javascript"."""
    return "javascript" in category


def is_java(category: str) -> bool:
    """BFCL's ``is_java``: the name contains "java" and is not JavaScript."""
    return "java" in category and not is_js(category)


def is_irrelevance(category: str) -> bool:
    """Irrelevance categories pass when the model makes no function call."""
    return "irrelevance" in category


def is_relevance_or_irrelevance(category: str) -> bool:
    """These categories have no expected-answer file; BFCL only checks for a call."""
    return "relevance" in category  # also matches "irrelevance", as in BFCL
