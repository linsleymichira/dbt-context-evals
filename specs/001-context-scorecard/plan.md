# Implementation Plan: Context Coverage Scorecard

**Branch**: `001-context-scorecard` (spec directory only, work stays on `master`) | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-context-scorecard/spec.md`

## Summary

One command refreshes the dbt project, reads the resolved column descriptions and the built column list, grades every built column on the 4 rubric parts with code-based rules derived from the user's `rubric.md` sentences, and writes a deterministic Markdown report to `results/` named for the commit it scored. An optional `--llm` flag adds a model grade beside the rule grade for the two judgment parts. See [research.md](research.md) for the decisions behind each step.

## Technical Context

**Language/Version**: Python 3.12 (the existing root `.venv`)

**Primary Dependencies**: `dbt-core` 1.11 and `dbt-duckdb` (already installed), Python standard library for everything else. `anthropic` as an optional extra, used only by `--llm`.

**Storage**: Files only. Reads `jaffle-shop/target/manifest.json`, `jaffle-shop/target/catalog.json` and `rubric.md`. Writes `results/<short-sha>.md`.

**Testing**: `pytest` against small fixture manifest and catalog dictionaries. TDD per `~/.claude/reference/rules/testing.md`.

**Target Platform**: macOS laptop, local only. No cloud account.

**Project Type**: Single-file CLI script plus tests.

**Performance Goals**: Under 10 seconds per run with `--llm` off (SC-001). Measured refresh cost on 2026-10-07: `dbt build` 2.5 seconds plus `dbt docs generate` 1.9 seconds, about 4.3 seconds before grading.

**Constraints**: Byte-identical output for the same commit (SC-004), so the report carries no timestamps or run durations and every table is sorted. No employer data (SC-006).

**Scale/Scope**: 5 models, 27 built columns. Of those, 15 have description text, 12 are undocumented (`customers.customer_lifetime_value` plus all 11 staging columns, 5 of which have tests but blank descriptions), and 1 documented column is stale (`customers.total_order_amount`). Corrected 2026-10-07 from a first count of 20 and 7, which treated blank YAML entries as documented. The vault plan's "21 columns" counts YAML entries, stale and blank ones included.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.* Checked against constitution v1.1.0.

|Principle|Check|Status|
|---|---|---|
|I. The Rubric Is the Standard|Each rule reads its part's sentence from `rubric.md` at runtime and prints it beside the rule summary (FR-003). The scorecard exits on any remaining `<!-- YOU WRITE` marker (FR-010). Rule bodies are written only after the user writes the sentences and approves each rule.|Pass|
|II. Baseline and Diffable History|Report filename and header carry the short commit hash. Any uncommitted change outside `results/` (descriptions, rubric, or the scorecard code) adds a `-dirty` suffix and a warning line, so no number is ever attributed to a commit that does not contain it.|Pass|
|III. Score What dbt Resolves|Descriptions come from `manifest.json`. Verified 2026-10-07: `orders.status` holds the resolved `docs.md` text, not the `{{ doc() }}` call. A failing `dbt build` stops the run with no report, which is this principle working as intended.|Pass|
|IV. Code Scores, the Model Judges|Test-derived signals (keys, `accepted_values`) are pure code. Judgment parts get code heuristics labeled as heuristic (clarification 1), and the model grader is opt-in and never overrides.|Pass|
|V. Smallest Harness That Works|One script, standard library plus dbt, no database or service. `anthropic` is an optional extra.|Pass|

Post-design re-check: still passes. The design adds one root `pyproject.toml`, which is needed for "one command per step from a fresh clone", not a new framework.

## Project Structure

### Documentation (this feature)

```text
specs/001-context-scorecard/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Phase 1 entities
├── quickstart.md        # Phase 1 validation guide
├── contracts/
│   └── cli.md           # Command, flags, exit codes, report layout
└── tasks.md             # Phase 2 output (/speckit-tasks, not created here)
```

### Source Code (repository root)

```text
dbt-context-evals/
├── score_context.py     # refresh, load, grade, render, write
├── tests/
│   ├── conftest.py      # fixture manifest, catalog and rubric builders
│   └── test_score_context.py
├── results/             # committed reports, one per scored commit
├── pyproject.toml       # deps: dbt-core, dbt-duckdb. dev: pytest. extra "llm": anthropic
├── .env.example         # ANTHROPIC_API_KEY= (name only)
├── rubric.md            # user-authored, read at runtime
└── jaffle-shop/         # the scored dbt project
```

**Structure Decision**: one root script, matching the vault plan's § 5 build spec (`score_context.py`). Rules live in the same file as one function per rubric part. A separate rules module would be an abstraction with one caller.

## Complexity Tracking

No constitution violations to justify.
