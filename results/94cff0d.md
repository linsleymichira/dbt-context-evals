# Context coverage scorecard at `94cff0d`

These grades come from rules and are a heuristic, not a judgment of quality. The rules for business meaning and interpretation guidance match patterns, and the rubric table marks them as heuristic.

## Rubric

|Part|Rubric sentence|Rule|Heuristic|
|---|---|---|---|
|Business meaning|A description passes when it gives the definition this business has agreed on for the column, which another company might define differently, and does more than restate the column name.|The description has at least 2 content words that are not in the column name and are not filler. A key column must name the table it joins to.|yes|
|Allowed values|A description passes when a categorical column lists every expected value and what each one means, and a numeric or date column states the range or kind of values to expect. A data type alone never passes.|A column with an accepted_values test names every tested value in its description. A numeric or date column has a unit code in parentheses, a unit word, or an explicit range.|no|
|Interpretation guidance|A description passes when it says how to read the column correctly and names at least one case where the obvious reading is wrong.|The description contains a caveat phrase: unless, except, excluding, does not include, not the same as, even if, only when.|yes|
|Default filter|A description passes when it says which rows to include or exclude by default, and when to override that.|The description has a filter phrase (filter to, exclude, include only, by default) and an override phrase (unless, except when, only if).|no|
|Not applicable|A key column skips allowed values and default filter, but it must still pass business meaning by saying what one row is and what the key joins to. A free-text column skips allowed values. Every other part applies to every column.|A key column (unique plus not_null tests, or a relationships test) skips allowed values and default filter. A free-text column (varchar with no accepted_values test) skips allowed values.|no|
|Table grain|A table description passes when it says what one row is.|The description contains a grain phrase: one row per, one row for each, each row, one record per.|yes|
|Table source|A table description passes when it says where the data comes from.|The description contains a source phrase: sourced from, loaded from, built from, comes from, derived from, source system.|yes|
|Table scope|A table description passes when it says what the table leaves out, or when to use a different table.|The description contains an exclusion or redirect phrase: excludes, excluding, does not include, only includes, instead, unless, except.|yes|

## Pass rate by part

|Part|Passed|Applicable|Rate|
|---|---|---|---|
|Business meaning|11|27|41%|
|Allowed values|9|17|53%|
|Interpretation guidance|0|27|0%|
|Default filter|0|21|0%|

## Pass rate by table part

|Part|Passed|Applicable|Rate|
|---|---|---|---|
|Table grain|0|5|0%|
|Table source|0|5|0%|
|Table scope|0|5|0%|

## Pass rate by model

|Model|Passed|Applicable|Rate|
|---|---|---|---|
|customers|5|24|21%|
|orders|15|32|47%|
|stg_customers|0|8|0%|
|stg_orders|0|14|0%|
|stg_payments|0|14|0%|

## Drift

Undocumented (12): [`customers.customer_lifetime_value`](../jaffle-shop/models/customers.sql), [`stg_customers.customer_id`](../jaffle-shop/models/staging/schema.yml#L6), [`stg_customers.first_name`](../jaffle-shop/models/staging/stg_customers.sql), [`stg_customers.last_name`](../jaffle-shop/models/staging/stg_customers.sql), [`stg_orders.customer_id`](../jaffle-shop/models/staging/stg_orders.sql), [`stg_orders.order_date`](../jaffle-shop/models/staging/stg_orders.sql), [`stg_orders.order_id`](../jaffle-shop/models/staging/schema.yml#L13), [`stg_orders.status`](../jaffle-shop/models/staging/schema.yml#L17), [`stg_payments.amount`](../jaffle-shop/models/staging/stg_payments.sql), [`stg_payments.order_id`](../jaffle-shop/models/staging/stg_payments.sql), [`stg_payments.payment_id`](../jaffle-shop/models/staging/schema.yml#L25), [`stg_payments.payment_method`](../jaffle-shop/models/staging/schema.yml#L29)

Stale (1): [`customers.total_order_amount`](../jaffle-shop/models/schema.yml#L29)

Undocumented tables (3): [`stg_customers`](../jaffle-shop/models/staging/schema.yml#L4), [`stg_orders`](../jaffle-shop/models/staging/schema.yml#L11), [`stg_payments`](../jaffle-shop/models/staging/schema.yml#L23)

## Tables

|Model|Table grain|Table source|Table scope|Why it failed|
|---|---|---|---|---|
|[customers](../jaffle-shop/models/schema.yml#L4)|fail|fail|fail|Table grain: does not say what one row is. Table source: does not say where the data comes from. Table scope: does not say what the table leaves out or which table to use|
|[orders](../jaffle-shop/models/schema.yml#L32)|fail|fail|fail|Table grain: does not say what one row is. Table source: does not say where the data comes from. Table scope: does not say what the table leaves out or which table to use|
|[stg_customers](../jaffle-shop/models/staging/schema.yml#L4)|fail|fail|fail|Table grain, Table source, Table scope: no description|
|[stg_orders](../jaffle-shop/models/staging/schema.yml#L11)|fail|fail|fail|Table grain, Table source, Table scope: no description|
|[stg_payments](../jaffle-shop/models/staging/schema.yml#L23)|fail|fail|fail|Table grain, Table source, Table scope: no description|

## Columns

|Model|Column|PII|Business meaning|Allowed values|Interpretation guidance|Default filter|Why it failed|
|---|---|---|---|---|---|---|---|
|customers|[customer_id](../jaffle-shop/models/schema.yml#L8)||fail|n/a|fail|n/a|Business meaning: key names no table it joins to. Interpretation guidance: names no case where the obvious reading is wrong|
|customers|[customer_lifetime_value](../jaffle-shop/models/customers.sql)||fail|fail|fail|fail|Business meaning, Allowed values, Interpretation guidance, Default filter: no description|
|customers|[first_name](../jaffle-shop/models/schema.yml#L14)|PII|fail|n/a|fail|fail|Business meaning: adds fewer than 2 words to the column name. Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|customers|[first_order](../jaffle-shop/models/schema.yml#L20)||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|customers|[last_name](../jaffle-shop/models/schema.yml#L17)|PII|fail|n/a|fail|fail|Business meaning: adds fewer than 2 words to the column name. Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|customers|[most_recent_order](../jaffle-shop/models/schema.yml#L23)||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|customers|[number_of_orders](../jaffle-shop/models/schema.yml#L26)||pass|fail|fail|fail|Allowed values: no unit or range, only a type. Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|[amount](../jaffle-shop/models/schema.yml#L61)||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|[bank_transfer_amount](../jaffle-shop/models/schema.yml#L76)||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|[coupon_amount](../jaffle-shop/models/schema.yml#L71)||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|[credit_card_amount](../jaffle-shop/models/schema.yml#L66)||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|[customer_id](../jaffle-shop/models/schema.yml#L42)||pass|n/a|fail|n/a|Interpretation guidance: names no case where the obvious reading is wrong|
|orders|[gift_card_amount](../jaffle-shop/models/schema.yml#L81)||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|[order_date](../jaffle-shop/models/schema.yml#L51)||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|[order_id](../jaffle-shop/models/schema.yml#L36)||fail|n/a|fail|n/a|Business meaning: key names no table it joins to. Interpretation guidance: names no case where the obvious reading is wrong|
|orders|[status](../jaffle-shop/models/docs.md#L1)||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|stg_customers|[customer_id](../jaffle-shop/models/staging/schema.yml#L6)||fail|n/a|fail|n/a|Business meaning, Interpretation guidance: no description|
|stg_customers|[first_name](../jaffle-shop/models/staging/stg_customers.sql)||fail|n/a|fail|fail|Business meaning, Interpretation guidance, Default filter: no description|
|stg_customers|[last_name](../jaffle-shop/models/staging/stg_customers.sql)||fail|n/a|fail|fail|Business meaning, Interpretation guidance, Default filter: no description|
|stg_orders|[customer_id](../jaffle-shop/models/staging/stg_orders.sql)||fail|fail|fail|fail|Business meaning, Allowed values, Interpretation guidance, Default filter: no description|
|stg_orders|[order_date](../jaffle-shop/models/staging/stg_orders.sql)||fail|fail|fail|fail|Business meaning, Allowed values, Interpretation guidance, Default filter: no description|
|stg_orders|[order_id](../jaffle-shop/models/staging/schema.yml#L13)||fail|n/a|fail|n/a|Business meaning, Interpretation guidance: no description|
|stg_orders|[status](../jaffle-shop/models/staging/schema.yml#L17)||fail|fail|fail|fail|Business meaning, Allowed values, Interpretation guidance, Default filter: no description|
|stg_payments|[amount](../jaffle-shop/models/staging/stg_payments.sql)||fail|fail|fail|fail|Business meaning, Allowed values, Interpretation guidance, Default filter: no description|
|stg_payments|[order_id](../jaffle-shop/models/staging/stg_payments.sql)||fail|fail|fail|fail|Business meaning, Allowed values, Interpretation guidance, Default filter: no description|
|stg_payments|[payment_id](../jaffle-shop/models/staging/schema.yml#L25)||fail|n/a|fail|n/a|Business meaning, Interpretation guidance: no description|
|stg_payments|[payment_method](../jaffle-shop/models/staging/schema.yml#L29)||fail|fail|fail|fail|Business meaning, Allowed values, Interpretation guidance, Default filter: no description|

## Examples

|Model|Column|Description|Business meaning|Allowed values|Interpretation guidance|Default filter|Why it failed|
|---|---|---|---|---|---|---|---|
|customers|[first_order](../jaffle-shop/models/schema.yml#L20)|Date (UTC) of a customer's first order|pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|customers|[number_of_orders](../jaffle-shop/models/schema.yml#L26)|Count of the number of orders a customer has placed|pass|fail|fail|fail|Allowed values: no unit or range, only a type. Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|[customer_id](../jaffle-shop/models/schema.yml#L42)|Foreign key to the customers table|pass|n/a|fail|n/a|Interpretation guidance: names no case where the obvious reading is wrong|
|customers|[customer_id](../jaffle-shop/models/schema.yml#L8)|This is a unique identifier for a customer|fail|n/a|fail|n/a|Business meaning: key names no table it joins to. Interpretation guidance: names no case where the obvious reading is wrong|
|customers|[customer_lifetime_value](../jaffle-shop/models/customers.sql)|(none)|fail|fail|fail|fail|Business meaning, Allowed values, Interpretation guidance, Default filter: no description|
