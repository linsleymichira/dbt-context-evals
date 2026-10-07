# Research: Context Coverage Scorecard

All decisions dated 2026-10-07. No NEEDS CLARIFICATION items remain.

## R1. How the run refreshes dbt output (FR-012)

- **Decision**: run `dbt build` then `dbt docs generate` as subprocesses with `--project-dir jaffle-shop --profiles-dir jaffle-shop`, and stop with the dbt error and no report if either exits nonzero.
- **Rationale**: the built column list comes from `catalog.json`, which queries the warehouse, and a fresh clone has no `.duckdb` file, so `build` must come first. Measured cost is about 4.3 seconds, inside SC-001's 10 seconds. A subprocess keeps dbt's own error output intact and avoids path coupling.
- **Alternatives considered**: `dbt parse` alone (no catalog, so undocumented columns are invisible). `dbtRunner` in-process (works, but adds dbt internals to the script for no gain). Querying DuckDB's `information_schema` directly (duplicates what `docs generate` already does and couples to one adapter).

## R2. Where resolved descriptions come from (FR-002)

- **Decision**: `manifest.json` → `nodes[<model id>].columns[<name>].description`.
- **Rationale**: verified on 2026-10-07 that `orders.status` holds the resolved `docs.md` text ("Orders can be one of the following statuses: ..."), not `{{ doc("orders_status") }}`.
- **Alternatives considered**: parsing `schema.yml` and `docs.md` directly (re-implements dbt's Jinja resolution and breaks Principle III).

## R3. Drift detection (FR-006)

- **Decision**: compare, per model, lowercased column names in `catalog.json` against lowercased keys in `manifest.json` columns. Catalog only → undocumented. Manifest only → stale. Empty or whitespace description → undocumented.
- **Rationale**: DuckDB returns lowercase names. On the baseline this yields 7 undocumented and 1 stale, matching a manual check.
- **Alternatives considered**: none worth keeping.

## R4. Not-applicable signals (FR-004)

- **Decision**: the scorecard exposes deterministic column facts from the manifest's test nodes (`test_metadata.name` plus `attached_node` and `column_name`), and the user's "Not applicable" sentence chooses which facts exempt which parts.
  - `unique` and `not_null` both present → primary key
  - `relationships` present → foreign key
  - `accepted_values` present → values enumerated by a test
  - catalog data type (date, numeric, text)
- **Rationale**: keeps the N/A decision with the user (Principle I) while making it code-checkable (Principle IV).
- **Alternatives considered**: name heuristics like `*_id` (weaker than the tests that already exist, and wrong for undocumented staging keys that carry no tests).

## R5. Rule shape and traceability (FR-003, FR-010)

- **Decision**: one function per rubric part. Each returns a pass, fail or N/A outcome plus a one-line reason, and carries a plain-language summary string. At runtime the script reads the sentence under each `## N. <part>` heading in `rubric.md` and prints it beside the summary. A remaining `<!-- YOU WRITE` marker exits before any grading and names each unwritten section.
- **Rationale**: the user can audit every rule against their own words in one screen, which is what SC-003's walkthrough needs.
- **Dependency, not an open question**: rule bodies are written during `/speckit-implement`, after the user writes the 5 sentences and approves each rule in chat. Candidate heuristics to propose then, each `[Assumption]` until approved:
  - Business meaning: the description has content words beyond the column name's own tokens and generic filler ("this is", "identifier").
  - Allowed values: an `accepted_values` test exists, or the description enumerates values.
  - Interpretation guidance: the description names a unit, timezone, source system, grain, or caveat.
  - Default filter: the description says which rows to include or exclude.

## R6. PII flag

- **Decision**: strip a standalone `PII.` token before grading and record a `pii` flag on the column, shown in the report.
- **Rationale**: the spec's edge case says the flag must not count toward any part, and the constitution says it must survive rewrites, so the report keeps it visible.

## R7. Report naming and determinism (FR-005, FR-011, SC-004, SC-005)

- **Decision**: `results/<short-sha>.md`, with `-dirty` appended when `git status --porcelain` shows any change outside `results/`, because edits to descriptions, the rubric or `score_context.py` all change the grades. No timestamps, durations, absolute paths or dict-order-dependent output. Rows sort by model, then column.
- **Rationale**: byte-identical reruns are the test for SC-004. A dirty suffix stops a number being credited to a commit that lacks the text it graded.
- **Alternatives considered**: timestamped filenames (break determinism and clutter `results/`).

## R8. Optional model grader (FR-009, User Story 3)

- **Decision**: `--llm` imports `anthropic` lazily, reads `ANTHROPIC_API_KEY` from the environment or a gitignored `.env`, and grades only business meaning and interpretation guidance. Model id defaults to `claude-sonnet-5-5`, overridable with `SCORECARD_MODEL`. The prompt carries the user's rubric sentence and the resolved description. Output is a grade plus a one-sentence reason in a separate report column. A missing key or package exits before any grading.
- **Rationale**: the default run needs no key, and the model never changes a published number.
- **Alternatives considered**: LangSmith-logged runs (belong to MVP 1). Grading all 4 parts by model (the mechanical parts are better answered by code, Principle IV).

## R9. Dependencies and reproducibility

- **Decision**: add a root `pyproject.toml` managed with `uv`: `dbt-core>=1.11,<1.12` and `dbt-duckdb` as runtime deps, `pytest` as a dev dep, `anthropic` as the `llm` extra. Nothing is installed during planning.
- **Rationale**: the vault plan's "one command per step from a fresh clone" criterion fails without a declared manifest. `uv` is already on the machine. dbt 1.12 failed to install on a certificate error during setup, hence the upper pin.
- **Alternatives considered**: `requirements.txt` (no extras or dev groups).
