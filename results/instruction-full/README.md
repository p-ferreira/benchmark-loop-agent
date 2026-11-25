# The whole single-turn benchmark with one hand-written instruction, against Phase 0

Every single-turn BFCL case, 3,641 per model, on `gpt-6-sol` and `claude-opus-5-5`, with one instruction text of four lines sent with every request (SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, in each run's folder). Run on November 25, 2026 at runner commit `3f7551b`, provider default settings, 8 requests in flight. The baseline is [Phase 0](../phase-0/README.md), the same cases and models without an instruction, run on November 24, 2026. The protocol, with the rules for each statement below, was committed before the runs: `p-ferreira/agent-system-lab`, `docs/experiments/2026-11-bfcl-instruction-full-benchmark.md`.

## Summary

| | `gpt-6-sol` | `claude-opus-5-5` |
| --- | --- | --- |
| Phase 0, no instruction | 79.0% (2,878 of 3,641) | 83.5% (3,041 of 3,640) |
| **With the instruction** | **82.8%** (3,016 of 3,641) | **86.1%** (3,134 of 3,640) |
| Cases won / lost against Phase 0 | 236 / 98 | 146 / 53 |
| Input tokens | 2,007,622 | 4,539,848 |
| Output tokens | 262,147 | 558,153 |
| Cost at list rates | $6.64 (Phase 0: $5.97) | $29.32 (Phase 0: $32.00) |

Accuracy is pass / (pass + fail). One case is unscored for `claude-opus-5-5` in both runs (`live_simple_67-31-0`, refused by the provider for a parameter name). "Won / lost" counts the cases that passed only with the instruction and only in Phase 0; an exact two-sided sign test on each pair of counts gives p below 0.000001. By the rule fixed beforehand **the instruction improves both models on the whole benchmark**.

## Does it hold on cases the instruction was not written from?

The instruction was written from failures on the development part of `data/split.json` and first measured on the validation part. Only the held-out part was never used to write or choose it.

| Part | Cases | `gpt-6-sol`: Phase 0, with, won / lost | `claude-opus-5-5`: Phase 0, with, won / lost |
| --- | ---: | --- | --- |
| Development | 1,820 | 1,453 → 1,526, 114 / 41 | 1,535 → 1,578, 65 / 22 |
| Validation | 729 | 555 → 579, 50 / 26 | 585 → 606, 33 / 12 |
| **Held-out** | **1,092** | **870 → 911, 72 / 31** (p = 0.00007) | **921 → 950, 48 / 19** (p = 0.0005) |

By the rule fixed beforehand **the improvement holds on the held-out part for both models**: 79.7% to 83.4% for `gpt-6-sol` and 84.4% to 87.1% for `claude-opus-5-5` (of 1,091 scored).

## The cheaper model with the instruction against the dearer one without

`gpt-6-sol` with the instruction passed 3,016 cases for $6.64; `claude-opus-5-5` in Phase 0 passed 3,041 for $32.00. Case by case, 186 passed only for `claude-opus-5-5` and 160 only for `gpt-6-sol` (p = 0.18). By the rule fixed beforehand it **matches**: neither is ahead, and they differ by 25 cases, under 1%. On the held-out part alone: 911 against 921.

## Accuracy by category

| Category | Cases | `gpt-6-sol` Phase 0 | `gpt-6-sol` with the instruction | `claude-opus-5-5` Phase 0 | `claude-opus-5-5` with the instruction |
| --- | ---: | ---: | ---: | ---: | ---: |
| `simple_python` | 400 | 88.5% | 91.0% | 97.0% | 96.5% |
| `simple_java` | 100 | 58.0% | 64.0% | 67.0% | 70.0% |
| `simple_javascript` | 50 | 58.0% | 68.0% | 82.0% | 86.0% |
| `multiple` | 200 | 88.0% | 94.0% | 94.0% | 96.0% |
| `parallel` | 200 | 85.5% | 91.0% | 91.5% | 94.0% |
| `parallel_multiple` | 200 | 64.0% | 80.5% | 87.0% | 90.5% |
| `irrelevance` | 240 | 87.1% | 92.1% | 81.2% | 90.0% |
| `live_simple` | 258 | 78.3% | 81.0% | 86.0% | 85.6% |
| `live_multiple` | 1,053 | 73.8% | 75.5% | 80.6% | 81.4% |
| `live_parallel` | 16 | 75.0% | 81.2% | 81.2% | 87.5% |
| `live_parallel_multiple` | 24 | 58.3% | 66.7% | 66.7% | 75.0% |
| `live_irrelevance` | 884 | 83.3% | 86.1% | 78.6% | 83.6% |
| `live_relevance` | 16 | 75.0% | 50.0% | 68.8% | 62.5% |
| **Overall** | **3,641** | **79.0%** | **82.8%** | **83.5%** | **86.1%** |

`live_relevance` has 16 cases, and both models lost ground there: it is the one category where any call passes, and the instruction's third rule makes a model more willing to decline.

## What to keep in mind

- **The baseline is a day older.** Two runs of the same model without an instruction differ by about 1% of the pass count either way, and a change at the provider between the two days cannot be told apart from the instruction. Same-day comparisons on parts of the benchmark are in [`instruction-validation`](../instruction-validation/README.md), [`learned-instruction`](../learned-instruction/README.md) and [`instruction-ladder`](../instruction-ladder/README.md), and agree in direction and size.
- **One run per arm.**
- **The whole-benchmark figure includes the cases the instruction was written from.** The held-out row is the evidence that it generalizes.
- **This benchmark only**, and only its single-turn categories. Multi-turn, web search, memory and format sensitivity are not run, so these overall figures are not the leaderboard's.
- **Cost** counts all input at the uncached rate in `data/rates.json`.

## What is in this folder

| Path | What |
| --- | --- |
| `gpt-6-sol/`, `claude-opus-5-5/` | `records.jsonl`, `run.json`, the instruction text and the generated report, with failures by class. |
| `compare-phase-0-gpt-6-sol/`, `compare-phase-0-claude-opus-5-5/` | Each run against its Phase 0 run, case by case. |

## Regenerate

```sh
uv run --locked python -m benchmark_loop_agent.report results/instruction-full/gpt-6-sol --output-dir results/instruction-full/gpt-6-sol
uv run --locked python -m benchmark_loop_agent.report --compare results/phase-0/gpt-6-sol results/instruction-full/gpt-6-sol --output-dir results/instruction-full/compare-phase-0-gpt-6-sol
```

and the same for `claude-opus-5-5`.
