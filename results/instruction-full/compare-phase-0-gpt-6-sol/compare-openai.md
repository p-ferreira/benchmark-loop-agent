# Comparison of two runs (openai)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/phase-0/gpt-6-sol` | `gpt-6-sol` | none |
| B | `results/instruction-full/gpt-6-sol` | `gpt-6-sol` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |

* Cases both runs selected (compared): 3641
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 400 | 400 | 9 | 19 | 345 | 27 | 0 |
| `simple_java` | 100 | 100 | 1 | 7 | 57 | 35 | 0 |
| `simple_javascript` | 50 | 50 | 1 | 6 | 28 | 15 | 0 |
| `multiple` | 200 | 200 | 3 | 15 | 173 | 9 | 0 |
| `parallel` | 200 | 200 | 1 | 12 | 170 | 17 | 0 |
| `parallel_multiple` | 200 | 200 | 4 | 37 | 124 | 35 | 0 |
| `irrelevance` | 240 | 240 | 2 | 14 | 207 | 17 | 0 |
| `live_simple` | 258 | 258 | 7 | 14 | 195 | 42 | 0 |
| `live_multiple` | 1053 | 1053 | 37 | 55 | 740 | 221 | 0 |
| `live_parallel` | 16 | 16 | 0 | 1 | 12 | 3 | 0 |
| `live_parallel_multiple` | 24 | 24 | 0 | 2 | 14 | 8 | 0 |
| `live_irrelevance` | 884 | 884 | 29 | 54 | 707 | 94 | 0 |
| `live_relevance` | 16 | 16 | 4 | 0 | 8 | 4 | 0 |
| **Overall** | 3641 | 3641 | 98 | 236 | 2780 | 527 | 0 |

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
| `simple_python` | `pass` | `no-call` | 3 |
| `simple_python` | `pass` | `wrong-call` | 6 |
| `simple_python` | `no-call` | `pass` | 7 |
| `simple_python` | `no-call` | `no-call` | 2 |
| `simple_python` | `no-call` | `wrong-call` | 1 |
| `simple_python` | `too-many-calls` | `no-call` | 1 |
| `simple_python` | `too-many-calls` | `too-many-calls` | 1 |
| `simple_python` | `wrong-call` | `pass` | 12 |
| `simple_python` | `wrong-call` | `no-call` | 1 |
| `simple_python` | `wrong-call` | `wrong-call` | 21 |
| `simple_java` | `pass` | `wrong-call` | 1 |
| `simple_java` | `no-call` | `pass` | 5 |
| `simple_java` | `no-call` | `no-call` | 1 |
| `simple_java` | `wrong-call` | `pass` | 2 |
| `simple_java` | `wrong-call` | `no-call` | 3 |
| `simple_java` | `wrong-call` | `wrong-call` | 31 |
| `simple_javascript` | `pass` | `no-call` | 1 |
| `simple_javascript` | `no-call` | `pass` | 4 |
| `simple_javascript` | `no-call` | `no-call` | 4 |
| `simple_javascript` | `no-call` | `wrong-call` | 3 |
| `simple_javascript` | `too-many-calls` | `pass` | 1 |
| `simple_javascript` | `wrong-call` | `pass` | 1 |
| `simple_javascript` | `wrong-call` | `no-call` | 2 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 6 |
| `multiple` | `pass` | `no-call` | 2 |
| `multiple` | `pass` | `wrong-call` | 1 |
| `multiple` | `no-call` | `pass` | 3 |
| `multiple` | `no-call` | `no-call` | 1 |
| `multiple` | `too-many-calls` | `too-many-calls` | 2 |
| `multiple` | `too-many-calls` | `wrong-call` | 1 |
| `multiple` | `wrong-call` | `pass` | 12 |
| `multiple` | `wrong-call` | `wrong-call` | 5 |
| `parallel` | `pass` | `wrong-call` | 1 |
| `parallel` | `no-call` | `pass` | 2 |
| `parallel` | `no-call` | `no-call` | 1 |
| `parallel` | `too-few-calls` | `pass` | 2 |
| `parallel` | `too-few-calls` | `no-call` | 1 |
| `parallel` | `too-few-calls` | `too-few-calls` | 5 |
| `parallel` | `too-few-calls` | `too-many-calls` | 1 |
| `parallel` | `wrong-call` | `pass` | 8 |
| `parallel` | `wrong-call` | `wrong-call` | 9 |
| `parallel_multiple` | `pass` | `no-call` | 1 |
| `parallel_multiple` | `pass` | `too-many-calls` | 1 |
| `parallel_multiple` | `pass` | `wrong-call` | 2 |
| `parallel_multiple` | `no-call` | `pass` | 2 |
| `parallel_multiple` | `too-few-calls` | `pass` | 27 |
| `parallel_multiple` | `too-few-calls` | `no-call` | 2 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 14 |
| `parallel_multiple` | `too-few-calls` | `wrong-call` | 5 |
| `parallel_multiple` | `wrong-call` | `pass` | 8 |
| `parallel_multiple` | `wrong-call` | `no-call` | 1 |
| `parallel_multiple` | `wrong-call` | `too-few-calls` | 1 |
| `parallel_multiple` | `wrong-call` | `too-many-calls` | 1 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 11 |
| `irrelevance` | `pass` | `called-when-none-applied` | 2 |
| `irrelevance` | `called-when-none-applied` | `pass` | 14 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 17 |
| `live_simple` | `pass` | `no-call` | 3 |
| `live_simple` | `pass` | `wrong-call` | 4 |
| `live_simple` | `no-call` | `pass` | 10 |
| `live_simple` | `no-call` | `no-call` | 2 |
| `live_simple` | `no-call` | `wrong-call` | 5 |
| `live_simple` | `too-many-calls` | `pass` | 1 |
| `live_simple` | `too-many-calls` | `no-call` | 1 |
| `live_simple` | `too-many-calls` | `too-many-calls` | 1 |
| `live_simple` | `wrong-call` | `pass` | 3 |
| `live_simple` | `wrong-call` | `no-call` | 1 |
| `live_simple` | `wrong-call` | `wrong-call` | 32 |
| `live_multiple` | `pass` | `no-call` | 21 |
| `live_multiple` | `pass` | `too-many-calls` | 7 |
| `live_multiple` | `pass` | `wrong-call` | 9 |
| `live_multiple` | `no-call` | `pass` | 15 |
| `live_multiple` | `no-call` | `no-call` | 42 |
| `live_multiple` | `no-call` | `wrong-call` | 13 |
| `live_multiple` | `too-many-calls` | `pass` | 10 |
| `live_multiple` | `too-many-calls` | `no-call` | 7 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 27 |
| `live_multiple` | `too-many-calls` | `wrong-call` | 2 |
| `live_multiple` | `wrong-call` | `pass` | 30 |
| `live_multiple` | `wrong-call` | `no-call` | 23 |
| `live_multiple` | `wrong-call` | `too-many-calls` | 7 |
| `live_multiple` | `wrong-call` | `wrong-call` | 100 |
| `live_parallel` | `no-call` | `pass` | 1 |
| `live_parallel` | `too-few-calls` | `too-few-calls` | 1 |
| `live_parallel` | `wrong-call` | `wrong-call` | 2 |
| `live_parallel_multiple` | `too-few-calls` | `pass` | 2 |
| `live_parallel_multiple` | `too-few-calls` | `too-few-calls` | 3 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 5 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 29 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 54 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 94 |
| `live_relevance` | `pass` | `no-call` | 4 |
| `live_relevance` | `no-call` | `no-call` | 4 |
| **Overall** | `pass` | `called-when-none-applied` | 31 |
| **Overall** | `pass` | `no-call` | 35 |
| **Overall** | `pass` | `too-many-calls` | 8 |
| **Overall** | `pass` | `wrong-call` | 24 |
| **Overall** | `called-when-none-applied` | `pass` | 68 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 111 |
| **Overall** | `no-call` | `pass` | 49 |
| **Overall** | `no-call` | `no-call` | 57 |
| **Overall** | `no-call` | `wrong-call` | 22 |
| **Overall** | `too-few-calls` | `pass` | 31 |
| **Overall** | `too-few-calls` | `no-call` | 3 |
| **Overall** | `too-few-calls` | `too-few-calls` | 23 |
| **Overall** | `too-few-calls` | `too-many-calls` | 1 |
| **Overall** | `too-few-calls` | `wrong-call` | 5 |
| **Overall** | `too-many-calls` | `pass` | 12 |
| **Overall** | `too-many-calls` | `no-call` | 9 |
| **Overall** | `too-many-calls` | `too-many-calls` | 31 |
| **Overall** | `too-many-calls` | `wrong-call` | 3 |
| **Overall** | `wrong-call` | `pass` | 76 |
| **Overall** | `wrong-call` | `no-call` | 31 |
| **Overall** | `wrong-call` | `too-few-calls` | 1 |
| **Overall** | `wrong-call` | `too-many-calls` | 8 |
| **Overall** | `wrong-call` | `wrong-call` | 222 |
