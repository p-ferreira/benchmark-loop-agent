# Comparison of two runs (anthropic)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/instruction-ladder/opus-plain` | `claude-opus-5-5` | none |
| B | `results/instruction-ladder/opus-instruction` | `claude-opus-5-5` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |

* Cases both runs selected (compared): 729
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 80 | 80 | 2 | 2 | 74 | 2 | 0 |
| `simple_java` | 20 | 20 | 0 | 1 | 13 | 6 | 0 |
| `simple_javascript` | 10 | 10 | 0 | 0 | 8 | 2 | 0 |
| `multiple` | 40 | 40 | 0 | 2 | 38 | 0 | 0 |
| `parallel` | 40 | 40 | 0 | 1 | 36 | 3 | 0 |
| `parallel_multiple` | 40 | 40 | 1 | 3 | 31 | 5 | 0 |
| `irrelevance` | 48 | 48 | 0 | 4 | 39 | 5 | 0 |
| `live_simple` | 52 | 52 | 3 | 1 | 36 | 12 | 0 |
| `live_multiple` | 211 | 211 | 2 | 6 | 156 | 47 | 0 |
| `live_parallel` | 3 | 3 | 0 | 0 | 3 | 0 | 0 |
| `live_parallel_multiple` | 5 | 5 | 0 | 1 | 4 | 0 | 0 |
| `live_irrelevance` | 177 | 177 | 1 | 13 | 133 | 30 | 0 |
| `live_relevance` | 3 | 3 | 0 | 0 | 2 | 1 | 0 |
| **Overall** | 729 | 729 | 9 | 34 | 573 | 113 | 0 |

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
| `simple_python` | `too-many-calls` | `pass` | 1 |
| `simple_python` | `wrong-call` | `pass` | 1 |
| `simple_python` | `wrong-call` | `wrong-call` | 2 |
| `simple_java` | `no-call` | `no-call` | 1 |
| `simple_java` | `wrong-call` | `pass` | 1 |
| `simple_java` | `wrong-call` | `wrong-call` | 5 |
| `simple_javascript` | `no-call` | `no-call` | 1 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 1 |
| `multiple` | `too-many-calls` | `pass` | 1 |
| `multiple` | `wrong-call` | `pass` | 1 |
| `parallel` | `too-few-calls` | `pass` | 1 |
| `parallel` | `too-few-calls` | `too-few-calls` | 1 |
| `parallel` | `wrong-call` | `wrong-call` | 2 |
| `parallel_multiple` | `pass` | `too-few-calls` | 1 |
| `parallel_multiple` | `no-call` | `pass` | 1 |
| `parallel_multiple` | `too-few-calls` | `pass` | 2 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 1 |
| `parallel_multiple` | `too-few-calls` | `wrong-call` | 1 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 3 |
| `irrelevance` | `called-when-none-applied` | `pass` | 4 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 5 |
| `live_simple` | `pass` | `wrong-call` | 3 |
| `live_simple` | `too-many-calls` | `too-many-calls` | 1 |
| `live_simple` | `wrong-call` | `pass` | 1 |
| `live_simple` | `wrong-call` | `too-many-calls` | 1 |
| `live_simple` | `wrong-call` | `wrong-call` | 10 |
| `live_multiple` | `pass` | `too-many-calls` | 1 |
| `live_multiple` | `pass` | `wrong-call` | 1 |
| `live_multiple` | `no-call` | `no-call` | 2 |
| `live_multiple` | `too-many-calls` | `pass` | 2 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 4 |
| `live_multiple` | `too-many-calls` | `wrong-call` | 1 |
| `live_multiple` | `wrong-call` | `pass` | 4 |
| `live_multiple` | `wrong-call` | `no-call` | 1 |
| `live_multiple` | `wrong-call` | `too-many-calls` | 1 |
| `live_multiple` | `wrong-call` | `wrong-call` | 38 |
| `live_parallel_multiple` | `wrong-call` | `pass` | 1 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 1 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 13 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 30 |
| `live_relevance` | `no-call` | `no-call` | 1 |
| **Overall** | `pass` | `called-when-none-applied` | 1 |
| **Overall** | `pass` | `no-call` | 2 |
| **Overall** | `pass` | `too-few-calls` | 1 |
| **Overall** | `pass` | `too-many-calls` | 1 |
| **Overall** | `pass` | `wrong-call` | 4 |
| **Overall** | `called-when-none-applied` | `pass` | 17 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 35 |
| **Overall** | `no-call` | `pass` | 1 |
| **Overall** | `no-call` | `no-call` | 5 |
| **Overall** | `too-few-calls` | `pass` | 3 |
| **Overall** | `too-few-calls` | `too-few-calls` | 2 |
| **Overall** | `too-few-calls` | `wrong-call` | 1 |
| **Overall** | `too-many-calls` | `pass` | 4 |
| **Overall** | `too-many-calls` | `too-many-calls` | 5 |
| **Overall** | `too-many-calls` | `wrong-call` | 1 |
| **Overall** | `wrong-call` | `pass` | 9 |
| **Overall** | `wrong-call` | `no-call` | 1 |
| **Overall** | `wrong-call` | `too-many-calls` | 2 |
| **Overall** | `wrong-call` | `wrong-call` | 61 |
