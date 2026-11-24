# Benchmark report: `claude-opus-5-5` (anthropic)

> **Incomplete run.** 1 case(s) are unscored.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 97.0% (388/400) | 388 | 12 | 0 |
| `simple_java` | 67.0% (67/100) | 67 | 33 | 0 |
| `simple_javascript` | 82.0% (41/50) | 41 | 9 | 0 |
| `multiple` | 94.0% (188/200) | 188 | 12 | 0 |
| `parallel` | 91.5% (183/200) | 183 | 17 | 0 |
| `parallel_multiple` | 87.0% (174/200) | 174 | 26 | 0 |
| `irrelevance` | 81.2% (195/240) | 195 | 45 | 0 |
| `live_simple` | 86.0% (221/257) | 221 | 36 | 1 |
| `live_multiple` | 80.6% (849/1053) | 849 | 204 | 0 |
| `live_parallel` | 81.2% (13/16) | 13 | 3 | 0 |
| `live_parallel_multiple` | 66.7% (16/24) | 16 | 8 | 0 |
| `live_irrelevance` | 78.6% (695/884) | 695 | 189 | 0 |
| `live_relevance` | 68.8% (11/16) | 11 | 5 | 0 |
| **Overall** | **83.5% (3041/3640)** | 3041 | 599 | 1 |

## Tokens and cost

* Input tokens: 3,982,928
* Output tokens: 803,252
* Records with complete usage: 3640 of 3641
* 1 case(s) lack reported usage (the missing count is named); the counts that were reported are included, nothing was estimated for the missing ones, so the tokens and the cost are a lower bound: `live_simple_67-31-0` (input and output)
* Cost: **$31.9968** at 4.00 (input) and 20.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://platform.claude.com/docs/en/about-claude/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 1144.0 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-24T16:06:24+00:00 | 2026-11-24T16:25:28+00:00 | 1144.0 s |

## Run

* Run identifier: `38aaebdcc8e649b5a1afe67c6cf5d095`
* Requested model: `claude-opus-5-5`
* Actual model (as the responses report it): `claude-opus-5-5`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Providers in the run: anthropic
