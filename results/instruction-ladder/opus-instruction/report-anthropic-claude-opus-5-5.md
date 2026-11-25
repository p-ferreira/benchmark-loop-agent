# Benchmark report: `claude-opus-5-5` (anthropic)

> **Part: `validation`.** This run selected only the cases of the validation part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 95.0% (76/80) | 76 | 4 | 0 |
| `simple_java` | 70.0% (14/20) | 14 | 6 | 0 |
| `simple_javascript` | 80.0% (8/10) | 8 | 2 | 0 |
| `multiple` | 100.0% (40/40) | 40 | 0 | 0 |
| `parallel` | 92.5% (37/40) | 37 | 3 | 0 |
| `parallel_multiple` | 85.0% (34/40) | 34 | 6 | 0 |
| `irrelevance` | 89.6% (43/48) | 43 | 5 | 0 |
| `live_simple` | 71.2% (37/52) | 37 | 15 | 0 |
| `live_multiple` | 76.8% (162/211) | 162 | 49 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 0 | 0 |
| `live_parallel_multiple` | 100.0% (5/5) | 5 | 0 | 0 |
| `live_irrelevance` | 82.5% (146/177) | 146 | 31 | 0 |
| `live_relevance` | 66.7% (2/3) | 2 | 1 | 0 |
| **Overall** | **83.3% (607/729)** | 607 | 122 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 95.0% (76/80) | 80 | 76 | 4 | 0 | 0 |
| `simple_java` | 70.0% (14/20) | 20 | 14 | 6 | 0 | 0 |
| `simple_javascript` | 80.0% (8/10) | 10 | 8 | 2 | 0 | 0 |
| `multiple` | 100.0% (40/40) | 40 | 40 | 0 | 0 | 0 |
| `parallel` | 92.5% (37/40) | 40 | 37 | 3 | 0 | 0 |
| `parallel_multiple` | 85.0% (34/40) | 40 | 34 | 6 | 0 | 0 |
| `irrelevance` | 89.6% (43/48) | 48 | 43 | 5 | 0 | 0 |
| `live_simple` | 71.2% (37/52) | 52 | 37 | 15 | 0 | 0 |
| `live_multiple` | 76.8% (162/211) | 211 | 162 | 49 | 0 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 3 | 0 | 0 | 0 |
| `live_parallel_multiple` | 100.0% (5/5) | 5 | 5 | 0 | 0 | 0 |
| `live_irrelevance` | 82.5% (146/177) | 177 | 146 | 31 | 0 | 0 |
| `live_relevance` | 66.7% (2/3) | 3 | 2 | 1 | 0 | 0 |
| **Overall** | **83.3% (607/729)** | 729 | 607 | 122 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 4 | 0 | 0 | 2 | 0 | 0 | 2 |
| `simple_java` | 6 | 0 | 0 | 1 | 0 | 0 | 5 |
| `simple_javascript` | 2 | 0 | 0 | 1 | 0 | 0 | 1 |
| `multiple` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `parallel` | 3 | 0 | 0 | 0 | 1 | 0 | 2 |
| `parallel_multiple` | 6 | 0 | 0 | 0 | 2 | 0 | 4 |
| `irrelevance` | 5 | 5 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 15 | 0 | 0 | 0 | 0 | 2 | 13 |
| `live_multiple` | 49 | 0 | 0 | 3 | 0 | 6 | 40 |
| `live_parallel` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `live_parallel_multiple` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `live_irrelevance` | 31 | 31 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| **Overall** | 122 | 36 | 0 | 8 | 3 | 8 | 67 |

## Tokens and cost

* Input tokens: 909,787
* Output tokens: 115,767
* Records with complete usage: 729 of 729
* Cost: **$5.9545** at 4.00 (input) and 20.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://platform.claude.com/docs/en/about-claude/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 168.6 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T19:29:50+00:00 | 2026-11-25T19:32:38+00:00 | 168.6 s |

## Run

* Run identifier: `8a7a7daeb9ca4eff84c058fe43a74778`
* Requested model: `claude-opus-5-5`
* Actual model (as the responses report it): `claude-opus-5-5`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: validation
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: anthropic
