# Benchmark report: `claude-opus-5-5` (anthropic)

> **Part: `validation`.** This run selected only the cases of the validation part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 95.0% (76/80) | 76 | 4 | 0 |
| `simple_java` | 65.0% (13/20) | 13 | 7 | 0 |
| `simple_javascript` | 80.0% (8/10) | 8 | 2 | 0 |
| `multiple` | 95.0% (38/40) | 38 | 2 | 0 |
| `parallel` | 90.0% (36/40) | 36 | 4 | 0 |
| `parallel_multiple` | 80.0% (32/40) | 32 | 8 | 0 |
| `irrelevance` | 81.2% (39/48) | 39 | 9 | 0 |
| `live_simple` | 75.0% (39/52) | 39 | 13 | 0 |
| `live_multiple` | 74.9% (158/211) | 158 | 53 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 4 | 1 | 0 |
| `live_irrelevance` | 75.7% (134/177) | 134 | 43 | 0 |
| `live_relevance` | 66.7% (2/3) | 2 | 1 | 0 |
| **Overall** | **79.8% (582/729)** | 582 | 147 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 95.0% (76/80) | 80 | 76 | 4 | 0 | 0 |
| `simple_java` | 65.0% (13/20) | 20 | 13 | 7 | 0 | 0 |
| `simple_javascript` | 80.0% (8/10) | 10 | 8 | 2 | 0 | 0 |
| `multiple` | 95.0% (38/40) | 40 | 38 | 2 | 0 | 0 |
| `parallel` | 90.0% (36/40) | 40 | 36 | 4 | 0 | 0 |
| `parallel_multiple` | 80.0% (32/40) | 40 | 32 | 8 | 0 | 0 |
| `irrelevance` | 81.2% (39/48) | 48 | 39 | 9 | 0 | 0 |
| `live_simple` | 75.0% (39/52) | 52 | 39 | 13 | 0 | 0 |
| `live_multiple` | 74.9% (158/211) | 211 | 158 | 53 | 0 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 3 | 0 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 5 | 4 | 1 | 0 | 0 |
| `live_irrelevance` | 75.7% (134/177) | 177 | 134 | 43 | 0 | 0 |
| `live_relevance` | 66.7% (2/3) | 3 | 2 | 1 | 0 | 0 |
| **Overall** | **79.8% (582/729)** | 729 | 582 | 147 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 4 | 0 | 0 | 0 | 0 | 1 | 3 |
| `simple_java` | 7 | 0 | 0 | 1 | 0 | 0 | 6 |
| `simple_javascript` | 2 | 0 | 0 | 1 | 0 | 0 | 1 |
| `multiple` | 2 | 0 | 0 | 0 | 0 | 1 | 1 |
| `parallel` | 4 | 0 | 0 | 0 | 2 | 0 | 2 |
| `parallel_multiple` | 8 | 0 | 0 | 1 | 4 | 0 | 3 |
| `irrelevance` | 9 | 9 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 13 | 0 | 0 | 0 | 0 | 1 | 12 |
| `live_multiple` | 53 | 0 | 0 | 2 | 0 | 7 | 44 |
| `live_parallel` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `live_parallel_multiple` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_irrelevance` | 43 | 43 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| **Overall** | 147 | 52 | 0 | 6 | 6 | 10 | 73 |

## Tokens and cost

* Input tokens: 798,250
* Output tokens: 160,648
* Records with complete usage: 729 of 729
* Cost: **$6.4060** at 4.00 (input) and 20.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://platform.claude.com/docs/en/about-claude/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 219.7 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T19:29:50+00:00 | 2026-11-25T19:33:30+00:00 | 219.7 s |

## Run

* Run identifier: `6ec59ae4e06c4cc5aad1c4a793b92c32`
* Requested model: `claude-opus-5-5`
* Actual model (as the responses report it): `claude-opus-5-5`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: validation
* Instruction: none used
* Providers in the run: anthropic
