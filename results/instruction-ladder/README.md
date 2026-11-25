# The hand-written instruction on four models: validation part

The 729 validation cases of single-turn BFCL (`data/split.json`), each model without and with the same instruction, the hand-written text of [`instruction-validation`](../instruction-validation/README.md) (SHA-256 `0f7c3d7a9ef588991ee546081c3d23d3e6b972a4fb86e6fab57858c3ab4ffec9`). Run on November 25, 2026 at runner commit `3f7551b`, provider default settings, 8 requests in flight. The protocol, with the rules for each statement below, was committed before the runs: `p-ferreira/agent-system-lab`, `docs/experiments/2026-11-bfcl-instruction-two-models-and-ladder.md`.

The `gpt-6-sol` rows are the two runs of `instruction-validation`, made the same day.

## Result

| Model | List price per million tokens, input / output | Passes without | Passes with | Won / lost with the instruction | Cost of the run with it |
| --- | --- | --- | --- | --- | ---: |
| `gpt-6-luna` | $0.10 / $0.50 | 545 (74.8%) | 578 (79.3%) | 57 / 24 | $0.07 |
| `gpt-6.1-terra` | $1.00 / $5.00 | 558 (76.5%) | 589 (80.8%) | 48 / 17 | $0.68 |
| `gpt-6-sol` | $2.00 / $10.00 | 547 (75.0%) | 586 (80.4%) | 57 / 18 | $1.36 |
| `claude-opus-5-5` | $4 / $20 | 582 (79.8%) | 607 (83.3%) | 34 / 9 | $5.95 |

"Won / lost" counts the cases that passed only with the instruction and only without it. By the rule fixed beforehand (more won than lost, exact two-sided sign test below 0.05) **the instruction helps every one of the four models**: p = 0.0003, 0.0002, 0.000007 and 0.0002.

## A cheaper model with the instruction against the next model without it

| Step | Cheaper model, with | Next model, without | Only the cheaper passed / only the next passed | Verdict by the rule |
| --- | --- | --- | --- | --- |
| `gpt-6-luna` against `gpt-6.1-terra` | 578, $0.07 | 558, $0.61 | 56 / 36, p = 0.047 | **beats** |
| `gpt-6.1-terra` against `gpt-6-sol` | 589, $0.68 | 547, $1.17 | 67 / 25, p = 0.00001 | **beats** |
| `gpt-6-sol` against `claude-opus-5-5` | 586, $1.36 | 582, $6.41 | 42 / 38, p = 0.74 | **matches** |

Not one of the comparisons fixed beforehand, so only an observation: `gpt-6-luna` with the instruction passed 578 cases for 7 cents, and `claude-opus-5-5` without it 582 for 6.41 dollars.

## Failures by class

| Run | All | `called-when-none-applied` | `no-call` | `too-few-calls` | `too-many-calls` | `wrong-call` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gpt-6-luna` | 184 | 47 | 38 | 12 | 0 | 87 |
| `gpt-6-luna` + instruction | 151 | 39 | 25 | 5 | 5 | 77 |
| `gpt-6.1-terra` | 171 | 40 | 29 | 13 | 10 | 79 |
| `gpt-6.1-terra` + instruction | 140 | 22 | 29 | 6 | 8 | 75 |
| `claude-opus-5-5` | 147 | 52 | 6 | 6 | 10 | 73 |
| `claude-opus-5-5` + instruction | 122 | 36 | 8 | 3 | 8 | 67 |

## Tokens and cost at list rates

| Run | Input tokens | Output tokens | Cost |
| --- | ---: | ---: | ---: |
| `claude-opus-5-5` | 798,250 | 160,648 | $6.41 |
| `claude-opus-5-5` + instruction | 909,787 | 115,767 | $5.95 |
| `gpt-6.1-terra` | 308,344 | 61,181 | $0.61 |
| `gpt-6.1-terra` + instruction | 402,385 | 55,698 | $0.68 |
| `gpt-6-luna` | 308,344 | 69,106 | $0.07 |
| `gpt-6-luna` + instruction | 402,385 | 55,336 | $0.07 |
| **Total of the six runs** | | | **$13.79** |

All input is counted at the uncached rate. The rates of `gpt-6.1-terra` and `gpt-6-luna` are not in `data/rates.json`, so their generated reports give no cost; the figures here use the standard rates read on `developers.openai.com/api/docs/pricing` on November 25, 2026.

## What to keep in mind

- **One run per arm, one day.** Two runs of `gpt-6-sol` without an instruction differed in 30 of these 729 cases.
- **Validation only.** The held-out part was not run for these models. The instruction was written for `gpt-6-sol` from its development failures; its author had seen aggregate pass counts of every part.
- **`gpt-6-luna` against `gpt-6.1-terra`** passes the rule narrowly (p = 0.047).
- **Accuracy on this benchmark only.** The four models score within a few points of each other here without an instruction; this says nothing about other tasks.
- **Cost** is list price for these requests; latency was not compared.

## What is in this folder

| Path | What |
| --- | --- |
| `opus-plain/`, `opus-instruction/`, `terra-plain/`, `terra-instruction/`, `luna-plain/`, `luna-instruction/` | `records.jsonl`, `run.json`, the instruction text where one was used, and the generated report. |
| `compare-opus/`, `compare-terra/`, `compare-luna/` | Each model without against with the instruction. |
| `compare-terra-plain-luna-instruction/`, `compare-sol-plain-terra-instruction/` | Two steps of the ladder. The third crosses providers, which the comparison command refuses; its counts were computed from the two runs' records by case identifier. |
