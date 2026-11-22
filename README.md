# benchmark-loop-agent

Runs one pinned, single-turn Python function-calling case from the
[Berkeley Function Calling Leaderboard (BFCL)](https://github.com/ShishirPatil/gorilla)
through the OpenAI and Anthropic APIs, scores each returned tool call with
BFCL's own AST checker, and prints one JSON record per provider. A returned
call is only compared with the expected answer. It is never executed.

## Install

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/). The project has no
runtime dependencies (HTTP uses the standard library).

```sh
uv sync --locked
```

## Run

Model IDs are configuration and have no default. API keys are read from the
environment at run time and are never written to records or logs.

```sh
export OPENAI_API_KEY=...        OPENAI_MODEL=<openai model id>
export ANTHROPIC_API_KEY=...     ANTHROPIC_MODEL=<anthropic model id>

uv run --locked python -m benchmark_loop_agent                      # both providers
uv run --locked python -m benchmark_loop_agent --provider openai    # only one
```

Records go to stdout as JSON Lines (one object per line); a one-line summary
per provider goes to stderr.

### Exit code

| Code | Meaning |
|------|---------|
| 0 | every selected provider passed |
| 1 | at least one `fail`, none `unscored` |
| 2 | bad command-line usage (argparse) |
| 3 | at least one provider `unscored` (takes precedence over `fail`) |

## Record

| Field | Meaning |
|-------|---------|
| `provider`, `requested_model` | provider name and the model ID from `*_MODEL` (`null` if unset) |
| `actual_model` | model name as the response reports it (`null` if no response) |
| `case_id`, `dataset_revision`, `scorer_revision` | what was run and the pinned sources |
| `returned_calls` | tool calls as `{function: {param: value}}`; `null` when unscored. A non-finite number (e.g. `1e400`) is written as `{"unrepresentable_number": "Infinity"}` so the line stays strict JSON |
| `outcome` | `pass`, `fail` (response arrived; call wrong or missing) or `unscored` (API call failed, including a missing key or model) |
| `reasons` | why it failed or was not scored; empty on pass |
| `latency_seconds` | request time; `null` if no request was made |
| `input_tokens`, `output_tokens` | usage as the response reports it, else `null` |

One provider failing never changes or prevents the other's record.

## Pinned case and revisions

- Case: `simple_python_0` (BFCL v4 `simple_python`): "Find the area of a triangle
  with a base of 10 units and height of 5 units."
- Dataset and scorer revision: `ShishirPatil/gorilla` commit
  `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`.
- Scorer: `ast_checker.py` and the files it imports are copied unmodified into
  `vendor/` (listed in `NOTICE`, licence in `vendor/LICENSE-gorilla`). The one
  exception is `vendor/bfcl_eval/constants/model_config.py`, a small stand-in
  written here, because BFCL's real module imports every supported model SDK.
  The checker reads it only for function names containing ".", which this case
  does not have.
- The model-visible part (`data/simple_python_0.case.json`) and the expected
  answer (`data/simple_python_0.answer.json`) are separate files. The answer is
  loaded only by the scoring step, after the model has replied.

## Tests

Offline, no network and no API keys:

```sh
uv run --locked python -m unittest discover -s tests -v
```

## Licence

Apache 2.0, see `LICENSE`. BFCL material is Apache 2.0 too; see `NOTICE`.
