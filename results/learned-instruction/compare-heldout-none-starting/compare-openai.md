# Comparison of two runs (openai)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/learned-instruction/heldout-none` | `gpt-6-sol` | none |
| B | `results/learned-instruction/heldout-starting` | `gpt-6-sol` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |

* Cases both runs selected (compared): 1092
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 120 | 120 | 3 | 6 | 104 | 7 | 0 |
| `simple_java` | 30 | 30 | 0 | 2 | 16 | 12 | 0 |
| `simple_javascript` | 15 | 15 | 1 | 0 | 12 | 2 | 0 |
| `multiple` | 60 | 60 | 1 | 6 | 50 | 3 | 0 |
| `parallel` | 60 | 60 | 0 | 2 | 52 | 6 | 0 |
| `parallel_multiple` | 60 | 60 | 1 | 11 | 34 | 14 | 0 |
| `irrelevance` | 72 | 72 | 0 | 4 | 66 | 2 | 0 |
| `live_simple` | 77 | 77 | 2 | 4 | 61 | 10 | 0 |
| `live_multiple` | 316 | 316 | 14 | 14 | 222 | 66 | 0 |
| `live_parallel` | 5 | 5 | 0 | 0 | 4 | 1 | 0 |
| `live_parallel_multiple` | 7 | 7 | 0 | 1 | 4 | 2 | 0 |
| `live_irrelevance` | 265 | 265 | 10 | 13 | 212 | 30 | 0 |
| `live_relevance` | 5 | 5 | 3 | 0 | 2 | 0 | 0 |
| **Overall** | 1092 | 1092 | 35 | 63 | 839 | 155 | 0 |

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
| `simple_python` | `no-call` | `pass` | 4 |
| `simple_python` | `no-call` | `wrong-call` | 1 |
| `simple_python` | `too-many-calls` | `too-many-calls` | 1 |
| `simple_python` | `too-many-calls` | `wrong-call` | 1 |
| `simple_python` | `wrong-call` | `pass` | 2 |
| `simple_python` | `wrong-call` | `wrong-call` | 4 |
| `simple_java` | `no-call` | `pass` | 1 |
| `simple_java` | `wrong-call` | `pass` | 1 |
| `simple_java` | `wrong-call` | `wrong-call` | 12 |
| `simple_javascript` | `pass` | `wrong-call` | 1 |
| `simple_javascript` | `no-call` | `no-call` | 1 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 1 |
| `multiple` | `pass` | `no-call` | 1 |
| `multiple` | `no-call` | `pass` | 2 |
| `multiple` | `no-call` | `no-call` | 1 |
| `multiple` | `too-many-calls` | `pass` | 1 |
| `multiple` | `wrong-call` | `pass` | 3 |
| `multiple` | `wrong-call` | `wrong-call` | 2 |
| `parallel` | `no-call` | `pass` | 1 |
| `parallel` | `no-call` | `wrong-call` | 1 |
| `parallel` | `wrong-call` | `pass` | 1 |
| `parallel` | `wrong-call` | `wrong-call` | 5 |
| `parallel_multiple` | `pass` | `too-many-calls` | 1 |
| `parallel_multiple` | `too-few-calls` | `pass` | 7 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 3 |
| `parallel_multiple` | `too-few-calls` | `wrong-call` | 3 |
| `parallel_multiple` | `wrong-call` | `pass` | 4 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 8 |
| `irrelevance` | `called-when-none-applied` | `pass` | 4 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 2 |
| `live_simple` | `pass` | `no-call` | 1 |
| `live_simple` | `pass` | `wrong-call` | 1 |
| `live_simple` | `no-call` | `pass` | 3 |
| `live_simple` | `no-call` | `no-call` | 1 |
| `live_simple` | `no-call` | `wrong-call` | 2 |
| `live_simple` | `too-many-calls` | `pass` | 1 |
| `live_simple` | `wrong-call` | `no-call` | 1 |
| `live_simple` | `wrong-call` | `wrong-call` | 6 |
| `live_multiple` | `pass` | `no-call` | 7 |
| `live_multiple` | `pass` | `too-many-calls` | 2 |
| `live_multiple` | `pass` | `wrong-call` | 5 |
| `live_multiple` | `no-call` | `pass` | 7 |
| `live_multiple` | `no-call` | `no-call` | 19 |
| `live_multiple` | `no-call` | `too-many-calls` | 1 |
| `live_multiple` | `no-call` | `wrong-call` | 2 |
| `live_multiple` | `too-many-calls` | `pass` | 2 |
| `live_multiple` | `too-many-calls` | `no-call` | 4 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 5 |
| `live_multiple` | `too-many-calls` | `wrong-call` | 2 |
| `live_multiple` | `wrong-call` | `pass` | 5 |
| `live_multiple` | `wrong-call` | `no-call` | 5 |
| `live_multiple` | `wrong-call` | `wrong-call` | 28 |
| `live_parallel` | `wrong-call` | `wrong-call` | 1 |
| `live_parallel_multiple` | `too-few-calls` | `too-few-calls` | 1 |
| `live_parallel_multiple` | `wrong-call` | `pass` | 1 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 1 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 10 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 13 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 30 |
| `live_relevance` | `pass` | `no-call` | 3 |
| **Overall** | `pass` | `called-when-none-applied` | 10 |
| **Overall** | `pass` | `no-call` | 14 |
| **Overall** | `pass` | `too-many-calls` | 3 |
| **Overall** | `pass` | `wrong-call` | 8 |
| **Overall** | `called-when-none-applied` | `pass` | 17 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 32 |
| **Overall** | `no-call` | `pass` | 18 |
| **Overall** | `no-call` | `no-call` | 22 |
| **Overall** | `no-call` | `too-many-calls` | 1 |
| **Overall** | `no-call` | `wrong-call` | 6 |
| **Overall** | `too-few-calls` | `pass` | 7 |
| **Overall** | `too-few-calls` | `too-few-calls` | 4 |
| **Overall** | `too-few-calls` | `wrong-call` | 3 |
| **Overall** | `too-many-calls` | `pass` | 4 |
| **Overall** | `too-many-calls` | `no-call` | 4 |
| **Overall** | `too-many-calls` | `too-many-calls` | 6 |
| **Overall** | `too-many-calls` | `wrong-call` | 3 |
| **Overall** | `wrong-call` | `pass` | 17 |
| **Overall** | `wrong-call` | `no-call` | 6 |
| **Overall** | `wrong-call` | `wrong-call` | 68 |
