# Phase 2: a hand-over rule for `gpt-6-luna` on retail

Work of `p-ferreira/agent-system-lab#268`. With `--handover-rule` the transfer tool is sent to the model only after the customer asks for a person (see the README of the repository).

## Replay, no model call

`replay.py` asks the rule's own test where it would have stepped in over the 800 recorded conversations of `gpt-6-luna` (`replay.txt`). Outside tasks 38, 52 and 105, which no model has passed: 44 of 95 failed conversations hold a transfer made before the customer asked for a person, and so do 65 of 657 passed ones.

## Pilot: twelve design tasks, four trials (`pilot-luna/`)

Run at commit `b88aa88` on November 26, 2026, under the protocol `docs/experiments/2026-11-tau-retail-handover-rule-pilot.md` of the Lab repository. The tasks were chosen because the rule touches them: this is a screen for a full run, not a result about the benchmark. Baselines are the two existing runs with nothing changed.

| Task | With the rule | `phase-2/tau-retail-paragraph/control-luna` | `phase-1/tau-retail/luna` |
| ---: | ---: | ---: | ---: |
| 18 | 4 of 4 | 2 | 4 |
| 19 | 2 | 3 | 4 |
| 21 | 3 | 2 | 3 |
| 25 | 4 | 4 | 4 |
| 26 | 4 | 4 | 3 |
| 32 | 4 | 0 | 0 |
| 36 | 1 | 3 | 4 |
| 50 | 4 | 4 | 4 |
| 53 | 4 | 4 | 4 |
| 59 | 4 | 2 | 2 |
| 68 | 0 | 4 | 1 |
| 97 | 4 | 4 | 4 |
| Conversations passed, of 48 | 38 | 36 | 37 |
| Tasks passed in all four trials, of 12 | 8 | 6 | 7 |

**The screen fixed beforehand is cleared, at its threshold:** at least 8 tasks passed in all four trials (8), at least 36 conversations passed (38), and task 32 passed with its changes made after the point where the recorded runs transferred (4 of 4; it had failed in all 16 recorded conversations). No conversation was unscored, and no announcement of a transfer reached the customer without the tool; one reply was asked again. The tool was offered in 25 of the 48 conversations, after the customer asked for a person.

Tasks 68 and 36 did worse than in either baseline. In task 68 the customer asks for someone else after the agent says it cannot tell which order is the most recent, the tool is then offered, and the agent transfers without telling the order total. Total spent: $0.70.

## The full design set: 50 tasks, four trials (`design-luna/`)

Run at commit `b88aa88` on November 26, 2026, under `docs/experiments/2026-11-tau-retail-handover-rule-design-set.md` of the Lab repository, all 200 conversations fresh.

| `gpt-6-luna` | Passed | Pass rate | Tasks passed in all 4 trials | Whole cost per conversation |
| --- | ---: | ---: | ---: | ---: |
| with the rule | 161 of 200 | 80.5% | 29 of 50 | $0.0139 |
| no change, `phase-2/tau-retail-paragraph/control-luna` | 165 of 200 | 82.5% | 32 of 50 | $0.0133 |
| no change, `phase-1/tau-retail/luna` | 165 of 200 | 82.5% | 35 of 50 | $0.0135 |

**Result: no gain shown.** Against the control, 5 tasks won and 8 lost on "passed in all four trials" (−3), where the rule fixed beforehand asked for at least +5, and the pass rate is lower. Against the earlier run with nothing changed: 4 won and 10 lost (−6). The rule is not adopted and the 64 unseen tasks were not run.

The rule worked as built: the tool was offered in 38 conversations, after the customer asked for a person; no conversation was unscored and no announcement of a transfer reached the customer without the tool. Task 32, passed four times of four in the pilot, passed twice of four here. The 39 failed conversations are spread over 21 tasks, 10 of them with a single failure. Total spent: $2.79.
