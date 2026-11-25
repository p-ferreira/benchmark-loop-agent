# One hand-written instruction against none: `gpt-6-sol`, validation part

The 729 validation cases of single-turn BFCL (`data/split.json`), run on November 25, 2026 on `gpt-6-sol` twice at the same time: without an instruction, and with one instruction text sent with every request (`--instructions`). Runner commit `1ac2aec`, provider default settings, 8 requests in flight. The protocol, with the rule for what counts as a gain, was committed before the runs: `p-ferreira/agent-system-lab`, `docs/experiments/2026-11-bfcl-instruction-validation.md`.

## Result

| | No instruction | With the instruction |
| --- | --- | --- |
| **Passes over selected cases** | **75.0%** (547 of 729) | **80.4%** (586 of 729) |
| Fail / unscored | 182 / 0 | 143 / 0 |
| Input tokens | 308,344 | 402,385 |
| Output tokens | 55,701 | 55,541 |
| Cost at list rates | $1.17 | $1.36 |

Paired, case by case: 57 cases passed only with the instruction, 18 only without it, 529 in both and 125 in neither. An exact two-sided sign test on 57 against 18 gives p = 0.000007.

How much two runs without an instruction differ: against the Phase 0 run of November 24 on the same 729 cases, 19 cases passed only in Phase 0 and 11 only in the new run (p = 0.20).

## Failures by class

| Class | No instruction | With the instruction |
| --- | ---: | ---: |
| `called-when-none-applied` | 44 | 28 |
| `no-call` | 38 | 29 |
| `too-few-calls` | 14 | 4 |
| `too-many-calls` | 4 | 7 |
| `wrong-call` | 82 | 75 |
| `malformed-call` | 0 | 0 |
| **All failures** | **182** | **143** |

## What to keep in mind

- **One run per arm.** The comparison with Phase 0 is the only measure of run-to-run movement.
- **One model.** `claude-opus-5-5` was not run.
- **Validation only.** The held-out part was not run. The instruction was written from failures on the development part and from sources that use no benchmark case; its author had seen Phase 0 pass counts per category on all parts, and no single validation or held-out case.
- **Cost** counts all input at the uncached rate in `data/rates.json`.

## The instruction

[`instruction/instruction-openai.txt`](instruction/instruction-openai.txt), SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`, 604 bytes.

## What is in this folder

| Path | What |
| --- | --- |
| `control/`, `instruction/` | `records.jsonl`, `run.json` and the generated report of each run; the instruction text beside the second. |
| `compare-control-instruction/` | The two runs compared case by case, with the movement between failure classes. |
| `compare-phase-0-control/` | Phase 0 against the new run without an instruction, over the 729 cases both selected. |

## Regenerate

```sh
uv run --locked python -m benchmark_loop_agent.report results/instruction-validation/control --output-dir results/instruction-validation/control
uv run --locked python -m benchmark_loop_agent.report results/instruction-validation/instruction --output-dir results/instruction-validation/instruction
uv run --locked python -m benchmark_loop_agent.report --compare results/instruction-validation/control results/instruction-validation/instruction --output-dir results/instruction-validation/compare-control-instruction
uv run --locked python -m benchmark_loop_agent.report --compare results/phase-0/gpt-6-sol results/instruction-validation/control --output-dir results/instruction-validation/compare-phase-0-control
```
