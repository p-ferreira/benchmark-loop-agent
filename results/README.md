# Results

Each folder holds one set of benchmark runs: the records, the run parameters and the reports generated from them.

| Folder | What was run | When |
| --- | --- | --- |
| [phase-0](phase-0/README.md) | Every single-turn BFCL case, 3,641 per model, on `gpt-6-sol` and `claude-opus-5-5` | November 24, 2026 |
| [instruction-validation](instruction-validation/README.md) | The 729 validation cases on `gpt-6-sol`, with and without one hand-written instruction | November 25, 2026 |
| [learned-instruction](learned-instruction/README.md) | A learning loop's instruction against the hand-written one on `gpt-6-sol`: development, validation and held-out parts | November 25, 2026 |
| [instruction-ladder](instruction-ladder/README.md) | The hand-written instruction on `claude-opus-5-5`, `gpt-6.1-terra` and `gpt-6-luna`, validation part, with and without | November 25, 2026 |
| [instruction-six-models](instruction-six-models/README.md) | Every single-turn BFCL case, raw and with the hand-written instruction, on `gpt-6.1-terra`, `gpt-6-luna`, `claude-sonnet-5-5` and `claude-haiku-5-5`; one table across six models | November 25, 2026 |
