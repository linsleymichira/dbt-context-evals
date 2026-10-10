# Context rubric

A column description passes a part when it does what that part asks. The scorecard checks these four parts for every documented column.

The standard to aim for is the `account_status` example from LangChain's post "How LangChain Built an Agent-First Data Stack" (July 27, 2026). It names the source system, says what each value means, and gives a default filter.

## 1. Business meaning

A description passes when it gives the definition this business has agreed on for the column, which another company might define differently, and does more than restate the column name.

## 2. Allowed values

A description passes when a categorical column lists every expected value and what each one means, and a numeric column states the range or kind of values to expect. A data type alone never passes.

## 3. Interpretation guidance

A description passes when it says how to read the column correctly and names at least one case where the obvious reading is wrong.

## 4. Default filter

A description passes when it says which rows to include or exclude by default, and when to override that.

## Not applicable

A key column skips allowed values and default filter, but it must still pass business meaning by saying what one row is and what the key joins to. A free-text column skips allowed values. Every other part applies to every column.
