# Phase 2: a finish check in code on retail

`claude-haiku-5-5` and `gpt-6-luna` on the 50 English retail tasks of the text benchmark of `sierra-research/tau2-bench` (release `v2.0.0`, commit `989d3285ae669e49503324bdb9981bf14fccedeb`), four trials each, with `--finish-check` and no instruction file. Run with the retail command of this repository at commit `a66bbff` on November 26, 2026, the two runs side by side, under the protocol of `p-ferreira/agent-system-lab#260` (`docs/experiments/2026-11-tau-retail-finish-check.md` there). The runs without the check are those of `../tau-retail-paragraph` (`control-haiku`, `control-luna`, the same day); nothing of them was run again.

With the check, bla holds a reply once and asks the model again before a hand-over to a human, and before the reply to the customer after a change (see the README of the repository).

| Agent | Arm | Passed | Pass rate | Tasks passed in all 4 trials | Agent calls | Agent cost per conversation | Whole cost per conversation |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-haiku-5-5` | no check | 177 of 200 | 88.5% | 39 of 50 | 2,239 | $0.0028 | $0.0159 |
| `claude-haiku-5-5` | finish check | 184 of 200 | 92.0% | 43 of 50 | 2,516 | $0.0033 | $0.0164 |
| `gpt-6-luna` | no check | 165 of 200 | 82.5% | 32 of 50 | 2,362 | $0.0016 | $0.0133 |
| `gpt-6-luna` | finish check | 164 of 200 | 82.0% | 35 of 50 | 2,648 | $0.0018 | $0.0135 |

**Result: no gain shown for either model, by the rule fixed beforehand.** The rule asked for at least 5 more tasks won than lost on "passed in all four trials", and more than two runs without the check differ by. `claude-haiku-5-5` is one task short of it.

| Agent | Won with the check | Lost with it | Won − lost | Won − lost between two runs without it |
| --- | ---: | ---: | ---: | ---: |
| `claude-haiku-5-5` | 5 | 1 | +4 | +1 (3 and 2) |
| `gpt-6-luna` | 6 | 3 | +3 | −3 (6 and 9) |

Against the earlier run without the check (`phase-1/tau-retail`): +5 (6 and 1) for `claude-haiku-5-5`, 0 (6 and 6) for `gpt-6-luna`.

Replies held: for `claude-haiku-5-5`, 235 replies after a change in 175 conversations and 36 hand-overs; for `gpt-6-luna`, 225 in 169 and 39.

Failed conversations by what the agent did, without the check and with it (`classes.py`):

| What the agent did | `claude-haiku-5-5` | `gpt-6-luna` |
| --- | ---: | ---: |
| Some of the requested changes, not all | 5 → 0 | 7 → 6 |
| Changed nothing, handed to a human | 4 → 4 | 11 → 10 |
| Changed nothing | 1 → 1 | 1 → 2 |
| Right action, wrong detail | 6 → 6 | 9 → 9 |
| Changed the order correctly and failed a written check | 5 → 5 | 6 → 8 |
| Other | 2 → 0 | 1 → 1 |
| All failed conversations | 23 → 16 | 35 → 36 |

**The check was written from the failure classes of these same 50 tasks,** so any difference here is fitted to them. One run per arm, one day, one seed. No conversation was unscored, and none was read by a person or an agent. Costs use `../tau-retail-paragraph/rates-2026-11-26.json`. Total spent: $5.99, the one sanity conversation (`sanity-haiku-16`) included.

Each directory holds `run.json`, `records.jsonl`, `conversations.jsonl` and `report.md`. To regenerate:

    uv run --locked python -m benchmark_loop_agent.tau --report results/phase-2/tau-retail-finish-check/haiku --rates results/phase-2/tau-retail-paragraph/rates-2026-11-26.json
    cd results/phase-2/tau-retail-paragraph && python3 compare.py control-haiku ../tau-retail-finish-check/haiku
    python3 results/phase-2/tau-retail-finish-check/classes.py
