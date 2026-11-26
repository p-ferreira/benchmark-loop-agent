"""The vendored τ-bench code, the pinned task set and the digest check.

``vendor/tau2_bench`` holds an unmodified copy of ``src/tau2`` from
``sierra-research/tau2-bench`` at the pinned commit, and the data files the retail and airline
text benchmarks read (see ``NOTICE``). Importing this module does not import
upstream; ``load`` does, once, and points it at the vendored data.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

UPSTREAM_REPOSITORY = "sierra-research/tau2-bench"
UPSTREAM_RELEASE = "v2.0.0"
UPSTREAM_COMMIT = "989d3285ae669e49503324bdb9981bf14fccedeb"
BENCHMARK_VERSION = "text-v1"
LANGUAGE = "en"
DOMAIN = "retail"
SUBSET_NAME = "retail_50"
# The SHA-256 of ``retail_50.json``, written here as well as in upstream's manifest
# (``benchmarks/text.json``), so that neither file alone can change the task set.
SUBSET_SHA256 = "dc7490f023d1bf9c345edf9c37a8e658298ac3a5be884e012bfb271b3678f2be"
SUBSET_SIZE = 50
# The domains bla runs, each with its frozen subset and the digest of that subset's file (the one in upstream's manifest too).
DOMAINS: dict[str, tuple[str, str]] = {
    "retail": (SUBSET_NAME, SUBSET_SHA256),
    "airline": ("airline_50", "055b5d4f8a0a09d297226ee1fe6f2fb01115ac0953e705388fd3dc34b46998db"),
}
AGENT_NAME = "bla_agent"  # the name bla registers its agent under in upstream's registry

VENDOR_ROOT = Path(__file__).resolve().parents[2] / "vendor" / "tau2_bench"


class TaskSetError(ValueError):
    """The task set on disk is not the pinned one; nothing may run."""


def subset_of(domain: str) -> tuple[str, str]:
    """The subset name and pinned digest of a domain."""
    if domain not in DOMAINS:
        raise TaskSetError(f"unknown domain {domain!r}; bla runs {', '.join(DOMAINS)}")
    return DOMAINS[domain]


def identity(domain: str = DOMAIN) -> dict[str, Any]:
    """What ``run.json`` records about the upstream."""
    return {"repository": UPSTREAM_REPOSITORY, "release": UPSTREAM_RELEASE, "commit": UPSTREAM_COMMIT,
            "benchmark": BENCHMARK_VERSION, "language": LANGUAGE, "domain": domain}


def pinned_task_ids(root: Path | None = None, domain: str = DOMAIN) -> list[str]:
    """The 50 task identifiers of the domain's subset, in upstream's order, after the digest check.

    The bytes of the subset file must hash to the digest pinned here and to the one
    upstream's manifest records for the subset, and the identifiers are read from
    those very bytes. Anything else raises ``TaskSetError``.
    """
    subset_name, subset_sha256 = subset_of(domain)
    data = (root or VENDOR_ROOT) / "data" / "tau2"
    try:
        payload = (data / "task_subsets" / f"{subset_name}.json").read_bytes()
        manifest = json.loads((data / "benchmarks" / "text.json").read_text())
    except (OSError, ValueError) as error:
        raise TaskSetError(f"cannot read the task set or upstream's manifest: {error}") from None
    recorded = manifest.get("task_subsets", {}).get(domain, {})
    if manifest.get("benchmark_version") != BENCHMARK_VERSION or recorded.get("name") != subset_name:
        raise TaskSetError(f"upstream's manifest does not name {subset_name} for {domain} in {BENCHMARK_VERSION}")
    actual = hashlib.sha256(payload).hexdigest()
    if not (actual == subset_sha256 == recorded.get("sha256")):
        raise TaskSetError(
            f"{subset_name} hashes to {actual}, but the pinned digest is {subset_sha256} "
            f"and upstream's manifest records {recorded.get('sha256')}; refusing to run")
    ids = json.loads(payload)["task_ids"]
    if len(ids) != SUBSET_SIZE or len(set(ids)) != SUBSET_SIZE or not all(isinstance(i, str) for i in ids):
        raise TaskSetError(f"{subset_name} does not hold {SUBSET_SIZE} distinct task identifiers")
    return ids


_loaded: SimpleNamespace | None = None


def load() -> SimpleNamespace:
    """Import the vendored upstream (once) and return the pieces bla uses."""
    global _loaded
    if _loaded is not None:
        return _loaded
    os.environ["TAU2_DATA_DIR"] = str(VENDOR_ROOT / "data")  # the pinned data, whatever the environment says
    os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")  # litellm's own price list is not used: no fetch at import
    sys.path.insert(0, str(VENDOR_ROOT / "src"))
    try:
        from loguru import logger
    except ImportError:
        raise RuntimeError(
            "the retail benchmark needs upstream's dependencies and Python 3.12: run it in the environment "
            "that 'uv sync --locked' builds (the 'tau' dependency group); see the README") from None
    logger.remove()
    # Upstream's own default log level. Its price lookup logs an error for a model litellm has no price for
    # (every model newer than the pinned litellm); bla prices from its own rates file, so that line is dropped.
    logger.add(sys.stderr, level="ERROR", filter=lambda record: "isn't mapped yet" not in record["message"])
    from tau2.config import DEFAULT_BENCHMARK_USER_ARGS
    from tau2.data_model.simulation import TerminationReason, TextRunConfig
    from tau2.registry import registry
    from tau2.runner import simulation as simulation_module
    from tau2.runner.batch import _load_run_tasks, run_single_task
    from tau2.runner.build import agent_domain_policy, build_environment
    from tau2.runner.presets import binding_revision, load_cell_language, load_manifest
    from tau2.task_subsets.store import load_subset, verify_subset
    from tau2.utils import llm_utils
    _loaded = SimpleNamespace(
        DEFAULT_BENCHMARK_USER_ARGS=DEFAULT_BENCHMARK_USER_ARGS, TerminationReason=TerminationReason, TextRunConfig=TextRunConfig,
        registry=registry, simulation_module=simulation_module, load_run_tasks=_load_run_tasks, run_single_task=run_single_task,
        agent_domain_policy=agent_domain_policy, build_environment=build_environment, binding_revision=binding_revision,
        load_cell_language=load_cell_language, load_manifest=load_manifest, load_subset=load_subset, verify_subset=verify_subset,
        llm_utils=llm_utils)
    return _loaded


def prepare(task_ids: list[str], agent_model: str, customer_route: str, trials: int, seed: int,
            agent: str = AGENT_NAME, domain: str = DOMAIN) -> tuple[Any, dict[str, Any]]:
    """Upstream's run config for the ``text-v1`` English cell of the domain, and its tasks by canonical identifier.

    This does for one cell what upstream's ``resolve_configs`` does for each cell of a released
    benchmark (its own ``load_cell_language``, the binding revision its manifest records, the
    customer defaults of a released benchmark); the other languages and domains of the manifest
    are not vendored and not run. The agent is ``AGENT_NAME``, which ``agent.register_agent`` registers (tests pass ``llm_agent``, upstream's own).
    """
    subset_name, _ = subset_of(domain)
    upstream = load()
    subset = upstream.load_subset(subset_name)  # upstream's own checks of the frozen subset
    upstream.verify_subset(subset)
    if list(subset.task_ids) != pinned_task_ids(domain=domain):
        raise TaskSetError("upstream's loader and the pinned file disagree on the task identifiers")
    manifest, _ = upstream.load_manifest("text")
    cell = next(c for c in manifest.cells if c.language == LANGUAGE and c.domain == domain)
    loaded = upstream.load_cell_language(LANGUAGE, domain, "text")
    if upstream.binding_revision(loaded) != cell.binding_revision:
        raise TaskSetError(f"the vendored English {domain} binding is not the one upstream's manifest records")
    local = {meta.canonical_task_id: task_id for task_id, meta in loaded.metadata.items()}
    missing = [i for i in task_ids if i not in local]
    if missing:
        raise TaskSetError(f"tasks missing from upstream's {domain} data: {', '.join(missing)}")
    template = upstream.TextRunConfig(agent=agent, llm_agent=agent_model, llm_user=customer_route,
                                      llm_args_user=dict(upstream.DEFAULT_BENCHMARK_USER_ARGS), num_trials=trials, seed=seed)
    values = template.template_values()
    values.update(domain=domain, language=LANGUAGE, task_set_name=None, task_split_name=None,
                  task_ids=[local[i] for i in task_ids], num_tasks=None, num_trials=trials, auto_resume=False,
                  save_to=None, benchmark=None, pack_extension=loaded.pack_extension, language_artifacts=loaded.artifact_pins)
    config = upstream.TextRunConfig.model_validate(values)
    by_local = {task.id: task for task in upstream.load_run_tasks(config)}
    return config, {i: by_local[local[i]] for i in task_ids}
