# τ-bench retail report: anthropic `claude-sonnet-5-5`

- upstream: `sierra-research/tau2-bench` v2.0.0 (`989d3285ae669e49503324bdb9981bf14fccedeb`), benchmark `text-v1`, language `en`, subset `retail_50` (SHA-256 `dc7490f023d1bf9c345edf9c37a8e658298ac3a5be884e012bfb271b3678f2be`)
- agent `claude-sonnet-5-5` (anthropic); customer `gpt-6-sol` with reasoning `low`; judges: upstream's defaults
- trials 1, seed 300
- instructions: none (upstream's policy only)

## Conversations

- tasks: 50; trials: 1; conversations asked for: 50
- scored: 50; unscored: 0; no record yet: 0

## Pass rate

**90.0%** (45 of 50 scored conversations)

Unscored conversations are left out of this rate; they are listed below.

## Unscored

None.

## Tokens, from the attempts that gave the results

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 508 | 1490 | 275673 | 4373895 | 79782 |
| customer `gpt-6-sol` | 287 | 177697 | 0 | 162490 | 13751 |
| judges `gpt-5.4-mini-2026-03-17` | 16 | 63335 | 0 | 0 | 2203 |

## Tokens, from unscored attempts (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried)

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 0 | 0 | 0 | 0 | 0 |
| customer | 0 | 0 | 0 | 0 | 0 |
| judges | 0 | 0 | 0 | 0 | 0 |

## Cost

Rates: `results/phase-1/tau-retail/rates-2026-11-25.json` (US dollars per 1 million tokens).

- cost per scored conversation: $0.0502
  - agent: $0.0385
  - customer: $0.0105
  - judges: $0.0011

- total spent: $2.5102
  - attempts that gave a result: $2.5102
  - unscored attempts, shown apart (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried): none (no tokens used)

