# Results

Each folder holds one set of benchmark runs: the records, the run parameters and the reports generated from them.

| Folder | What was run | When |
| --- | --- | --- |
| [phase-0](phase-0/README.md) | Every single-turn BFCL case, 3,641 per model, on `gpt-6-sol` and `claude-opus-5-5` | November 24, 2026 |
| [instruction-validation](instruction-validation/README.md) | The 729 validation cases on `gpt-6-sol`, with and without one hand-written instruction | November 25, 2026 |
| [learned-instruction](learned-instruction/README.md) | A learning loop's instruction against the hand-written one on `gpt-6-sol`: development, validation and held-out parts | November 25, 2026 |
| [instruction-ladder](instruction-ladder/README.md) | The hand-written instruction on `claude-opus-5-5`, `gpt-6.1-terra` and `gpt-6-luna`, validation part, with and without | November 25, 2026 |
| [instruction-full](instruction-full/README.md) | Every single-turn BFCL case on `gpt-6-sol` and `claude-opus-5-5` with the hand-written instruction, against Phase 0 | November 25, 2026 |
| [instruction-six-models](instruction-six-models/README.md) | Every single-turn BFCL case, raw and with the hand-written instruction, on `gpt-6.1-terra`, `gpt-6-luna`, `claude-sonnet-5-5` and `claude-haiku-5-5`; one table across six models | November 25, 2026 |
| [phase-1/tau-retail](phase-1/tau-retail/README.md) | τ-bench retail, 50 tasks, no instruction: `claude-sonnet-5-5` and `gpt-6-sol` once, `claude-haiku-5-5` and `gpt-6-luna` four times | November 25, 2026 |
| [phase-2/tau-retail-paragraph](phase-2/tau-retail-paragraph/README.md) | τ-bench retail, 50 tasks, four trials: `claude-haiku-5-5` and `gpt-6-luna` without an instruction and with one reasoning paragraph; no gain shown | November 26, 2026 |
| [phase-2/tau-retail-larger](phase-2/tau-retail-larger/README.md) | τ-bench retail, 50 tasks, four trials, no instruction: `claude-sonnet-5-5` and `gpt-6-sol`; not separated from the cheaper models on tasks passed in all four trials | November 26, 2026 |
| [phase-2/tau-retail-finish-check](phase-2/tau-retail-finish-check/README.md) | τ-bench retail, 50 tasks, four trials: `claude-haiku-5-5` and `gpt-6-luna` with a finish check in code; no gain shown by the rule, `claude-haiku-5-5` one task short | November 26, 2026 |
| [phase-2/tau-retail-handover-rule](phase-2/tau-retail-handover-rule/README.md) | τ-bench retail: a replay of a hand-over rule over the recorded `gpt-6-luna` conversations, and a pilot of it on twelve tasks, four trials; the screen for a full run is cleared at its threshold | November 26, 2026 |
