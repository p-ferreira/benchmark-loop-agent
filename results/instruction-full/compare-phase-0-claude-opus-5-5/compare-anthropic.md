# Comparison of two runs (anthropic)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/phase-0/claude-opus-5-5` | `claude-opus-5-5` | none |
| B | `results/instruction-full/claude-opus-5-5` | `claude-opus-5-5` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |

* Cases both runs selected (compared): 3641
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 400 | 400 | 4 | 2 | 384 | 10 | 0 |
| `simple_java` | 100 | 100 | 1 | 4 | 66 | 29 | 0 |
| `simple_javascript` | 50 | 50 | 2 | 4 | 39 | 5 | 0 |
| `multiple` | 200 | 200 | 1 | 5 | 187 | 7 | 0 |
| `parallel` | 200 | 200 | 2 | 7 | 181 | 10 | 0 |
| `parallel_multiple` | 200 | 200 | 6 | 13 | 168 | 13 | 0 |
| `irrelevance` | 240 | 240 | 1 | 22 | 194 | 23 | 0 |
| `live_simple` | 258 | 257 | 6 | 5 | 215 | 31 | 1 |
| `live_multiple` | 1053 | 1053 | 20 | 28 | 829 | 176 | 0 |
| `live_parallel` | 16 | 16 | 1 | 2 | 12 | 1 | 0 |
| `live_parallel_multiple` | 24 | 24 | 0 | 2 | 16 | 6 | 0 |
| `live_irrelevance` | 884 | 884 | 8 | 52 | 687 | 137 | 0 |
| `live_relevance` | 16 | 16 | 1 | 0 | 10 | 5 | 0 |
| **Overall** | 3641 | 3640 | 53 | 146 | 2988 | 453 | 1 |

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
| `simple_python` | `pass` | `wrong-call` | 2 |
| `simple_python` | `too-many-calls` | `no-call` | 1 |
| `simple_python` | `too-many-calls` | `too-many-calls` | 1 |
| `simple_python` | `wrong-call` | `pass` | 2 |
| `simple_python` | `wrong-call` | `wrong-call` | 8 |
| `simple_java` | `pass` | `no-call` | 1 |
| `simple_java` | `no-call` | `pass` | 2 |
| `simple_java` | `no-call` | `no-call` | 1 |
| `simple_java` | `wrong-call` | `pass` | 2 |
| `simple_java` | `wrong-call` | `wrong-call` | 28 |
| `simple_javascript` | `pass` | `no-call` | 1 |
| `simple_javascript` | `pass` | `wrong-call` | 1 |
| `simple_javascript` | `no-call` | `no-call` | 1 |
| `simple_javascript` | `wrong-call` | `pass` | 4 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 4 |
| `multiple` | `pass` | `too-many-calls` | 1 |
| `multiple` | `no-call` | `pass` | 1 |
| `multiple` | `too-many-calls` | `pass` | 1 |
| `multiple` | `too-many-calls` | `too-many-calls` | 2 |
| `multiple` | `too-many-calls` | `wrong-call` | 1 |
| `multiple` | `wrong-call` | `pass` | 3 |
| `multiple` | `wrong-call` | `wrong-call` | 4 |
| `parallel` | `pass` | `too-many-calls` | 2 |
| `parallel` | `too-few-calls` | `pass` | 2 |
| `parallel` | `too-few-calls` | `too-few-calls` | 3 |
| `parallel` | `too-many-calls` | `pass` | 1 |
| `parallel` | `wrong-call` | `pass` | 4 |
| `parallel` | `wrong-call` | `wrong-call` | 7 |
| `parallel_multiple` | `pass` | `too-few-calls` | 1 |
| `parallel_multiple` | `pass` | `too-many-calls` | 2 |
| `parallel_multiple` | `pass` | `wrong-call` | 3 |
| `parallel_multiple` | `no-call` | `pass` | 1 |
| `parallel_multiple` | `too-few-calls` | `pass` | 7 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 2 |
| `parallel_multiple` | `too-few-calls` | `wrong-call` | 2 |
| `parallel_multiple` | `wrong-call` | `pass` | 5 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 9 |
| `irrelevance` | `pass` | `called-when-none-applied` | 1 |
| `irrelevance` | `called-when-none-applied` | `pass` | 22 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 23 |
| `live_simple` | `pass` | `too-many-calls` | 1 |
| `live_simple` | `pass` | `wrong-call` | 5 |
| `live_simple` | `no-call` | `pass` | 1 |
| `live_simple` | `no-call` | `wrong-call` | 1 |
| `live_simple` | `too-many-calls` | `pass` | 1 |
| `live_simple` | `too-many-calls` | `too-many-calls` | 1 |
| `live_simple` | `wrong-call` | `pass` | 3 |
| `live_simple` | `wrong-call` | `too-many-calls` | 1 |
| `live_simple` | `wrong-call` | `wrong-call` | 28 |
| `live_multiple` | `pass` | `no-call` | 6 |
| `live_multiple` | `pass` | `too-many-calls` | 4 |
| `live_multiple` | `pass` | `wrong-call` | 10 |
| `live_multiple` | `no-call` | `pass` | 10 |
| `live_multiple` | `no-call` | `no-call` | 14 |
| `live_multiple` | `no-call` | `wrong-call` | 3 |
| `live_multiple` | `too-many-calls` | `pass` | 6 |
| `live_multiple` | `too-many-calls` | `no-call` | 2 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 32 |
| `live_multiple` | `too-many-calls` | `wrong-call` | 3 |
| `live_multiple` | `wrong-call` | `pass` | 12 |
| `live_multiple` | `wrong-call` | `no-call` | 7 |
| `live_multiple` | `wrong-call` | `too-many-calls` | 5 |
| `live_multiple` | `wrong-call` | `wrong-call` | 110 |
| `live_parallel` | `pass` | `wrong-call` | 1 |
| `live_parallel` | `wrong-call` | `pass` | 2 |
| `live_parallel` | `wrong-call` | `wrong-call` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `pass` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `too-few-calls` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `wrong-call` | 1 |
| `live_parallel_multiple` | `wrong-call` | `pass` | 1 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 4 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 8 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 52 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 137 |
| `live_relevance` | `pass` | `no-call` | 1 |
| `live_relevance` | `no-call` | `no-call` | 5 |
| **Overall** | `pass` | `called-when-none-applied` | 9 |
| **Overall** | `pass` | `no-call` | 11 |
| **Overall** | `pass` | `too-few-calls` | 1 |
| **Overall** | `pass` | `too-many-calls` | 10 |
| **Overall** | `pass` | `wrong-call` | 22 |
| **Overall** | `called-when-none-applied` | `pass` | 74 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 160 |
| **Overall** | `no-call` | `pass` | 15 |
| **Overall** | `no-call` | `no-call` | 21 |
| **Overall** | `no-call` | `wrong-call` | 4 |
| **Overall** | `too-few-calls` | `pass` | 10 |
| **Overall** | `too-few-calls` | `too-few-calls` | 6 |
| **Overall** | `too-few-calls` | `wrong-call` | 3 |
| **Overall** | `too-many-calls` | `pass` | 9 |
| **Overall** | `too-many-calls` | `no-call` | 3 |
| **Overall** | `too-many-calls` | `too-many-calls` | 36 |
| **Overall** | `too-many-calls` | `wrong-call` | 4 |
| **Overall** | `wrong-call` | `pass` | 38 |
| **Overall** | `wrong-call` | `no-call` | 7 |
| **Overall** | `wrong-call` | `too-many-calls` | 6 |
| **Overall** | `wrong-call` | `wrong-call` | 203 |
