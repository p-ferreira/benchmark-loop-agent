# Benchmark report: `claude-opus-5-5` (anthropic)

> **Incomplete run.** 1 case(s) are unscored.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 96.5% (386/400) | 386 | 14 | 0 |
| `simple_java` | 70.0% (70/100) | 70 | 30 | 0 |
| `simple_javascript` | 86.0% (43/50) | 43 | 7 | 0 |
| `multiple` | 96.0% (192/200) | 192 | 8 | 0 |
| `parallel` | 94.0% (188/200) | 188 | 12 | 0 |
| `parallel_multiple` | 90.5% (181/200) | 181 | 19 | 0 |
| `irrelevance` | 90.0% (216/240) | 216 | 24 | 0 |
| `live_simple` | 85.6% (220/257) | 220 | 37 | 1 |
| `live_multiple` | 81.4% (857/1053) | 857 | 196 | 0 |
| `live_parallel` | 87.5% (14/16) | 14 | 2 | 0 |
| `live_parallel_multiple` | 75.0% (18/24) | 18 | 6 | 0 |
| `live_irrelevance` | 83.6% (739/884) | 739 | 145 | 0 |
| `live_relevance` | 62.5% (10/16) | 10 | 6 | 0 |
| **Overall** | **86.1% (3134/3640)** | 3134 | 506 | 1 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 96.5% (386/400) | 400 | 386 | 14 | 0 | 0 |
| `simple_java` | 70.0% (70/100) | 100 | 70 | 30 | 0 | 0 |
| `simple_javascript` | 86.0% (43/50) | 50 | 43 | 7 | 0 | 0 |
| `multiple` | 96.0% (192/200) | 200 | 192 | 8 | 0 | 0 |
| `parallel` | 94.0% (188/200) | 200 | 188 | 12 | 0 | 0 |
| `parallel_multiple` | 90.5% (181/200) | 200 | 181 | 19 | 0 | 0 |
| `irrelevance` | 90.0% (216/240) | 240 | 216 | 24 | 0 | 0 |
| `live_simple` | 85.3% (220/258) | 258 | 220 | 37 | 1 | 0 |
| `live_multiple` | 81.4% (857/1053) | 1053 | 857 | 196 | 0 | 0 |
| `live_parallel` | 87.5% (14/16) | 16 | 14 | 2 | 0 | 0 |
| `live_parallel_multiple` | 75.0% (18/24) | 24 | 18 | 6 | 0 | 0 |
| `live_irrelevance` | 83.6% (739/884) | 884 | 739 | 145 | 0 | 0 |
| `live_relevance` | 62.5% (10/16) | 16 | 10 | 6 | 0 | 0 |
| **Overall** | **86.1% (3134/3641)** | 3641 | 3134 | 506 | 1 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 14 | 0 | 0 | 3 | 0 | 1 | 10 |
| `simple_java` | 30 | 0 | 0 | 2 | 0 | 0 | 28 |
| `simple_javascript` | 7 | 0 | 0 | 2 | 0 | 0 | 5 |
| `multiple` | 8 | 0 | 0 | 0 | 0 | 3 | 5 |
| `parallel` | 12 | 0 | 0 | 0 | 3 | 2 | 7 |
| `parallel_multiple` | 19 | 0 | 0 | 0 | 3 | 2 | 14 |
| `irrelevance` | 24 | 24 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 37 | 0 | 0 | 0 | 0 | 3 | 34 |
| `live_multiple` | 196 | 0 | 0 | 29 | 0 | 41 | 126 |
| `live_parallel` | 2 | 0 | 0 | 0 | 0 | 0 | 2 |
| `live_parallel_multiple` | 6 | 0 | 0 | 0 | 1 | 0 | 5 |
| `live_irrelevance` | 145 | 145 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 6 | 0 | 0 | 6 | 0 | 0 | 0 |
| **Overall** | 506 | 169 | 0 | 42 | 7 | 52 | 236 |

## Tokens and cost

* Input tokens: 4,539,848
* Output tokens: 558,153
* Records with complete usage: 3640 of 3641
* 1 case(s) lack reported usage (the missing count is named); the counts that were reported are included, nothing was estimated for the missing ones, so the tokens and the cost are a lower bound: `live_simple_67-31-0` (input and output)
* Cost: **$29.3225** at 4.00 (input) and 20.00 (output) US dollars per 1 million tokens, standard tier ([pricing page](https://platform.claude.com/docs/en/about-claude/pricing), read on 2026-11-23).
* The cost counts all input tokens at the uncached input rate. The records do not separate cached input, which both providers price lower, so the cost can overstate what was charged. With missing usage, the figure is a lower bound only on this uncached-rate calculation from complete usage; real discounts can put the charge below it.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 831.5 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T20:19:48+00:00 | 2026-11-25T20:33:39+00:00 | 831.5 s |

## Run

* Run identifier: `132bc99d69ee41e0a7d60ab24f148691`
* Requested model: `claude-opus-5-5`
* Actual model (as the responses report it): `claude-opus-5-5`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: none, every case of the categories
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: anthropic
