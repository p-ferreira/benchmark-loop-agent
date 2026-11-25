# Benchmark report: `gpt-6-luna` (openai)

> **Part: `validation`.** This run selected only the cases of the validation part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 91.2% (73/80) | 73 | 7 | 0 |
| `simple_java` | 70.0% (14/20) | 14 | 6 | 0 |
| `simple_javascript` | 70.0% (7/10) | 7 | 3 | 0 |
| `multiple` | 100.0% (40/40) | 40 | 0 | 0 |
| `parallel` | 82.5% (33/40) | 33 | 7 | 0 |
| `parallel_multiple` | 75.0% (30/40) | 30 | 10 | 0 |
| `irrelevance` | 87.5% (42/48) | 42 | 6 | 0 |
| `live_simple` | 76.9% (40/52) | 40 | 12 | 0 |
| `live_multiple` | 69.7% (147/211) | 147 | 64 | 0 |
| `live_parallel` | 66.7% (2/3) | 2 | 1 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 4 | 1 | 0 |
| `live_irrelevance` | 81.4% (144/177) | 144 | 33 | 0 |
| `live_relevance` | 66.7% (2/3) | 2 | 1 | 0 |
| **Overall** | **79.3% (578/729)** | 578 | 151 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 91.2% (73/80) | 80 | 73 | 7 | 0 | 0 |
| `simple_java` | 70.0% (14/20) | 20 | 14 | 6 | 0 | 0 |
| `simple_javascript` | 70.0% (7/10) | 10 | 7 | 3 | 0 | 0 |
| `multiple` | 100.0% (40/40) | 40 | 40 | 0 | 0 | 0 |
| `parallel` | 82.5% (33/40) | 40 | 33 | 7 | 0 | 0 |
| `parallel_multiple` | 75.0% (30/40) | 40 | 30 | 10 | 0 | 0 |
| `irrelevance` | 87.5% (42/48) | 48 | 42 | 6 | 0 | 0 |
| `live_simple` | 76.9% (40/52) | 52 | 40 | 12 | 0 | 0 |
| `live_multiple` | 69.7% (147/211) | 211 | 147 | 64 | 0 | 0 |
| `live_parallel` | 66.7% (2/3) | 3 | 2 | 1 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 5 | 4 | 1 | 0 | 0 |
| `live_irrelevance` | 81.4% (144/177) | 177 | 144 | 33 | 0 | 0 |
| `live_relevance` | 66.7% (2/3) | 3 | 2 | 1 | 0 | 0 |
| **Overall** | **79.3% (578/729)** | 729 | 578 | 151 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 7 | 0 | 0 | 0 | 0 | 0 | 7 |
| `simple_java` | 6 | 0 | 0 | 0 | 0 | 0 | 6 |
| `simple_javascript` | 3 | 0 | 0 | 0 | 0 | 0 | 3 |
| `multiple` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `parallel` | 7 | 0 | 0 | 1 | 1 | 0 | 5 |
| `parallel_multiple` | 10 | 0 | 0 | 1 | 4 | 1 | 4 |
| `irrelevance` | 6 | 6 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 12 | 0 | 0 | 0 | 0 | 1 | 11 |
| `live_multiple` | 64 | 0 | 0 | 22 | 0 | 3 | 39 |
| `live_parallel` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_parallel_multiple` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_irrelevance` | 33 | 33 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| **Overall** | 151 | 39 | 0 | 25 | 5 | 5 | 77 |

## Tokens and cost

* Input tokens: 402,385
* Output tokens: 55,336
* Records with complete usage: 729 of 729
* Cost: not given, the rates file has no entry for `gpt-6-luna`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 124.8 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T19:29:50+00:00 | 2026-11-25T19:31:55+00:00 | 124.8 s |

## Run

* Run identifier: `1f275abc4bb3493593e6d9644c6086f2`
* Requested model: `gpt-6-luna`
* Actual model (as the responses report it): `gpt-6-luna`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: validation
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: openai
