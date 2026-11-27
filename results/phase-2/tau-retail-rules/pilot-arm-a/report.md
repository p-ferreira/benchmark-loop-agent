# τ-bench retail report: openai `gpt-6-luna`

- upstream: `sierra-research/tau2-bench` v2.0.0 (`989d3285ae669e49503324bdb9981bf14fccedeb`), benchmark `text-v1`, language `en`, subset `retail_50` (SHA-256 `dc7490f023d1bf9c345edf9c37a8e658298ac3a5be884e012bfb271b3678f2be`)
- agent `gpt-6-luna` (openai); customer `gpt-6-sol` with reasoning `low`; judges: upstream's defaults
- trials 4, seed 300
- instructions: none (upstream's policy only)
- rules in code: address, country, payment, products; replies held and asked again: handover-once 0, payment 2, country 7; address calls corrected: 0

## Conversations

- tasks: 12; trials: 4; conversations asked for: 48
- scored: 48; unscored: 0; no record yet: 0

## Pass rate

**75.0%** (36 of 48 scored conversations)

Unscored conversations are left out of this rate; they are listed below.

## Tasks passed in all k trials

pass^k as upstream defines it (the chance that k of a task's trials, drawn together, all pass), averaged over the tasks whose every trial is scored (12 of 12 tasks).

| k | pass^k |
| --- | --- |
| 1 | 75.0% |
| 2 | 59.7% |
| 3 | 52.1% |
| 4 | 50.0% |

Tasks left out for an unscored or missing trial: 0

## Unscored

None.

## Tokens, from the attempts that gave the results

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 603 | 185273 | 0 | 3048344 | 72659 |
| customer `gpt-6-sol` | 274 | 169081 | 0 | 141750 | 15728 |
| judges `gpt-5.4-mini-2026-03-17` | 8 | 24587 | 0 | 0 | 1648 |

## Tokens, from unscored attempts (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried)

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 0 | 0 | 0 | 0 | 0 |
| customer | 0 | 0 | 0 | 0 | 0 |
| judges | 0 | 0 | 0 | 0 | 0 |

## Cost

Rates: `results/phase-2/tau-retail-paragraph/rates-2026-11-26.json` (US dollars per 1 million tokens).

- cost per scored conversation: $0.0132
  - agent: $0.0018
  - customer: $0.0109
  - judges: $0.0005

- total spent: $0.6350
  - attempts that gave a result: $0.6350
  - unscored attempts, shown apart (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried): none (no tokens used)

