# Benchmark report: `claude-sonnet-5-5` (anthropic)

> **Incomplete run.** 1 case(s) are unscored.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 94.8% (379/400) | 379 | 21 | 0 |
| `simple_java` | 66.0% (66/100) | 66 | 34 | 0 |
| `simple_javascript` | 78.0% (39/50) | 39 | 11 | 0 |
| `multiple` | 96.5% (193/200) | 193 | 7 | 0 |
| `parallel` | 94.0% (188/200) | 188 | 12 | 0 |
| `parallel_multiple` | 89.5% (179/200) | 179 | 21 | 0 |
| `irrelevance` | 89.6% (215/240) | 215 | 25 | 0 |
| `live_simple` | 87.5% (225/257) | 225 | 32 | 1 |
| `live_multiple` | 81.7% (860/1053) | 860 | 193 | 0 |
| `live_parallel` | 87.5% (14/16) | 14 | 2 | 0 |
| `live_parallel_multiple` | 83.3% (20/24) | 20 | 4 | 0 |
| `live_irrelevance` | 86.7% (766/884) | 766 | 118 | 0 |
| `live_relevance` | 68.8% (11/16) | 11 | 5 | 0 |
| **Overall** | **86.7% (3155/3640)** | 3155 | 485 | 1 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 94.8% (379/400) | 400 | 379 | 21 | 0 | 0 |
| `simple_java` | 66.0% (66/100) | 100 | 66 | 34 | 0 | 0 |
| `simple_javascript` | 78.0% (39/50) | 50 | 39 | 11 | 0 | 0 |
| `multiple` | 96.5% (193/200) | 200 | 193 | 7 | 0 | 0 |
| `parallel` | 94.0% (188/200) | 200 | 188 | 12 | 0 | 0 |
| `parallel_multiple` | 89.5% (179/200) | 200 | 179 | 21 | 0 | 0 |
| `irrelevance` | 89.6% (215/240) | 240 | 215 | 25 | 0 | 0 |
| `live_simple` | 87.2% (225/258) | 258 | 225 | 32 | 1 | 0 |
| `live_multiple` | 81.7% (860/1053) | 1053 | 860 | 193 | 0 | 0 |
| `live_parallel` | 87.5% (14/16) | 16 | 14 | 2 | 0 | 0 |
| `live_parallel_multiple` | 83.3% (20/24) | 24 | 20 | 4 | 0 | 0 |
| `live_irrelevance` | 86.7% (766/884) | 884 | 766 | 118 | 0 | 0 |
| `live_relevance` | 68.8% (11/16) | 16 | 11 | 5 | 0 | 0 |
| **Overall** | **86.7% (3155/3641)** | 3641 | 3155 | 485 | 1 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 21 | 0 | 0 | 3 | 0 | 3 | 15 |
| `simple_java` | 34 | 0 | 0 | 1 | 0 | 1 | 32 |
| `simple_javascript` | 11 | 0 | 0 | 4 | 0 | 0 | 7 |
| `multiple` | 7 | 0 | 0 | 1 | 0 | 4 | 2 |
| `parallel` | 12 | 0 | 0 | 0 | 4 | 2 | 6 |
| `parallel_multiple` | 21 | 0 | 0 | 0 | 2 | 3 | 16 |
| `irrelevance` | 25 | 25 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 32 | 0 | 0 | 2 | 0 | 4 | 26 |
| `live_multiple` | 193 | 0 | 0 | 33 | 0 | 51 | 109 |
| `live_parallel` | 2 | 0 | 0 | 0 | 1 | 0 | 1 |
| `live_parallel_multiple` | 4 | 0 | 0 | 0 | 1 | 1 | 2 |
| `live_irrelevance` | 118 | 118 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 5 | 0 | 0 | 5 | 0 | 0 | 0 |
| **Overall** | 485 | 143 | 0 | 49 | 8 | 69 | 216 |

## Tokens and cost

* Input tokens: 4,539,848
* Output tokens: 535,005
* Records with complete usage: 3640 of 3641
* 1 case(s) lack reported usage (the missing count is named); the counts that were reported are included, nothing was estimated for the missing ones, so the tokens and the cost are a lower bound: `live_simple_67-31-0` (input and output)
* Cost: not given, the rates file has no entry for `claude-sonnet-5-5`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 725.8 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T20:51:43+00:00 | 2026-11-25T21:03:49+00:00 | 725.8 s |

## Run

* Run identifier: `f58bab8d6c2342f6b19bf6e28686caec`
* Requested model: `claude-sonnet-5-5`
* Actual model (as the responses report it): `claude-sonnet-5-5`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: none, every case of the categories
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: anthropic
