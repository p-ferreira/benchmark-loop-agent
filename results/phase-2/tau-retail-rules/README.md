# Phase 2: retail rules in code for `gpt-6-luna` (`--rules`)

Work of `p-ferreira/agent-system-lab#268`. The rules are in `benchmark_loop_agent/tau/rules.py`, off by default: code searches a product's variants and builds the offer (`offers`), holds an item change that would lock an order before its address change (`order-lock`) or whose payment method the customer never chose (`payment`), puts address fields in the database's forms and looks the state up from the ZIP code (`address`), and refuses one early transfer (`handover-once`). The protocols and readings are in the Lab repository: `docs/experiments/2026-11-tau-retail-rules-pilot.md`, `2026-11-tau-retail-offers-in-code.md` and `2026-11-tau-retail-rules-unseen-tasks.md`.

| Run of `gpt-6-luna`, four trials | Conversations passed | Tasks passed in all four trials | Agent cost per conversation |
| --- | --- | --- | --- |
| 50 design tasks, nothing changed (`phase-1/tau-retail/luna`, `phase-2/tau-retail-paragraph/control-luna`) | 165 of 200 (82.5%), twice | 35 and 32 | $0.0016 |
| 50 design tasks, first full run (`full-luna`) | 167 of 200 (83.5%) | 37 | $0.0018 |
| 50 design tasks, second round (`full-luna-2`) | 178 of 200 (89.0%) | 38 | $0.0019 |
| 64 unseen tasks, nothing changed (`unseen-plain`) | 183 of 256 (71.5%) | 33 | $0.0015 |
| 64 unseen tasks, with the rules (`unseen-rules`) | 188 of 256 (73.4%) | 34 | $0.0018 |

The rules were fitted to the 50 design tasks over two rounds of reading their failed conversations. On those tasks the pass rate rose by 6.5 points; on the 64 tasks they were not fitted to, the difference is inside what one run an arm can tell from noise. Rates: `../tau-retail-paragraph/rates-2026-11-26.json`.

To reproduce the second round: `python -m benchmark_loop_agent.tau --output-dir DIR --provider openai --openai-model gpt-6-luna --trials 4 --rules offers,order-lock,payment,address,handover-once` at commit `e6fb83f`; add `--unseen` for the 64 other tasks (commit `1268117` or later).

## What else is here

- `pilot-arm-a`, `pilot-arm-b`, `replay.txt`: the pilot of five smaller rules (commit `eab77c6`), of which only the refused early transfer was kept. `replay.txt` was printed by a script of that commit which the later design replaced.
- `decision_points.py`, `decision-points.txt`, `decision-point-rounds/`: one reply of the model re-asked at the moment an offer is made, plain and under the rules, on moments cut from recorded conversations. Used while building the search; about 13 cents for five rounds.
