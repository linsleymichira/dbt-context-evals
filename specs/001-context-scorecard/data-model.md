# Data Model: Context Coverage Scorecard

In-memory records only. Nothing is persisted except the rendered report.

## RubricPart

|Field|Type|Rule|
|---|---|---|
|key|one of `business_meaning`, `allowed_values`, `interpretation_guidance`, `default_filter`|fixed set of 4|
|sentence|text|read from `rubric.md`, MUST be non-empty and free of `<!-- YOU WRITE` (FR-010)|
|rule_summary|text|plain-language statement of the code check, printed beside `sentence` (FR-003)|
|heuristic|bool|true for `business_meaning` and `interpretation_guidance` (FR-009)|

## Column

|Field|Type|Rule|
|---|---|---|
|model|text|dbt model name, from the `jaffle_shop` package only|
|name|text|lowercased|
|status|`documented`, `undocumented` or `stale`|catalog only → undocumented, manifest only → stale, both with empty text → undocumented|
|description|text|resolved text from the manifest, `PII.` token removed|
|pii|bool|true when the original description carried `PII.`|
|facts|set|any of `primary_key`, `foreign_key`, `accepted_values_test`, plus the catalog data type|

Identity: (`model`, `name`). Stale columns are listed but never graded.

## ColumnGrade

|Field|Type|Rule|
|---|---|---|
|model, name|text|references a Column with status `documented` or `undocumented`|
|part|RubricPart key||
|outcome|`pass`, `fail` or `n/a`|`n/a` only from the user's Not applicable rule (FR-004). Undocumented columns fail every applicable part.|
|reason|text|required when outcome is `fail` (FR-005)|
|grader|`rule` or `model`|`model` grades exist only with `--llm` and never replace a `rule` grade|

## CoverageReport

|Field|Rule|
|---|---|
|commit|short SHA, with `-dirty` when relevant (R7)|
|rubric|the 4 RubricParts, sentence beside rule summary|
|pass rate by part|passes / (graded columns minus `n/a`), per part|
|pass rate by model|passes / applicable grades, per model|
|per-column table|every graded column, 4 outcomes, reasons for fails, PII flag|
|drift|undocumented list and stale list, separately|
|examples|3 to 5 columns with at least one pass and one fail (FR-008), chosen by a fixed sort so reruns pick the same ones|
|heuristic notice|always present (FR-007)|

## Baseline expectations (commit `e68d4c3`)

27 graded column records: 15 documented, 12 undocumented. Plus 1 stale record, listed but not graded.
