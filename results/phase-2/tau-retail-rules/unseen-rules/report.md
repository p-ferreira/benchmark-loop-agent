# τ-bench retail report: openai `gpt-6-luna`

- upstream: `sierra-research/tau2-bench` v2.0.0 (`989d3285ae669e49503324bdb9981bf14fccedeb`), benchmark `text-v1`, language `en`, subset `retail_50` (SHA-256 `dc7490f023d1bf9c345edf9c37a8e658298ac3a5be884e012bfb271b3678f2be`)
- agent `gpt-6-luna` (openai); customer `gpt-6-sol` with reasoning `low`; judges: upstream's defaults
- trials 4, seed 300
- instructions: none (upstream's policy only)
- task set: the retail tasks of upstream's base split outside the pinned subset
- rules in code: address, handover-once, offers, order-lock, payment; replies held and asked again: handover-once 37, unsearched 9, same-item 0, order-lock 28, payment 2, state 9; searches run in code: 259; address calls corrected: 0

## Conversations

- tasks: 64; trials: 4; conversations asked for: 256
- scored: 256; unscored: 0; no record yet: 0

## Pass rate

**73.4%** (188 of 256 scored conversations)

Unscored conversations are left out of this rate; they are listed below.

## Tasks passed in all k trials

pass^k as upstream defines it (the chance that k of a task's trials, drawn together, all pass), averaged over the tasks whose every trial is scored (64 of 64 tasks).

| k | pass^k |
| --- | --- |
| 1 | 73.4% |
| 2 | 63.0% |
| 3 | 57.0% |
| 4 | 53.1% |

Tasks left out for an unscored or missing trial: 0

## Unscored

None.

## Tokens, from the attempts that gave the results

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 3235 | 993250 | 0 | 17489567 | 370460 |
| customer `gpt-6-sol` | 1398 | 943912 | 0 | 535606 | 84540 |
| judges `gpt-5.4-mini-2026-03-17` | 96 | 344910 | 0 | 0 | 12819 |

## Tokens, from unscored attempts (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried)

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 0 | 0 | 0 | 0 | 0 |
| customer | 0 | 0 | 0 | 0 | 0 |
| judges | 0 | 0 | 0 | 0 | 0 |

## Cost

Rates: `results/phase-2/tau-retail-paragraph/rates-2026-11-26.json` (US dollars per 1 million tokens).

- cost per scored conversation: $0.0141
  - agent: $0.0018
  - customer: $0.0111
  - judges: $0.0012

- total spent: $3.6162
  - attempts that gave a result: $3.6162
  - unscored attempts, shown apart (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried): none (no tokens used)

