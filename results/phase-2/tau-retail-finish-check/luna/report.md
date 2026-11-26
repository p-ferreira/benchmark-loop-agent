# τ-bench retail report: openai `gpt-6-luna`

- upstream: `sierra-research/tau2-bench` v2.0.0 (`989d3285ae669e49503324bdb9981bf14fccedeb`), benchmark `text-v1`, language `en`, subset `retail_50` (SHA-256 `dc7490f023d1bf9c345edf9c37a8e658298ac3a5be884e012bfb271b3678f2be`)
- agent `gpt-6-luna` (openai); customer `gpt-6-sol` with reasoning `low`; judges: upstream's defaults
- trials 4, seed 300
- instructions: none (upstream's policy only)
- finish check: on (a reply is held once and asked again before a hand-over to a human, and before the reply after a change); replies held: 264

## Conversations

- tasks: 50; trials: 4; conversations asked for: 200
- scored: 200; unscored: 0; no record yet: 0

## Pass rate

**82.0%** (164 of 200 scored conversations)

Unscored conversations are left out of this rate; they are listed below.

## Tasks passed in all k trials

pass^k as upstream defines it (the chance that k of a task's trials, drawn together, all pass), averaged over the tasks whose every trial is scored (50 of 50 tasks).

| k | pass^k |
| --- | --- |
| 1 | 82.0% |
| 2 | 75.7% |
| 3 | 72.0% |
| 4 | 70.0% |

Tasks left out for an unscored or missing trial: 0

## Unscored

None.

## Tokens, from the attempts that gave the results

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 2648 | 723490 | 0 | 13537833 | 314182 |
| customer `gpt-6-sol` | 1129 | 736894 | 0 | 489473 | 55749 |
| judges `gpt-5.4-mini-2026-03-17` | 64 | 223128 | 0 | 0 | 9333 |

## Tokens, from unscored attempts (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried)

| Component | Calls | Uncached input | Cache write | Cache read | Output |
| --- | --- | --- | --- | --- | --- |
| agent | 0 | 0 | 0 | 0 | 0 |
| customer | 0 | 0 | 0 | 0 | 0 |
| judges | 0 | 0 | 0 | 0 | 0 |

## Cost

Rates: `results/phase-2/tau-retail-paragraph/rates-2026-11-26.json` (US dollars per 1 million tokens).

- cost per scored conversation: $0.0135
  - agent: $0.0018
  - customer: $0.0106
  - judges: $0.0010

- total spent: $2.7033
  - attempts that gave a result: $2.7033
  - unscored attempts, shown apart (0 still unscored, 0 earlier unscored attempt(s) of conversations since scored or retried): none (no tokens used)

