# Comparison of two runs (openai)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/instruction-six-models/luna-plain` | `gpt-6-luna` | none |
| B | `results/instruction-six-models/luna-instruction` | `gpt-6-luna` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |

* Cases both runs selected (compared): 3641
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 400 | 400 | 7 | 20 | 340 | 33 | 0 |
| `simple_java` | 100 | 100 | 3 | 2 | 60 | 35 | 0 |
| `simple_javascript` | 50 | 50 | 3 | 2 | 34 | 11 | 0 |
| `multiple` | 200 | 200 | 3 | 10 | 176 | 11 | 0 |
| `parallel` | 200 | 200 | 3 | 8 | 171 | 18 | 0 |
| `parallel_multiple` | 200 | 200 | 8 | 26 | 137 | 29 | 0 |
| `irrelevance` | 240 | 240 | 3 | 15 | 199 | 23 | 0 |
| `live_simple` | 258 | 258 | 2 | 19 | 202 | 35 | 0 |
| `live_multiple` | 1053 | 1053 | 50 | 58 | 730 | 215 | 0 |
| `live_parallel` | 16 | 16 | 0 | 2 | 12 | 2 | 0 |
| `live_parallel_multiple` | 24 | 24 | 1 | 5 | 11 | 7 | 0 |
| `live_irrelevance` | 884 | 884 | 29 | 57 | 685 | 113 | 0 |
| `live_relevance` | 16 | 16 | 0 | 1 | 10 | 5 | 0 |
| **Overall** | 3641 | 3641 | 112 | 225 | 2767 | 537 | 0 |

## Cases not paired

A case that is unscored, or has no record, in a run is not paired. It is counted below for each run in which that is so; a case in this state in both runs is counted in both lines, and **Not paired** above counts it once, so Paired and Not paired add up to Compared.

| Category | A unscored | A no record | B unscored | B no record | Not paired |
| --- | --- | --- | --- | --- | --- |
| `simple_python` | 0 | 0 | 0 | 0 | 0 |
| `simple_java` | 0 | 0 | 0 | 0 | 0 |
| `simple_javascript` | 0 | 0 | 0 | 0 | 0 |
| `multiple` | 0 | 0 | 0 | 0 | 0 |
| `parallel` | 0 | 0 | 0 | 0 | 0 |
| `parallel_multiple` | 0 | 0 | 0 | 0 | 0 |
| `irrelevance` | 0 | 0 | 0 | 0 | 0 |
| `live_simple` | 0 | 0 | 0 | 0 | 0 |
| `live_multiple` | 0 | 0 | 0 | 0 | 0 |
| `live_parallel` | 0 | 0 | 0 | 0 | 0 |
| `live_parallel_multiple` | 0 | 0 | 0 | 0 | 0 |
| `live_irrelevance` | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 0 | 0 | 0 | 0 | 0 |
| **Overall** | 0 | 0 | 0 | 0 | 0 |

## Movement between failure classes

Paired cases that failed in both runs or changed outcome, by A's class (or pass) and B's. The classes are `called-when-none-applied`, `malformed-call`, `no-call`, `too-few-calls`, `too-many-calls`, `wrong-call`. Only counts above zero are listed.

| Category | In A | In B | Cases |
| --- | --- | --- | --- |
| `simple_python` | `pass` | `no-call` | 2 |
| `simple_python` | `pass` | `wrong-call` | 5 |
| `simple_python` | `no-call` | `pass` | 6 |
| `simple_python` | `no-call` | `no-call` | 1 |
| `simple_python` | `no-call` | `wrong-call` | 3 |
| `simple_python` | `too-many-calls` | `too-many-calls` | 1 |
| `simple_python` | `wrong-call` | `pass` | 14 |
| `simple_python` | `wrong-call` | `too-many-calls` | 1 |
| `simple_python` | `wrong-call` | `wrong-call` | 27 |
| `simple_java` | `pass` | `wrong-call` | 3 |
| `simple_java` | `no-call` | `no-call` | 1 |
| `simple_java` | `wrong-call` | `pass` | 2 |
| `simple_java` | `wrong-call` | `no-call` | 2 |
| `simple_java` | `wrong-call` | `wrong-call` | 32 |
| `simple_javascript` | `pass` | `no-call` | 2 |
| `simple_javascript` | `pass` | `wrong-call` | 1 |
| `simple_javascript` | `no-call` | `no-call` | 1 |
| `simple_javascript` | `wrong-call` | `pass` | 2 |
| `simple_javascript` | `wrong-call` | `no-call` | 2 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 8 |
| `multiple` | `pass` | `no-call` | 3 |
| `multiple` | `no-call` | `pass` | 3 |
| `multiple` | `no-call` | `no-call` | 1 |
| `multiple` | `too-many-calls` | `too-many-calls` | 3 |
| `multiple` | `wrong-call` | `pass` | 7 |
| `multiple` | `wrong-call` | `wrong-call` | 7 |
| `parallel` | `pass` | `no-call` | 1 |
| `parallel` | `pass` | `too-few-calls` | 1 |
| `parallel` | `pass` | `wrong-call` | 1 |
| `parallel` | `no-call` | `pass` | 1 |
| `parallel` | `no-call` | `no-call` | 1 |
| `parallel` | `no-call` | `too-many-calls` | 1 |
| `parallel` | `too-few-calls` | `pass` | 3 |
| `parallel` | `too-few-calls` | `too-few-calls` | 4 |
| `parallel` | `too-few-calls` | `wrong-call` | 2 |
| `parallel` | `wrong-call` | `pass` | 4 |
| `parallel` | `wrong-call` | `wrong-call` | 10 |
| `parallel_multiple` | `pass` | `no-call` | 1 |
| `parallel_multiple` | `pass` | `too-few-calls` | 3 |
| `parallel_multiple` | `pass` | `wrong-call` | 4 |
| `parallel_multiple` | `no-call` | `pass` | 1 |
| `parallel_multiple` | `no-call` | `no-call` | 1 |
| `parallel_multiple` | `too-few-calls` | `pass` | 17 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 5 |
| `parallel_multiple` | `too-few-calls` | `wrong-call` | 5 |
| `parallel_multiple` | `too-many-calls` | `pass` | 1 |
| `parallel_multiple` | `wrong-call` | `pass` | 7 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 18 |
| `irrelevance` | `pass` | `called-when-none-applied` | 3 |
| `irrelevance` | `called-when-none-applied` | `pass` | 15 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 23 |
| `live_simple` | `pass` | `no-call` | 1 |
| `live_simple` | `pass` | `wrong-call` | 1 |
| `live_simple` | `no-call` | `pass` | 9 |
| `live_simple` | `no-call` | `no-call` | 2 |
| `live_simple` | `no-call` | `wrong-call` | 1 |
| `live_simple` | `too-many-calls` | `pass` | 1 |
| `live_simple` | `wrong-call` | `pass` | 9 |
| `live_simple` | `wrong-call` | `wrong-call` | 32 |
| `live_multiple` | `pass` | `no-call` | 32 |
| `live_multiple` | `pass` | `too-many-calls` | 6 |
| `live_multiple` | `pass` | `wrong-call` | 12 |
| `live_multiple` | `no-call` | `pass` | 21 |
| `live_multiple` | `no-call` | `no-call` | 53 |
| `live_multiple` | `no-call` | `too-many-calls` | 3 |
| `live_multiple` | `no-call` | `wrong-call` | 18 |
| `live_multiple` | `too-many-calls` | `pass` | 1 |
| `live_multiple` | `too-many-calls` | `no-call` | 3 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 6 |
| `live_multiple` | `too-many-calls` | `wrong-call` | 1 |
| `live_multiple` | `wrong-call` | `pass` | 36 |
| `live_multiple` | `wrong-call` | `no-call` | 15 |
| `live_multiple` | `wrong-call` | `too-many-calls` | 2 |
| `live_multiple` | `wrong-call` | `wrong-call` | 114 |
| `live_parallel` | `too-few-calls` | `too-few-calls` | 1 |
| `live_parallel` | `wrong-call` | `pass` | 2 |
| `live_parallel` | `wrong-call` | `wrong-call` | 1 |
| `live_parallel_multiple` | `pass` | `too-many-calls` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `pass` | 2 |
| `live_parallel_multiple` | `too-few-calls` | `too-few-calls` | 3 |
| `live_parallel_multiple` | `too-few-calls` | `too-many-calls` | 1 |
| `live_parallel_multiple` | `wrong-call` | `pass` | 3 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 3 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 29 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 57 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 113 |
| `live_relevance` | `no-call` | `pass` | 1 |
| `live_relevance` | `no-call` | `no-call` | 5 |
| **Overall** | `pass` | `called-when-none-applied` | 32 |
| **Overall** | `pass` | `no-call` | 42 |
| **Overall** | `pass` | `too-few-calls` | 4 |
| **Overall** | `pass` | `too-many-calls` | 7 |
| **Overall** | `pass` | `wrong-call` | 27 |
| **Overall** | `called-when-none-applied` | `pass` | 72 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 136 |
| **Overall** | `no-call` | `pass` | 42 |
| **Overall** | `no-call` | `no-call` | 66 |
| **Overall** | `no-call` | `too-many-calls` | 4 |
| **Overall** | `no-call` | `wrong-call` | 22 |
| **Overall** | `too-few-calls` | `pass` | 22 |
| **Overall** | `too-few-calls` | `too-few-calls` | 13 |
| **Overall** | `too-few-calls` | `too-many-calls` | 1 |
| **Overall** | `too-few-calls` | `wrong-call` | 7 |
| **Overall** | `too-many-calls` | `pass` | 3 |
| **Overall** | `too-many-calls` | `no-call` | 3 |
| **Overall** | `too-many-calls` | `too-many-calls` | 10 |
| **Overall** | `too-many-calls` | `wrong-call` | 1 |
| **Overall** | `wrong-call` | `pass` | 86 |
| **Overall** | `wrong-call` | `no-call` | 19 |
| **Overall** | `wrong-call` | `too-many-calls` | 3 |
| **Overall** | `wrong-call` | `wrong-call` | 252 |
