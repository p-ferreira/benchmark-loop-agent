# Comparison of two runs (anthropic)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/instruction-six-models/sonnet-plain` | `claude-sonnet-5-5` | none |
| B | `results/instruction-six-models/sonnet-instruction` | `claude-sonnet-5-5` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |

* Cases both runs selected (compared): 3641
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 400 | 400 | 6 | 7 | 372 | 15 | 0 |
| `simple_java` | 100 | 100 | 4 | 5 | 61 | 30 | 0 |
| `simple_javascript` | 50 | 50 | 0 | 0 | 39 | 11 | 0 |
| `multiple` | 200 | 200 | 1 | 7 | 186 | 6 | 0 |
| `parallel` | 200 | 200 | 2 | 3 | 185 | 10 | 0 |
| `parallel_multiple` | 200 | 200 | 3 | 8 | 171 | 18 | 0 |
| `irrelevance` | 240 | 240 | 2 | 14 | 201 | 23 | 0 |
| `live_simple` | 258 | 257 | 4 | 7 | 218 | 28 | 1 |
| `live_multiple` | 1053 | 1053 | 18 | 32 | 828 | 175 | 0 |
| `live_parallel` | 16 | 16 | 0 | 1 | 13 | 2 | 0 |
| `live_parallel_multiple` | 24 | 24 | 0 | 2 | 18 | 4 | 0 |
| `live_irrelevance` | 884 | 884 | 17 | 60 | 706 | 101 | 0 |
| `live_relevance` | 16 | 16 | 2 | 1 | 10 | 3 | 0 |
| **Overall** | 3641 | 3640 | 59 | 147 | 3008 | 426 | 1 |

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
| `simple_python` | `pass` | `too-many-calls` | 2 |
| `simple_python` | `pass` | `wrong-call` | 2 |
| `simple_python` | `too-many-calls` | `no-call` | 1 |
| `simple_python` | `too-many-calls` | `too-many-calls` | 1 |
| `simple_python` | `wrong-call` | `pass` | 7 |
| `simple_python` | `wrong-call` | `wrong-call` | 13 |
| `simple_java` | `pass` | `too-many-calls` | 1 |
| `simple_java` | `pass` | `wrong-call` | 3 |
| `simple_java` | `no-call` | `pass` | 1 |
| `simple_java` | `no-call` | `no-call` | 1 |
| `simple_java` | `wrong-call` | `pass` | 4 |
| `simple_java` | `wrong-call` | `wrong-call` | 29 |
| `simple_javascript` | `no-call` | `no-call` | 2 |
| `simple_javascript` | `wrong-call` | `no-call` | 2 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 7 |
| `multiple` | `pass` | `too-many-calls` | 1 |
| `multiple` | `no-call` | `pass` | 2 |
| `multiple` | `no-call` | `no-call` | 1 |
| `multiple` | `too-many-calls` | `pass` | 1 |
| `multiple` | `too-many-calls` | `too-many-calls` | 3 |
| `multiple` | `wrong-call` | `pass` | 4 |
| `multiple` | `wrong-call` | `wrong-call` | 2 |
| `parallel` | `pass` | `too-many-calls` | 1 |
| `parallel` | `pass` | `wrong-call` | 1 |
| `parallel` | `too-few-calls` | `too-few-calls` | 4 |
| `parallel` | `wrong-call` | `pass` | 3 |
| `parallel` | `wrong-call` | `too-many-calls` | 1 |
| `parallel` | `wrong-call` | `wrong-call` | 5 |
| `parallel_multiple` | `pass` | `too-many-calls` | 2 |
| `parallel_multiple` | `pass` | `wrong-call` | 1 |
| `parallel_multiple` | `no-call` | `pass` | 1 |
| `parallel_multiple` | `too-few-calls` | `pass` | 4 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 2 |
| `parallel_multiple` | `too-few-calls` | `wrong-call` | 3 |
| `parallel_multiple` | `too-many-calls` | `too-many-calls` | 1 |
| `parallel_multiple` | `wrong-call` | `pass` | 3 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 12 |
| `irrelevance` | `pass` | `called-when-none-applied` | 2 |
| `irrelevance` | `called-when-none-applied` | `pass` | 14 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 23 |
| `live_simple` | `pass` | `no-call` | 1 |
| `live_simple` | `pass` | `too-many-calls` | 1 |
| `live_simple` | `pass` | `wrong-call` | 2 |
| `live_simple` | `no-call` | `pass` | 1 |
| `live_simple` | `no-call` | `no-call` | 1 |
| `live_simple` | `too-many-calls` | `pass` | 2 |
| `live_simple` | `too-many-calls` | `too-many-calls` | 2 |
| `live_simple` | `wrong-call` | `pass` | 4 |
| `live_simple` | `wrong-call` | `too-many-calls` | 1 |
| `live_simple` | `wrong-call` | `wrong-call` | 24 |
| `live_multiple` | `pass` | `no-call` | 5 |
| `live_multiple` | `pass` | `too-many-calls` | 5 |
| `live_multiple` | `pass` | `wrong-call` | 8 |
| `live_multiple` | `no-call` | `pass` | 4 |
| `live_multiple` | `no-call` | `no-call` | 17 |
| `live_multiple` | `too-many-calls` | `pass` | 7 |
| `live_multiple` | `too-many-calls` | `no-call` | 2 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 42 |
| `live_multiple` | `too-many-calls` | `wrong-call` | 4 |
| `live_multiple` | `wrong-call` | `pass` | 21 |
| `live_multiple` | `wrong-call` | `no-call` | 9 |
| `live_multiple` | `wrong-call` | `too-many-calls` | 4 |
| `live_multiple` | `wrong-call` | `wrong-call` | 97 |
| `live_parallel` | `wrong-call` | `pass` | 1 |
| `live_parallel` | `wrong-call` | `too-few-calls` | 1 |
| `live_parallel` | `wrong-call` | `wrong-call` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `too-few-calls` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `wrong-call` | 1 |
| `live_parallel_multiple` | `too-many-calls` | `too-many-calls` | 1 |
| `live_parallel_multiple` | `wrong-call` | `pass` | 2 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 1 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 17 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 60 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 101 |
| `live_relevance` | `pass` | `no-call` | 2 |
| `live_relevance` | `no-call` | `pass` | 1 |
| `live_relevance` | `no-call` | `no-call` | 3 |
| **Overall** | `pass` | `called-when-none-applied` | 19 |
| **Overall** | `pass` | `no-call` | 10 |
| **Overall** | `pass` | `too-many-calls` | 13 |
| **Overall** | `pass` | `wrong-call` | 17 |
| **Overall** | `called-when-none-applied` | `pass` | 74 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 124 |
| **Overall** | `no-call` | `pass` | 10 |
| **Overall** | `no-call` | `no-call` | 25 |
| **Overall** | `too-few-calls` | `pass` | 4 |
| **Overall** | `too-few-calls` | `too-few-calls` | 7 |
| **Overall** | `too-few-calls` | `wrong-call` | 4 |
| **Overall** | `too-many-calls` | `pass` | 10 |
| **Overall** | `too-many-calls` | `no-call` | 3 |
| **Overall** | `too-many-calls` | `too-many-calls` | 50 |
| **Overall** | `too-many-calls` | `wrong-call` | 4 |
| **Overall** | `wrong-call` | `pass` | 49 |
| **Overall** | `wrong-call` | `no-call` | 11 |
| **Overall** | `wrong-call` | `too-few-calls` | 1 |
| **Overall** | `wrong-call` | `too-many-calls` | 6 |
| **Overall** | `wrong-call` | `wrong-call` | 191 |
