# Comparison of two runs (openai)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/instruction-six-models/terra-plain` | `gpt-6.1-terra` | none |
| B | `results/instruction-six-models/terra-instruction` | `gpt-6.1-terra` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |

* Cases both runs selected (compared): 3641
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 400 | 400 | 10 | 27 | 336 | 27 | 0 |
| `simple_java` | 100 | 100 | 3 | 3 | 61 | 33 | 0 |
| `simple_javascript` | 50 | 50 | 3 | 3 | 31 | 13 | 0 |
| `multiple` | 200 | 200 | 2 | 12 | 173 | 13 | 0 |
| `parallel` | 200 | 200 | 2 | 9 | 172 | 17 | 0 |
| `parallel_multiple` | 200 | 200 | 3 | 31 | 134 | 32 | 0 |
| `irrelevance` | 240 | 240 | 0 | 19 | 201 | 20 | 0 |
| `live_simple` | 258 | 258 | 7 | 17 | 193 | 41 | 0 |
| `live_multiple` | 1053 | 1053 | 42 | 51 | 723 | 237 | 0 |
| `live_parallel` | 16 | 16 | 0 | 3 | 10 | 3 | 0 |
| `live_parallel_multiple` | 24 | 24 | 0 | 3 | 14 | 7 | 0 |
| `live_irrelevance` | 884 | 884 | 17 | 51 | 733 | 83 | 0 |
| `live_relevance` | 16 | 16 | 3 | 2 | 7 | 4 | 0 |
| **Overall** | 3641 | 3641 | 92 | 231 | 2788 | 530 | 0 |

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
| `simple_python` | `pass` | `no-call` | 4 |
| `simple_python` | `pass` | `wrong-call` | 6 |
| `simple_python` | `no-call` | `pass` | 3 |
| `simple_python` | `no-call` | `no-call` | 2 |
| `simple_python` | `too-many-calls` | `pass` | 1 |
| `simple_python` | `too-many-calls` | `no-call` | 2 |
| `simple_python` | `too-many-calls` | `too-many-calls` | 1 |
| `simple_python` | `too-many-calls` | `wrong-call` | 1 |
| `simple_python` | `wrong-call` | `pass` | 23 |
| `simple_python` | `wrong-call` | `wrong-call` | 21 |
| `simple_java` | `pass` | `no-call` | 1 |
| `simple_java` | `pass` | `wrong-call` | 2 |
| `simple_java` | `no-call` | `no-call` | 2 |
| `simple_java` | `wrong-call` | `pass` | 3 |
| `simple_java` | `wrong-call` | `no-call` | 2 |
| `simple_java` | `wrong-call` | `wrong-call` | 29 |
| `simple_javascript` | `pass` | `wrong-call` | 3 |
| `simple_javascript` | `no-call` | `pass` | 3 |
| `simple_javascript` | `no-call` | `no-call` | 3 |
| `simple_javascript` | `no-call` | `wrong-call` | 1 |
| `simple_javascript` | `wrong-call` | `no-call` | 3 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 6 |
| `multiple` | `pass` | `no-call` | 2 |
| `multiple` | `no-call` | `pass` | 1 |
| `multiple` | `no-call` | `no-call` | 2 |
| `multiple` | `too-many-calls` | `pass` | 2 |
| `multiple` | `too-many-calls` | `too-many-calls` | 1 |
| `multiple` | `too-many-calls` | `wrong-call` | 1 |
| `multiple` | `wrong-call` | `pass` | 9 |
| `multiple` | `wrong-call` | `wrong-call` | 9 |
| `parallel` | `pass` | `too-many-calls` | 2 |
| `parallel` | `no-call` | `pass` | 1 |
| `parallel` | `no-call` | `no-call` | 1 |
| `parallel` | `too-few-calls` | `pass` | 4 |
| `parallel` | `too-few-calls` | `too-few-calls` | 5 |
| `parallel` | `too-few-calls` | `wrong-call` | 2 |
| `parallel` | `too-many-calls` | `too-many-calls` | 1 |
| `parallel` | `wrong-call` | `pass` | 4 |
| `parallel` | `wrong-call` | `wrong-call` | 8 |
| `parallel_multiple` | `pass` | `no-call` | 1 |
| `parallel_multiple` | `pass` | `too-many-calls` | 1 |
| `parallel_multiple` | `pass` | `wrong-call` | 1 |
| `parallel_multiple` | `no-call` | `pass` | 1 |
| `parallel_multiple` | `too-few-calls` | `pass` | 25 |
| `parallel_multiple` | `too-few-calls` | `no-call` | 2 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 7 |
| `parallel_multiple` | `too-few-calls` | `too-many-calls` | 1 |
| `parallel_multiple` | `too-few-calls` | `wrong-call` | 6 |
| `parallel_multiple` | `too-many-calls` | `pass` | 1 |
| `parallel_multiple` | `wrong-call` | `pass` | 4 |
| `parallel_multiple` | `wrong-call` | `no-call` | 2 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 14 |
| `irrelevance` | `called-when-none-applied` | `pass` | 19 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 20 |
| `live_simple` | `pass` | `no-call` | 3 |
| `live_simple` | `pass` | `too-many-calls` | 1 |
| `live_simple` | `pass` | `wrong-call` | 3 |
| `live_simple` | `no-call` | `pass` | 7 |
| `live_simple` | `no-call` | `no-call` | 2 |
| `live_simple` | `no-call` | `wrong-call` | 4 |
| `live_simple` | `too-many-calls` | `pass` | 1 |
| `live_simple` | `too-many-calls` | `too-many-calls` | 1 |
| `live_simple` | `wrong-call` | `pass` | 9 |
| `live_simple` | `wrong-call` | `no-call` | 2 |
| `live_simple` | `wrong-call` | `too-many-calls` | 1 |
| `live_simple` | `wrong-call` | `wrong-call` | 31 |
| `live_multiple` | `pass` | `no-call` | 27 |
| `live_multiple` | `pass` | `too-many-calls` | 4 |
| `live_multiple` | `pass` | `wrong-call` | 11 |
| `live_multiple` | `no-call` | `pass` | 12 |
| `live_multiple` | `no-call` | `no-call` | 56 |
| `live_multiple` | `no-call` | `too-many-calls` | 2 |
| `live_multiple` | `no-call` | `wrong-call` | 9 |
| `live_multiple` | `too-many-calls` | `pass` | 12 |
| `live_multiple` | `too-many-calls` | `no-call` | 4 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 34 |
| `live_multiple` | `too-many-calls` | `wrong-call` | 5 |
| `live_multiple` | `wrong-call` | `pass` | 27 |
| `live_multiple` | `wrong-call` | `no-call` | 18 |
| `live_multiple` | `wrong-call` | `too-many-calls` | 5 |
| `live_multiple` | `wrong-call` | `wrong-call` | 104 |
| `live_parallel` | `no-call` | `pass` | 1 |
| `live_parallel` | `too-few-calls` | `too-few-calls` | 1 |
| `live_parallel` | `wrong-call` | `pass` | 2 |
| `live_parallel` | `wrong-call` | `wrong-call` | 2 |
| `live_parallel_multiple` | `too-few-calls` | `pass` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `too-few-calls` | 3 |
| `live_parallel_multiple` | `too-many-calls` | `wrong-call` | 1 |
| `live_parallel_multiple` | `wrong-call` | `pass` | 2 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 3 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 17 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 51 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 83 |
| `live_relevance` | `pass` | `no-call` | 3 |
| `live_relevance` | `no-call` | `pass` | 2 |
| `live_relevance` | `no-call` | `no-call` | 4 |
| **Overall** | `pass` | `called-when-none-applied` | 17 |
| **Overall** | `pass` | `no-call` | 41 |
| **Overall** | `pass` | `too-many-calls` | 8 |
| **Overall** | `pass` | `wrong-call` | 26 |
| **Overall** | `called-when-none-applied` | `pass` | 70 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 103 |
| **Overall** | `no-call` | `pass` | 31 |
| **Overall** | `no-call` | `no-call` | 72 |
| **Overall** | `no-call` | `too-many-calls` | 2 |
| **Overall** | `no-call` | `wrong-call` | 14 |
| **Overall** | `too-few-calls` | `pass` | 30 |
| **Overall** | `too-few-calls` | `no-call` | 2 |
| **Overall** | `too-few-calls` | `too-few-calls` | 16 |
| **Overall** | `too-few-calls` | `too-many-calls` | 1 |
| **Overall** | `too-few-calls` | `wrong-call` | 8 |
| **Overall** | `too-many-calls` | `pass` | 17 |
| **Overall** | `too-many-calls` | `no-call` | 6 |
| **Overall** | `too-many-calls` | `too-many-calls` | 38 |
| **Overall** | `too-many-calls` | `wrong-call` | 8 |
| **Overall** | `wrong-call` | `pass` | 83 |
| **Overall** | `wrong-call` | `no-call` | 27 |
| **Overall** | `wrong-call` | `too-many-calls` | 6 |
| **Overall** | `wrong-call` | `wrong-call` | 227 |
