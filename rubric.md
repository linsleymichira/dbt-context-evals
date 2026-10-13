# Context rubric

A description passes a part when it does what that part asks. The scorecard checks the four column parts for every documented column and the three table parts for every table.

The standard to aim for in a column description is the `account_status` example from LangChain's post "How LangChain Built an Agent-First Data Stack" (July 27, 2026). It names the source system, says what each value means, and gives a default filter.

## 1. Business meaning

A description passes when it gives the definition this business has agreed on for the column, which another company might define differently, and does more than restate the column name.

## 2. Allowed values

A description passes when a categorical column lists every expected value and what each one means, and a numeric or date column states the range or kind of values to expect. A data type alone never passes.

## 3. Interpretation guidance

A description passes when it says how to read the column correctly and names at least one case where the obvious reading is wrong.

## 4. Default filter

A description passes when it says which rows to include or exclude by default, and when to override that.

## Not applicable

A key column skips allowed values and default filter, but it must still pass business meaning by saying what one row is and what the key joins to. A free-text column skips allowed values. Every other part applies to every column.

## Table grain

A table description passes when it says what one row is.

## Table source

A table description passes when it says where the data comes from.

## Table scope

A table description passes when it says what the table leaves out, or when to use a different table.
