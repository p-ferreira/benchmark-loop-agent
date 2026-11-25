# Benchmark report: `gpt-6.1-terra` (openai)

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 90.8% (363/400) | 363 | 37 | 0 |
| `simple_java` | 64.0% (64/100) | 64 | 36 | 0 |
| `simple_javascript` | 68.0% (34/50) | 34 | 16 | 0 |
| `multiple` | 92.5% (185/200) | 185 | 15 | 0 |
| `parallel` | 90.5% (181/200) | 181 | 19 | 0 |
| `parallel_multiple` | 82.5% (165/200) | 165 | 35 | 0 |
| `irrelevance` | 91.7% (220/240) | 220 | 20 | 0 |
| `live_simple` | 81.4% (210/258) | 210 | 48 | 0 |
| `live_multiple` | 73.5% (774/1053) | 774 | 279 | 0 |
| `live_parallel` | 81.2% (13/16) | 13 | 3 | 0 |
| `live_parallel_multiple` | 70.8% (17/24) | 17 | 7 | 0 |
| `live_irrelevance` | 88.7% (784/884) | 784 | 100 | 0 |
| `live_relevance` | 56.2% (9/16) | 9 | 7 | 0 |
| **Overall** | **82.9% (3019/3641)** | 3019 | 622 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 90.8% (363/400) | 400 | 363 | 37 | 0 | 0 |
| `simple_java` | 64.0% (64/100) | 100 | 64 | 36 | 0 | 0 |
| `simple_javascript` | 68.0% (34/50) | 50 | 34 | 16 | 0 | 0 |
| `multiple` | 92.5% (185/200) | 200 | 185 | 15 | 0 | 0 |
| `parallel` | 90.5% (181/200) | 200 | 181 | 19 | 0 | 0 |
| `parallel_multiple` | 82.5% (165/200) | 200 | 165 | 35 | 0 | 0 |
| `irrelevance` | 91.7% (220/240) | 240 | 220 | 20 | 0 | 0 |
| `live_simple` | 81.4% (210/258) | 258 | 210 | 48 | 0 | 0 |
| `live_multiple` | 73.5% (774/1053) | 1053 | 774 | 279 | 0 | 0 |
| `live_parallel` | 81.2% (13/16) | 16 | 13 | 3 | 0 | 0 |
| `live_parallel_multiple` | 70.8% (17/24) | 24 | 17 | 7 | 0 | 0 |
| `live_irrelevance` | 88.7% (784/884) | 884 | 784 | 100 | 0 | 0 |
| `live_relevance` | 56.2% (9/16) | 16 | 9 | 7 | 0 | 0 |
| **Overall** | **82.9% (3019/3641)** | 3641 | 3019 | 622 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 37 | 0 | 0 | 8 | 0 | 1 | 28 |
| `simple_java` | 36 | 0 | 0 | 5 | 0 | 0 | 31 |
| `simple_javascript` | 16 | 0 | 0 | 6 | 0 | 0 | 10 |
| `multiple` | 15 | 0 | 0 | 4 | 0 | 1 | 10 |
| `parallel` | 19 | 0 | 0 | 1 | 5 | 3 | 10 |
| `parallel_multiple` | 35 | 0 | 0 | 5 | 7 | 2 | 21 |
| `irrelevance` | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 48 | 0 | 0 | 7 | 0 | 3 | 38 |
| `live_multiple` | 279 | 0 | 0 | 105 | 0 | 45 | 129 |
| `live_parallel` | 3 | 0 | 0 | 0 | 1 | 0 | 2 |
| `live_parallel_multiple` | 7 | 0 | 0 | 0 | 3 | 0 | 4 |
| `live_irrelevance` | 100 | 100 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 7 | 0 | 0 | 7 | 0 | 0 | 0 |
| **Overall** | 622 | 120 | 0 | 148 | 16 | 55 | 283 |

## Tokens and cost

* Input tokens: 2,007,622
* Output tokens: 261,731
* Records with complete usage: 3641 of 3641
* Cost: not given, the rates file has no entry for `gpt-6.1-terra`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 1050.5 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T20:51:43+00:00 | 2026-11-25T21:09:14+00:00 | 1050.5 s |

## Run

* Run identifier: `b9ccb99f213f408ebd61723f46be8f84`
* Requested model: `gpt-6.1-terra`
* Actual model (as the responses report it): `gpt-6.1-terra`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: none, every case of the categories
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: openai
