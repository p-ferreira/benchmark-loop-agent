# A learned instruction against the hand-written one: `gpt-6-sol`

Run on November 25, 2026 at runner commit `3f7551b`, `gpt-6-sol` at provider default settings, 8 requests in flight. The protocol, with the candidates and the rules for a gain, was committed before the runs: `p-ferreira/agent-system-lab`, `docs/experiments/2026-11-bfcl-learned-instruction.md`.

## Result

**The learning loop made the model worse, and the hand-written instruction held on the held-out part.**

Validation part, 729 cases, the three runs at the same time:

| Instruction | Passes | Only it passed | Only the hand-written file passed |
| --- | --- | ---: | ---: |
| Hand-written (604 bytes) | 586 (80.4%) | | |
| Candidate A: hand-written plus 7 learned rules (1,996 bytes) | 505 (69.3%) | 32 | 113 |
| Candidate B: hand-written plus the first 3 learned rules (1,220 bytes) | 540 (74.1%) | 28 | 74 |

Neither candidate beat the hand-written file, so by the protocol none went to the held-out part.

Held-out part, 1,092 cases, run once, two arms at the same time:

| Instruction | Passes |
| --- | --- |
| None | 874 (80.0%) |
| Hand-written | 902 (82.6%) |

Case by case: 63 cases passed only with the hand-written instruction and 35 only without it. An exact two-sided sign test gives p = 0.006. By the rule fixed beforehand, the hand-written gain holds.

## Why the learned rules hurt

Failures by class on validation:

| Class | Hand-written | Candidate A | Candidate B |
| --- | ---: | ---: | ---: |
| `called-when-none-applied` | 30 | 5 | 10 |
| `no-call` | 28 | 158 | 102 |
| `too-few-calls` | 5 | 3 | 10 |
| `too-many-calls` | 6 | 3 | 7 |
| `wrong-call` | 74 | 55 | 60 |
| **All failures** | **143** | **224** | **189** |

The learned rules are mostly reasons not to call a function. They removed most calls made when none applied, and stopped the model from calling in many cases where a call was expected.

## Learning

The development part (1,820 cases) was run with the hand-written instruction: 1,536 passes, 284 failures. The `learn` command sent those failures to `claude-opus-5-5` in 15 batches. It returned 44 rules: 7 were kept, 29 were refused because the file had reached its 2,000-byte limit, and 8 because they contained an expected value of a case of their batch. The writer was never sent an expected answer. [`learning/learned.txt`](learning/learned.txt) is the file; [`learning/learned.txt.log.jsonl`](learning/learned.txt.log.jsonl) is the log.

## Tokens and cost at list rates

| Step | Input tokens | Output tokens | Cost |
| --- | ---: | ---: | ---: |
| Development run, hand-written | 1,023,815 | 126,566 | $3.31 |
| Learning, `claude-opus-5-5` | 419,743 | 16,591 | $2.01 |
| Validation, hand-written | | | $1.35 |
| Validation, candidate A | | | $1.85 |
| Validation, candidate B | | | $1.61 |
| Held-out, none | 440,554 | 85,420 | $1.74 |
| Held-out, hand-written | 581,422 | 81,229 | $1.98 |
| **Total** | | | **$13.85** |

All input is counted at the uncached rate in `data/rates.json`. Each run's own report gives its tokens.

## What to keep in mind

- **One run per arm, one model, one day.**
- **One learning pass, one writer, one size limit.** This shows that this loop, as configured, did not help. It does not show that no learned instruction can.
- **The held-out part has now been used** for the hand-written instruction against none. A later experiment that reads these held-out records is no longer testing on unseen cases.
- **Small categories.** Several have 5 to 30 held-out cases.

## What is in this folder

| Path | What |
| --- | --- |
| `development-starting/` | The development run the loop learned from. |
| `learning/` | The starting file, the learned file, the two candidates and the learning log. |
| `validation-starting/`, `validation-candidate-a/`, `validation-candidate-b/` | The three validation runs. |
| `heldout-none/`, `heldout-starting/` | The two held-out runs. |
| `compare-*/` | The paired comparisons, with the movement between failure classes. |

Every run folder holds `records.jsonl`, `run.json`, the instruction text it used and its generated report.
