# Benchmark report: `gpt-6.1-terra` (openai)

> **Part: `validation`.** This run selected only the cases of the validation part of the split.

## Accuracy

Accuracy is pass / (pass + fail): unscored cases were not judged and are left out of it (they are counted below). **Overall** pools every judged case of the model, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

| Category | Accuracy | Pass | Fail | Unscored |
| --- | --- | --- | --- | --- |
| `simple_python` | 87.5% (70/80) | 70 | 10 | 0 |
| `simple_java` | 65.0% (13/20) | 13 | 7 | 0 |
| `simple_javascript` | 70.0% (7/10) | 7 | 3 | 0 |
| `multiple` | 95.0% (38/40) | 38 | 2 | 0 |
| `parallel` | 85.0% (34/40) | 34 | 6 | 0 |
| `parallel_multiple` | 70.0% (28/40) | 28 | 12 | 0 |
| `irrelevance` | 95.8% (46/48) | 46 | 2 | 0 |
| `live_simple` | 71.2% (37/52) | 37 | 15 | 0 |
| `live_multiple` | 71.6% (151/211) | 151 | 60 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 4 | 1 | 0 |
| `live_irrelevance` | 88.7% (157/177) | 157 | 20 | 0 |
| `live_relevance` | 33.3% (1/3) | 1 | 2 | 0 |
| **Overall** | **80.8% (589/729)** | 589 | 140 | 0 |

## Comparison figure

Passes divided by the cases the run selected, as `run.json` records them. Unscored cases and selected cases with no record stay in the denominator, so both count against the figure.

| Category | Comparison figure | Selected | Pass | Fail | Unscored | No record |
| --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 87.5% (70/80) | 80 | 70 | 10 | 0 | 0 |
| `simple_java` | 65.0% (13/20) | 20 | 13 | 7 | 0 | 0 |
| `simple_javascript` | 70.0% (7/10) | 10 | 7 | 3 | 0 | 0 |
| `multiple` | 95.0% (38/40) | 40 | 38 | 2 | 0 | 0 |
| `parallel` | 85.0% (34/40) | 40 | 34 | 6 | 0 | 0 |
| `parallel_multiple` | 70.0% (28/40) | 40 | 28 | 12 | 0 | 0 |
| `irrelevance` | 95.8% (46/48) | 48 | 46 | 2 | 0 | 0 |
| `live_simple` | 71.2% (37/52) | 52 | 37 | 15 | 0 | 0 |
| `live_multiple` | 71.6% (151/211) | 211 | 151 | 60 | 0 | 0 |
| `live_parallel` | 100.0% (3/3) | 3 | 3 | 0 | 0 | 0 |
| `live_parallel_multiple` | 80.0% (4/5) | 5 | 4 | 1 | 0 | 0 |
| `live_irrelevance` | 88.7% (157/177) | 177 | 157 | 20 | 0 | 0 |
| `live_relevance` | 33.3% (1/3) | 3 | 1 | 2 | 0 | 0 |
| **Overall** | **80.8% (589/729)** | 729 | 589 | 140 | 0 | 0 |

## Failure classes

Each failed case has exactly one class, the first of these that applies: `called-when-none-applied` (a failure in `irrelevance` or `live_irrelevance`); `malformed-call` (a returned call could not be scored: arguments that are not a JSON object, or nested too deep); `no-call` (a call was expected and none came back); `too-few-calls` and `too-many-calls` (the number of calls differs from the expected answer's); `wrong-call` (the number is right and the checker rejected a name, a parameter, a type or a value). Unscored cases are not failures and are not counted here.

| Category | Failed | `called-when-none-applied` | `malformed-call` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 10 | 0 | 0 | 2 | 0 | 1 | 7 |
| `simple_java` | 7 | 0 | 0 | 2 | 0 | 0 | 5 |
| `simple_javascript` | 3 | 0 | 0 | 1 | 0 | 0 | 2 |
| `multiple` | 2 | 0 | 0 | 1 | 0 | 0 | 1 |
| `parallel` | 6 | 0 | 0 | 1 | 2 | 0 | 3 |
| `parallel_multiple` | 12 | 0 | 0 | 3 | 4 | 0 | 5 |
| `irrelevance` | 2 | 2 | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 15 | 0 | 0 | 0 | 0 | 1 | 14 |
| `live_multiple` | 60 | 0 | 0 | 17 | 0 | 6 | 37 |
| `live_parallel` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `live_parallel_multiple` | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `live_irrelevance` | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 2 | 0 | 0 | 2 | 0 | 0 | 0 |
| **Overall** | 140 | 22 | 0 | 29 | 6 | 8 | 75 |

## Tokens and cost

* Input tokens: 402,385
* Output tokens: 55,698
* Records with complete usage: 729 of 729
* Cost: not given, the rates file has no entry for `gpt-6.1-terra`.

## Time

The wall time is that of the whole run, as saved in `run.json`; all providers of the run share its invocations.

* Wall time: 210.1 s over 1 invocation(s)

| Invocation | Concurrency | Started | Ended | Wall time |
| --- | --- | --- | --- | --- |
| 1 | 8 | 2026-11-25T19:29:50+00:00 | 2026-11-25T19:33:20+00:00 | 210.1 s |

## Run

* Run identifier: `75db064f0de049028290ffe4308fb72e`
* Requested model: `gpt-6.1-terra`
* Actual model (as the responses report it): `gpt-6.1-terra`
* Dataset revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`
* Scorer revision: `ShishirPatil/gorilla@6ea57973c7a6097fd7c5915698c54c17c5b1b6c8:berkeley-function-call-leaderboard/bfcl_eval/eval_checker (ast_checker.py, eval_runner.py rules)`
* Categories: `simple_python`, `simple_java`, `simple_javascript`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `live_parallel`, `live_parallel_multiple`, `live_irrelevance`, `live_relevance`
* Sample size per category: all cases
* Seed: 0
* Split part: validation
* Instruction: SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes
* Providers in the run: openai
