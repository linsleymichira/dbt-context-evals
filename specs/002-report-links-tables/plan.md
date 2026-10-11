# Implementation Plan: Scorecard Report with Links, a Data File and Table Grades

**Branch**: `002-report-links-tables` (spec directory only, work stays on `master`) | **Date**: 2026-10-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-report-links-tables/spec.md`

## Summary

The scorecard learns where each description is written, holds one result per run, and writes that result twice: as the Markdown report and as a JSON data file. Every column row and table row links to its location. The scorecard's own sentences are brought to the user's eight writing rules. Table descriptions are graded on three table parts, in their own rows, once the constitution allows it. See [research.md](research.md) for the decisions.

**Build order**: User Stories 1, 2 and 4 are built now. User Story 3 is designed here and gated on a constitution amendment (see Constitution Check).

## Technical Context

**Language/Version**: Python 3.12 (the existing root `.venv`)

**Primary Dependencies**: `dbt-core` 1.11 and `dbt-duckdb`, plus the standard library. Line numbers come from PyYAML, which `dbt-core` already installs as a hard dependency (research R1). No new entry in `pyproject.toml`.

**Storage**: Files only. Reads `manifest.json`, `catalog.json`, `rubric.md`, and now the project's documentation files for locations only. Writes `results/<label>.md` and `results/<label>.json`, or the `-llm` pair with `--llm`.

**Testing**: `pytest`, test first. Location tests write small documentation files into `tmp_path`. Existing tests stay green without edits, apart from the tests that assert the reworded notice and warning.

**Target Platform**: macOS laptop, local only.

**Project Type**: Single-file CLI script plus tests.

**Performance Goals**: Under 10 seconds per default run (SC-008). Measured 2026-10-10: 6.6 seconds before this feature. Reading 3 small files adds no measurable time.

**Constraints**: Byte-identical Markdown and JSON for a commit on a default run. No timestamps, no absolute paths, sorted keys and rows. Column pass rates do not move (SC-005).

**Scale/Scope**: 5 models, 27 built columns, 1 stale column, 2 documentation files, 1 shared documentation block.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.* Checked against constitution v1.2.0 as it stands in the working tree on 2026-10-10 (amended that day, not yet committed).

|Principle|Check|Status|
|---|---|---|
|I. The Rubric Is the Standard|User Stories 1, 2 and 4 add no criterion and change no rule. **User Story 3 adds three table parts, and Principle I defines the rubric as the standard for a column description only.** The amendment notes say scoring another kind of context needs its own amendment. The user approved the three table sentences on 2026-10-10, which meets "authored by the user" once the principle covers tables.|Pass for US1, US2, US4. **Blocked for US3 until amended**|
|II. Baseline and Diffable History|Both files carry the commit label. `results/8eabd21.md` is never rewritten (FR-017).|Pass|
|III. Score What dbt Resolves|Grades still read `manifest.json`. Documentation files are read only to find a line number, and a missing location never changes a grade (FR-004).|Pass|
|IV. Code Scores, the Model Judges|Locations and the data file are pure code. Table rules are code, with the pattern rules marked heuristic.|Pass|
|V. Smallest Harness That Works|No service, database or framework is added. PyYAML arrives with dbt (R1).|Pass|
|VI. Pre-Register the Eval|Applies to the eval harness, which this feature does not touch.|Not applicable|

Post-design re-check: unchanged. US3 stays gated. Tasks for US3 start with a USER GATE for the amendment.

## Project Structure

### Documentation (this feature)

```text
specs/002-report-links-tables/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── report.md        # file names, JSON shape, Markdown layout changes
└── tasks.md             # /speckit-tasks, not created here
```

### Source Code (repository root)

```text
dbt-context-evals/
├── score_context.py     # adds: locations, the result dict, JSON writing, table grades
├── tests/
│   ├── test_locations.py   # new, US1
│   ├── test_result.py      # new, US2
│   ├── test_wording.py     # new, US4
│   └── test_tables.py      # new, US3 (gated)
├── results/             # <label>.md and <label>.json per scored commit
└── rubric.md            # gains 3 table sections with US3
```

**Structure Decision**: everything stays in `score_context.py`, as in feature 001. The file grows from about 750 lines to about 1,000. A split into modules would be a refactor nobody asked for, and it is noted here as the next thing to consider if a third feature lands in the same file.

## Complexity Tracking

No violation to justify. The one gate is recorded above: US3 waits for an amendment to Principle I.
