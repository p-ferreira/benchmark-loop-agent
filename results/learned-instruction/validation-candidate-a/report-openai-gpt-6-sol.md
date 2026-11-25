# Benchmark report: `gpt-6-sol` (openai)

> **Part: `validation`.** This run selected only the cases of the validation part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 67.5% (54/80) | 54 | 26 | 0 |
| `simple_java` | 65.0% (13/20) | 13 | 7 | 0 |
| `simple_javascript` | 40.0% (4/10) | 4 | 6 | 0 |
| `multiple` | 72.5% (29/40) | 29 | 11 | 0 |
| `parallel` | 70.0% (28/40) | 28 | 12 | 0 |
| `parallel_multiple` | 62.5% (25/40) | 25 | 15 | 0 |
| `irrelevance` | 97.9% (47/48) | 47 | 1 | 0 |
| `live_simple` | 53.8% (28/52) | 28 | 24 | 0 |
| `live_multiple` | 46.9% (99/211) | 99 | 112 | 0 |
| `live_parallel` | 0.0% (0/3) | 0 | 3 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 4 | 1 | 0 |
| `live_irrelevance` | 97.7% (173/177) | 173 | 4 | 0 |
| `live_relevance` | 33.3% (1/3) | 1 | 2 | 0 |
| **Overall** | **69.3% (505/729)** | 505 | 224 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 67.5% (54/80) | 80 | 54 | 26 | 0 | 0 |
| `simple_java` | 65.0% (13/20) | 20 | 13 | 7 | 0 | 0 |
| `simple_javascript` | 40.0% (4/10) | 10 | 4 | 6 | 0 | 0 |
| `multiple` | 72.5% (29/40) | 40 | 29 | 11 | 0 | 0 |
| `parallel` | 70.0% (28/40) | 40 | 28 | 12 | 0 | 0 |
| `parallel_multiple` | 62.5% (25/40) | 40 | 25 | 15 | 0 | 0 |
| `irrelevance` | 97.9% (47/48) | 48 | 47 | 1 | 0 | 0 |
| `live_simple` | 53.8% (28/52) | 52 | 28 | 24 | 0 | 0 |
| `live_multiple` | 46.9% (99/211) | 211 | 99 | 112 | 0 | 0 |
| `live_parallel` | 0.0% (0/3) | 3 | 0 | 3 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 5 | 4 | 1 | 0 | 0 |
| `live_irrelevance` | 97.7% (173/177) | 177 | 173 | 4 | 0 | 0 |
| `live_relevance` | 33.3% (1/3) | 3 | 1 | 2 | 0 | 0 |
| **Overall** | **69.3% (505/729)** | 729 | 505 | 224 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 26 | 0 | 0 | 22 | 0 | 0 | 4 |
| `simple_java` | 7 | 0 | 0 | 3 | 0 | 0 | 4 |
| `simple_javascript` | 6 | 0 | 0 | 4 | 0 | 0 | 2 |
| `multiple` | 11 | 0 | 0 | 10 | 0 | 0 | 1 |
| `parallel` | 12 | 0 | 0 | 9 | 0 | 0 | 3 |
| `parallel_multiple` | 15 | 0 | 0 | 11 | 3 | 0 | 1 |
| `irrelevance` | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 24 | 0 | 0 | 16 | 0 | 0 | 8 |
| `live_multiple` | 112 | 0 | 0 | 78 | 0 | 3 | 31 |
| `live_parallel` | 3 | 0 | 0 | 3 | 0 | 0 | 0 |
| `live_parallel_multiple` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_irrelevance` | 4 | 4 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 2 | 0 | 0 | 2 | 0 | 0 | 0 |
| **Overall** | 224 | 5 | 0 | 158 | 3 | 3 | 55 |

## Tokens and cost

* Input tokens: 610,879
* Output tokens: 63,294
* Records with complete usage: 729 of 729
* Cost: **$1.8547** at 2.00 (input) and 10.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://developers.openai.com/api/docs/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 140.7 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T18:53:18+00:00 | 2026-11-25T18:55:39+00:00 | 140.7 s |

## Run

* Run identifier: `28e25cf2b88240d7b7f89021480ab031`
* Requested model: `gpt-6-sol`
* Actual model (as the responses report it): `gpt-6-sol`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: validation
* Instruction: SHA-256 `f4bf3a94cd4e6a7bef4e478a5687940c0917e7e81eb993b1f09da62fe6f578e1`, 1996 bytes
* Providers in the run: openai
