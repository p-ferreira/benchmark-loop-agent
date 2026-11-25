# Benchmark report: `gpt-6-sol` (openai)

> **Part: `held-out`.** This run selected only the cases of the held-out part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 91.7% (110/120) | 110 | 10 | 0 |
| `simple_java` | 60.0% (18/30) | 18 | 12 | 0 |
| `simple_javascript` | 80.0% (12/15) | 12 | 3 | 0 |
| `multiple` | 93.3% (56/60) | 56 | 4 | 0 |
| `parallel` | 90.0% (54/60) | 54 | 6 | 0 |
| `parallel_multiple` | 75.0% (45/60) | 45 | 15 | 0 |
| `irrelevance` | 97.2% (70/72) | 70 | 2 | 0 |
| `live_simple` | 84.4% (65/77) | 65 | 12 | 0 |
| `live_multiple` | 74.7% (236/316) | 236 | 80 | 0 |
| `live_parallel` | 80.0% (4/5) | 4 | 1 | 0 |
| `live_parallel_multiple` | 71.4% (5/7) | 5 | 2 | 0 |
| `live_irrelevance` | 84.9% (225/265) | 225 | 40 | 0 |
| `live_relevance` | 40.0% (2/5) | 2 | 3 | 0 |
| **Overall** | **82.6% (902/1092)** | 902 | 190 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 91.7% (110/120) | 120 | 110 | 10 | 0 | 0 |
| `simple_java` | 60.0% (18/30) | 30 | 18 | 12 | 0 | 0 |
| `simple_javascript` | 80.0% (12/15) | 15 | 12 | 3 | 0 | 0 |
| `multiple` | 93.3% (56/60) | 60 | 56 | 4 | 0 | 0 |
| `parallel` | 90.0% (54/60) | 60 | 54 | 6 | 0 | 0 |
| `parallel_multiple` | 75.0% (45/60) | 60 | 45 | 15 | 0 | 0 |
| `irrelevance` | 97.2% (70/72) | 72 | 70 | 2 | 0 | 0 |
| `live_simple` | 84.4% (65/77) | 77 | 65 | 12 | 0 | 0 |
| `live_multiple` | 74.7% (236/316) | 316 | 236 | 80 | 0 | 0 |
| `live_parallel` | 80.0% (4/5) | 5 | 4 | 1 | 0 | 0 |
| `live_parallel_multiple` | 71.4% (5/7) | 7 | 5 | 2 | 0 | 0 |
| `live_irrelevance` | 84.9% (225/265) | 265 | 225 | 40 | 0 | 0 |
| `live_relevance` | 40.0% (2/5) | 5 | 2 | 3 | 0 | 0 |
| **Overall** | **82.6% (902/1092)** | 1092 | 902 | 190 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 10 | 0 | 0 | 2 | 0 | 1 | 7 |
| `simple_java` | 12 | 0 | 0 | 0 | 0 | 0 | 12 |
| `simple_javascript` | 3 | 0 | 0 | 1 | 0 | 0 | 2 |
| `multiple` | 4 | 0 | 0 | 2 | 0 | 0 | 2 |
| `parallel` | 6 | 0 | 0 | 0 | 0 | 0 | 6 |
| `parallel_multiple` | 15 | 0 | 0 | 0 | 3 | 1 | 11 |
| `irrelevance` | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 12 | 0 | 0 | 3 | 0 | 0 | 9 |
| `live_multiple` | 80 | 0 | 0 | 35 | 0 | 8 | 37 |
| `live_parallel` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_parallel_multiple` | 2 | 0 | 0 | 0 | 1 | 0 | 1 |
| `live_irrelevance` | 40 | 40 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 3 | 0 | 0 | 3 | 0 | 0 | 0 |
| **Overall** | 190 | 42 | 0 | 46 | 4 | 10 | 88 |

## Tokens and cost

* Input tokens: 581,422
* Output tokens: 81,229
* Records with complete usage: 1092 of 1092
* Cost: **$1.9751** at 2.00 (input) and 10.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://developers.openai.com/api/docs/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 195.3 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T18:55:59+00:00 | 2026-11-25T18:59:14+00:00 | 195.3 s |

## Run

* Run identifier: `c928facf23f44209ba4a4ee622c4b56b`
* Requested model: `gpt-6-sol`
* Actual model (as the responses report it): `gpt-6-sol`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: held-out
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: openai
