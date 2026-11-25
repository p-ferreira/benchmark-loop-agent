# Benchmark report: `claude-sonnet-5-5` (anthropic)

> **Incomplete run.** 1 case(s) are unscored.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 94.5% (378/400) | 378 | 22 | 0 |
| `simple_java` | 65.0% (65/100) | 65 | 35 | 0 |
| `simple_javascript` | 78.0% (39/50) | 39 | 11 | 0 |
| `multiple` | 93.5% (187/200) | 187 | 13 | 0 |
| `parallel` | 93.5% (187/200) | 187 | 13 | 0 |
| `parallel_multiple` | 87.0% (174/200) | 174 | 26 | 0 |
| `irrelevance` | 84.6% (203/240) | 203 | 37 | 0 |
| `live_simple` | 86.4% (222/257) | 222 | 35 | 1 |
| `live_multiple` | 80.3% (846/1053) | 846 | 207 | 0 |
| `live_parallel` | 81.2% (13/16) | 13 | 3 | 0 |
| `live_parallel_multiple` | 75.0% (18/24) | 18 | 6 | 0 |
| `live_irrelevance` | 81.8% (723/884) | 723 | 161 | 0 |
| `live_relevance` | 75.0% (12/16) | 12 | 4 | 0 |
| **Overall** | **84.3% (3067/3640)** | 3067 | 573 | 1 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 94.5% (378/400) | 400 | 378 | 22 | 0 | 0 |
| `simple_java` | 65.0% (65/100) | 100 | 65 | 35 | 0 | 0 |
| `simple_javascript` | 78.0% (39/50) | 50 | 39 | 11 | 0 | 0 |
| `multiple` | 93.5% (187/200) | 200 | 187 | 13 | 0 | 0 |
| `parallel` | 93.5% (187/200) | 200 | 187 | 13 | 0 | 0 |
| `parallel_multiple` | 87.0% (174/200) | 200 | 174 | 26 | 0 | 0 |
| `irrelevance` | 84.6% (203/240) | 240 | 203 | 37 | 0 | 0 |
| `live_simple` | 86.0% (222/258) | 258 | 222 | 35 | 1 | 0 |
| `live_multiple` | 80.3% (846/1053) | 1053 | 846 | 207 | 0 | 0 |
| `live_parallel` | 81.2% (13/16) | 16 | 13 | 3 | 0 | 0 |
| `live_parallel_multiple` | 75.0% (18/24) | 24 | 18 | 6 | 0 | 0 |
| `live_irrelevance` | 81.8% (723/884) | 884 | 723 | 161 | 0 | 0 |
| `live_relevance` | 75.0% (12/16) | 16 | 12 | 4 | 0 | 0 |
| **Overall** | **84.2% (3067/3641)** | 3641 | 3067 | 573 | 1 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 22 | 0 | 0 | 0 | 0 | 2 | 20 |
| `simple_java` | 35 | 0 | 0 | 2 | 0 | 0 | 33 |
| `simple_javascript` | 11 | 0 | 0 | 2 | 0 | 0 | 9 |
| `multiple` | 13 | 0 | 0 | 3 | 0 | 4 | 6 |
| `parallel` | 13 | 0 | 0 | 0 | 4 | 0 | 9 |
| `parallel_multiple` | 26 | 0 | 0 | 1 | 9 | 1 | 15 |
| `irrelevance` | 37 | 37 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 35 | 0 | 0 | 2 | 0 | 4 | 29 |
| `live_multiple` | 207 | 0 | 0 | 21 | 0 | 55 | 131 |
| `live_parallel` | 3 | 0 | 0 | 0 | 0 | 0 | 3 |
| `live_parallel_multiple` | 6 | 0 | 0 | 0 | 2 | 1 | 3 |
| `live_irrelevance` | 161 | 161 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 4 | 0 | 0 | 4 | 0 | 0 | 0 |
| **Overall** | 573 | 198 | 0 | 35 | 15 | 67 | 258 |

## Tokens and cost

* Input tokens: 3,982,929
* Output tokens: 728,505
* Records with complete usage: 3640 of 3641
* 1 case(s) lack reported usage (the missing count is named); the counts that were reported are included, nothing was estimated for the missing ones, so the tokens and the cost are a lower bound: `live_simple_67-31-0` (input and output)
* Cost: not given, the rates file has no entry for `claude-sonnet-5-5`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 907.0 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T20:51:43+00:00 | 2026-11-25T21:06:50+00:00 | 907.0 s |

## Run

* Run identifier: `aafcb0913f9f4dda85da1e313d228d1b`
* Requested model: `claude-sonnet-5-5`
* Actual model (as the responses report it): `claude-sonnet-5-5`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: none, every case of the categories
* Instruction: none used
* Providers in the run: anthropic
