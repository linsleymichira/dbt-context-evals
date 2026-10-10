"""The approved scoring rules (tasks.md T015, FR-003, FR-004, FR-009).

Each rule implements one sentence the user wrote in rubric.md. A test
here fails when the rule drifts from that sentence, which is the only
standard a description is held to.
"""

import score_context
from score_context import Column

MODELS = frozenset({"customers", "orders"})


def _column(name, description, data_type="varchar", facts=(), values=()):
    return Column(
        model="orders",
        name=name,
        status="documented" if description else "undocumented",
        description=description,
        pii=False,
        facts=frozenset(facts),
        data_type=data_type,
        accepted_values=tuple(values),
    )


def _outcomes(column):
    return {
        grade.part: grade.outcome
        for grade in score_context.grade_column(column, MODELS)
    }


def _grade(column, part):
    return next(
        grade
        for grade in score_context.grade_column(column, MODELS)
        if grade.part == part
    )


# --- business meaning -----------------------------------------------------


def test_restating_the_column_name_is_not_business_meaning():
    column = _column("first_name", "Customer's first name.")

    grade = _grade(column, "business_meaning")

    assert grade.outcome == "fail"
    assert grade.reason


def test_a_description_that_adds_to_the_name_has_business_meaning():
    column = _column(
        "order_date", "Date (UTC) that the order was placed", "date"
    )

    assert _outcomes(column)["business_meaning"] == "pass"


def test_a_key_that_names_no_table_does_not_say_what_it_joins_to():
    column = _column(
        "customer_id",
        "This is a unique identifier for a customer",
        "integer",
        facts={"primary_key"},
    )

    assert _outcomes(column)["business_meaning"] == "fail"


def test_a_key_that_names_its_table_says_what_it_joins_to():
    column = _column(
        "customer_id",
        "Foreign key to the customers table",
        "integer",
        facts={"foreign_key"},
    )

    assert _outcomes(column)["business_meaning"] == "pass"


# --- allowed values -------------------------------------------------------


def test_a_categorical_column_must_list_every_tested_value():
    values = ("placed", "shipped", "returned")
    listed = _column(
        "status",
        "placed means not yet sent, shipped means in transit, "
        "returned means received back at the warehouse",
        facts={"accepted_values_test"},
        values=values,
    )
    partial = _column(
        "status",
        "One of placed or shipped",
        facts={"accepted_values_test"},
        values=values,
    )

    assert _outcomes(listed)["allowed_values"] == "pass"
    missing = _grade(partial, "allowed_values")
    assert missing.outcome == "fail"
    assert "returned" in missing.reason


def test_a_numeric_column_needs_a_unit_or_range_not_just_a_type():
    with_unit = _column("amount", "Total amount (AUD) of the order", "double")
    with_range = _column(
        "number_of_orders", "Orders placed, 0 or more", "bigint"
    )
    type_only = _column(
        "number_of_orders",
        "Count of the number of orders a customer has placed",
        "bigint",
    )

    assert _outcomes(with_unit)["allowed_values"] == "pass"
    assert _outcomes(with_range)["allowed_values"] == "pass"
    assert _outcomes(type_only)["allowed_values"] == "fail"


def test_a_date_column_is_held_to_the_numeric_rule():
    column = _column(
        "order_date", "Date (UTC) that the order was placed", "date"
    )

    assert _outcomes(column)["allowed_values"] == "pass"


# --- interpretation guidance ----------------------------------------------


def test_a_description_with_no_caveat_gives_no_interpretation_guidance():
    column = _column("amount", "Total amount (AUD) of the order", "double")

    assert _outcomes(column)["interpretation_guidance"] == "fail"


def test_naming_a_case_where_the_obvious_reading_is_wrong_is_guidance():
    column = _column(
        "amount",
        "Total amount (AUD) of the order. Does not include refunds.",
        "double",
    )

    assert _outcomes(column)["interpretation_guidance"] == "pass"


# --- default filter -------------------------------------------------------


def test_a_default_filter_needs_both_the_default_and_the_override():
    both = _column(
        "status",
        "Filter to completed unless the analysis covers returns.",
    )
    default_only = _column("status", "Filter to completed orders.")

    assert _outcomes(both)["default_filter"] == "pass"
    assert _outcomes(default_only)["default_filter"] == "fail"


# --- not applicable -------------------------------------------------------


def test_a_key_skips_allowed_values_and_default_filter_only():
    column = _column(
        "order_id",
        "This is a unique identifier for an order",
        "integer",
        facts={"primary_key"},
    )

    outcomes = _outcomes(column)

    assert outcomes["allowed_values"] == "n/a"
    assert outcomes["default_filter"] == "n/a"
    assert outcomes["business_meaning"] != "n/a"
    assert outcomes["interpretation_guidance"] != "n/a"


def test_free_text_skips_allowed_values_but_not_default_filter():
    column = _column("first_name", "Customer's first name.")

    outcomes = _outcomes(column)

    assert outcomes["allowed_values"] == "n/a"
    assert outcomes["default_filter"] == "fail"


def test_a_tested_varchar_is_categorical_not_free_text():
    column = _column(
        "status",
        "The order status",
        facts={"accepted_values_test"},
        values=("placed",),
    )

    assert _outcomes(column)["allowed_values"] == "fail"


# --- shape ----------------------------------------------------------------


def test_every_fail_carries_a_reason_and_only_judgment_parts_are_heuristic():
    column = _column("first_name", "Customer's first name.")

    grades = score_context.grade_column(column, MODELS)

    assert [g.part for g in grades] == list(score_context.PARTS)
    assert all(g.reason for g in grades if g.outcome == "fail")
    assert score_context.HEURISTIC_PARTS == frozenset(
        {"business_meaning", "interpretation_guidance"}
    )
    assert set(score_context.RULE_SUMMARIES) == set(
        score_context.RUBRIC_SECTIONS
    )


def test_a_range_counts_wherever_it_sits_in_the_sentence():
    # A description that opens with the range is still stating a range.
    column = _column("number_of_orders", "Between 0 and 5 orders", "bigint")

    assert _outcomes(column)["allowed_values"] == "pass"


def test_a_value_made_of_punctuation_can_still_be_listed():
    column = _column(
        "status",
        "placed means sent. (none) means the order never shipped.",
        facts={"accepted_values_test"},
        values=("placed", "(none)"),
    )

    assert _outcomes(column)["allowed_values"] == "pass"
