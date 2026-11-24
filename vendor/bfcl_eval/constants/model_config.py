"""Stand-in for BFCL's ``bfcl_eval.constants.model_config`` (NOT copied from BFCL).

BFCL's real module imports every model handler it supports, which pulls in
dozens of SDKs. ``ast_checker.py`` reads exactly one thing from it:
``MODEL_CONFIG_MAPPING[model].underscore_to_dot``, used to decide whether a
function name containing "." is compared in its "_" form. At the pinned
commit BFCL sets ``underscore_to_dot=True`` for every OpenAI and Claude model
run through native function calling (e.g. ``gpt-5.2-2025-12-11-FC`` and
``claude-opus-4-5-20251101-FC``), so one entry with that value stands in for
both providers. ``benchmark_loop_agent.scoring`` passes this entry's name to
the checker. Any other name raises ``KeyError`` rather than mis-scoring.
"""

from dataclasses import dataclass

NATIVE_FC_MODEL = "native-function-calling"


@dataclass(frozen=True)
class ModelConfig:
    """The one field of BFCL's ``ModelConfig`` that the checker reads."""

    underscore_to_dot: bool = False


MODEL_CONFIG_MAPPING: dict = {NATIVE_FC_MODEL: ModelConfig(underscore_to_dot=True)}
