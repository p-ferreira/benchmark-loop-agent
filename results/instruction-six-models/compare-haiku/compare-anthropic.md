# Comparison of two runs (anthropic)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/instruction-six-models/haiku-plain` | `claude-haiku-5-5` | none |
| B | `results/instruction-six-models/haiku-instruction` | `claude-haiku-5-5` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |

* Cases both runs selected (compared): 3641
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 400 | 400 | 5 | 3 | 376 | 16 | 0 |
| `simple_java` | 100 | 100 | 5 | 3 | 53 | 39 | 0 |
| `simple_javascript` | 50 | 50 | 4 | 2 | 25 | 19 | 0 |
| `multiple` | 200 | 200 | 1 | 3 | 186 | 10 | 0 |
| `parallel` | 200 | 200 | 4 | 5 | 176 | 15 | 0 |
| `parallel_multiple` | 200 | 200 | 4 | 4 | 166 | 26 | 0 |
| `irrelevance` | 240 | 240 | 1 | 12 | 203 | 24 | 0 |
| `live_simple` | 258 | 257 | 3 | 8 | 211 | 35 | 1 |
| `live_multiple` | 1053 | 1053 | 29 | 27 | 778 | 219 | 0 |
| `live_parallel` | 16 | 16 | 0 | 1 | 14 | 1 | 0 |
| `live_parallel_multiple` | 24 | 24 | 0 | 1 | 18 | 5 | 0 |
| `live_irrelevance` | 884 | 884 | 8 | 45 | 712 | 119 | 0 |
| `live_relevance` | 16 | 16 | 0 | 0 | 11 | 5 | 0 |
| **Overall** | 3641 | 3640 | 64 | 114 | 2929 | 533 | 1 |

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
| `live_simple` | 1 | 0 | 1 | 0 | 1 |
| `live_multiple` | 0 | 0 | 0 | 0 | 0 |
| `live_parallel` | 0 | 0 | 0 | 0 | 0 |
| `live_parallel_multiple` | 0 | 0 | 0 | 0 | 0 |
| `live_irrelevance` | 0 | 0 | 0 | 0 | 0 |
| `live_relevance` | 0 | 0 | 0 | 0 | 0 |
| **Overall** | 1 | 0 | 1 | 0 | 1 |

## Movement between failure classes

Paired cases that failed in both runs or changed outcome, by A's class (or pass) and B's. The classes are `called-when-none-applied`, `malformed-call`, `no-call`, `too-few-calls`, `too-many-calls`, `wrong-call`. Only counts above zero are listed.

| Category | In A | In B | Cases |
| --- | --- | --- | --- |
| `simple_python` | `pass` | `no-call` | 2 |
| `simple_python` | `pass` | `wrong-call` | 3 |
| `simple_python` | `no-call` | `no-call` | 2 |
| `simple_python` | `no-call` | `too-many-calls` | 1 |
| `simple_python` | `no-call` | `wrong-call` | 1 |
| `simple_python` | `too-many-calls` | `no-call` | 1 |
| `simple_python` | `wrong-call` | `pass` | 3 |
| `simple_python` | `wrong-call` | `wrong-call` | 11 |
| `simple_java` | `pass` | `no-call` | 3 |
| `simple_java` | `pass` | `wrong-call` | 2 |
| `simple_java` | `no-call` | `pass` | 3 |
| `simple_java` | `no-call` | `no-call` | 4 |
| `simple_java` | `wrong-call` | `no-call` | 3 |
| `simple_java` | `wrong-call` | `wrong-call` | 32 |
| `simple_javascript` | `pass` | `no-call` | 4 |
| `simple_javascript` | `no-call` | `no-call` | 9 |
| `simple_javascript` | `wrong-call` | `pass` | 2 |
| `simple_javascript` | `wrong-call` | `no-call` | 2 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 8 |
| `multiple` | `pass` | `no-call` | 1 |
| `multiple` | `no-call` | `pass` | 2 |
| `multiple` | `no-call` | `no-call` | 1 |
| `multiple` | `too-many-calls` | `pass` | 1 |
| `multiple` | `too-many-calls` | `too-many-calls` | 3 |
| `multiple` | `wrong-call` | `wrong-call` | 6 |
| `parallel` | `pass` | `no-call` | 2 |
| `parallel` | `pass` | `too-few-calls` | 2 |
| `parallel` | `too-few-calls` | `pass` | 1 |
| `parallel` | `too-few-calls` | `too-few-calls` | 4 |
| `parallel` | `too-many-calls` | `pass` | 1 |
| `parallel` | `wrong-call` | `pass` | 3 |
| `parallel` | `wrong-call` | `wrong-call` | 11 |
| `parallel_multiple` | `pass` | `too-few-calls` | 2 |
| `parallel_multiple` | `pass` | `wrong-call` | 2 |
| `parallel_multiple` | `no-call` | `pass` | 1 |
| `parallel_multiple` | `no-call` | `no-call` | 1 |
| `parallel_multiple` | `too-few-calls` | `pass` | 1 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 10 |
| `parallel_multiple` | `too-many-calls` | `too-many-calls` | 1 |
| `parallel_multiple` | `wrong-call` | `pass` | 2 |
| `parallel_multiple` | `wrong-call` | `too-few-calls` | 1 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 13 |
| `irrelevance` | `pass` | `called-when-none-applied` | 1 |
| `irrelevance` | `called-when-none-applied` | `pass` | 12 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 24 |
| `live_simple` | `pass` | `wrong-call` | 3 |
| `live_simple` | `no-call` | `pass` | 2 |
| `live_simple` | `no-call` | `no-call` | 5 |
| `live_simple` | `wrong-call` | `pass` | 6 |
| `live_simple` | `wrong-call` | `wrong-call` | 30 |
| `live_multiple` | `pass` | `no-call` | 18 |
| `live_multiple` | `pass` | `too-many-calls` | 2 |
| `live_multiple` | `pass` | `wrong-call` | 9 |
| `live_multiple` | `no-call` | `pass` | 7 |
| `live_multiple` | `no-call` | `no-call` | 29 |
| `live_multiple` | `no-call` | `too-many-calls` | 1 |
| `live_multiple` | `no-call` | `wrong-call` | 3 |
| `live_multiple` | `too-many-calls` | `pass` | 4 |
| `live_multiple` | `too-many-calls` | `no-call` | 5 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 30 |
| `live_multiple` | `too-many-calls` | `wrong-call` | 9 |
| `live_multiple` | `wrong-call` | `pass` | 16 |
| `live_multiple` | `wrong-call` | `no-call` | 23 |
| `live_multiple` | `wrong-call` | `too-many-calls` | 1 |
| `live_multiple` | `wrong-call` | `wrong-call` | 118 |
| `live_parallel` | `wrong-call` | `pass` | 1 |
| `live_parallel` | `wrong-call` | `wrong-call` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `pass` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `too-few-calls` | 3 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 2 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 8 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 45 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 119 |
| `live_relevance` | `no-call` | `no-call` | 5 |
| **Overall** | `pass` | `called-when-none-applied` | 9 |
| **Overall** | `pass` | `no-call` | 30 |
| **Overall** | `pass` | `too-few-calls` | 4 |
| **Overall** | `pass` | `too-many-calls` | 2 |
| **Overall** | `pass` | `wrong-call` | 19 |
| **Overall** | `called-when-none-applied` | `pass` | 57 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 143 |
| **Overall** | `no-call` | `pass` | 15 |
| **Overall** | `no-call` | `no-call` | 56 |
| **Overall** | `no-call` | `too-many-calls` | 2 |
| **Overall** | `no-call` | `wrong-call` | 4 |
| **Overall** | `too-few-calls` | `pass` | 3 |
| **Overall** | `too-few-calls` | `too-few-calls` | 17 |
| **Overall** | `too-many-calls` | `pass` | 6 |
| **Overall** | `too-many-calls` | `no-call` | 6 |
| **Overall** | `too-many-calls` | `too-many-calls` | 34 |
| **Overall** | `too-many-calls` | `wrong-call` | 9 |
| **Overall** | `wrong-call` | `pass` | 33 |
| **Overall** | `wrong-call` | `no-call` | 28 |
| **Overall** | `wrong-call` | `too-few-calls` | 1 |
| **Overall** | `wrong-call` | `too-many-calls` | 1 |
| **Overall** | `wrong-call` | `wrong-call` | 232 |
