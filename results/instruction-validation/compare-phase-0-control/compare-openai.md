# Comparison of two runs (openai)

Run A and run B are compared case by case on the cases both selected; a case is never paired with another provider's. A case is paired when both runs scored it (pass or fail).

| Run | Directory | Model | Instruction |
| --- | --- | --- | --- |
| A | `results/phase-0/gpt-6-sol` | `gpt-6-sol` | none |
| B | `results/instruction-validation/control` | `gpt-6-sol` | none |

* Cases both runs selected (compared): 729
* Cases only A selected: 2912
* Cases only B selected: 0

## Passes

| Category | Compared | Paired | Only A passed | Only B passed | Both passed | Both failed | Not paired |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `simple_python` | 80 | 80 | 2 | 1 | 66 | 11 | 0 |
| `simple_java` | 20 | 20 | 0 | 0 | 13 | 7 | 0 |
| `simple_javascript` | 10 | 10 | 2 | 0 | 4 | 4 | 0 |
| `multiple` | 40 | 40 | 1 | 0 | 37 | 2 | 0 |
| `parallel` | 40 | 40 | 0 | 0 | 31 | 9 | 0 |
| `parallel_multiple` | 40 | 40 | 0 | 0 | 24 | 16 | 0 |
| `irrelevance` | 48 | 48 | 0 | 1 | 41 | 6 | 0 |
| `live_simple` | 52 | 52 | 1 | 4 | 33 | 14 | 0 |
| `live_multiple` | 211 | 211 | 6 | 4 | 140 | 61 | 0 |
| `live_parallel` | 3 | 3 | 0 | 0 | 3 | 0 | 0 |
| `live_parallel_multiple` | 5 | 5 | 0 | 0 | 4 | 1 | 0 |
| `live_irrelevance` | 177 | 177 | 6 | 1 | 138 | 32 | 0 |
| `live_relevance` | 3 | 3 | 1 | 0 | 2 | 0 | 0 |
| **Overall** | 729 | 729 | 19 | 11 | 536 | 163 | 0 |

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
| `simple_python` | `pass` | `wrong-call` | 2 |
| `simple_python` | `no-call` | `no-call` | 4 |
| `simple_python` | `too-many-calls` | `too-many-calls` | 1 |
| `simple_python` | `wrong-call` | `pass` | 1 |
| `simple_python` | `wrong-call` | `wrong-call` | 6 |
| `simple_java` | `no-call` | `no-call` | 2 |
| `simple_java` | `wrong-call` | `wrong-call` | 5 |
| `simple_javascript` | `pass` | `no-call` | 1 |
| `simple_javascript` | `pass` | `wrong-call` | 1 |
| `simple_javascript` | `no-call` | `no-call` | 2 |
| `simple_javascript` | `wrong-call` | `wrong-call` | 2 |
| `multiple` | `pass` | `no-call` | 1 |
| `multiple` | `wrong-call` | `wrong-call` | 2 |
| `parallel` | `too-few-calls` | `no-call` | 1 |
| `parallel` | `too-few-calls` | `too-few-calls` | 1 |
| `parallel` | `wrong-call` | `too-few-calls` | 1 |
| `parallel` | `wrong-call` | `wrong-call` | 6 |
| `parallel_multiple` | `too-few-calls` | `too-few-calls` | 12 |
| `parallel_multiple` | `wrong-call` | `wrong-call` | 4 |
| `irrelevance` | `called-when-none-applied` | `pass` | 1 |
| `irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 6 |
| `live_simple` | `pass` | `no-call` | 1 |
| `live_simple` | `no-call` | `pass` | 3 |
| `live_simple` | `no-call` | `no-call` | 1 |
| `live_simple` | `no-call` | `wrong-call` | 1 |
| `live_simple` | `too-many-calls` | `wrong-call` | 1 |
| `live_simple` | `wrong-call` | `pass` | 1 |
| `live_simple` | `wrong-call` | `no-call` | 1 |
| `live_simple` | `wrong-call` | `wrong-call` | 10 |
| `live_multiple` | `pass` | `no-call` | 2 |
| `live_multiple` | `pass` | `wrong-call` | 4 |
| `live_multiple` | `no-call` | `pass` | 1 |
| `live_multiple` | `no-call` | `no-call` | 16 |
| `live_multiple` | `no-call` | `wrong-call` | 1 |
| `live_multiple` | `too-many-calls` | `pass` | 2 |
| `live_multiple` | `too-many-calls` | `too-many-calls` | 2 |
| `live_multiple` | `wrong-call` | `pass` | 1 |
| `live_multiple` | `wrong-call` | `no-call` | 5 |
| `live_multiple` | `wrong-call` | `too-many-calls` | 1 |
| `live_multiple` | `wrong-call` | `wrong-call` | 36 |
| `live_parallel_multiple` | `wrong-call` | `wrong-call` | 1 |
| `live_irrelevance` | `pass` | `called-when-none-applied` | 6 |
| `live_irrelevance` | `called-when-none-applied` | `pass` | 1 |
| `live_irrelevance` | `called-when-none-applied` | `called-when-none-applied` | 32 |
| `live_relevance` | `pass` | `no-call` | 1 |
| **Overall** | `pass` | `called-when-none-applied` | 6 |
| **Overall** | `pass` | `no-call` | 6 |
| **Overall** | `pass` | `wrong-call` | 7 |
| **Overall** | `called-when-none-applied` | `pass` | 2 |
| **Overall** | `called-when-none-applied` | `called-when-none-applied` | 38 |
| **Overall** | `no-call` | `pass` | 4 |
| **Overall** | `no-call` | `no-call` | 25 |
| **Overall** | `no-call` | `wrong-call` | 2 |
| **Overall** | `too-few-calls` | `no-call` | 1 |
| **Overall** | `too-few-calls` | `too-few-calls` | 13 |
| **Overall** | `too-many-calls` | `pass` | 2 |
| **Overall** | `too-many-calls` | `too-many-calls` | 3 |
| **Overall** | `too-many-calls` | `wrong-call` | 1 |
| **Overall** | `wrong-call` | `pass` | 3 |
| **Overall** | `wrong-call` | `no-call` | 6 |
| **Overall** | `wrong-call` | `too-few-calls` | 1 |
| **Overall** | `wrong-call` | `too-many-calls` | 1 |
| **Overall** | `wrong-call` | `wrong-call` | 72 |
