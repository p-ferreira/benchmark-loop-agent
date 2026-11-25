# Benchmark report: `gpt-6-sol` (openai)

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 91.0% (364/400) | 364 | 36 | 0 |
| `simple_java` | 64.0% (64/100) | 64 | 36 | 0 |
| `simple_javascript` | 68.0% (34/50) | 34 | 16 | 0 |
| `multiple` | 94.0% (188/200) | 188 | 12 | 0 |
| `parallel` | 91.0% (182/200) | 182 | 18 | 0 |
| `parallel_multiple` | 80.5% (161/200) | 161 | 39 | 0 |
| `irrelevance` | 92.1% (221/240) | 221 | 19 | 0 |
| `live_simple` | 81.0% (209/258) | 209 | 49 | 0 |
| `live_multiple` | 75.5% (795/1053) | 795 | 258 | 0 |
| `live_parallel` | 81.2% (13/16) | 13 | 3 | 0 |
| `live_parallel_multiple` | 66.7% (16/24) | 16 | 8 | 0 |
| `live_irrelevance` | 86.1% (761/884) | 761 | 123 | 0 |
| `live_relevance` | 50.0% (8/16) | 8 | 8 | 0 |
| **Overall** | **82.8% (3016/3641)** | 3016 | 625 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 91.0% (364/400) | 400 | 364 | 36 | 0 | 0 |
| `simple_java` | 64.0% (64/100) | 100 | 64 | 36 | 0 | 0 |
| `simple_javascript` | 68.0% (34/50) | 50 | 34 | 16 | 0 | 0 |
| `multiple` | 94.0% (188/200) | 200 | 188 | 12 | 0 | 0 |
| `parallel` | 91.0% (182/200) | 200 | 182 | 18 | 0 | 0 |
| `parallel_multiple` | 80.5% (161/200) | 200 | 161 | 39 | 0 | 0 |
| `irrelevance` | 92.1% (221/240) | 240 | 221 | 19 | 0 | 0 |
| `live_simple` | 81.0% (209/258) | 258 | 209 | 49 | 0 | 0 |
| `live_multiple` | 75.5% (795/1053) | 1053 | 795 | 258 | 0 | 0 |
| `live_parallel` | 81.2% (13/16) | 16 | 13 | 3 | 0 | 0 |
| `live_parallel_multiple` | 66.7% (16/24) | 24 | 16 | 8 | 0 | 0 |
| `live_irrelevance` | 86.1% (761/884) | 884 | 761 | 123 | 0 | 0 |
| `live_relevance` | 50.0% (8/16) | 16 | 8 | 8 | 0 | 0 |
| **Overall** | **82.8% (3016/3641)** | 3641 | 3016 | 625 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 36 | 0 | 0 | 7 | 0 | 1 | 28 |
| `simple_java` | 36 | 0 | 0 | 4 | 0 | 0 | 32 |
| `simple_javascript` | 16 | 0 | 0 | 7 | 0 | 0 | 9 |
| `multiple` | 12 | 0 | 0 | 3 | 0 | 2 | 7 |
| `parallel` | 18 | 0 | 0 | 2 | 5 | 1 | 10 |
| `parallel_multiple` | 39 | 0 | 0 | 4 | 15 | 2 | 18 |
| `irrelevance` | 19 | 19 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 49 | 0 | 0 | 7 | 0 | 1 | 41 |
| `live_multiple` | 258 | 0 | 0 | 93 | 0 | 41 | 124 |
| `live_parallel` | 3 | 0 | 0 | 0 | 1 | 0 | 2 |
| `live_parallel_multiple` | 8 | 0 | 0 | 0 | 3 | 0 | 5 |
| `live_irrelevance` | 123 | 123 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 8 | 0 | 0 | 8 | 0 | 0 | 0 |
| **Overall** | 625 | 142 | 0 | 135 | 24 | 48 | 276 |

## Tokens and cost

* Input tokens: 2,007,622
* Output tokens: 262,147
* Records with complete usage: 3641 of 3641
* Cost: **$6.6367** at 2.00 (input) and 10.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://developers.openai.com/api/docs/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 667.4 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T20:19:48+00:00 | 2026-11-25T20:30:55+00:00 | 667.4 s |

## Run

* Run identifier: `e0b3c11872834d59af2129fcdc7950b0`
* Requested model: `gpt-6-sol`
* Actual model (as the responses report it): `gpt-6-sol`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: none, every case of the categories
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: openai
