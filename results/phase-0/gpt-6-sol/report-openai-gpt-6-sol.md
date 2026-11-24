# Benchmark report: `gpt-6-sol` (openai)

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 88.5% (354/400) | 354 | 46 | 0 |
| `simple_java` | 58.0% (58/100) | 58 | 42 | 0 |
| `simple_javascript` | 58.0% (29/50) | 29 | 21 | 0 |
| `multiple` | 88.0% (176/200) | 176 | 24 | 0 |
| `parallel` | 85.5% (171/200) | 171 | 29 | 0 |
| `parallel_multiple` | 64.0% (128/200) | 128 | 72 | 0 |
| `irrelevance` | 87.1% (209/240) | 209 | 31 | 0 |
| `live_simple` | 78.3% (202/258) | 202 | 56 | 0 |
| `live_multiple` | 73.8% (777/1053) | 777 | 276 | 0 |
| `live_parallel` | 75.0% (12/16) | 12 | 4 | 0 |
| `live_parallel_multiple` | 58.3% (14/24) | 14 | 10 | 0 |
| `live_irrelevance` | 83.3% (736/884) | 736 | 148 | 0 |
| `live_relevance` | 75.0% (12/16) | 12 | 4 | 0 |
| **Overall** | **79.0% (2878/3641)** | 2878 | 763 | 0 |

## Tokens and cost

* Input tokens: 1,537,933
* Output tokens: 289,726
* Records with complete usage: 3641 of 3641
* Cost: **$5.9731** at 2.00 (input) and 10.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://developers.openai.com/api/docs/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 712.1 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-24T16:06:24+00:00 | 2026-11-24T16:18:16+00:00 | 712.1 s |

## Run

* Run identifier: `949fad47a2864f26a150e2e4eb85fd8a`
* Requested model: `gpt-6-sol`
* Actual model (as the responses report it): `gpt-6-sol`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Providers in the run: openai
