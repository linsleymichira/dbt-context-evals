# dbt-context-evals

A scorecard for dbt column and table descriptions, read as context for an agent that writes SQL. One command grades every built column on four parts and every table on three parts, and prints the coverage.

The four parts come from LangChain's post "How LangChain Built an Agent-First Data Stack" (July 27, 2026). The post holds up one `account_status` description as a stronger example. That description names the source system, defines each value and gives a default filter. The sample is dbt Labs' public `jaffle_shop_duckdb` project, vendored under `jaffle-shop/` with its descriptions untouched.

## Run it

```shell
uv sync --all-extras
.venv/bin/python score_context.py
```

The command runs `dbt build` and `dbt docs generate`, grades every column and prints the report. It writes the report to `results/<commit>.md` and the same grades as data to `results/<commit>.json`. It takes about 7 seconds. Two runs on the same commit produce the same two files, byte for byte.

## The rubric

Each sentence is from [`rubric.md`](rubric.md). The rule beside it is what the code applies.

|Part|A description passes when|The rule|
|---|---|---|
|Business meaning|It gives the definition this business has agreed on for the column, which another company might define differently, and does more than restate the column name.|At least 2 content words that are not in the column name and are not filler. A key column must name the table it joins to.|
|Allowed values|A categorical column lists every expected value and what each one means, and a numeric or date column states the range or kind of values to expect. A data type alone never passes.|A column with an `accepted_values` test names every tested value. A numeric or date column has a unit code in parentheses, a unit word or an explicit range.|
|Interpretation guidance|It says how to read the column correctly and names at least one case where the obvious reading is wrong.|A caveat phrase: unless, except, excluding, does not include, not the same as, even if, only when.|
|Default filter|It says which rows to include or exclude by default, and when to override that.|A filter phrase (filter to, exclude, include only, by default) and an override phrase (unless, except when, only if).|

A key column skips allowed values and default filter. A free-text column skips allowed values. A skipped part shows as `n/a` and does not count in any pass rate.

## What the sample scores

From [`results/94cff0d.md`](results/94cff0d.md), on the sample exactly as dbt Labs ships it: 27 built columns across 5 models. The data file is [`results/94cff0d.json`](results/94cff0d.json). Each column in the report links to the file and line where its description is written. A column with no description links to the place it is defined.

Two earlier reports are kept as the record: [`results/8eabd21.md`](results/8eabd21.md) in the first format, and [`results/1163cc8.md`](results/1163cc8.md) from before tables were graded. Their column pass rates are the same.

|Part|Passed|Applicable|Rate|
|---|---|---|---|
|Business meaning|11|27|41%|
|Allowed values|9|17|53%|
|Interpretation guidance|0|27|0%|
|Default filter|0|21|0%|

|Model|Passed|Applicable|Rate|
|---|---|---|---|
|customers|5|24|21%|
|orders|15|32|47%|
|stg_customers|0|8|0%|
|stg_orders|0|14|0%|
|stg_payments|0|14|0%|

No column in the sample says when its obvious reading is wrong, and none says which rows to leave out by default. Those are the two parts the `account_status` example is built around.

## Table descriptions

An agent picks a table before it picks a column, so each model's table description is graded too. The three table parts are in [`rubric.md`](rubric.md). Table grades have their own rows in the report and never change a column pass rate.

|Part|A table description passes when|The rule|
|---|---|---|
|Table grain|It says what one row is.|A grain phrase: one row per, one row for each, each row, one record per.|
|Table source|It says where the data comes from.|A source phrase: sourced from, loaded from, built from, comes from, derived from, source system.|
|Table scope|It says what the table leaves out, or when to use a different table.|An exclusion or redirect phrase: excludes, excluding, does not include, only includes, instead, unless, except.|

On the sample, in the same report, 5 tables get 3 grades each.

|Part|Passed|Applicable|Rate|
|---|---|---|---|
|Table grain|0|5|0%|
|Table source|0|5|0%|
|Table scope|0|5|0%|

`customers` and `orders` have a table description, and neither says what one row is. The three staging models have no table description.

## Drift it found

The scorecard compares the documented columns with the columns dbt actually built, and lists each table with no description.

- **3 undocumented tables.** `stg_customers`, `stg_orders` and `stg_payments`.
- **12 undocumented columns.** All 11 staging columns, plus `customers.customer_lifetime_value`.
- **1 stale column.** `customers.total_order_amount` is documented and no longer exists.

The last two look like one rename. `customers.sql` builds the sum of a customer's payments as `customer_lifetime_value`, and `schema.yml` still describes a `total_order_amount` as the total value of a customer's orders. An agent reading the docs is told about a column it cannot query and nothing about the one it can.

An undocumented column fails every part that applies to it. A stale column is listed and never graded.

## Graded examples

|Column|Description|Business meaning|Allowed values|Interpretation guidance|Default filter|
|---|---|---|---|---|---|
|`customers.first_order`|Date (UTC) of a customer's first order|pass|pass|fail|fail|
|`customers.number_of_orders`|Count of the number of orders a customer has placed|pass|fail|fail|fail|
|`orders.customer_id`|Foreign key to the customers table|pass|n/a|fail|n/a|
|`customers.customer_id`|This is a unique identifier for a customer|fail|n/a|fail|n/a|
|`customers.customer_lifetime_value`|(none)|fail|fail|fail|fail|

Why each one lands where it does:

- `first_order` passes allowed values on the `(UTC)` unit code. It fails the last two parts because nothing says whether a returned order counts as a first order.
- `number_of_orders` fails allowed values because "count" is a type, not a range.
- `orders.customer_id` passes business meaning because a key has to name the table it joins to, and it does.
- `customers.customer_id` fails business meaning for the same reason: it restates its own name and names no table.
- `customer_lifetime_value` has no description, so it fails everything.

## Read the numbers as a heuristic

These grades come from pattern rules, not from a judgment of quality. Allowed values and default filter are close to mechanical. Business meaning and interpretation guidance need judgment, and the code can only look for signs of it, so the report marks both as heuristic. The report marks all three table rules as heuristic for the same reason. "Each row is checked nightly" would pass table grain and say nothing about what one row is. A description could pass interpretation guidance with the word "unless" and still say nothing useful, and a good caveat phrased another way would fail.

`--llm` adds a model's grade and one-sentence reason beside the rule grade for business meaning and interpretation guidance. It does not grade tables. It needs `ANTHROPIC_API_KEY` in the environment or in a gitignored `.env`. The model is a second opinion. It never changes a rule grade or a pass rate. Its report and data file go to `results/<commit>-llm.md` and `results/<commit>-llm.json`, so the repeatable pair for the commit is never overwritten.

## Layout

|Path|What it is|
|---|---|
|`rubric.md`|The four column parts, when a column skips one, and the three table parts, one sentence each|
|`score_context.py`|The scorecard|
|`results/`|One committed report and data file per scored commit|
|`jaffle-shop/`|The sample, vendored|
|`tests/`|`.venv/bin/python -m pytest`|
|`specs/001-context-scorecard/`|Spec, plan, CLI contract and tasks|
|`specs/002-report-links-tables/`|Spec, plan, report contract and tasks for the links, the data file and table grades|
