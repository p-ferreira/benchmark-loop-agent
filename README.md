# benchmark-loop-agent

Runs the single-turn function-calling cases of the
[Berkeley Function Calling Leaderboard (BFCL)](https://github.com/ShishirPatil/gorilla)
through the OpenAI and Anthropic APIs, scores every returned tool call with
BFCL's own checker, and writes one record per case and provider to disk. A
returned call is only compared with the expected answer. It is never executed.
An interrupted run resumes without repeating finished cases.

## Install

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/). Requests are
made with the official `openai` and `anthropic` Python libraries.

```sh
uv sync --locked
```

## Run

Model IDs are configuration and have no default. API keys are read from the
environment at run time and are never written to records or logs.

```sh
export OPENAI_API_KEY=...        OPENAI_MODEL=<openai model id>
export ANTHROPIC_API_KEY=...     ANTHROPIC_MODEL=<anthropic model id>

# every case of every category, both providers
uv run --locked python -m benchmark_loop_agent --output-dir runs/full

# a seeded sample: 4 cases per category, one provider
uv run --locked python -m benchmark_loop_agent --output-dir runs/small \
    --sample-size 4 --seed 0 --provider openai
```

Running the same command again on the same `--output-dir` resumes the run.

### Parameters

| Option | Meaning |
|--------|---------|
| `--output-dir DIR` (required) | where `records.jsonl` and `run.json` are written |
| `--categories C [C ...]` | categories to run (default: all thirteen) |
| `--sample-size N` | cases per category, drawn with `--seed` (default: every case) |
| `--seed S` | seed for the draw (default `0`); the same seed picks the same cases, and a category's draw does not depend on which other categories run |
| `--provider P` | `openai` or `anthropic`; repeat for both (default: both) |
| `--openai-model ID`, `--anthropic-model ID` | model IDs; otherwise `OPENAI_MODEL` / `ANTHROPIC_MODEL`. No default in code: a provider without one is `unscored` |
| `--concurrency N` | requests in flight at once (default `4`) |

### Exit code

| Code | Meaning |
|------|---------|
| 0 | every case of the run passed |
| 1 | at least one `fail`, none `unscored` |
| 2 | bad command-line usage, or `--output-dir` holds a run with different parameters |
| 3 | at least one case `unscored` (takes precedence over `fail`) |

## Categories

The thirteen categories of BFCL's `SINGLE_TURN_CATEGORY` at the pinned
commit (multi-turn, web search, memory and format sensitivity are out). The
number of cases is counted from the question files in `data/questions/`; a test
checks this table against them.

| Category | Judged by | Cases |
|----------|-----------|-------|
| `simple_python` | AST checker, one call | 400 |
| `simple_java` | AST checker, one call, Java values as strings | 100 |
| `simple_javascript` | AST checker, one call, JavaScript values as strings | 50 |
| `multiple` | AST checker, one call chosen among several functions | 200 |
| `parallel` | AST checker, several calls in any order | 200 |
| `parallel_multiple` | AST checker, several calls among several functions | 200 |
| `irrelevance` | passes if the model makes no call | 240 |
| `live_simple` | AST checker, one call | 258 |
| `live_multiple` | AST checker, one call chosen among several functions | 1053 |
| `live_parallel` | AST checker, several calls in any order | 16 |
| `live_parallel_multiple` | AST checker, several calls among several functions | 24 |
| `live_irrelevance` | passes if the model makes no call | 884 |
| `live_relevance` | passes if the model makes a call | 16 |
| **Total** | | 3641 |

## Output directory

* `records.jsonl`: one JSON Lines record per case and provider, appended as
  each case finishes.
* `run.json`: the run's parameters (categories, sample size, seed, providers,
  model IDs), the dataset and scorer revisions, and for every invocation its
  number, concurrency, start time, end time and wall time. A model ID that
  contains a configured API key is refused before anything is written. A run that was
  interrupted has an invocation with no end time.

### Record

| Field | Meaning |
|-------|---------|
| `provider`, `requested_model` | provider name and the model ID that was requested (`null` if unset) |
| `actual_model` | model name as the response reports it (`null` if no response) |
| `case_id`, `category`, `dataset_revision`, `scorer_revision` | what was run and the pinned sources |
| `returned_calls` | tool calls as `{function: {param: value}}`; `null` when unscored. A non-finite number (e.g. `1e400`) is written as `{"unrepresentable_number": "Infinity"}` so the line stays strict JSON |
| `outcome` | `pass`, `fail` (response arrived; answer wrong, or the checker could not judge it, with the reason) or `unscored` (the API call failed, including a missing key or model) |
| `reasons` | why it failed or was not scored; empty on pass |
| `latency_seconds` | request time including any retry waits; `null` if no request was made |
| `input_tokens`, `output_tokens` | usage as the response reports it, else `null` |

One case's or one provider's failure never changes or prevents another record.

## Resume and retries

* A case with a `pass` or `fail` record is skipped. An `unscored` one runs
  again, and its old record is replaced, so the file keeps one record per case
  and provider. A line cut short by an interruption is dropped.
* Resuming with different parameters (categories, sample size, seed, providers
  or models) is refused, since the records would no longer belong to one run.
  Concurrency may change; each invocation records its own.
* Rate limits (429), server errors (5xx), timeouts and dropped connections are
  retried with exponential backoff (1 s, 2 s, 4 s, ... up to 30 s, plus up to
  1 s of jitter), at most 5 tries in all. The libraries' own retrying is off,
  so that number is exact. A case that still fails is `unscored` with the last
  error. Other errors (bad key, unknown model) are not retried.

## What the models are given

A model sees the case's messages and function schemas, never the expected
answer: `Case` has no field for it, the question files hold none, answers are
read from a separate file by the scoring step after the model has replied, and
a test builds the request of every case in every category to check it.

The schemas are converted the way BFCL's native function-calling handlers do
at the pinned commit; none of this is a new design (the code names the BFCL
function it follows, in `benchmark_loop_agent/tools.py`):

* **Types.** BFCL's `convert_to_tool` / `_cast_to_openai_type` map BFCL's type
  names (`dict`, `float`, `ArrayList`, ...) to JSON Schema types with the
  vendored `GORILLA_TO_OPENAPI`.
* **Language note.** BFCL's `_func_doc_language_specific_pre_processing` adds
  " Note that the provided function is in Java 8 SDK syntax." (JavaScript
  syntax / Python 3 syntax) to each function description. BFCL does this for
  every category, so the Python categories get the note too. For
  `simple_java` and `simple_javascript` it also turns every parameter into a
  string that holds the value in that language, with a note on its type, and
  drops `items` and (JavaScript) `properties` into the description text.
* **Function names.** Both providers reject "." in a tool name, so, as BFCL
  does for these models (`convert_to_tool`), "." is sent as "_". The checker
  must compare names in the same form. BFCL tells it so through
  `MODEL_CONFIG_MAPPING[model].underscore_to_dot`, which is `True` for every
  OpenAI and Claude model BFCL runs through native function calling. The
  stand-in `vendor/bfcl_eval/constants/model_config.py` therefore holds one
  entry with `underscore_to_dot=True`, and the scorer passes that entry's name
  to the checker. The stand-in is the only vendored file not copied from BFCL.
* **Messages.** As in BFCL: for OpenAI the `system` role is sent as `developer`;
  for Anthropic the system message goes in the `system` field and consecutive
  user messages are merged. A case with no functions sends no `tools`.

Differences from BFCL's own handlers, on purpose: OpenAI tools carry
`strict: false` (BFCL's schemas have optional parameters, which strict mode
rejects), no temperature is sent, and Anthropic's `max_tokens` is 4096.

## Scoring

* `simple_*`, `multiple`, `parallel*` and the `live_` versions: BFCL's
  `ast_checker` against the expected answer, with the schema as stored in the
  dataset (BFCL scores without the language note). Arguments that are not a
  JSON object are a `fail`, as a decoding failure is in BFCL. If the checker
  itself raises on an odd answer, the case is a `fail` and the reason says so.
* `irrelevance`, `live_irrelevance`, `live_relevance`: BFCL's rule from
  `eval_runner._evaluate_single_relevance_entry`. The model "made a call" if
  its output decodes to a non-empty list of calls; undecodable arguments, or
  arguments that are not an object, count as no call. Irrelevance passes
  without a call, relevance passes with one. These categories have no expected
  answers, and BFCL has no answer files for them.

## Data and revisions

- Dataset and scorer revision: `ShishirPatil/gorilla` commit
  `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`.
- `data/questions/BFCL_v4_<category>.json` and `data/answers/BFCL_v4_<category>.json`
  are BFCL's files from `berkeley-function-call-leaderboard/bfcl_eval/data/` and
  `.../data/possible_answer/`, unchanged (see `NOTICE`).
- Scorer: `ast_checker.py` and the files it imports are copied unmodified into
  `vendor/` (listed in `NOTICE`, licence in `vendor/LICENSE-gorilla`), apart
  from the stand-in described above, which exists because BFCL's real
  `model_config.py` imports every supported model SDK.

## Tracing in Phoenix

A run can be traced in [Arize Phoenix](https://arize.com/docs/phoenix) over
OTLP. Every case of a run appears there as one trace per case and provider.
The `openai` and `anthropic` requests are recorded by the standard
OpenInference instrumentation (`openinference-instrumentation-openai` and
`-anthropic`); this code adds no span for what they already record. It adds
one parent span, `benchmark_case`, per attempt at a case, so the
instrumentation's request spans sit inside the case's trace.

Start a local Phoenix, then set the endpoint:

```sh
docker run -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest
export PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
uv run --locked python -m benchmark_loop_agent --output-dir runs/small --sample-size 4
```

| Setting | Meaning |
|---------|---------|
| `PHOENIX_COLLECTOR_ENDPOINT` | base address of Phoenix; the code appends the OTLP path `/v1/traces`. **Unset: nothing is sent and the run behaves as before** |
| `PHOENIX_API_KEY` | only for a Phoenix that requires one; sent as a bearer token. Treated like the provider keys: never in a record, log (exporter errors included), error message or trace; every span is scrubbed before export |
| `PHOENIX_PROJECT_NAME` | Phoenix project the traces go to (default `benchmark-loop-agent`) |

Each `benchmark_case` span carries `benchmark.run_id` (also in `run.json`, and
kept when a run resumes), `benchmark.case_id`, `benchmark.category`,
`benchmark.provider`, `benchmark.requested_model`, `benchmark.actual_model`,
`benchmark.verdict` (`pass`, `fail` or `unscored`), `benchmark.failure_reason`
and `benchmark.invocation`, and a `metadata` JSON with the same facts. In
Phoenix, filter for example with
`metadata["category"] == "irrelevance" and metadata["verdict"] == "fail"`.

* **Each attempt is its own trace.** A case that was `unscored` and passes on a
  resume has two traces; the first stays `unscored`. Nothing rewrites a trace.
* **Unscored before any reply** (a missing key, say): the trace has the
  requested model and the reason; the actual model and the tokens are absent.
* **The expected answer** is not sent before the model has replied: the
  case's span starts with the facts above only, and the verdict and reason are
  added after scoring. A failure reason from the checker can name the expected
  value; that is sent after the reply.
* **Best effort.** A failed or slow export never changes a record, a verdict or
  the exit code. A case whose export failed keeps its record and its trace is
  **not** sent again on a resume; no unsent trace is kept on disk. Traces of
  such a case are missing from Phoenix, not queued.
* Exports are sent in batches with a 5 second request timeout, and the end of
  a run waits at most 10 seconds to send what is queued.

## Report

One Markdown file per model, built only from the run directory
(`records.jsonl`, `run.json`) and the rates file, never from Phoenix, so it can
be regenerated at any time:

```sh
uv run --locked python -m benchmark_loop_agent.report runs/full [--output-dir DIR] [--rates FILE]
```

The files are named `report-<provider>-<model>.md` and go to the run
directory unless `--output-dir` says otherwise. A report holds:

* accuracy per category and overall, with pass, fail and unscored counts.
  Accuracy is pass / (pass + fail); unscored cases were not judged. **Overall**
  pools every judged case, so each case counts once and a larger category
  weighs more; it is not the mean of the category figures;
* input and output tokens, and the cases without reported usage, counted and
  named (their tokens are not estimated);
* cost, from `data/rates.json`: input and output tokens at the rate of the
  requested model. Each entry has the price (US dollars per 1 million tokens,
  standard tier), the address of the provider's pricing page and the date it
  was read; prices are copied from those pages, not from memory. A model with
  no entry gets no cost, and the report says so. Both providers price cached
  input lower and the records do not separate it, so the cost counts all input
  at the uncached rate and can overstate what was charged;
* wall time and concurrency of every invocation, from the start and end times
  saved in `run.json`. An invocation with no end time (interrupted) is shown
  as unavailable and no total is given; nothing is derived from case latencies.
  The wall time is that of the run, shared by all its providers;
* the requested and actual model, dataset and scorer revisions, and the run's
  parameters;
* a note at the top if the run was sampled (`--sample-size`) or is incomplete
  (unscored cases, a category with fewer records than the run selected for it
  (the selection size is saved in `run.json`), or a last invocation that never
  ended). A record with only one token count still contributes that count; cases
  missing either are all named, with the missing one.

## Tests

Offline: no network and no API keys. The test setup makes any connection
attempt fail, except to the tests' own stand-in OTLP receiver on 127.0.0.1.

```sh
env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY -u PHOENIX_API_KEY -u PHOENIX_COLLECTOR_ENDPOINT uv run --locked python -m unittest discover -s tests -v
```

## Licence

Apache 2.0, see `LICENSE`. BFCL material is Apache 2.0 too; see `NOTICE`.
