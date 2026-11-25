# Benchmark report: `gpt-6-luna` (openai)

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 86.8% (347/400) | 347 | 53 | 0 |
| `simple_java` | 63.0% (63/100) | 63 | 37 | 0 |
| `simple_javascript` | 74.0% (37/50) | 37 | 13 | 0 |
| `multiple` | 89.5% (179/200) | 179 | 21 | 0 |
| `parallel` | 87.0% (174/200) | 174 | 26 | 0 |
| `parallel_multiple` | 72.5% (145/200) | 145 | 55 | 0 |
| `irrelevance` | 84.2% (202/240) | 202 | 38 | 0 |
| `live_simple` | 79.1% (204/258) | 204 | 54 | 0 |
| `live_multiple` | 74.1% (780/1053) | 780 | 273 | 0 |
| `live_parallel` | 75.0% (12/16) | 12 | 4 | 0 |
| `live_parallel_multiple` | 50.0% (12/24) | 12 | 12 | 0 |
| `live_irrelevance` | 80.8% (714/884) | 714 | 170 | 0 |
| `live_relevance` | 62.5% (10/16) | 10 | 6 | 0 |
| **Overall** | **79.1% (2879/3641)** | 2879 | 762 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 86.8% (347/400) | 400 | 347 | 53 | 0 | 0 |
| `simple_java` | 63.0% (63/100) | 100 | 63 | 37 | 0 | 0 |
| `simple_javascript` | 74.0% (37/50) | 50 | 37 | 13 | 0 | 0 |
| `multiple` | 89.5% (179/200) | 200 | 179 | 21 | 0 | 0 |
| `parallel` | 87.0% (174/200) | 200 | 174 | 26 | 0 | 0 |
| `parallel_multiple` | 72.5% (145/200) | 200 | 145 | 55 | 0 | 0 |
| `irrelevance` | 84.2% (202/240) | 240 | 202 | 38 | 0 | 0 |
| `live_simple` | 79.1% (204/258) | 258 | 204 | 54 | 0 | 0 |
| `live_multiple` | 74.1% (780/1053) | 1053 | 780 | 273 | 0 | 0 |
| `live_parallel` | 75.0% (12/16) | 16 | 12 | 4 | 0 | 0 |
| `live_parallel_multiple` | 50.0% (12/24) | 24 | 12 | 12 | 0 | 0 |
| `live_irrelevance` | 80.8% (714/884) | 884 | 714 | 170 | 0 | 0 |
| `live_relevance` | 62.5% (10/16) | 16 | 10 | 6 | 0 | 0 |
| **Overall** | **79.1% (2879/3641)** | 3641 | 2879 | 762 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 53 | 0 | 0 | 10 | 0 | 1 | 42 |
| `simple_java` | 37 | 0 | 0 | 1 | 0 | 0 | 36 |
| `simple_javascript` | 13 | 0 | 0 | 1 | 0 | 0 | 12 |
| `multiple` | 21 | 0 | 0 | 4 | 0 | 3 | 14 |
| `parallel` | 26 | 0 | 0 | 3 | 9 | 0 | 14 |
| `parallel_multiple` | 55 | 0 | 0 | 2 | 27 | 1 | 25 |
| `irrelevance` | 38 | 38 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 54 | 0 | 0 | 12 | 0 | 1 | 41 |
| `live_multiple` | 273 | 0 | 0 | 95 | 0 | 11 | 167 |
| `live_parallel` | 4 | 0 | 0 | 0 | 1 | 0 | 3 |
| `live_parallel_multiple` | 12 | 0 | 0 | 0 | 6 | 0 | 6 |
| `live_irrelevance` | 170 | 170 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 6 | 0 | 0 | 6 | 0 | 0 | 0 |
| **Overall** | 762 | 208 | 0 | 134 | 43 | 17 | 360 |

## Tokens and cost

* Input tokens: 1,537,933
* Output tokens: 345,076
* Records with complete usage: 3641 of 3641
* Cost: not given, the rates file has no entry for `gpt-6-luna`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 685.8 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T20:51:43+00:00 | 2026-11-25T21:03:09+00:00 | 685.8 s |

## Run

* Run identifier: `08f6b0e8c4d84f109945c0b1344228e4`
* Requested model: `gpt-6-luna`
* Actual model (as the responses report it): `gpt-6-luna`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: none, every case of the categories
* Instruction: none used
* Providers in the run: openai
