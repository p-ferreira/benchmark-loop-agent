# τ-bench retail report: openai `gpt-6-luna`

- upstream: `sierra-research/tau2-bench` v2.0.0 (`989d3285ae669e49503324bdb9981bf14fccedeb`), benchmark `text-v1`, language `en`, subset `retail_50` (SHA-256 `dc7490f023d1bf9c345edf9c37a8e658298ac3a5be884e012bfb271b3678f2be`)
- agent `gpt-6-luna` (openai); customer `gpt-6-sol` with reasoning `low`; judges: upstream's defaults
- trials 4, seed 300
- instructions: none (upstream's policy only)
- rules in code: handover-once; replies held and asked again: handover-once 11, payment 0, country 0; address calls corrected: 0

## Conversations

- tasks: 4; trials: 4; conversations asked for: 16
- scored: 16; unscored: 0; no record yet: 0

## Pass rate

**87.5%** (14 of 16 scored conversations)

Unscored conversations are left out of this rate; they are listed below.

## Tasks passed in all k trials

pass^k as upstream defines it (the chance that k of a task's trials, drawn together, all pass), averaged over the tasks whose every trial is scored (4 of 4 tasks).

| k | pass^k |
| --- | --- |
| 1 | 87.5% |
| 2 | 75.0% |
| 3 | 62.5% |
| 4 | 50.0% |

Tasks left out for an unscored or missing trial: 0

## Unscored

None.

## Tokens, from the attempts that gave the results

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 236 | 78016 | 0 | 1159003 | 24686 |
| customer `gpt-6-sol` | 107 | 64309 | 0 | 57561 | 5131 |
| judges `gpt-5.4-mini-2026-03-17` | 8 | 21360 | 0 | 0 | 920 |

## Tokens, from unscored attempts (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried)

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 0 | 0 | 0 | 0 | 0 |
| customer | 0 | 0 | 0 | 0 | 0 |
| judges | 0 | 0 | 0 | 0 | 0 |

## Cost

Rates: `results/phase-2/tau-retail-paragraph/rates-2026-11-26.json` (US dollars per 1 million tokens).

- cost per scored conversation: $0.0152
  - agent: $0.0020
  - customer: $0.0120
  - judges: $0.0013

- total spent: $0.2433
  - attempts that gave a result: $0.2433
  - unscored attempts, shown apart (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried): none (no tokens used)

