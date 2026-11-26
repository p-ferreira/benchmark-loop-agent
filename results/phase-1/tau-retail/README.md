# Phase 1: raw baselines on τ-bench retail

Four models, with no instruction file, on the 50 English retail tasks of the text benchmark of `sierra-research/tau2-bench` (release `v2.0.0`, commit `989d3285ae669e49503324bdb9981bf14fccedeb`), run with the retail command of this repository at commit `0660e78` on November 25, 2026. Tracked in `p-ferreira/agent-system-lab#239`; the protocol, written before the runs, is `docs/experiments/2026-11-tau-retail-baselines.md` in that repository.

The customer is `gpt-6-sol` in every run. The judge is upstream's default for written assertions, `gpt-5.4-mini-2026-03-17`; upstream's other judge was not called by any conversation.

| Agent | Trials | Passed | Pass rate | All 4 trials | Agent cost per conversation | Whole cost per conversation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-sonnet-5-5` | 1 | 45 of 50 | 90.0% | not run | $0.0385 | $0.0502 |
| `gpt-6-sol` | 1 | 40 of 50 | 80.0% | not run | $0.0265 | $0.0390 |
| `claude-haiku-5-5` | 4 | 178 of 200 | 89.0% | 76.0% | $0.0028 | $0.0158 |
| `gpt-6-luna` | 4 | 165 of 200 | 82.5% | 70.0% | $0.0016 | $0.0135 |

No conversation was unscored. "All 4 trials" is upstream's pass^4. The whole cost adds the customer and the judge, which are the same in every run and cost more than either cheaper agent. Costs use `rates-2026-11-25.json`, read from the providers' pricing pages that day. Total spent: $10.34, the one sanity conversation included.

One trial of 50 tasks is uncertain by about 7 points, and four trials by about 3.5: the differences between the models' pass rates are not separated by these runs. Tasks 52 and 105 were passed by no model in any trial.

Each directory holds `run.json`, `records.jsonl` (one line per conversation), `conversations.jsonl` (the full conversations) and `report.md`. `sanity-haiku-16` is the one conversation run first, to see a judge called.

To regenerate a report:

    uv run --locked python -m benchmark_loop_agent.tau --report results/phase-1/tau-retail/haiku --rates results/phase-1/tau-retail/rates-2026-11-25.json
