# Benchmark report: `gpt-6.1-terra` (openai)

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 86.5% (346/400) | 346 | 54 | 0 |
| `simple_java` | 64.0% (64/100) | 64 | 36 | 0 |
| `simple_javascript` | 68.0% (34/50) | 34 | 16 | 0 |
| `multiple` | 87.5% (175/200) | 175 | 25 | 0 |
| `parallel` | 87.0% (174/200) | 174 | 26 | 0 |
| `parallel_multiple` | 68.5% (137/200) | 137 | 63 | 0 |
| `irrelevance` | 83.8% (201/240) | 201 | 39 | 0 |
| `live_simple` | 77.5% (200/258) | 200 | 58 | 0 |
| `live_multiple` | 72.6% (765/1053) | 765 | 288 | 0 |
| `live_parallel` | 62.5% (10/16) | 10 | 6 | 0 |
| `live_parallel_multiple` | 58.3% (14/24) | 14 | 10 | 0 |
| `live_irrelevance` | 84.8% (750/884) | 750 | 134 | 0 |
| `live_relevance` | 62.5% (10/16) | 10 | 6 | 0 |
| **Overall** | **79.1% (2880/3641)** | 2880 | 761 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 86.5% (346/400) | 400 | 346 | 54 | 0 | 0 |
| `simple_java` | 64.0% (64/100) | 100 | 64 | 36 | 0 | 0 |
| `simple_javascript` | 68.0% (34/50) | 50 | 34 | 16 | 0 | 0 |
| `multiple` | 87.5% (175/200) | 200 | 175 | 25 | 0 | 0 |
| `parallel` | 87.0% (174/200) | 200 | 174 | 26 | 0 | 0 |
| `parallel_multiple` | 68.5% (137/200) | 200 | 137 | 63 | 0 | 0 |
| `irrelevance` | 83.8% (201/240) | 240 | 201 | 39 | 0 | 0 |
| `live_simple` | 77.5% (200/258) | 258 | 200 | 58 | 0 | 0 |
| `live_multiple` | 72.6% (765/1053) | 1053 | 765 | 288 | 0 | 0 |
| `live_parallel` | 62.5% (10/16) | 16 | 10 | 6 | 0 | 0 |
| `live_parallel_multiple` | 58.3% (14/24) | 24 | 14 | 10 | 0 | 0 |
| `live_irrelevance` | 84.8% (750/884) | 884 | 750 | 134 | 0 | 0 |
| `live_relevance` | 62.5% (10/16) | 16 | 10 | 6 | 0 | 0 |
| **Overall** | **79.1% (2880/3641)** | 3641 | 2880 | 761 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 54 | 0 | 0 | 5 | 0 | 5 | 44 |
| `simple_java` | 36 | 0 | 0 | 2 | 0 | 0 | 34 |
| `simple_javascript` | 16 | 0 | 0 | 7 | 0 | 0 | 9 |
| `multiple` | 25 | 0 | 0 | 3 | 0 | 4 | 18 |
| `parallel` | 26 | 0 | 0 | 2 | 11 | 1 | 12 |
| `parallel_multiple` | 63 | 0 | 0 | 1 | 41 | 1 | 20 |
| `irrelevance` | 39 | 39 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 58 | 0 | 0 | 13 | 0 | 2 | 43 |
| `live_multiple` | 288 | 0 | 0 | 79 | 0 | 55 | 154 |
| `live_parallel` | 6 | 0 | 0 | 1 | 1 | 0 | 4 |
| `live_parallel_multiple` | 10 | 0 | 0 | 0 | 4 | 1 | 5 |
| `live_irrelevance` | 134 | 134 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 6 | 0 | 0 | 6 | 0 | 0 | 0 |
| **Overall** | 761 | 173 | 0 | 119 | 57 | 69 | 343 |

## Tokens and cost

* Input tokens: 1,537,933
* Output tokens: 304,978
* Records with complete usage: 3641 of 3641
* Cost: not given, the rates file has no entry for `gpt-6.1-terra`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 1173.2 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T20:51:43+00:00 | 2026-11-25T21:11:17+00:00 | 1173.2 s |

## Run

* Run identifier: `59bfdaa675ca40cd85d9061df0e4f372`
* Requested model: `gpt-6.1-terra`
* Actual model (as the responses report it): `gpt-6.1-terra`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: none, every case of the categories
* Instruction: none used
* Providers in the run: openai
