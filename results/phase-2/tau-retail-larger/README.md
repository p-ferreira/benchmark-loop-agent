# Phase 2: the larger models on retail, four trials

`claude-sonnet-5-5` and `gpt-6-sol` on the 50 English retail tasks of the text benchmark of `sierra-research/tau2-bench` (release `v2.0.0`, commit `989d3285ae669e49503324bdb9981bf14fccedeb`), four trials each, without an instruction file. Run with the retail command of this repository at commit `e96a29b` on November 26, 2026, the two runs side by side, under the protocol of `p-ferreira/agent-system-lab#261` (`docs/experiments/2026-11-tau-retail-larger-models.md` there). Nothing was under test: the runs give the larger models the measure the cheaper ones already had, tasks passed in all four trials.

The customer is `gpt-6-sol` and the seed 300, as in `phase-1/tau-retail` and `phase-2/tau-retail-paragraph`, whose runs without an instruction are the cheaper models' rows below.

| Agent | Run | Passed | Pass rate | Tasks passed in all 4 trials | Agent cost per conversation | Whole cost per conversation |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `claude-sonnet-5-5` | this directory | 180 of 200 | 90.0% | 42 of 50 | $0.0386 | $0.0505 |
| `claude-haiku-5-5` | `phase-1/tau-retail` | 178 of 200 | 89.0% | 38 of 50 | $0.0028 | $0.0158 |
| `claude-haiku-5-5` | `phase-2/tau-retail-paragraph`, no instruction | 177 of 200 | 88.5% | 39 of 50 | $0.0028 | $0.0159 |
| `gpt-6-sol` | this directory | 156 of 200 | 78.0% | 33 of 50 | $0.0266 | $0.0389 |
| `gpt-6-luna` | `phase-1/tau-retail` | 165 of 200 | 82.5% | 35 of 50 | $0.0016 | $0.0135 |
| `gpt-6-luna` | `phase-2/tau-retail-paragraph`, no instruction | 165 of 200 | 82.5% | 32 of 50 | $0.0016 | $0.0133 |

**Result: not separated, for either pair.** The rule fixed beforehand calls a gap shown when the larger model passes, in all four trials, at least 5 tasks more than the better of the cheaper model's two runs, and a reverse gap when it passes at least 5 fewer than the worse of them. `claude-sonnet-5-5` is 3 above `claude-haiku-5-5`'s better run (42 against 39); `gpt-6-sol` lies between `gpt-6-luna`'s two runs (33 against 35 and 32).

By task, from `count.py`: `claude-sonnet-5-5` passes in all four trials 6 tasks the phase 1 run of `claude-haiku-5-5` does not and misses 2 it does (4 and 1 against the phase 2 run); `gpt-6-sol` 6 and 8 against the phase 1 run of `gpt-6-luna`, 8 and 7 against the phase 2 run.

No conversation was unscored. Costs use `../tau-retail-paragraph/rates-2026-11-26.json`; the rows these runs use were read again on the providers' pricing pages on November 26, 2026 and are the same. Total spent: $17.88 ($10.10 and $7.78).

Not shown: anything beyond one day, one seed and provider default settings; a difference smaller than the rule's 5 tasks; why a task fails (no conversation was read). The comparison across providers was not fixed beforehand.

Each directory holds `run.json`, `records.jsonl`, `conversations.jsonl` and `report.md`. To regenerate a report and the counts:

    uv run --locked python -m benchmark_loop_agent.tau --report results/phase-2/tau-retail-larger/sonnet --rates results/phase-2/tau-retail-paragraph/rates-2026-11-26.json
    python3 results/phase-2/tau-retail-larger/count.py
