# τ-bench retail report: openai `gpt-6-sol`

- upstream: `sierra-research/tau2-bench` v2.0.0 (`989d3285ae669e49503324bdb9981bf14fccedeb`), benchmark `text-v1`, language `en`, subset `retail_50` (SHA-256 `dc7490f023d1bf9c345edf9c37a8e658298ac3a5be884e012bfb271b3678f2be`)
- agent `gpt-6-sol` (openai); customer `gpt-6-sol` with reasoning `low`; judges: upstream's defaults
- trials 1, seed 300
- instructions: none (upstream's policy only)

## Conversations

- tasks: 50; trials: 1; conversations asked for: 50
- scored: 50; unscored: 0; no record yet: 0

## Pass rate

**80.0%** (40 of 50 scored conversations)

Unscored conversations are left out of this rate; they are listed below.

## Unscored

None.

## Tokens, from the attempts that gave the results

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 601 | 158732 | 0 | 2866941 | 43434 |
| customer `gpt-6-sol` | 303 | 204963 | 0 | 116876 | 14206 |
| judges `gpt-5.4-mini-2026-03-17` | 16 | 54714 | 0 | 0 | 2352 |

## Tokens, from unscored attempts (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried)

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 0 | 0 | 0 | 0 | 0 |
| customer | 0 | 0 | 0 | 0 | 0 |
| judges | 0 | 0 | 0 | 0 | 0 |

## Cost

Rates: `results/phase-1/tau-retail/rates-2026-11-25.json` (US dollars per 1 million tokens).

- cost per scored conversation: $0.0390
  - agent: $0.0265
  - customer: $0.0115
  - judges: $0.0010

- total spent: $1.9522
  - attempts that gave a result: $1.9522
  - unscored attempts, shown apart (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried): none (no tokens used)

