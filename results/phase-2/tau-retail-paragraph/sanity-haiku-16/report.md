# τ-bench retail report: anthropic `claude-haiku-5-5`

- upstream: `sierra-research/tau2-bench` v2.0.0 (`989d3285ae669e49503324bdb9981bf14fccedeb`), benchmark `text-v1`, language `en`, subset `retail_50` (SHA-256 `dc7490f023d1bf9c345edf9c37a8e658298ac3a5be884e012bfb271b3678f2be`)
- agent `claude-haiku-5-5` (anthropic); customer `gpt-6-sol` with reasoning `low`; judges: upstream's defaults
- trials 1, seed 300
- instructions: SHA-256 `57cac4d27d83077aaab798dbcd896945e115fd9c63e52a4ea7e44a1153473a13`, 564 bytes

## Conversations

- tasks: 1; trials: 1; conversations asked for: 1
- scored: 1; unscored: 0; no record yet: 0

## Pass rate

**100.0%** (1 of 1 scored conversations)

Unscored conversations are left out of this rate; they are listed below.

## Unscored

None.

## Tokens, from the attempts that gave the results

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 9 | 24 | 12320 | 70021 | 2577 |
| customer `gpt-6-sol` | 4 | 2848 | 0 | 1160 | 180 |
| judges `gpt-5.4-mini-2026-03-17` | 1 | 4047 | 0 | 0 | 120 |

## Tokens, from unscored attempts (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried)

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 0 | 0 | 0 | 0 | 0 |
| customer | 0 | 0 | 0 | 0 | 0 |
| judges | 0 | 0 | 0 | 0 | 0 |

## Cost

Rates: `results/phase-2/tau-retail-paragraph/rates-2026-11-26.json` (US dollars per 1 million tokens).

- cost per scored conversation: $0.0148
  - agent: $0.0035
  - customer: $0.0077
  - judges: $0.0036

- total spent: $0.0148
  - attempts that gave a result: $0.0148
  - unscored attempts, shown apart (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried): none (no tokens used)

