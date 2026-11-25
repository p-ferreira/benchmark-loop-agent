# Benchmark report: `gpt-6-sol` (openai)

> **Part: `held-out`.** This run selected only the cases of the held-out part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 89.2% (107/120) | 107 | 13 | 0 |
| `simple_java` | 53.3% (16/30) | 16 | 14 | 0 |
| `simple_javascript` | 86.7% (13/15) | 13 | 2 | 0 |
| `multiple` | 85.0% (51/60) | 51 | 9 | 0 |
| `parallel` | 86.7% (52/60) | 52 | 8 | 0 |
| `parallel_multiple` | 58.3% (35/60) | 35 | 25 | 0 |
| `irrelevance` | 91.7% (66/72) | 66 | 6 | 0 |
| `live_simple` | 81.8% (63/77) | 63 | 14 | 0 |
| `live_multiple` | 74.7% (236/316) | 236 | 80 | 0 |
| `live_parallel` | 80.0% (4/5) | 4 | 1 | 0 |
| `live_parallel_multiple` | 57.1% (4/7) | 4 | 3 | 0 |
| `live_irrelevance` | 83.8% (222/265) | 222 | 43 | 0 |
| `live_relevance` | 100.0% (5/5) | 5 | 0 | 0 |
| **Overall** | **80.0% (874/1092)** | 874 | 218 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 89.2% (107/120) | 120 | 107 | 13 | 0 | 0 |
| `simple_java` | 53.3% (16/30) | 30 | 16 | 14 | 0 | 0 |
| `simple_javascript` | 86.7% (13/15) | 15 | 13 | 2 | 0 | 0 |
| `multiple` | 85.0% (51/60) | 60 | 51 | 9 | 0 | 0 |
| `parallel` | 86.7% (52/60) | 60 | 52 | 8 | 0 | 0 |
| `parallel_multiple` | 58.3% (35/60) | 60 | 35 | 25 | 0 | 0 |
| `irrelevance` | 91.7% (66/72) | 72 | 66 | 6 | 0 | 0 |
| `live_simple` | 81.8% (63/77) | 77 | 63 | 14 | 0 | 0 |
| `live_multiple` | 74.7% (236/316) | 316 | 236 | 80 | 0 | 0 |
| `live_parallel` | 80.0% (4/5) | 5 | 4 | 1 | 0 | 0 |
| `live_parallel_multiple` | 57.1% (4/7) | 7 | 4 | 3 | 0 | 0 |
| `live_irrelevance` | 83.8% (222/265) | 265 | 222 | 43 | 0 | 0 |
| `live_relevance` | 100.0% (5/5) | 5 | 5 | 0 | 0 | 0 |
| **Overall** | **80.0% (874/1092)** | 1092 | 874 | 218 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 13 | 0 | 0 | 5 | 0 | 2 | 6 |
| `simple_java` | 14 | 0 | 0 | 1 | 0 | 0 | 13 |
| `simple_javascript` | 2 | 0 | 0 | 1 | 0 | 0 | 1 |
| `multiple` | 9 | 0 | 0 | 3 | 0 | 1 | 5 |
| `parallel` | 8 | 0 | 0 | 2 | 0 | 0 | 6 |
| `parallel_multiple` | 25 | 0 | 0 | 0 | 13 | 0 | 12 |
| `irrelevance` | 6 | 6 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 14 | 0 | 0 | 6 | 0 | 1 | 7 |
| `live_multiple` | 80 | 0 | 0 | 29 | 0 | 13 | 38 |
| `live_parallel` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_parallel_multiple` | 3 | 0 | 0 | 0 | 1 | 0 | 2 |
| `live_irrelevance` | 43 | 43 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Overall** | 218 | 49 | 0 | 47 | 14 | 17 | 91 |

## Tokens and cost

* Input tokens: 440,554
* Output tokens: 85,420
* Records with complete usage: 1092 of 1092
* Cost: **$1.7353** at 2.00 (input) and 10.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://developers.openai.com/api/docs/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 201.3 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T18:55:59+00:00 | 2026-11-25T18:59:20+00:00 | 201.3 s |

## Run

* Run identifier: `7a0643081a8c46388d0c55412c986409`
* Requested model: `gpt-6-sol`
* Actual model (as the responses report it): `gpt-6-sol`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: held-out
* Instruction: none used
* Providers in the run: openai
