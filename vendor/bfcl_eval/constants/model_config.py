"""Stand-in for BFCL's ``bfcl_eval.constants.model_config`` (NOT copied from BFCL).

BFCL's real module imports every model handler it supports, which pulls in
dozens of SDKs. ``ast_checker.py`` only reads ``MODEL_CONFIG_MAPPING`` while
normalising a function name that contains a ".", and the pinned case's
function name has none, so an empty mapping is never consulted. If a future
case uses a dotted name, the checker raises ``KeyError`` instead of silently
mis-scoring, which is the behaviour we want.
"""

MODEL_CONFIG_MAPPING: dict = {}
