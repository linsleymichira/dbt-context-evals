# Report Contract: files, JSON shape and Markdown changes

Extends [feature 001's CLI contract](../../001-context-scorecard/contracts/cli.md). Invocation, steps and exit codes are unchanged.

## Files written

|Run|Files|
|---|---|
|Default|`results/<label>.md` and `results/<label>.json`|
|`--llm`|`results/<label>-llm.md` and `results/<label>-llm.json`. The default pair is not touched|
|Any exit code other than 0|None|

`<label>` is the short commit hash, with `-dirty` when the tree has uncommitted changes outside `results/`.

## JSON shape

```json
{
  "schema_version": 1,
  "commit": "abc1234",
  "dirty": false,
  "rubric": [
    {
      "part": "business_meaning",
      "applies_to": "column",
      "sentence": "…",
      "rule": "…",
      "heuristic": true
    }
  ],
  "pass_rates": {
    "by_part": [
      {"part": "business_meaning", "passed": 11, "applicable": 27, "rate": 41}
    ],
    "by_model": [
      {"model": "customers", "passed": 5, "applicable": 24, "rate": 21}
    ]
  },
  "drift": {
    "undocumented_columns": ["customers.customer_lifetime_value"],
    "stale_columns": ["customers.total_order_amount"]
  },
  "columns": [
    {
      "model": "customers",
      "column": "first_order",
      "status": "documented",
      "pii": false,
      "description": "Date (UTC) of a customer's first order",
      "location": {"path": "jaffle-shop/models/schema.yml", "line": 20},
      "grades": {
        "business_meaning": {"outcome": "pass", "reason": ""},
        "default_filter": {
          "outcome": "fail",
          "reason": "says no default rows to include or exclude"
        }
      }
    }
  ]
}
```

- A stale column has `"status": "stale"` and an empty `grades` object.
- A missing location is `"location": null`.
- With `--llm`, each judged part of a column also has `"model_grade": {"outcome": "…", "reason": "…"}`.
- With User Story 3, the file gains `"tables"`, `pass_rates.table_parts`, `drift.undocumented_tables`, and rubric entries with `"applies_to": "table"`.
- `rate` is a whole-number percent, or null when `applicable` is 0.

## Markdown changes

1. The Column cell of the per-column table and of the examples table is a link to the location. A row with no location shows the plain name.
2. The drift lists link each column the same way.
3. The heuristic notice and the dirty warning use the wording in research R7.
4. A reason shared by several parts of one row is written once, after the parts it applies to.
5. With User Story 3: the rubric table gains 3 table rows, a "Pass rate by table part" table follows "Pass rate by part", the drift section gains an undocumented-tables line, and a "Tables" table comes before "Columns".

Section order is otherwise unchanged. No timestamp or absolute path appears in either file.
