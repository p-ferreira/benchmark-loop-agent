# Benchmark report: `gpt-6-sol` (openai)

> **Part: `development`.** This run selected only the cases of the development part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 93.5% (187/200) | 187 | 13 | 0 |
| `simple_java` | 66.0% (33/50) | 33 | 17 | 0 |
| `simple_javascript` | 64.0% (16/25) | 16 | 9 | 0 |
| `multiple` | 93.0% (93/100) | 93 | 7 | 0 |
| `parallel` | 94.0% (94/100) | 94 | 6 | 0 |
| `parallel_multiple` | 88.0% (88/100) | 88 | 12 | 0 |
| `irrelevance` | 88.3% (106/120) | 106 | 14 | 0 |
| `live_simple` | 84.5% (109/129) | 109 | 20 | 0 |
| `live_multiple` | 77.4% (407/526) | 407 | 119 | 0 |
| `live_parallel` | 75.0% (6/8) | 6 | 2 | 0 |
| `live_parallel_multiple` | 58.3% (7/12) | 7 | 5 | 0 |
| `live_irrelevance` | 87.1% (385/442) | 385 | 57 | 0 |
| `live_relevance` | 62.5% (5/8) | 5 | 3 | 0 |
| **Overall** | **84.4% (1536/1820)** | 1536 | 284 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 93.5% (187/200) | 200 | 187 | 13 | 0 | 0 |
| `simple_java` | 66.0% (33/50) | 50 | 33 | 17 | 0 | 0 |
| `simple_javascript` | 64.0% (16/25) | 25 | 16 | 9 | 0 | 0 |
| `multiple` | 93.0% (93/100) | 100 | 93 | 7 | 0 | 0 |
| `parallel` | 94.0% (94/100) | 100 | 94 | 6 | 0 | 0 |
| `parallel_multiple` | 88.0% (88/100) | 100 | 88 | 12 | 0 | 0 |
| `irrelevance` | 88.3% (106/120) | 120 | 106 | 14 | 0 | 0 |
| `live_simple` | 84.5% (109/129) | 129 | 109 | 20 | 0 | 0 |
| `live_multiple` | 77.4% (407/526) | 526 | 407 | 119 | 0 | 0 |
| `live_parallel` | 75.0% (6/8) | 8 | 6 | 2 | 0 | 0 |
| `live_parallel_multiple` | 58.3% (7/12) | 12 | 7 | 5 | 0 | 0 |
| `live_irrelevance` | 87.1% (385/442) | 442 | 385 | 57 | 0 | 0 |
| `live_relevance` | 62.5% (5/8) | 8 | 5 | 3 | 0 | 0 |
| **Overall** | **84.4% (1536/1820)** | 1820 | 1536 | 284 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 13 | 0 | 0 | 0 | 0 | 0 | 13 |
| `simple_java` | 17 | 0 | 0 | 2 | 0 | 0 | 15 |
| `simple_javascript` | 9 | 0 | 0 | 4 | 0 | 0 | 5 |
| `multiple` | 7 | 0 | 0 | 1 | 0 | 1 | 5 |
| `parallel` | 6 | 0 | 0 | 0 | 4 | 1 | 1 |
| `parallel_multiple` | 12 | 0 | 0 | 1 | 6 | 0 | 5 |
| `irrelevance` | 14 | 14 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 20 | 0 | 0 | 2 | 0 | 0 | 18 |
| `live_multiple` | 119 | 0 | 0 | 35 | 0 | 24 | 60 |
| `live_parallel` | 2 | 0 | 0 | 0 | 1 | 0 | 1 |
| `live_parallel_multiple` | 5 | 0 | 0 | 0 | 3 | 0 | 2 |
| `live_irrelevance` | 57 | 57 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 3 | 0 | 0 | 3 | 0 | 0 | 0 |
| **Overall** | 284 | 71 | 0 | 48 | 14 | 26 | 125 |

## Tokens and cost

* Input tokens: 1,023,815
* Output tokens: 126,566
* Records with complete usage: 1820 of 1820
* Cost: **$3.3133** at 2.00 (input) and 10.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://developers.openai.com/api/docs/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 332.7 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T18:43:59+00:00 | 2026-11-25T18:49:32+00:00 | 332.7 s |

## Run

* Run identifier: `eea3ed644a9847c286b149603af7672d`
* Requested model: `gpt-6-sol`
* Actual model (as the responses report it): `gpt-6-sol`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: development
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: openai
