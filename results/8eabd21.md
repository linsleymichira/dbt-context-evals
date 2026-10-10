# Context coverage scorecard at `8eabd21`

These grades come from rule-based checks and are a heuristic, not a judgment of quality. Business meaning and interpretation guidance are pattern checks and are marked heuristic below.

## Rubric

|Part|Rubric sentence|Rule|Heuristic|
|---|---|---|---|
|Business meaning|A description passes when it gives the definition this business has agreed on for the column, which another company might define differently, and does more than restate the column name.|The description has at least 2 content words that are not in the column name and are not filler. A key column must name the table it joins to.|yes|
|Allowed values|A description passes when a categorical column lists every expected value and what each one means, and a numeric or date column states the range or kind of values to expect. A data type alone never passes.|A column with an accepted_values test names every tested value in its description. A numeric or date column has a unit code in parentheses, a unit word, or an explicit range.|no|
|Interpretation guidance|A description passes when it says how to read the column correctly and names at least one case where the obvious reading is wrong.|The description contains a caveat phrase: unless, except, excluding, does not include, not the same as, even if, only when.|yes|
|Default filter|A description passes when it says which rows to include or exclude by default, and when to override that.|The description has a filter phrase (filter to, exclude, include only, by default) and an override phrase (unless, except when, only if).|no|
|Not applicable|A key column skips allowed values and default filter, but it must still pass business meaning by saying what one row is and what the key joins to. A free-text column skips allowed values. Every other part applies to every column.|A key column (unique plus not_null tests, or a relationships test) skips allowed values and default filter. A free-text column (varchar with no accepted_values test) skips allowed values.|no|

## Pass rate by part

|Part|Passed|Applicable|Rate|
|---|---|---|---|
|Business meaning|11|27|41%|
|Allowed values|9|17|53%|
|Interpretation guidance|0|27|0%|
|Default filter|0|21|0%|

## Pass rate by model

|Model|Passed|Applicable|Rate|
|---|---|---|---|
|customers|5|24|21%|
|orders|15|32|47%|
|stg_customers|0|8|0%|
|stg_orders|0|14|0%|
|stg_payments|0|14|0%|

## Drift

Undocumented (12): `customers.customer_lifetime_value`, `stg_customers.customer_id`, `stg_customers.first_name`, `stg_customers.last_name`, `stg_orders.customer_id`, `stg_orders.order_date`, `stg_orders.order_id`, `stg_orders.status`, `stg_payments.amount`, `stg_payments.order_id`, `stg_payments.payment_id`, `stg_payments.payment_method`

Stale (1): `customers.total_order_amount`

## Columns

|Model|Column|PII|Business meaning|Allowed values|Interpretation guidance|Default filter|Why it failed|
|---|---|---|---|---|---|---|---|
|customers|customer_id||fail|n/a|fail|n/a|Business meaning: key names no table it joins to. Interpretation guidance: names no case where the obvious reading is wrong|
|customers|customer_lifetime_value||fail|fail|fail|fail|Business meaning: no description. Allowed values: no description. Interpretation guidance: no description. Default filter: no description|
|customers|first_name|PII|fail|n/a|fail|fail|Business meaning: adds fewer than 2 words to the column name. Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|customers|first_order||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|customers|last_name|PII|fail|n/a|fail|fail|Business meaning: adds fewer than 2 words to the column name. Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|customers|most_recent_order||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|customers|number_of_orders||pass|fail|fail|fail|Allowed values: no unit or range, only a type. Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|amount||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|bank_transfer_amount||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|coupon_amount||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|credit_card_amount||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|customer_id||pass|n/a|fail|n/a|Interpretation guidance: names no case where the obvious reading is wrong|
|orders|gift_card_amount||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|order_date||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|order_id||fail|n/a|fail|n/a|Business meaning: key names no table it joins to. Interpretation guidance: names no case where the obvious reading is wrong|
|orders|status||pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|stg_customers|customer_id||fail|n/a|fail|n/a|Business meaning: no description. Interpretation guidance: no description|
|stg_customers|first_name||fail|n/a|fail|fail|Business meaning: no description. Interpretation guidance: no description. Default filter: no description|
|stg_customers|last_name||fail|n/a|fail|fail|Business meaning: no description. Interpretation guidance: no description. Default filter: no description|
|stg_orders|customer_id||fail|fail|fail|fail|Business meaning: no description. Allowed values: no description. Interpretation guidance: no description. Default filter: no description|
|stg_orders|order_date||fail|fail|fail|fail|Business meaning: no description. Allowed values: no description. Interpretation guidance: no description. Default filter: no description|
|stg_orders|order_id||fail|n/a|fail|n/a|Business meaning: no description. Interpretation guidance: no description|
|stg_orders|status||fail|fail|fail|fail|Business meaning: no description. Allowed values: no description. Interpretation guidance: no description. Default filter: no description|
|stg_payments|amount||fail|fail|fail|fail|Business meaning: no description. Allowed values: no description. Interpretation guidance: no description. Default filter: no description|
|stg_payments|order_id||fail|fail|fail|fail|Business meaning: no description. Allowed values: no description. Interpretation guidance: no description. Default filter: no description|
|stg_payments|payment_id||fail|n/a|fail|n/a|Business meaning: no description. Interpretation guidance: no description|
|stg_payments|payment_method||fail|fail|fail|fail|Business meaning: no description. Allowed values: no description. Interpretation guidance: no description. Default filter: no description|

## Examples

|Model|Column|Description|Business meaning|Allowed values|Interpretation guidance|Default filter|Why it failed|
|---|---|---|---|---|---|---|---|
|customers|first_order|Date (UTC) of a customer's first order|pass|pass|fail|fail|Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|customers|number_of_orders|Count of the number of orders a customer has placed|pass|fail|fail|fail|Allowed values: no unit or range, only a type. Interpretation guidance: names no case where the obvious reading is wrong. Default filter: says no default rows to include or exclude|
|orders|customer_id|Foreign key to the customers table|pass|n/a|fail|n/a|Interpretation guidance: names no case where the obvious reading is wrong|
|customers|customer_id|This is a unique identifier for a customer|fail|n/a|fail|n/a|Business meaning: key names no table it joins to. Interpretation guidance: names no case where the obvious reading is wrong|
|customers|customer_lifetime_value|(none)|fail|fail|fail|fail|Business meaning: no description. Allowed values: no description. Interpretation guidance: no description. Default filter: no description|
