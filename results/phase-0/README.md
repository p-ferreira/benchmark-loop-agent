# Phase 0 results: single-turn BFCL, `gpt-6-sol` and `claude-opus-5-5`

Every single-turn case of the Berkeley Function Calling Leaderboard (BFCL), 3,641 per model across thirteen categories, run once through each model's native function calling on November 24, 2026 and scored with BFCL's own checker.

## Summary

| | `gpt-6-sol` | `claude-opus-5-5` |
| --- | --- | --- |
| **Overall accuracy** | **79.0%** (2,878 of 3,641) | **83.5%** (3,041 of 3,640) |
| Pass / fail / unscored | 2,878 / 763 / 0 | 3,041 / 599 / 1 |
| Input tokens | 1,537,933 | 3,982,928 |
| Output tokens | 289,726 | 803,252 |
| Cost at list rates | $5.97 | $32.00 |
| Wall time, 8 requests in flight | 712 s | 1144 s |
| Full report | [report-openai-gpt-6-sol.md](gpt-6-sol/report-openai-gpt-6-sol.md) | [report-anthropic-claude-opus-5-5.md](claude-opus-5-5/report-anthropic-claude-opus-5-5.md) |

Accuracy is pass / (pass + fail). Overall pools every judged case, so each case counts once and a larger category weighs more; it is not the mean of the category figures.

## Accuracy by category

| Category | Cases | `gpt-6-sol` | `claude-opus-5-5` | Difference (points) |
| --- | ---: | ---: | ---: | ---: |
| `simple_python` | 400 | 88.5% | 97.0% | +8.5 |
| `simple_java` | 100 | 58.0% | 67.0% | +9.0 |
| `simple_javascript` | 50 | 58.0% | 82.0% | +24.0 |
| `multiple` | 200 | 88.0% | 94.0% | +6.0 |
| `parallel` | 200 | 85.5% | 91.5% | +6.0 |
| `parallel_multiple` | 200 | 64.0% | 87.0% | +23.0 |
| `irrelevance` | 240 | 87.1% | 81.2% | -5.8 |
| `live_simple` | 258 | 78.3% | 86.0% | +7.7 |
| `live_multiple` | 1,053 | 73.8% | 80.6% | +6.8 |
| `live_parallel` | 16 | 75.0% | 81.2% | +6.2 |
| `live_parallel_multiple` | 24 | 58.3% | 66.7% | +8.3 |
| `live_irrelevance` | 884 | 83.3% | 78.6% | -4.6 |
| `live_relevance` | 16 | 75.0% | 68.8% | -6.2 |
| **Overall** | **3,641** | **79.0%** | **83.5%** | **+4.5** |

The difference is `claude-opus-5-5` minus `gpt-6-sol`. Three categories have 16 to 24 cases, where one case is worth 4 to 6 points; read their figures with that in mind.

## What to keep in mind

- **Scope.** These are BFCL's single-turn categories only. BFCL's leaderboard overall also covers multi-turn, web search, memory and format sensitivity, so the overall figure here is not the leaderboard's overall. Per-category figures use BFCL's data and checker at the pinned revision.
- **One run.** Each case was run once per model, with no sampling setting changed from the providers' defaults. No repeat runs, so there is no measure of run-to-run variation.
- **One unscored case.** `live_simple_67-31-0` for `claude-opus-5-5`: Anthropic's API refused the request because a parameter name in that case's tool does not match the API's naming rule. It is counted as unscored, not as a failure, and its report is marked incomplete for that reason.
- **Cost.** Input and output tokens at the list rates in [`data/rates.json`](../../data/rates.json), read on the providers' pricing pages on the date given there and read again, unchanged, on the day of the run. All input is counted at the uncached rate, so the figure can overstate what was charged.
- **Wall time.** The two models ran at the same time as two separate processes, so each wall time is that model's own.

## What is in this folder

| Path | What |
| --- | --- |
| `gpt-6-sol/records.jsonl`, `claude-opus-5-5/records.jsonl` | One record per case: category, outcome (`pass`, `fail`, `unscored`), the checker's reasons, the calls the model returned, tokens, latency, requested and actual model, dataset and scorer revisions. |
| `gpt-6-sol/run.json`, `claude-opus-5-5/run.json` | The run's parameters, the number of cases selected per category, and each invocation's start, end, wall time and concurrency. |
| `*/report-*.md` | The report generated from the two files above. |

## Regenerate the reports

The reports are built only from the records, `run.json` and the rates file, so anyone can rebuild them:

```sh
uv run --locked python -m benchmark_loop_agent.report results/phase-0/gpt-6-sol
uv run --locked python -m benchmark_loop_agent.report results/phase-0/claude-opus-5-5
```

Each command rewrites the report in its folder; `git diff` then shows whether anything changed.

## Look at single cases

Failed cases of one category, with the checker's reason:

```sh
jq -c 'select(.category == "parallel_multiple" and .outcome == "fail") | {case_id, reasons}' results/phase-0/gpt-6-sol/records.jsonl
```

Cases one model passed and the other failed:

```sh
join <(jq -r 'select(.outcome == "pass") | .case_id' results/phase-0/claude-opus-5-5/records.jsonl | sort) \
     <(jq -r 'select(.outcome == "fail") | .case_id' results/phase-0/gpt-6-sol/records.jsonl | sort)
```

## Reproduce the run

The run used this repository at commit `8314c75f7e26bdb9dec5b1da425c183d26d6bf91`, with both keys in the environment:

```sh
uv run --locked python -m benchmark_loop_agent --output-dir runs/gpt-6-sol --provider openai --openai-model gpt-6-sol --concurrency 8
uv run --locked python -m benchmark_loop_agent --output-dir runs/claude-opus-5-5 --provider anthropic --anthropic-model claude-opus-5-5 --concurrency 8
```

A new run calls the models again, so its figures can differ from these. The run was traced in a local Phoenix ([Tracing in Phoenix](../../README.md#tracing-in-phoenix)); the traces are not part of the repository.
