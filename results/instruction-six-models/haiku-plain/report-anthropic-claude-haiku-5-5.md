# Benchmark report: `claude-haiku-5-5` (anthropic)

> **Incomplete run.** 1 case(s) are unscored.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 95.2% (381/400) | 381 | 19 | 0 |
| `simple_java` | 58.0% (58/100) | 58 | 42 | 0 |
| `simple_javascript` | 58.0% (29/50) | 29 | 21 | 0 |
| `multiple` | 93.5% (187/200) | 187 | 13 | 0 |
| `parallel` | 90.0% (180/200) | 180 | 20 | 0 |
| `parallel_multiple` | 85.0% (170/200) | 170 | 30 | 0 |
| `irrelevance` | 85.0% (204/240) | 204 | 36 | 0 |
| `live_simple` | 83.3% (214/257) | 214 | 43 | 1 |
| `live_multiple` | 76.6% (807/1053) | 807 | 246 | 0 |
| `live_parallel` | 87.5% (14/16) | 14 | 2 | 0 |
| `live_parallel_multiple` | 75.0% (18/24) | 18 | 6 | 0 |
| `live_irrelevance` | 81.4% (720/884) | 720 | 164 | 0 |
| `live_relevance` | 68.8% (11/16) | 11 | 5 | 0 |
| **Overall** | **82.2% (2993/3640)** | 2993 | 647 | 1 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 95.2% (381/400) | 400 | 381 | 19 | 0 | 0 |
| `simple_java` | 58.0% (58/100) | 100 | 58 | 42 | 0 | 0 |
| `simple_javascript` | 58.0% (29/50) | 50 | 29 | 21 | 0 | 0 |
| `multiple` | 93.5% (187/200) | 200 | 187 | 13 | 0 | 0 |
| `parallel` | 90.0% (180/200) | 200 | 180 | 20 | 0 | 0 |
| `parallel_multiple` | 85.0% (170/200) | 200 | 170 | 30 | 0 | 0 |
| `irrelevance` | 85.0% (204/240) | 240 | 204 | 36 | 0 | 0 |
| `live_simple` | 82.9% (214/258) | 258 | 214 | 43 | 1 | 0 |
| `live_multiple` | 76.6% (807/1053) | 1053 | 807 | 246 | 0 | 0 |
| `live_parallel` | 87.5% (14/16) | 16 | 14 | 2 | 0 | 0 |
| `live_parallel_multiple` | 75.0% (18/24) | 24 | 18 | 6 | 0 | 0 |
| `live_irrelevance` | 81.4% (720/884) | 884 | 720 | 164 | 0 | 0 |
| `live_relevance` | 68.8% (11/16) | 16 | 11 | 5 | 0 | 0 |
| **Overall** | **82.2% (2993/3641)** | 3641 | 2993 | 647 | 1 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 19 | 0 | 0 | 4 | 0 | 1 | 14 |
| `simple_java` | 42 | 0 | 0 | 7 | 0 | 0 | 35 |
| `simple_javascript` | 21 | 0 | 0 | 9 | 0 | 0 | 12 |
| `multiple` | 13 | 0 | 0 | 3 | 0 | 4 | 6 |
| `parallel` | 20 | 0 | 0 | 0 | 5 | 1 | 14 |
| `parallel_multiple` | 30 | 0 | 0 | 2 | 11 | 1 | 16 |
| `irrelevance` | 36 | 36 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 43 | 0 | 0 | 7 | 0 | 0 | 36 |
| `live_multiple` | 246 | 0 | 0 | 40 | 0 | 48 | 158 |
| `live_parallel` | 2 | 0 | 0 | 0 | 0 | 0 | 2 |
| `live_parallel_multiple` | 6 | 0 | 0 | 0 | 4 | 0 | 2 |
| `live_irrelevance` | 164 | 164 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 5 | 0 | 0 | 5 | 0 | 0 | 0 |
| **Overall** | 647 | 200 | 0 | 77 | 20 | 55 | 295 |

## Tokens and cost

* Input tokens: 3,982,928
* Output tokens: 825,810
* Records with complete usage: 3640 of 3641
* 1 case(s) lack reported usage (the missing count is named); the counts that were reported are included, nothing was estimated for the missing ones, so the tokens and the cost are a lower bound: `live_simple_67-31-0` (input and output)
* Cost: not given, the rates file has no entry for `claude-haiku-5-5`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 627.7 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T20:51:43+00:00 | 2026-11-25T21:02:11+00:00 | 627.7 s |

## Run

* Run identifier: `3b38547b6a4542af97e8793d9c7a8e63`
* Requested model: `claude-haiku-5-5`
* Actual model (as the responses report it): `claude-haiku-5-5`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: none, every case of the categories
* Instruction: none used
* Providers in the run: anthropic
