# benchmark-loop-agent

Runs the single-turn function-calling cases of the
[Berkeley Function Calling Leaderboard (BFCL)](https://github.com/ShishirPatil/gorilla)
through the OpenAI and Anthropic APIs, scores every returned tool call with
BFCL's own checker, and writes one record per case and provider to disk. A
returned call is only compared with the expected answer. It is never executed.
An interrupted run resumes without repeating finished cases.

## Results

Finished runs, with their records and reports, are in [`results/`](results/README.md). The first is every
single-turn BFCL case on `gpt-6-sol` and `claude-opus-5-5`:
[results/phase-0](results/phase-0/README.md).

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
| `--split PART` | `development`, `validation` or `held-out`: run only that part's cases of [`data/split.json`](#development-validation-and-held-out-split). Combines with `--categories`, `--sample-size` and `--seed` (the sample is drawn inside the part). Written in `run.json`; resuming with another part is refused. Without it nothing changes |
| `--provider P` | `openai` or `anthropic`; repeat for both (default: both) |
| `--openai-model ID`, `--anthropic-model ID` | model IDs; otherwise `OPENAI_MODEL` / `ANTHROPIC_MODEL`. No default in code: a provider without one is `unscored` |
| `--instructions FILE` | a UTF-8 text file of 1 to 8,000 bytes whose text goes first in every request, for each provider without its own file; see [Instruction file](#instruction-file) |
| `--openai-instructions FILE`, `--anthropic-instructions FILE` | the same for one provider; they win over `--instructions` for it |
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

## Development, validation and held-out split

A gain measured on cases an instruction was tuned on is not evidence, so every
one of the 3641 cases belongs to exactly one of three parts: development (to
tune on), validation (to choose between candidates) and held-out (to report
on). The split is committed as [`data/split.json`](data/split.json), with the
seed, the proportions and the dataset revision written in it. It holds case
identifiers and part names only: no question, tool or answer text.

Rebuild it, byte for byte, from the question files (the builder never reads the
expected answers):

```sh
uv run --locked python -m benchmark_loop_agent.split --seed 0 --development 50 --validation 20 --held-out 30
# --output FILE writes somewhere else; the defaults are the committed values
```

**Groups.** BFCL repeats tool sets and questions across cases and categories,
and a case that shares either with a case in another part would leak it. Two
cases are therefore in one group when they have the same set of tool
definitions (as parsed from the question files, independent of key order inside
a definition and of tool order) or an identical question (as parsed; the
expected answer and the category play no part). The case identifier is never
used. Grouping is transitive, and a group is never divided between parts. The
split is stratified by category: whole groups are given to the part whose share
of each category they bring closest to the proportions, so a group that spans
categories is assigned once.

Counted from the committed file and the question files (a test checks this
table):

| Part | Cases | Groups |
|------|-------|--------|
| development | 1820 | 773 |
| validation | 729 | 487 |
| held-out | 1092 | 604 |
| **Total** | 3641 | 1864 |

## Instruction file

`--instructions FILE` puts the file's text in the system position of every
request of the run: for OpenAI as a `developer` message placed first in the
input, for Anthropic in the `system` field. When a case already has a system
message, the instruction comes first and the case's own system text follows,
unchanged (for Anthropic as a second `system` block). `--openai-instructions`
and `--anthropic-instructions` give one provider its own file;
`--instructions` is the default for a provider without one.

* A file above 8,000 bytes, an empty file and a file that is not valid UTF-8
  are refused before any request.
* `run.json` records, per provider of the run, the SHA-256 and byte length of
  the file, and the text itself is saved beside it as
  `instruction-<provider>.txt`. Resuming a directory with another text, or with
  one where there was none, is refused like any other changed parameter.
* Without these options every request is what it was before, and earlier runs
  still resume.
* The report names the digest and length, or says none was used. Repeated runs
  with different digests are different configurations and are refused.
* The instruction is text you wrote; no expected answer reaches a model input,
  with or without it.

## Learning instruction lines

One command reads the failed cases of a development run and appends short general rules, written by a model (the
writer), to a copy of an instruction file:

```sh
uv run --locked python -m benchmark_loop_agent.learn --run-dir runs/dev --instructions start.txt --output learned.txt \
    --writer-provider anthropic --writer-model <model id>
```

| Option | Meaning |
|--------|---------|
| `--run-dir DIR`, `--instructions FILE`, `--output OUT` (required) | the development run, the file to start from, and the learned file |
| `--writer-provider openai\|anthropic`, `--writer-model ID` (required) | the writer; its key is read from `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` at run time and written nowhere |
| `--max-bytes N` | largest size of `OUT` (default 4,000; the runner's own limit of 8,000 always applies) |
| `--batch-size N` | failed cases per request (default 20) |
| `--lines-per-batch N` | most rules asked for per request (default 3) |
| `--log FILE` | default: `OUT` with `.log.jsonl` appended |

Exit codes: 0 done, 2 refused (before any request), 3 a writer request failed (after the runner's usual retries);
`OUT` and the log then stay as they were after the last finished batch.

**What the writer is sent.** For each failed record, in batches in case-identifier order: the case's messages, its
functions as the runner sent them to the provider, the calls the model returned, its `reply_text` (the field is left
out for a record of an older run that has none) and the failure class of `benchmark_loop_agent.failures`. Before the
cases of each batch it gets the text of `OUT` as it stands, with the rules kept from earlier batches, and the fixed
request in [`benchmark_loop_agent/learn_request.txt`](benchmark_loop_agent/learn_request.txt): at most
`--lines-per-batch` new rules, each one line of at most 300 characters, each a general rule about how to answer, none
naming a value, a function or a case. The reply is a JSON array of strings.

**What it is never sent.** The expected answer of any case, the checker's reasons (they quote expected values), a
case identifier, the category name of a case, and anything from the validation or held-out parts. The request is built
from the records and the question files without reading the answer files. The case's own messages and the calls the
model returned are sent as they are, even where they equal an expected value. A test gives the answer files of its
cases unique marker strings and fails if any request holds one.

**What is kept.** `OUT` starts as an exact copy of `FILE`; each rule is appended as its own line, as written, unless
it is refused (reasons in the log): `not-single-line` (any line break, also a trailing or Unicode one), `invalid-text`, `too-long` (over 300 characters), `duplicate`
(already in the file), `over-max-bytes`, `over-runner-limit` (past 8,000 bytes),
`expected-value` (it contains, as written, an expected string value of four characters or more from a case of its
batch; checked by code that reads the answers after the writer has replied; a rule that quotes an expected value of any
failed case of the run is refused the same way, because the log must never hold such a text) and `contains-key`.
The number of rules asked for is a request, not a ground for refusal. Nothing already in
the file is changed or removed.

**The log** starts with a header line holding the inputs and options of the run (digests of the run files, `FILE`,
the question and answer content of the failed cases, the writer and the limits), written before the first request.
It has one JSON line per batch (SHA-256 of each case identifier, the writer's provider and model as requested and as reported (`null` when the reply does not report one),
SHA-256 of the request, every rule with whether it was kept and why not, tokens) and a final line of totals (batches, rules returned, kept and refused by reason, tokens, SHA-256 and
byte length of `FILE` and `OUT`). A rule refused for an expected value or a key, and any rule, kept or not, that holds an expected value (two
characters or more) of a failed case of the run, is logged as its SHA-256 and length only (`text_withheld`); a resumed
run then takes a withheld kept rule from the line of `OUT` with that digest, and refuses when `OUT` lacks it. The log
holds no expected value and no key. A model ID that contains a configured key is refused, and so is an existing log
that this run cannot establish as its own: one that does not start with a complete first line, ending in a newline, that is exactly the header this command writes for these inputs and options (an empty file, a log without `OUT`, and an `OUT` without a log are refused too; no file is matched by a prefix; it is never truncated, and an `OUT` that is not one of the versions the log allows is never replaced). It is only appended to; the one thing ever cut is a last line left unfinished by an interruption. It is locked while a run uses it.

**Refusals (exit code 2, before any request).** A run that is not `--split development`; a run of several providers
or of none; any record, passing or not, whose case is not in the development part of `data/split.json`; a failed
record whose failure class cannot be found; an unreadable, empty, over-8,000-byte or non-UTF-8 `FILE`; a missing
key, or a key inside `FILE`; an unreadable `run.json`; an `OUT` or log that already exists but was made with other inputs or
options (run, `FILE`, question and answer content, writer, limits), an `OUT` that is neither the complete output of
the logged batches nor the version before the last one, or a log in use by another run. All of this is checked before
anything is written.

**Running it again** with the same inputs and options sends no batch that is already in the log and continues after
it. Learning needs the answer files for the failure classes, like the report does.

## Output directory

* `records.jsonl`: one JSON Lines record per case and provider, appended as
  each case finishes.
* `run.json`: the run's parameters (categories, sample size, seed, split part
  when `--split` was used, providers, model IDs), the number of cases selected per category, the dataset and scorer revisions, and for every invocation its
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
| `reply_text` | the text the model wrote: its text parts joined in order, cut to 4,000 characters; `""` when it wrote none; `null` when unscored. Records of earlier runs lack it and still load, report and resume |
| `reasons` | why it failed or was not scored; empty on pass |
| `latency_seconds` | request time including any retry waits; `null` if no request was made |
| `input_tokens`, `output_tokens` | usage as the response reports it, else `null` |

One case's or one provider's failure never changes or prevents another record.

## Resume and retries

* A case with a `pass` or `fail` record is skipped. An `unscored` one runs
  again, and its old record is replaced, so the file keeps one record per case
  and provider. A line cut short by an interruption is dropped.
* Resuming with different parameters (categories, sample size, seed, split part, providers
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
instrumentation's request spans sit inside the case's trace, and a second,
`bfcl_scoring`, for the scoring. The verdict is also sent as a Phoenix
annotation. A case is therefore one trace of three kinds of span:

| Span | Made by | Holds |
|------|---------|-------|
| `benchmark_case` (kind `CHAIN`) | this code | input: the question; output: the calls the model returned, as the record keeps them; status: **error only when the case is `unscored`** (the reason is the message), OK for `pass` and `fail` (a wrong answer is not an error) |
| `Response` / `messages.create` (kind `LLM`) | the instrumentation | the request, the reply, the tokens |
| `bfcl_scoring` (kind `EVALUATOR`) | this code, after the reply | input: the returned calls and the expected answer; output: the verdict and the checker's reason. For categories without an expected-answer file the input says the rule is BFCL's relevance rule and holds no expected answer. A case that was not scored (no reply, or unreadable reference data) has no scoring span |

No span is added for tool execution: the model only proposes calls here and
nothing runs them; the calls are in the request span.

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

**The `bfcl` annotation.** For every case of an invocation, once the spans
have been exported, the run sends one span annotation on the `benchmark_case`
span with `POST /v1/span_annotations` at the same address: name `bfcl`, label
`pass`, `fail` or `unscored`, score 1 for pass and 0 for fail (none for
unscored), the checker's reason as the explanation, annotator kind `CODE`.
Phoenix then lists and counts pass and fail as a score. To see the failed cases
of one category, filter the project's spans with
`name == 'benchmark_case' and metadata["category"] == "simple_python" and evals["bfcl"].label == "fail"`
(or filter on the annotation `bfcl` = `fail` in the UI); opening one shows the
question, the returned calls, the expected answer in its `bfcl_scoring` child
and the reason. Cases that could not be scored are the ones with error status.

* **Each attempt is its own trace.** A case that was `unscored` and passes on a
  resume has two traces; the first stays `unscored`. Nothing rewrites a trace.
* **Unscored before any reply** (a missing key, say): the trace has the
  requested model and the reason; the actual model and the tokens are absent.
* **The expected answer** is not sent before the model has replied: the
  case's span starts with the facts above only, and the verdict and reason are
  added after scoring. A failure reason from the checker can name the expected
  value; that is sent after the reply.
* **Best effort.** Annotations are sent in one pass at the end of the run,
  with a 5 second timeout per request and 10 seconds in all; a failed or slow
  send is dropped, never retried on a resume, never kept on disk, and a
  `PHOENIX_API_KEY` is sent with it as a bearer token and kept out of every log
  and message. A failed or slow export never changes a record, a verdict or
  the exit code. A case whose export failed keeps its record and its trace is
  **not** sent again on a resume; no unsent trace is kept on disk. Traces of
  such a case are missing from Phoenix, not queued.
* Exports are sent in batches with a 5 second request timeout, and the end of
  a run waits at most 10 seconds to send what is queued.

## Report

One Markdown file per model, built only from the run directory
(`records.jsonl`, `run.json`), the rates file and the pinned expected answers
under `data/answers` (the failure classes need the expected number of calls),
never from Phoenix, so it can be regenerated at any time. Anyone archiving a
run for later reports must keep that data revision too; a report is refused,
not written with gaps, when a failed case's expected answer cannot be found:

```sh
uv run --locked python -m benchmark_loop_agent.report runs/full [--output-dir DIR] [--rates FILE]
```

The files are named `report-<provider>-<model>.md` and go to the run
directory unless `--output-dir` says otherwise. A report holds:

* accuracy per category and overall, with pass, fail and unscored counts.
  Accuracy is pass / (pass + fail); unscored cases were not judged. **Overall**
  pools every judged case, so each case counts once and a larger category
  weighs more; it is not the mean of the category figures;
* the **comparison figure**, per category and overall: passes divided by the
  cases the run selected, as `run.json` records them. Unscored cases and
  selected cases with no record (an interrupted run) stay in the denominator, so
  they count against it, unlike accuracy, which is unchanged. An older run whose
  `run.json` does not record the selection shows the figure as unavailable.
  A `--split` run reports, and names, its part; a run without `--split` is not
  broken down by part;
* the **failure classes**: every failed case has exactly one class, per
  category and overall, as counts. The first that applies is the case's class:
  * `called-when-none-applied`: a failure in `irrelevance` or `live_irrelevance`;
  * `malformed-call`: in any other category, a returned call could not be
    scored (arguments that are not a JSON object, or nested too deep), before
    the checker saw it;
  * `no-call`: at least one call was expected and the model returned none;
  * `too-few-calls`, `too-many-calls`: at least one call came back, and fewer
    or more than the expected answer holds;
  * `wrong-call`: the number of calls is the expected one and the checker
    rejected a name, a parameter, a type or a value.

  `live_relevance` has no expected answer; there at least one call is expected,
  so its failures are `malformed-call` or `no-call`. The class is computed from
  the record and the expected answer when the report is built; it is not stored
  in the record. Unscored cases are not failures and stay apart;
* the instruction's digest and length, or that none was used;
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

### Comparing two runs

```sh
uv run --locked python -m benchmark_loop_agent.report --compare DIR_A DIR_B [--output-dir DIR]
```

Writes `compare-<provider>.md` (to `--output-dir`, by default the current directory) for each provider both directories hold, never
pairing a case across providers; it is refused when they share no provider.
It compares the cases both runs selected (a full run can be compared with a run
of one `--split` part), states how many cases only A and only B selected, and is
refused when they share no case. Per category and overall it gives the cases
only A passed, the cases only B passed, and how many paired cases moved from
each failure class to each other class or to a pass. A case that is unscored, or
has no record, in a run is not paired: it is counted in a line per run and per
category, so the paired counts and those lines account for every compared case.
Each run's model and instruction digest are named. The cases a run selected are
recomputed from its parameters and checked against the digest in its `run.json`.

### Repeated runs

Give the report command several run directories of one configuration (same
providers, models, split part, categories, sample size and seed) and it writes
`repeated-<provider>-<model>.md`: the lowest, highest and mean comparison
figure and the number of runs, per category and overall. Directories whose
configurations differ, or a run whose figure is unavailable, are refused with a
message that says why. Each run also records a fingerprint of the case ids it
selected; runs that selected other cases (for example after the split file was
rebuilt with another seed) are refused, as is resuming a directory after that
change. The order of the categories or providers does not matter. A run that
selected no cases has no overall figure and is refused.

```sh
uv run --locked python -m benchmark_loop_agent.report runs/a runs/b runs/c --output-dir runs/spread
```

## Tests

Offline: no network and no API keys. The test setup makes any connection
attempt fail, except to the tests' own stand-in OTLP receiver on 127.0.0.1.

```sh
env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY -u PHOENIX_API_KEY -u PHOENIX_COLLECTOR_ENDPOINT uv run --locked python -m unittest discover -s tests -v
```

## Licence

Apache 2.0, see `LICENSE`. BFCL material is Apache 2.0 too; see `NOTICE`.

**Known limits (follow-ups, not handled by this command).**

- *Lengths checked.* The `expected-value` check covers expected string values of four characters or more. Withholding a
  rule's text from the log covers values of two characters or more. A one-character expected value, or a value of two or
  three characters for the refusal, is outside the check.
- *Interrupted between the log and the output.* If a run is interrupted after a batch is written to the log and before
  `OUT` is replaced, and the log withholds a kept rule's text, a rerun refuses with exit code 2 and sends nothing. This
  state needs new output and log files.
- *Interrupted before the first line is complete.* If an interruption leaves the log's first line incomplete, a rerun
  refuses with exit code 2, sends nothing and leaves both files untouched. This state also needs new output and log files.
