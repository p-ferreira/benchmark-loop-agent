# Phase 2: a reasoning paragraph in the retail policy

`claude-haiku-5-5` and `gpt-6-luna` on the 50 English retail tasks of the text benchmark of `sierra-research/tau2-bench` (release `v2.0.0`, commit `989d3285ae669e49503324bdb9981bf14fccedeb`), four trials each, without an instruction file and with `paragraph.txt` appended to the policy (`--instructions`). Run with the retail command of this repository at commit `36b55cc` on November 26, 2026, the four runs started together. Tracked in `p-ferreira/agent-system-lab#258`; the protocol, committed before the runs, is `docs/experiments/2026-11-tau-retail-reasoning-paragraph.md` in that repository.

The customer is `gpt-6-sol` and the seed 300 in every run, as in `phase-1/tau-retail`.

| Agent | Arm | Passed | Pass rate | Tasks passed in all 4 trials | Agent cost per conversation | Whole cost per conversation |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `claude-haiku-5-5` | no instruction | 177 of 200 | 88.5% | 39 of 50 | $0.0028 | $0.0159 |
| `claude-haiku-5-5` | paragraph | 176 of 200 | 88.0% | 37 of 50 | $0.0029 | $0.0160 |
| `gpt-6-luna` | no instruction | 165 of 200 | 82.5% | 32 of 50 | $0.0016 | $0.0133 |
| `gpt-6-luna` | paragraph | 163 of 200 | 81.5% | 32 of 50 | $0.0017 | $0.0134 |

**Result: no gain shown for either model.** The rule fixed beforehand asked for at least 5 more tasks won than lost on "passed in all four trials", and more than two runs without the paragraph differ by.

| Agent | Won with the paragraph | Lost with it | Won − lost | Won − lost between `phase-1/tau-retail` and the fresh run without it |
| --- | ---: | ---: | ---: | ---: |
| `claude-haiku-5-5` | 3 | 5 | −2 | +1 (3 and 2) |
| `gpt-6-luna` | 7 | 7 | 0 | −3 (6 and 9) |

No conversation was unscored. Costs use `rates-2026-11-26.json`, read from the providers' pricing pages that day. Total spent: $11.75, the one sanity conversation included.

Two runs without the paragraph already differ on 5 tasks for `claude-haiku-5-5` and on 15 for `gpt-6-luna`: with 50 tasks and four trials, only a large effect can be seen.

Each directory holds `run.json`, `records.jsonl`, `conversations.jsonl` and `report.md`; the runs with the paragraph also hold `instructions.txt`. `sanity-haiku-16` is the one conversation run first with the paragraph.

To regenerate a report and the comparison:

    uv run --locked python -m benchmark_loop_agent.tau --report results/phase-2/tau-retail-paragraph/control-haiku --rates results/phase-2/tau-retail-paragraph/rates-2026-11-26.json
    cd results/phase-2/tau-retail-paragraph && python3 compare.py control-haiku treatment-haiku

`classify.py` classes every failed conversation of the three runs per model by what the agent did against the expected actions (handed over to a human, wrong detail, partial, written check failed). It was written after the figures above were fixed and is the starting evidence of the next item.
