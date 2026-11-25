# Benchmark report: `gpt-6-sol` (openai)

> **Part: `validation`.** This run selected only the cases of the validation part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 83.8% (67/80) | 67 | 13 | 0 |
| `simple_java` | 65.0% (13/20) | 13 | 7 | 0 |
| `simple_javascript` | 40.0% (4/10) | 4 | 6 | 0 |
| `multiple` | 92.5% (37/40) | 37 | 3 | 0 |
| `parallel` | 77.5% (31/40) | 31 | 9 | 0 |
| `parallel_multiple` | 60.0% (24/40) | 24 | 16 | 0 |
| `irrelevance` | 87.5% (42/48) | 42 | 6 | 0 |
| `live_simple` | 71.2% (37/52) | 37 | 15 | 0 |
| `live_multiple` | 68.2% (144/211) | 144 | 67 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 4 | 1 | 0 |
| `live_irrelevance` | 78.5% (139/177) | 139 | 38 | 0 |
| `live_relevance` | 66.7% (2/3) | 2 | 1 | 0 |
| **Overall** | **75.0% (547/729)** | 547 | 182 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 83.8% (67/80) | 80 | 67 | 13 | 0 | 0 |
| `simple_java` | 65.0% (13/20) | 20 | 13 | 7 | 0 | 0 |
| `simple_javascript` | 40.0% (4/10) | 10 | 4 | 6 | 0 | 0 |
| `multiple` | 92.5% (37/40) | 40 | 37 | 3 | 0 | 0 |
| `parallel` | 77.5% (31/40) | 40 | 31 | 9 | 0 | 0 |
| `parallel_multiple` | 60.0% (24/40) | 40 | 24 | 16 | 0 | 0 |
| `irrelevance` | 87.5% (42/48) | 48 | 42 | 6 | 0 | 0 |
| `live_simple` | 71.2% (37/52) | 52 | 37 | 15 | 0 | 0 |
| `live_multiple` | 68.2% (144/211) | 211 | 144 | 67 | 0 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 3 | 0 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 5 | 4 | 1 | 0 | 0 |
| `live_irrelevance` | 78.5% (139/177) | 177 | 139 | 38 | 0 | 0 |
| `live_relevance` | 66.7% (2/3) | 3 | 2 | 1 | 0 | 0 |
| **Overall** | **75.0% (547/729)** | 729 | 547 | 182 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 13 | 0 | 0 | 4 | 0 | 1 | 8 |
| `simple_java` | 7 | 0 | 0 | 2 | 0 | 0 | 5 |
| `simple_javascript` | 6 | 0 | 0 | 3 | 0 | 0 | 3 |
| `multiple` | 3 | 0 | 0 | 1 | 0 | 0 | 2 |
| `parallel` | 9 | 0 | 0 | 1 | 2 | 0 | 6 |
| `parallel_multiple` | 16 | 0 | 0 | 0 | 12 | 0 | 4 |
| `irrelevance` | 6 | 6 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 15 | 0 | 0 | 3 | 0 | 0 | 12 |
| `live_multiple` | 67 | 0 | 0 | 23 | 0 | 3 | 41 |
| `live_parallel` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `live_parallel_multiple` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_irrelevance` | 38 | 38 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| **Overall** | 182 | 44 | 0 | 38 | 14 | 4 | 82 |

## Tokens and cost

* Input tokens: 308,344
* Output tokens: 55,701
* Records with complete usage: 729 of 729
* Cost: **$1.1737** at 2.00 (input) and 10.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://developers.openai.com/api/docs/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 135.4 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T16:51:19+00:00 | 2026-11-25T16:53:35+00:00 | 135.4 s |

## Run

* Run identifier: `a69f5772bac740a7b6de792e159aaa6a`
* Requested model: `gpt-6-sol`
* Actual model (as the responses report it): `gpt-6-sol`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: validation
* Instruction: none used
* Providers in the run: openai
