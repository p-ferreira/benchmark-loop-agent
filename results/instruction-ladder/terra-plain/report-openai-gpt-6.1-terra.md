# Benchmark report: `gpt-6.1-terra` (openai)

> **Part: `validation`.** This run selected only the cases of the validation part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 85.0% (68/80) | 68 | 12 | 0 |
| `simple_java` | 65.0% (13/20) | 13 | 7 | 0 |
| `simple_javascript` | 70.0% (7/10) | 7 | 3 | 0 |
| `multiple` | 92.5% (37/40) | 37 | 3 | 0 |
| `parallel` | 75.0% (30/40) | 30 | 10 | 0 |
| `parallel_multiple` | 60.0% (24/40) | 24 | 16 | 0 |
| `irrelevance` | 79.2% (38/48) | 38 | 10 | 0 |
| `live_simple` | 67.3% (35/52) | 35 | 17 | 0 |
| `live_multiple` | 71.1% (150/211) | 150 | 61 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 4 | 1 | 0 |
| `live_irrelevance` | 83.1% (147/177) | 147 | 30 | 0 |
| `live_relevance` | 66.7% (2/3) | 2 | 1 | 0 |
| **Overall** | **76.5% (558/729)** | 558 | 171 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 85.0% (68/80) | 80 | 68 | 12 | 0 | 0 |
| `simple_java` | 65.0% (13/20) | 20 | 13 | 7 | 0 | 0 |
| `simple_javascript` | 70.0% (7/10) | 10 | 7 | 3 | 0 | 0 |
| `multiple` | 92.5% (37/40) | 40 | 37 | 3 | 0 | 0 |
| `parallel` | 75.0% (30/40) | 40 | 30 | 10 | 0 | 0 |
| `parallel_multiple` | 60.0% (24/40) | 40 | 24 | 16 | 0 | 0 |
| `irrelevance` | 79.2% (38/48) | 48 | 38 | 10 | 0 | 0 |
| `live_simple` | 67.3% (35/52) | 52 | 35 | 17 | 0 | 0 |
| `live_multiple` | 71.1% (150/211) | 211 | 150 | 61 | 0 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 3 | 0 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 5 | 4 | 1 | 0 | 0 |
| `live_irrelevance` | 83.1% (147/177) | 177 | 147 | 30 | 0 | 0 |
| `live_relevance` | 66.7% (2/3) | 3 | 2 | 1 | 0 | 0 |
| **Overall** | **76.5% (558/729)** | 729 | 558 | 171 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 12 | 0 | 0 | 2 | 0 | 1 | 9 |
| `simple_java` | 7 | 0 | 0 | 2 | 0 | 0 | 5 |
| `simple_javascript` | 3 | 0 | 0 | 1 | 0 | 0 | 2 |
| `multiple` | 3 | 0 | 0 | 1 | 0 | 0 | 2 |
| `parallel` | 10 | 0 | 0 | 2 | 3 | 1 | 4 |
| `parallel_multiple` | 16 | 0 | 0 | 1 | 10 | 1 | 4 |
| `irrelevance` | 10 | 10 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 17 | 0 | 0 | 3 | 0 | 0 | 14 |
| `live_multiple` | 61 | 0 | 0 | 16 | 0 | 7 | 38 |
| `live_parallel` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `live_parallel_multiple` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_irrelevance` | 30 | 30 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| **Overall** | 171 | 40 | 0 | 29 | 13 | 10 | 79 |

## Tokens and cost

* Input tokens: 308,344
* Output tokens: 61,181
* Records with complete usage: 729 of 729
* Cost: not given, the rates file has no entry for `gpt-6.1-terra`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 228.4 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T19:29:50+00:00 | 2026-11-25T19:33:38+00:00 | 228.4 s |

## Run

* Run identifier: `af69b00512db46ada4f1a31bd6991753`
* Requested model: `gpt-6.1-terra`
* Actual model (as the responses report it): `gpt-6.1-terra`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: validation
* Instruction: none used
* Providers in the run: openai
