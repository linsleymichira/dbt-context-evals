# Quickstart: validate the report with links, a data file and table grades

## Prerequisites

- Feature 001 passes its own quickstart.
- `uv sync --all-extras` has run at the repo root.

## Scenarios

|#|Run|Expected|Proves|
|---|---|---|---|
|1|`.venv/bin/python score_context.py` on a clean tree|Exit 0, `results/<sha>.md` and `results/<sha>.json` written|FR-005|
|2|Run scenario 1 twice and `diff` both pairs|No differences in either file|SC-004|
|3|Load `results/<sha>.json` and count|27 graded columns, 1 stale, every one with a location|SC-001|
|4|Compare the JSON pass rates with `results/8eabd21.md`|41%, 53%, 0%, 0% by part|SC-005|
|5|Open the report on GitHub and click `customers.first_order`, `orders.status` and `customers.customer_lifetime_value`|`schema.yml` at its line, the `docs.md` block, and `customers.sql`|SC-001, SC-002|
|6|`grep -c "/Users/" results/<sha>.md results/<sha>.json`|0 in both|FR-003|
|7|Edit one description without committing, run again|Files end in `-dirty`, and the warning starts with a command|US4|
|8|`--llm` with `ANTHROPIC_API_KEY` unset|Exit 4, no file written|FR-009|
|9|`.venv/bin/python -m pytest`|All tests pass|Regression net|
|10|After the amendment: run on the baseline|5 tables with 3 grades each, 3 undocumented tables, scenario 4 still holds|SC-006, FR-013|

Scenario 5 needs the commit pushed, so it is the user's to run. Scenario 10 is gated with User Story 3.

See [contracts/report.md](contracts/report.md) for the file shapes and [research.md](research.md) for the link rules.
