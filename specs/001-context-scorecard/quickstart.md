# Quickstart: validate the Context Coverage Scorecard

## Prerequisites

- `rubric.md` has all 5 sections written (no `<!-- YOU WRITE` left).
- Dependencies installed: `uv sync` at the repo root (see [research.md](research.md) R9).

## Scenarios

|#|Run|Expected|Proves|
|---|---|---|---|
|1|`.venv/bin/python score_context.py` with one `YOU WRITE` marker restored|Exit 2, the section named, no file in `results/`|FR-010|
|2|`.venv/bin/python score_context.py` on a clean tree|Exit 0 in under 10 seconds, `results/<sha>.md` written|SC-001, SC-005|
|3|Read the report's drift section|12 undocumented (including `customers.customer_lifetime_value`), 1 stale (`customers.total_order_amount`)|User Story 2, SC-002|
|4|Run scenario 2 twice and `diff` the two outputs|No differences|SC-004|
|5|Edit one description without committing, run again|File ends in `-dirty.md` with a warning line|Principle II|
|6|`--llm` with `ANTHROPIC_API_KEY` unset|Exit 4, key named, no file written|User Story 3, scenario 2|
|7|`.venv/bin/python -m pytest`|All tests pass|Regression net|
|8|Pick a random column and explain each grade aloud from the report and `rubric.md`|Under 1 minute|SC-003|

See [contracts/cli.md](contracts/cli.md) for exit codes and report layout, and [data-model.md](data-model.md) for grade and drift rules.
