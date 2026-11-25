# Benchmark report: `gpt-6-luna` (openai)

> **Part: `validation`.** This run selected only the cases of the validation part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 86.2% (69/80) | 69 | 11 | 0 |
| `simple_java` | 65.0% (13/20) | 13 | 7 | 0 |
| `simple_javascript` | 50.0% (5/10) | 5 | 5 | 0 |
| `multiple` | 90.0% (36/40) | 36 | 4 | 0 |
| `parallel` | 75.0% (30/40) | 30 | 10 | 0 |
| `parallel_multiple` | 67.5% (27/40) | 27 | 13 | 0 |
| `irrelevance` | 83.3% (40/48) | 40 | 8 | 0 |
| `live_simple` | 71.2% (37/52) | 37 | 15 | 0 |
| `live_multiple` | 67.3% (142/211) | 142 | 69 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 0 | 0 |
| `live_parallel_multiple` | 60.0% (3/5) | 3 | 2 | 0 |
| `live_irrelevance` | 78.0% (138/177) | 138 | 39 | 0 |
| `live_relevance` | 66.7% (2/3) | 2 | 1 | 0 |
| **Overall** | **74.8% (545/729)** | 545 | 184 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 86.2% (69/80) | 80 | 69 | 11 | 0 | 0 |
| `simple_java` | 65.0% (13/20) | 20 | 13 | 7 | 0 | 0 |
| `simple_javascript` | 50.0% (5/10) | 10 | 5 | 5 | 0 | 0 |
| `multiple` | 90.0% (36/40) | 40 | 36 | 4 | 0 | 0 |
| `parallel` | 75.0% (30/40) | 40 | 30 | 10 | 0 | 0 |
| `parallel_multiple` | 67.5% (27/40) | 40 | 27 | 13 | 0 | 0 |
| `irrelevance` | 83.3% (40/48) | 48 | 40 | 8 | 0 | 0 |
| `live_simple` | 71.2% (37/52) | 52 | 37 | 15 | 0 | 0 |
| `live_multiple` | 67.3% (142/211) | 211 | 142 | 69 | 0 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 3 | 0 | 0 | 0 |
| `live_parallel_multiple` | 60.0% (3/5) | 5 | 3 | 2 | 0 | 0 |
| `live_irrelevance` | 78.0% (138/177) | 177 | 138 | 39 | 0 | 0 |
| `live_relevance` | 66.7% (2/3) | 3 | 2 | 1 | 0 | 0 |
| **Overall** | **74.8% (545/729)** | 729 | 545 | 184 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 11 | 0 | 0 | 3 | 0 | 0 | 8 |
| `simple_java` | 7 | 0 | 0 | 1 | 0 | 0 | 6 |
| `simple_javascript` | 5 | 0 | 0 | 0 | 0 | 0 | 5 |
| `multiple` | 4 | 0 | 0 | 2 | 0 | 0 | 2 |
| `parallel` | 10 | 0 | 0 | 2 | 4 | 0 | 4 |
| `parallel_multiple` | 13 | 0 | 0 | 0 | 7 | 0 | 6 |
| `irrelevance` | 8 | 8 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 15 | 0 | 0 | 3 | 0 | 0 | 12 |
| `live_multiple` | 69 | 0 | 0 | 26 | 0 | 0 | 43 |
| `live_parallel` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `live_parallel_multiple` | 2 | 0 | 0 | 0 | 1 | 0 | 1 |
| `live_irrelevance` | 39 | 39 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| **Overall** | 184 | 47 | 0 | 38 | 12 | 0 | 87 |

## Tokens and cost

* Input tokens: 308,344
* Output tokens: 69,106
* Records with complete usage: 729 of 729
* Cost: not given, the rates file has no entry for `gpt-6-luna`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 134.0 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T19:29:50+00:00 | 2026-11-25T19:32:04+00:00 | 134.0 s |

## Run

* Run identifier: `99b067e36a9a4002849c6ce9423be6dd`
* Requested model: `gpt-6-luna`
* Actual model (as the responses report it): `gpt-6-luna`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: validation
* Instruction: none used
* Providers in the run: openai
