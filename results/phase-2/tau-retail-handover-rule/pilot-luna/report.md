# τ-bench retail report: openai `gpt-6-luna`

- upstream: `sierra-research/tau2-bench` v2.0.0 (`989d3285ae669e49503324bdb9981bf14fccedeb`), benchmark `text-v1`, language `en`, subset `retail_50` (SHA-256 `dc7490f023d1bf9c345edf9c37a8e658298ac3a5be884e012bfb271b3678f2be`)
- agent `gpt-6-luna` (openai); customer `gpt-6-sol` with reasoning `low`; judges: upstream's defaults
- trials 4, seed 300
- instructions: none (upstream's policy only)
- hand-over rule: on (the transfer tool is sent to the model only after the customer asks for a person); conversations where it was offered: 25; replies asked again for announcing a transfer without it: 1; announcements that reached the customer anyway: 0

## Conversations

- tasks: 12; trials: 4; conversations asked for: 48
- scored: 48; unscored: 0; no record yet: 0

## Pass rate

**79.2%** (38 of 48 scored conversations)

Unscored conversations are left out of this rate; they are listed below.

## Tasks passed in all k trials

pass^k as upstream defines it (the chance that k of a task's trials, drawn together, all pass), averaged over the tasks whose every trial is scored (12 of 12 tasks).

| k | pass^k |
| --- | --- |
| 1 | 79.2% |
| 2 | 72.2% |
| 3 | 68.8% |
| 4 | 66.7% |

Tasks left out for an unscored or missing trial: 0

## Unscored

None.

## Tokens, from the attempts that gave the results

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 585 | 230569 | 0 | 2751480 | 65196 |
| customer `gpt-6-sol` | 292 | 178839 | 0 | 143042 | 16304 |
| judges `gpt-5.4-mini-2026-03-17` | 20 | 73661 | 0 | 0 | 3282 |

## Tokens, from unscored attempts (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried)

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 0 | 0 | 0 | 0 | 0 |
| customer | 0 | 0 | 0 | 0 | 0 |
| judges | 0 | 0 | 0 | 0 | 0 |

## Cost

Rates: `results/phase-2/tau-retail-paragraph/rates-2026-11-26.json` (US dollars per 1 million tokens).

- cost per scored conversation: $0.0146
  - agent: $0.0017
  - customer: $0.0114
  - judges: $0.0015

- total spent: $0.7025
  - attempts that gave a result: $0.7025
  - unscored attempts, shown apart (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried): none (no tokens used)

