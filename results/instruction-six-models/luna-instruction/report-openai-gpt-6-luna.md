# Benchmark report: `gpt-6-luna` (openai)

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 90.0% (360/400) | 360 | 40 | 0 |
| `simple_java` | 62.0% (62/100) | 62 | 38 | 0 |
| `simple_javascript` | 72.0% (36/50) | 36 | 14 | 0 |
| `multiple` | 93.0% (186/200) | 186 | 14 | 0 |
| `parallel` | 89.5% (179/200) | 179 | 21 | 0 |
| `parallel_multiple` | 81.5% (163/200) | 163 | 37 | 0 |
| `irrelevance` | 89.2% (214/240) | 214 | 26 | 0 |
| `live_simple` | 85.7% (221/258) | 221 | 37 | 0 |
| `live_multiple` | 74.8% (788/1053) | 788 | 265 | 0 |
| `live_parallel` | 87.5% (14/16) | 14 | 2 | 0 |
| `live_parallel_multiple` | 66.7% (16/24) | 16 | 8 | 0 |
| `live_irrelevance` | 83.9% (742/884) | 742 | 142 | 0 |
| `live_relevance` | 68.8% (11/16) | 11 | 5 | 0 |
| **Overall** | **82.2% (2992/3641)** | 2992 | 649 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 90.0% (360/400) | 400 | 360 | 40 | 0 | 0 |
| `simple_java` | 62.0% (62/100) | 100 | 62 | 38 | 0 | 0 |
| `simple_javascript` | 72.0% (36/50) | 50 | 36 | 14 | 0 | 0 |
| `multiple` | 93.0% (186/200) | 200 | 186 | 14 | 0 | 0 |
| `parallel` | 89.5% (179/200) | 200 | 179 | 21 | 0 | 0 |
| `parallel_multiple` | 81.5% (163/200) | 200 | 163 | 37 | 0 | 0 |
| `irrelevance` | 89.2% (214/240) | 240 | 214 | 26 | 0 | 0 |
| `live_simple` | 85.7% (221/258) | 258 | 221 | 37 | 0 | 0 |
| `live_multiple` | 74.8% (788/1053) | 1053 | 788 | 265 | 0 | 0 |
| `live_parallel` | 87.5% (14/16) | 16 | 14 | 2 | 0 | 0 |
| `live_parallel_multiple` | 66.7% (16/24) | 24 | 16 | 8 | 0 | 0 |
| `live_irrelevance` | 83.9% (742/884) | 884 | 742 | 142 | 0 | 0 |
| `live_relevance` | 68.8% (11/16) | 16 | 11 | 5 | 0 | 0 |
| **Overall** | **82.2% (2992/3641)** | 3641 | 2992 | 649 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 40 | 0 | 0 | 3 | 0 | 2 | 35 |
| `simple_java` | 38 | 0 | 0 | 3 | 0 | 0 | 35 |
| `simple_javascript` | 14 | 0 | 0 | 5 | 0 | 0 | 9 |
| `multiple` | 14 | 0 | 0 | 4 | 0 | 3 | 7 |
| `parallel` | 21 | 0 | 0 | 2 | 5 | 1 | 13 |
| `parallel_multiple` | 37 | 0 | 0 | 2 | 8 | 0 | 27 |
| `irrelevance` | 26 | 26 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 37 | 0 | 0 | 3 | 0 | 0 | 34 |
| `live_multiple` | 265 | 0 | 0 | 103 | 0 | 17 | 145 |
| `live_parallel` | 2 | 0 | 0 | 0 | 1 | 0 | 1 |
| `live_parallel_multiple` | 8 | 0 | 0 | 0 | 3 | 2 | 3 |
| `live_irrelevance` | 142 | 142 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 5 | 0 | 0 | 5 | 0 | 0 | 0 |
| **Overall** | 649 | 168 | 0 | 130 | 17 | 25 | 309 |

## Tokens and cost

* Input tokens: 2,007,622
* Output tokens: 274,453
* Records with complete usage: 3641 of 3641
* Cost: not given, the rates file has no entry for `gpt-6-luna`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 653.6 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T20:51:43+00:00 | 2026-11-25T21:02:37+00:00 | 653.6 s |

## Run

* Run identifier: `d8f431302e0e4f2d87dde881a6a9e414`
* Requested model: `gpt-6-luna`
* Actual model (as the responses report it): `gpt-6-luna`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: none, every case of the categories
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: openai
