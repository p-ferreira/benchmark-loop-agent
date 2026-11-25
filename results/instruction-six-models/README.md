# Six models, raw and with one hand-written instruction: the whole single-turn benchmark

Every single-turn BFCL case, 3,641 per model, each model raw and with the same instruction of four lines (SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`). Runner commit `3f7551b`, provider default settings, 8 requests in flight. The protocol, with the rules for each statement below, was committed before the runs: `p-ferreira/agent-system-lab`, `docs/experiments/2026-11-bfcl-instruction-six-models.md`.

This folder holds the eight runs of November 25, 2026 for `gpt-6.1-terra`, `gpt-6-luna`, `claude-sonnet-5-5` and `claude-haiku-5-5`. The rows of `gpt-6-sol` and `claude-opus-5-5` come from [Phase 0](../phase-0/README.md) (raw, November 24) and [`instruction-full`](../instruction-full/README.md) (with the instruction, November 25).

## The table

| Model | List price per million tokens, input / output | Raw passes | Passes with the instruction | Won / lost | Cost raw | Cost with |
| --- | --- | --- | --- | --- | ---: | ---: |
| `gpt-6-luna` | $0.10 / $0.50 | 2,879 (79.1%) | 2,992 (82.2%) | 225 / 112 | $0.33 | $0.34 |
| `gpt-6.1-terra` | $1.00 / $5.00 | 2,880 (79.1%) | 3,019 (82.9%) | 231 / 92 | $3.06 | $3.32 |
| `gpt-6-sol` | $2.00 / $10.00 | 2,878 (79.0%) | 3,016 (82.8%) | 236 / 98 | $5.97 | $6.64 |
| `claude-haiku-5-5` | $0.10 / $0.50 | 2,993 (82.2%) | 3,043 (83.6%) | 114 / 64 | $0.81 | $0.79 |
| `claude-sonnet-5-5` | $2 / $10 | 3,067 (84.3%) | 3,155 (86.7%) | 147 / 59 | $15.25 | $14.43 |
| `claude-opus-5-5` | $4 / $20 | 3,041 (83.5%) | 3,134 (86.1%) | 146 / 53 | $32.00 | $29.32 |

Accuracy is pass / (pass + fail). One case is unscored for the three Claude models in every run (`live_simple_67-31-0`, refused by the provider for a parameter name), so their percentages are of 3,640. "Won / lost" counts the cases that passed only with the instruction and only raw. By the rule fixed beforehand (more won than lost, exact two-sided sign test below 0.05) **the instruction improves all six models on the whole benchmark**; the largest p is 0.0002.

## On the held-out part

The 1,092 cases never used to write or choose the instruction:

| Model | Raw | With the instruction | Won / lost | p | Holds by the rule |
| --- | --- | --- | --- | --- | --- |
| `gpt-6-luna` | 869 | 894 | 61 / 36 | 0.014 | yes |
| `gpt-6.1-terra` | 861 | 912 | 81 / 30 | 0.000001 | yes |
| `gpt-6-sol` | 870 | 911 | 72 / 31 | 0.00007 | yes |
| `claude-haiku-5-5` | 903 | 923 | 39 / 19 | 0.012 | yes |
| `claude-sonnet-5-5` | 931 | 944 | 41 / 28 | 0.15 | **not shown** |
| `claude-opus-5-5` | 921 | 950 | 48 / 19 | 0.0005 | yes |

For `claude-sonnet-5-5` the held-out gain is in the same direction and too small to pass the rule.

## A model with the instruction against the next one up, raw

| Step | With the instruction | Next model, raw | Only the first / only the second | p | Verdict |
| --- | --- | --- | --- | --- | --- |
| `gpt-6-luna` against `gpt-6.1-terra` | 2,992, $0.34 | 2,880, $3.06 | 267 / 155 | below 0.000001 | **beats** |
| `gpt-6.1-terra` against `gpt-6-sol` | 3,019, $3.32 | 2,878, $5.97 | 263 / 122 | below 0.000001 | **beats** |
| `claude-haiku-5-5` against `claude-sonnet-5-5` | 3,043, $0.79 | 3,067, $15.25 | 131 / 155 | 0.17 | **matches** |
| `claude-sonnet-5-5` against `claude-opus-5-5` | 3,155, $14.43 | 3,041, $32.00 | 194 / 80 | below 0.000001 | **beats** |

"Matches" means neither is ahead by the rule and the pass counts differ by 73 cases (2%) or fewer. From [`instruction-full`](../instruction-full/README.md): `gpt-6-sol` with the instruction matches `claude-opus-5-5` raw (3,016 against 3,041).

Two things the raw columns show, which the ladder has to be read with:

- The three OpenAI models are level raw: 2,879, 2,880 and 2,878 passes. A cheaper one with the instruction beats the next one up because the instruction helps, not because the grades differ here.
- `claude-sonnet-5-5` raw passes more cases than `claude-opus-5-5` raw (3,067 against 3,041), so its step is not a cheaper model catching a better one on this benchmark.

Not comparisons fixed beforehand, so observations only: `claude-haiku-5-5` with the instruction passed 3,043 cases for $0.79, and `claude-opus-5-5` raw 3,041 for $32.00; `gpt-6-luna` with the instruction passed 2,992 for $0.34, and `gpt-6-sol` raw 2,878 for $5.97.

## Tokens of the eight new runs

| Run | Cost at list rates |
| --- | ---: |
| `gpt-6-luna` raw / with | $0.33 / $0.34 |
| `gpt-6.1-terra` raw / with | $3.06 / $3.32 |
| `claude-haiku-5-5` raw / with | $0.81 / $0.79 |
| `claude-sonnet-5-5` raw / with | $15.25 / $14.43 |
| **Total** | **$38.32** |

All input is counted at the uncached rate. The rates of these four models are not in `data/rates.json`, so their generated reports give no cost; the figures use the standard rates read on November 25, 2026 on `developers.openai.com/api/docs/pricing` and `platform.claude.com/docs/en/about-claude/pricing`. Each run's report gives its token counts.

## What to keep in mind

- **One run per arm.** Two runs of one model without an instruction differ by about 1% of the pass count.
- **Two raw rows are a day older** (`gpt-6-sol` and `claude-opus-5-5`, Phase 0).
- **Single-turn BFCL only.** These are not the leaderboard's overall figures, and the models are within a few points of each other here; a cheaper model matching a dearer one on this benchmark says nothing about other work.
- **The instruction was written from `gpt-6-sol`'s failures** on the development part. That it helps five other models is a result; an instruction written for each was not tried.
- **Cost is list price for these requests.** Latency was not compared.

## What is in this folder

| Path | What |
| --- | --- |
| `luna-plain/`, `luna-instruction/`, `terra-plain/`, `terra-instruction/`, `haiku-plain/`, `haiku-instruction/`, `sonnet-plain/`, `sonnet-instruction/` | `records.jsonl`, `run.json`, the instruction text where one was used, and the generated report with failures by class. |
| `compare-luna/`, `compare-terra/`, `compare-haiku/`, `compare-sonnet/` | Each model raw against with the instruction, case by case. |

The steps between models were computed from the runs' records by case identifier.
