# Benchmark report: `gpt-6-sol` (openai)

> **Part: `validation`.** This run selected only the cases of the validation part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 71.2% (57/80) | 57 | 23 | 0 |
| `simple_java` | 60.0% (12/20) | 12 | 8 | 0 |
| `simple_javascript` | 60.0% (6/10) | 6 | 4 | 0 |
| `multiple` | 72.5% (29/40) | 29 | 11 | 0 |
| `parallel` | 75.0% (30/40) | 30 | 10 | 0 |
| `parallel_multiple` | 60.0% (24/40) | 24 | 16 | 0 |
| `irrelevance` | 97.9% (47/48) | 47 | 1 | 0 |
| `live_simple` | 59.6% (31/52) | 31 | 21 | 0 |
| `live_multiple` | 61.1% (129/211) | 129 | 82 | 0 |
| `live_parallel` | 66.7% (2/3) | 2 | 1 | 0 |
| `live_parallel_multiple` | 60.0% (3/5) | 3 | 2 | 0 |
| `live_irrelevance` | 94.9% (168/177) | 168 | 9 | 0 |
| `live_relevance` | 66.7% (2/3) | 2 | 1 | 0 |
| **Overall** | **74.1% (540/729)** | 540 | 189 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 71.2% (57/80) | 80 | 57 | 23 | 0 | 0 |
| `simple_java` | 60.0% (12/20) | 20 | 12 | 8 | 0 | 0 |
| `simple_javascript` | 60.0% (6/10) | 10 | 6 | 4 | 0 | 0 |
| `multiple` | 72.5% (29/40) | 40 | 29 | 11 | 0 | 0 |
| `parallel` | 75.0% (30/40) | 40 | 30 | 10 | 0 | 0 |
| `parallel_multiple` | 60.0% (24/40) | 40 | 24 | 16 | 0 | 0 |
| `irrelevance` | 97.9% (47/48) | 48 | 47 | 1 | 0 | 0 |
| `live_simple` | 59.6% (31/52) | 52 | 31 | 21 | 0 | 0 |
| `live_multiple` | 61.1% (129/211) | 211 | 129 | 82 | 0 | 0 |
| `live_parallel` | 66.7% (2/3) | 3 | 2 | 1 | 0 | 0 |
| `live_parallel_multiple` | 60.0% (3/5) | 5 | 3 | 2 | 0 | 0 |
| `live_irrelevance` | 94.9% (168/177) | 177 | 168 | 9 | 0 | 0 |
| `live_relevance` | 66.7% (2/3) | 3 | 2 | 1 | 0 | 0 |
| **Overall** | **74.1% (540/729)** | 729 | 540 | 189 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 23 | 0 | 0 | 18 | 0 | 1 | 4 |
| `simple_java` | 8 | 0 | 0 | 3 | 0 | 0 | 5 |
| `simple_javascript` | 4 | 0 | 0 | 2 | 0 | 0 | 2 |
| `multiple` | 11 | 0 | 0 | 10 | 0 | 0 | 1 |
| `parallel` | 10 | 0 | 0 | 7 | 1 | 0 | 2 |
| `parallel_multiple` | 16 | 0 | 0 | 5 | 8 | 0 | 3 |
| `irrelevance` | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 21 | 0 | 0 | 11 | 0 | 1 | 9 |
| `live_multiple` | 82 | 0 | 0 | 44 | 0 | 5 | 33 |
| `live_parallel` | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| `live_parallel_multiple` | 2 | 0 | 0 | 0 | 1 | 0 | 1 |
| `live_irrelevance` | 9 | 9 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| **Overall** | 189 | 10 | 0 | 102 | 10 | 7 | 60 |

## Tokens and cost

* Input tokens: 492,781
* Output tokens: 62,820
* Records with complete usage: 729 of 729
* Cost: **$1.6138** at 2.00 (input) and 10.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://developers.openai.com/api/docs/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 135.6 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T18:53:18+00:00 | 2026-11-25T18:55:33+00:00 | 135.6 s |

## Run

* Run identifier: `a31f43ddaa0f4c629c038c9493d40f43`
* Requested model: `gpt-6-sol`
* Actual model (as the responses report it): `gpt-6-sol`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: validation
* Instruction: SHA-256 `2403bf4f9dc20d38512022c0c6ff008ab1a6bd8e3d5b4e0b14ae232b44ccaf9c`, 1220 bytes
* Providers in the run: openai
