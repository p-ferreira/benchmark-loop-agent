# Comparison of two runs (openai)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/learned-instruction/validation-starting` | `gpt-6-sol` | sha256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes |
| B | `results/learned-instruction/validation-candidate-a` | `gpt-6-sol` | sha256 `f4bf3a94cd4e6a7bef4e478a5687940c0917e7e81eb993b1f09da62fe6f578e1`, 1996 bytes |

* Cases both runs selected (compared): 729
* Cases only A selected: 0
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 80 | 80 | 20 | 0 | 54 | 6 | 0 |
| `simple_java` | 20 | 20 | 1 | 0 | 13 | 6 | 0 |
| `simple_javascript` | 10 | 10 | 2 | 0 | 4 | 4 | 0 |
| `multiple` | 40 | 40 | 10 | 0 | 29 | 1 | 0 |
| `parallel` | 40 | 40 | 6 | 0 | 28 | 6 | 0 |
| `parallel_multiple` | 40 | 40 | 4 | 2 | 23 | 11 | 0 |
| `irrelevance` | 48 | 48 | 0 | 2 | 45 | 1 | 0 |
| `live_simple` | 52 | 52 | 10 | 2 | 26 | 14 | 0 |
| `live_multiple` | 211 | 211 | 56 | 3 | 96 | 56 | 0 |
| `live_parallel` | 3 | 3 | 3 | 0 | 0 | 0 | 0 |
| `live_parallel_multiple` | 5 | 5 | 0 | 0 | 4 | 1 | 0 |
| `live_irrelevance` | 177 | 177 | 0 | 23 | 150 | 4 | 0 |
| `live_relevance` | 3 | 3 | 1 | 0 | 1 | 1 | 0 |
| **Overall** | 729 | 729 | 113 | 32 | 473 | 111 | 0 |

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
| `simple_python` | `pass` | `no-call` | 18 |
| `simple_python` | `pass` | `wrong-call` | 2 |
| `simple_python` | `no-call` | `no-call` | 1 |
| `simple_python` | `too-many-calls` | `no-call` | 1 |
| `simple_python` | `wrong-call` | `no-call` | 2 |
| `simple_python` | `wrong-call` | `wrong-call` | 2 |
| `simple_java` | `pass` | `no-call` | 1 |
| `simple_java` | `no-call` | `no-call` | 2 |
| `simple_java` | `wrong-call` | `wrong-call` | 4 |
| `simple_javascript` | `pass` | `no-call` | 2 |
| `simple_javascript` | `no-call` | `no-call` | 2 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 2 |
| `multiple` | `pass` | `no-call` | 9 |
| `multiple` | `pass` | `wrong-call` | 1 |
| `multiple` | `no-call` | `no-call` | 1 |
| `parallel` | `pass` | `no-call` | 6 |
| `parallel` | `no-call` | `no-call` | 1 |
| `parallel` | `too-few-calls` | `no-call` | 1 |
| `parallel` | `wrong-call` | `no-call` | 1 |
| `parallel` | `wrong-call` | `wrong-call` | 3 |
| `parallel_multiple` | `pass` | `no-call` | 3 |
| `parallel_multiple` | `pass` | `too-few-calls` | 1 |
| `parallel_multiple` | `no-call` | `no-call` | 2 |
| `parallel_multiple` | `too-few-calls` | `pass` | 1 |
| `parallel_multiple` | `too-few-calls` | `no-call` | 2 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 1 |
| `parallel_multiple` | `wrong-call` | `pass` | 1 |
| `parallel_multiple` | `wrong-call` | `no-call` | 4 |
| `parallel_multiple` | `wrong-call` | `too-few-calls` | 1 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 1 |
| `irrelevance` | `called-when-none-applied` | `pass` | 2 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 1 |
| `live_simple` | `pass` | `no-call` | 9 |
| `live_simple` | `pass` | `wrong-call` | 1 |
| `live_simple` | `too-many-calls` | `no-call` | 1 |
| `live_simple` | `too-many-calls` | `wrong-call` | 1 |
| `live_simple` | `wrong-call` | `pass` | 2 |
| `live_simple` | `wrong-call` | `no-call` | 6 |
| `live_simple` | `wrong-call` | `wrong-call` | 6 |
| `live_multiple` | `pass` | `no-call` | 49 |
| `live_multiple` | `pass` | `too-many-calls` | 1 |
| `live_multiple` | `pass` | `wrong-call` | 6 |
| `live_multiple` | `no-call` | `no-call` | 18 |
| `live_multiple` | `too-many-calls` | `no-call` | 1 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 2 |
| `live_multiple` | `wrong-call` | `pass` | 3 |
| `live_multiple` | `wrong-call` | `no-call` | 10 |
| `live_multiple` | `wrong-call` | `wrong-call` | 25 |
| `live_parallel` | `pass` | `no-call` | 3 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 1 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 23 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 4 |
| `live_relevance` | `pass` | `no-call` | 1 |
| `live_relevance` | `no-call` | `no-call` | 1 |
| **Overall** | `pass` | `no-call` | 101 |
| **Overall** | `pass` | `too-few-calls` | 1 |
| **Overall** | `pass` | `too-many-calls` | 1 |
| **Overall** | `pass` | `wrong-call` | 10 |
| **Overall** | `called-when-none-applied` | `pass` | 25 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 5 |
| **Overall** | `no-call` | `no-call` | 28 |
| **Overall** | `too-few-calls` | `pass` | 1 |
| **Overall** | `too-few-calls` | `no-call` | 3 |
| **Overall** | `too-few-calls` | `too-few-calls` | 1 |
| **Overall** | `too-many-calls` | `no-call` | 3 |
| **Overall** | `too-many-calls` | `too-many-calls` | 2 |
| **Overall** | `too-many-calls` | `wrong-call` | 1 |
| **Overall** | `wrong-call` | `pass` | 6 |
| **Overall** | `wrong-call` | `no-call` | 23 |
| **Overall** | `wrong-call` | `too-few-calls` | 1 |
| **Overall** | `wrong-call` | `wrong-call` | 44 |
