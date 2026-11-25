# Benchmark report: `claude-haiku-5-5` (anthropic)

> **Incomplete run.** 1 case(s) are unscored.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 94.8% (379/400) | 379 | 21 | 0 |
| `simple_java` | 56.0% (56/100) | 56 | 44 | 0 |
| `simple_javascript` | 54.0% (27/50) | 27 | 23 | 0 |
| `multiple` | 94.5% (189/200) | 189 | 11 | 0 |
| `parallel` | 90.5% (181/200) | 181 | 19 | 0 |
| `parallel_multiple` | 85.0% (170/200) | 170 | 30 | 0 |
| `irrelevance` | 89.6% (215/240) | 215 | 25 | 0 |
| `live_simple` | 85.2% (219/257) | 219 | 38 | 1 |
| `live_multiple` | 76.4% (805/1053) | 805 | 248 | 0 |
| `live_parallel` | 93.8% (15/16) | 15 | 1 | 0 |
| `live_parallel_multiple` | 79.2% (19/24) | 19 | 5 | 0 |
| `live_irrelevance` | 85.6% (757/884) | 757 | 127 | 0 |
| `live_relevance` | 68.8% (11/16) | 11 | 5 | 0 |
| **Overall** | **83.6% (3043/3640)** | 3043 | 597 | 1 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 94.8% (379/400) | 400 | 379 | 21 | 0 | 0 |
| `simple_java` | 56.0% (56/100) | 100 | 56 | 44 | 0 | 0 |
| `simple_javascript` | 54.0% (27/50) | 50 | 27 | 23 | 0 | 0 |
| `multiple` | 94.5% (189/200) | 200 | 189 | 11 | 0 | 0 |
| `parallel` | 90.5% (181/200) | 200 | 181 | 19 | 0 | 0 |
| `parallel_multiple` | 85.0% (170/200) | 200 | 170 | 30 | 0 | 0 |
| `irrelevance` | 89.6% (215/240) | 240 | 215 | 25 | 0 | 0 |
| `live_simple` | 84.9% (219/258) | 258 | 219 | 38 | 1 | 0 |
| `live_multiple` | 76.4% (805/1053) | 1053 | 805 | 248 | 0 | 0 |
| `live_parallel` | 93.8% (15/16) | 16 | 15 | 1 | 0 | 0 |
| `live_parallel_multiple` | 79.2% (19/24) | 24 | 19 | 5 | 0 | 0 |
| `live_irrelevance` | 85.6% (757/884) | 884 | 757 | 127 | 0 | 0 |
| `live_relevance` | 68.8% (11/16) | 16 | 11 | 5 | 0 | 0 |
| **Overall** | **83.6% (3043/3641)** | 3641 | 3043 | 597 | 1 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 21 | 0 | 0 | 5 | 0 | 1 | 15 |
| `simple_java` | 44 | 0 | 0 | 10 | 0 | 0 | 34 |
| `simple_javascript` | 23 | 0 | 0 | 15 | 0 | 0 | 8 |
| `multiple` | 11 | 0 | 0 | 2 | 0 | 3 | 6 |
| `parallel` | 19 | 0 | 0 | 2 | 6 | 0 | 11 |
| `parallel_multiple` | 30 | 0 | 0 | 1 | 13 | 1 | 15 |
| `irrelevance` | 25 | 25 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 38 | 0 | 0 | 5 | 0 | 0 | 33 |
| `live_multiple` | 248 | 0 | 0 | 75 | 0 | 34 | 139 |
| `live_parallel` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_parallel_multiple` | 5 | 0 | 0 | 0 | 3 | 0 | 2 |
| `live_irrelevance` | 127 | 127 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 5 | 0 | 0 | 5 | 0 | 0 | 0 |
| **Overall** | 597 | 152 | 0 | 120 | 22 | 39 | 264 |

## Tokens and cost

* Input tokens: 4,539,848
* Output tokens: 668,985
* Records with complete usage: 3640 of 3641
* 1 case(s) lack reported usage (the missing count is named); the counts that were reported are included, nothing was estimated for the missing ones, so the tokens and the cost are a lower bound: `live_simple_67-31-0` (input and output)
* Cost: not given, the rates file has no entry for `claude-haiku-5-5`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 544.0 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T20:51:43+00:00 | 2026-11-25T21:00:47+00:00 | 544.0 s |

## Run

* Run identifier: `480c22e1e64247799610009c57f324ef`
* Requested model: `claude-haiku-5-5`
* Actual model (as the responses report it): `claude-haiku-5-5`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: none, every case of the categories
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: anthropic
