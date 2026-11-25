# Comparison of two runs (openai)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/instruction-ladder/luna-plain` | `gpt-6-luna` | none |
| B | `results/instruction-ladder/luna-instruction` | `gpt-6-luna` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |

* Cases both runs selected (compared): 729
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 80 | 80 | 0 | 4 | 69 | 7 | 0 |
| `simple_java` | 20 | 20 | 0 | 1 | 13 | 6 | 0 |
| `simple_javascript` | 10 | 10 | 1 | 3 | 4 | 2 | 0 |
| `multiple` | 40 | 40 | 0 | 4 | 36 | 0 | 0 |
| `parallel` | 40 | 40 | 1 | 4 | 29 | 6 | 0 |
| `parallel_multiple` | 40 | 40 | 2 | 5 | 25 | 8 | 0 |
| `irrelevance` | 48 | 48 | 0 | 2 | 40 | 6 | 0 |
| `live_simple` | 52 | 52 | 2 | 5 | 35 | 10 | 0 |
| `live_multiple` | 211 | 211 | 11 | 16 | 131 | 53 | 0 |
| `live_parallel` | 3 | 3 | 1 | 0 | 2 | 0 | 0 |
| `live_parallel_multiple` | 5 | 5 | 0 | 1 | 3 | 1 | 0 |
| `live_irrelevance` | 177 | 177 | 6 | 12 | 132 | 27 | 0 |
| `live_relevance` | 3 | 3 | 0 | 0 | 2 | 1 | 0 |
| **Overall** | 729 | 729 | 24 | 57 | 521 | 127 | 0 |

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
| `simple_python` | `no-call` | `pass` | 2 |
| `simple_python` | `no-call` | `wrong-call` | 1 |
| `simple_python` | `wrong-call` | `pass` | 2 |
| `simple_python` | `wrong-call` | `wrong-call` | 6 |
| `simple_java` | `no-call` | `pass` | 1 |
| `simple_java` | `wrong-call` | `wrong-call` | 6 |
| `simple_javascript` | `pass` | `wrong-call` | 1 |
| `simple_javascript` | `wrong-call` | `pass` | 3 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 2 |
| `multiple` | `no-call` | `pass` | 2 |
| `multiple` | `wrong-call` | `pass` | 2 |
| `parallel` | `pass` | `wrong-call` | 1 |
| `parallel` | `no-call` | `no-call` | 1 |
| `parallel` | `no-call` | `wrong-call` | 1 |
| `parallel` | `too-few-calls` | `pass` | 3 |
| `parallel` | `too-few-calls` | `too-few-calls` | 1 |
| `parallel` | `wrong-call` | `pass` | 1 |
| `parallel` | `wrong-call` | `wrong-call` | 3 |
| `parallel_multiple` | `pass` | `no-call` | 1 |
| `parallel_multiple` | `pass` | `too-few-calls` | 1 |
| `parallel_multiple` | `too-few-calls` | `pass` | 4 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 3 |
| `parallel_multiple` | `wrong-call` | `pass` | 1 |
| `parallel_multiple` | `wrong-call` | `too-many-calls` | 1 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 4 |
| `irrelevance` | `called-when-none-applied` | `pass` | 2 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 6 |
| `live_simple` | `pass` | `wrong-call` | 2 |
| `live_simple` | `no-call` | `pass` | 2 |
| `live_simple` | `no-call` | `wrong-call` | 1 |
| `live_simple` | `wrong-call` | `pass` | 3 |
| `live_simple` | `wrong-call` | `too-many-calls` | 1 |
| `live_simple` | `wrong-call` | `wrong-call` | 8 |
| `live_multiple` | `pass` | `no-call` | 5 |
| `live_multiple` | `pass` | `too-many-calls` | 2 |
| `live_multiple` | `pass` | `wrong-call` | 4 |
| `live_multiple` | `no-call` | `pass` | 8 |
| `live_multiple` | `no-call` | `no-call` | 14 |
| `live_multiple` | `no-call` | `too-many-calls` | 1 |
| `live_multiple` | `no-call` | `wrong-call` | 3 |
| `live_multiple` | `wrong-call` | `pass` | 8 |
| `live_multiple` | `wrong-call` | `no-call` | 3 |
| `live_multiple` | `wrong-call` | `wrong-call` | 32 |
| `live_parallel` | `pass` | `wrong-call` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `pass` | 1 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 1 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 6 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 12 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 27 |
| `live_relevance` | `no-call` | `no-call` | 1 |
| **Overall** | `pass` | `called-when-none-applied` | 6 |
| **Overall** | `pass` | `no-call` | 6 |
| **Overall** | `pass` | `too-few-calls` | 1 |
| **Overall** | `pass` | `too-many-calls` | 2 |
| **Overall** | `pass` | `wrong-call` | 9 |
| **Overall** | `called-when-none-applied` | `pass` | 14 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 33 |
| **Overall** | `no-call` | `pass` | 15 |
| **Overall** | `no-call` | `no-call` | 16 |
| **Overall** | `no-call` | `too-many-calls` | 1 |
| **Overall** | `no-call` | `wrong-call` | 6 |
| **Overall** | `too-few-calls` | `pass` | 8 |
| **Overall** | `too-few-calls` | `too-few-calls` | 4 |
| **Overall** | `wrong-call` | `pass` | 20 |
| **Overall** | `wrong-call` | `no-call` | 3 |
| **Overall** | `wrong-call` | `too-many-calls` | 2 |
| **Overall** | `wrong-call` | `wrong-call` | 62 |
