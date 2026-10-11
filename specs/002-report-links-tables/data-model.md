# Data Model: Scorecard Report with Links, a Data File and Table Grades

Changes to the records in [feature 001's data model](../001-context-scorecard/data-model.md). Nothing here is persisted except the two rendered files.

## Location (new)

|Field|Type|Rule|
|---|---|---|
|path|text|relative to the repo root, forward slashes, never absolute|
|line|whole number or null|null when the location is a whole file|

A Location is found from the documentation files and never changes a grade (FR-004). It can be missing.

## Column (changed)

|Field|Type|Rule|
|---|---|---|
|location|Location or null|new. Chosen by the cases in research R2|

All other fields are unchanged.

## Table (new, US3)

|Field|Type|Rule|
|---|---|---|
|model|text|dbt model name, `jaffle_shop` package only|
|status|`documented` or `undocumented`|undocumented when the table description is empty or whitespace|
|description|text|resolved text from the manifest|
|location|Location or null|the model's entry in its documentation file, else its query file|

## TablePart and TableGrade (new, US3)

Same shape as RubricPart and ColumnGrade. Part keys are `table_grain`, `table_source` and `table_scope`. Outcome is `pass` or `fail`. There is no `n/a` on the starting rubric.

## Result (new)

The one dictionary a run produces. See [contracts/report.md](contracts/report.md) for the exact shape.

|Field|Rule|
|---|---|
|schema_version|1|
|commit, dirty|the label, and whether it ends in `-dirty`|
|rubric|one entry per part: applies to, sentence, rule summary, heuristic|
|pass_rates|by part and by model, column grades only. Table parts in their own list|
|drift|undocumented columns, stale columns, undocumented tables|
|tables|US3. One entry per model with location and grades|
|columns|one entry per built or stale column with status, location and grades|

## Baseline expectations

27 graded columns and 1 stale column, each with a Location. 5 tables, each with a Location, 3 of them undocumented. Column pass rates 41%, 53%, 0% and 0%.
