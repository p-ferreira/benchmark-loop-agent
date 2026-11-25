# Comparison of two runs (openai)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/instruction-ladder/terra-plain` | `gpt-6.1-terra` | none |
| B | `results/instruction-ladder/terra-instruction` | `gpt-6.1-terra` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |

* Cases both runs selected (compared): 729
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 80 | 80 | 3 | 5 | 65 | 7 | 0 |
| `simple_java` | 20 | 20 | 0 | 0 | 13 | 7 | 0 |
| `simple_javascript` | 10 | 10 | 0 | 0 | 7 | 3 | 0 |
| `multiple` | 40 | 40 | 0 | 1 | 37 | 2 | 0 |
| `parallel` | 40 | 40 | 0 | 4 | 30 | 6 | 0 |
| `parallel_multiple` | 40 | 40 | 1 | 5 | 23 | 11 | 0 |
| `irrelevance` | 48 | 48 | 0 | 8 | 38 | 2 | 0 |
| `live_simple` | 52 | 52 | 1 | 3 | 34 | 14 | 0 |
| `live_multiple` | 211 | 211 | 8 | 9 | 142 | 52 | 0 |
| `live_parallel` | 3 | 3 | 0 | 0 | 3 | 0 | 0 |
| `live_parallel_multiple` | 5 | 5 | 0 | 0 | 4 | 1 | 0 |
| `live_irrelevance` | 177 | 177 | 3 | 13 | 144 | 17 | 0 |
| `live_relevance` | 3 | 3 | 1 | 0 | 1 | 1 | 0 |
| **Overall** | 729 | 729 | 17 | 48 | 541 | 123 | 0 |

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
| `simple_python` | `pass` | `wrong-call` | 1 |
| `simple_python` | `no-call` | `pass` | 1 |
| `simple_python` | `no-call` | `wrong-call` | 1 |
| `simple_python` | `too-many-calls` | `too-many-calls` | 1 |
| `simple_python` | `wrong-call` | `pass` | 4 |
| `simple_python` | `wrong-call` | `wrong-call` | 5 |
| `simple_java` | `no-call` | `no-call` | 2 |
| `simple_java` | `wrong-call` | `wrong-call` | 5 |
| `simple_javascript` | `no-call` | `no-call` | 1 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 2 |
| `multiple` | `no-call` | `no-call` | 1 |
| `multiple` | `wrong-call` | `pass` | 1 |
| `multiple` | `wrong-call` | `wrong-call` | 1 |
| `parallel` | `no-call` | `pass` | 1 |
| `parallel` | `no-call` | `no-call` | 1 |
| `parallel` | `too-few-calls` | `too-few-calls` | 2 |
| `parallel` | `too-few-calls` | `wrong-call` | 1 |
| `parallel` | `too-many-calls` | `wrong-call` | 1 |
| `parallel` | `wrong-call` | `pass` | 3 |
| `parallel` | `wrong-call` | `wrong-call` | 1 |
| `parallel_multiple` | `pass` | `no-call` | 1 |
| `parallel_multiple` | `no-call` | `no-call` | 1 |
| `parallel_multiple` | `too-few-calls` | `pass` | 3 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 4 |
| `parallel_multiple` | `too-few-calls` | `wrong-call` | 3 |
| `parallel_multiple` | `too-many-calls` | `wrong-call` | 1 |
| `parallel_multiple` | `wrong-call` | `pass` | 2 |
| `parallel_multiple` | `wrong-call` | `no-call` | 1 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 1 |
| `irrelevance` | `called-when-none-applied` | `pass` | 8 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 2 |
| `live_simple` | `pass` | `wrong-call` | 1 |
| `live_simple` | `no-call` | `pass` | 1 |
| `live_simple` | `no-call` | `wrong-call` | 2 |
| `live_simple` | `wrong-call` | `pass` | 2 |
| `live_simple` | `wrong-call` | `too-many-calls` | 1 |
| `live_simple` | `wrong-call` | `wrong-call` | 11 |
| `live_multiple` | `pass` | `no-call` | 3 |
| `live_multiple` | `pass` | `too-many-calls` | 2 |
| `live_multiple` | `pass` | `wrong-call` | 3 |
| `live_multiple` | `no-call` | `pass` | 2 |
| `live_multiple` | `no-call` | `no-call` | 12 |
| `live_multiple` | `no-call` | `wrong-call` | 2 |
| `live_multiple` | `too-many-calls` | `pass` | 3 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 3 |
| `live_multiple` | `too-many-calls` | `wrong-call` | 1 |
| `live_multiple` | `wrong-call` | `pass` | 4 |
| `live_multiple` | `wrong-call` | `no-call` | 2 |
| `live_multiple` | `wrong-call` | `too-many-calls` | 1 |
| `live_multiple` | `wrong-call` | `wrong-call` | 31 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 1 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 3 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 13 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 17 |
| `live_relevance` | `pass` | `no-call` | 1 |
| `live_relevance` | `no-call` | `no-call` | 1 |
| **Overall** | `pass` | `called-when-none-applied` | 3 |
| **Overall** | `pass` | `no-call` | 7 |
| **Overall** | `pass` | `too-many-calls` | 2 |
| **Overall** | `pass` | `wrong-call` | 5 |
| **Overall** | `called-when-none-applied` | `pass` | 21 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 19 |
| **Overall** | `no-call` | `pass` | 5 |
| **Overall** | `no-call` | `no-call` | 19 |
| **Overall** | `no-call` | `wrong-call` | 5 |
| **Overall** | `too-few-calls` | `pass` | 3 |
| **Overall** | `too-few-calls` | `too-few-calls` | 6 |
| **Overall** | `too-few-calls` | `wrong-call` | 4 |
| **Overall** | `too-many-calls` | `pass` | 3 |
| **Overall** | `too-many-calls` | `too-many-calls` | 4 |
| **Overall** | `too-many-calls` | `wrong-call` | 3 |
| **Overall** | `wrong-call` | `pass` | 16 |
| **Overall** | `wrong-call` | `no-call` | 3 |
| **Overall** | `wrong-call` | `too-many-calls` | 2 |
| **Overall** | `wrong-call` | `wrong-call` | 58 |
