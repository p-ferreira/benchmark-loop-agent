# Benchmark report: `gpt-6-sol` (openai)

> **Part: `validation`.** This run selected only the cases of the validation part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 92.5% (74/80) | 74 | 6 | 0 |
| `simple_java` | 70.0% (14/20) | 14 | 6 | 0 |
| `simple_javascript` | 60.0% (6/10) | 6 | 4 | 0 |
| `multiple` | 97.5% (39/40) | 39 | 1 | 0 |
| `parallel` | 85.0% (34/40) | 34 | 6 | 0 |
| `parallel_multiple` | 67.5% (27/40) | 27 | 13 | 0 |
| `irrelevance` | 93.8% (45/48) | 45 | 3 | 0 |
| `live_simple` | 69.2% (36/52) | 36 | 16 | 0 |
| `live_multiple` | 72.0% (152/211) | 152 | 59 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 4 | 1 | 0 |
| `live_irrelevance` | 84.7% (150/177) | 150 | 27 | 0 |
| `live_relevance` | 66.7% (2/3) | 2 | 1 | 0 |
| **Overall** | **80.4% (586/729)** | 586 | 143 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 92.5% (74/80) | 80 | 74 | 6 | 0 | 0 |
| `simple_java` | 70.0% (14/20) | 20 | 14 | 6 | 0 | 0 |
| `simple_javascript` | 60.0% (6/10) | 10 | 6 | 4 | 0 | 0 |
| `multiple` | 97.5% (39/40) | 40 | 39 | 1 | 0 | 0 |
| `parallel` | 85.0% (34/40) | 40 | 34 | 6 | 0 | 0 |
| `parallel_multiple` | 67.5% (27/40) | 40 | 27 | 13 | 0 | 0 |
| `irrelevance` | 93.8% (45/48) | 48 | 45 | 3 | 0 | 0 |
| `live_simple` | 69.2% (36/52) | 52 | 36 | 16 | 0 | 0 |
| `live_multiple` | 72.0% (152/211) | 211 | 152 | 59 | 0 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 3 | 0 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 5 | 4 | 1 | 0 | 0 |
| `live_irrelevance` | 84.7% (150/177) | 177 | 150 | 27 | 0 | 0 |
| `live_relevance` | 66.7% (2/3) | 3 | 2 | 1 | 0 | 0 |
| **Overall** | **80.4% (586/729)** | 729 | 586 | 143 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 6 | 0 | 0 | 1 | 0 | 1 | 4 |
| `simple_java` | 6 | 0 | 0 | 2 | 0 | 0 | 4 |
| `simple_javascript` | 4 | 0 | 0 | 2 | 0 | 0 | 2 |
| `multiple` | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| `parallel` | 6 | 0 | 0 | 1 | 1 | 0 | 4 |
| `parallel_multiple` | 13 | 0 | 0 | 2 | 4 | 0 | 7 |
| `irrelevance` | 3 | 3 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 16 | 0 | 0 | 0 | 0 | 2 | 14 |
| `live_multiple` | 59 | 0 | 0 | 18 | 0 | 3 | 38 |
| `live_parallel` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `live_parallel_multiple` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_irrelevance` | 27 | 27 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| **Overall** | 143 | 30 | 0 | 28 | 5 | 6 | 74 |

## Tokens and cost

* Input tokens: 402,385
* Output tokens: 54,860
* Records with complete usage: 729 of 729
* Cost: **$1.3534** at 2.00 (input) and 10.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://developers.openai.com/api/docs/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 133.5 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T18:53:18+00:00 | 2026-11-25T18:55:31+00:00 | 133.5 s |

## Run

* Run identifier: `d150aaca78ad410a98a8f87422723bcf`
* Requested model: `gpt-6-sol`
* Actual model (as the responses report it): `gpt-6-sol`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: validation
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: openai
