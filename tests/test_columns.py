"""Column loading decides what gets graded (FR-001, FR-006, data-model).

An undocumented built column is the worst case for an agent, so it must
be graded and fail. A stale entry describes nothing an agent can query,
so it must be listed and never graded.
"""

import score_context


def _by_key(columns):
    return {(c.model, c.name): c for c in columns}


def test_each_column_gets_the_status_its_drift_implies(manifest, catalog):
    cols = _by_key(score_context.load_columns(manifest, catalog))

    statuses = {key: c.status for key, c in cols.items()}
    assert statuses == {
        ("customers", "blank_col"): "undocumented",
        ("customers", "customer_id"): "documented",
        ("customers", "customer_lifetime_value"): "undocumented",
        ("customers", "first_name"): "documented",
        ("customers", "total_order_amount"): "stale",
        ("orders", "customer_id"): "undocumented",
        ("orders", "order_id"): "documented",
        ("orders", "status"): "documented",
    }


def test_other_packages_are_out_of_scope(manifest, catalog):
    models = {c.model for c in score_context.load_columns(manifest, catalog)}

    assert models == {"customers", "orders"}


def test_uppercase_catalog_names_match_their_documentation(manifest, catalog):
    cols = _by_key(score_context.load_columns(manifest, catalog))

    assert cols[("orders", "order_id")].status == "documented"


def test_pii_flag_is_kept_but_never_graded_as_content(manifest, catalog):
    first_name = _by_key(score_context.load_columns(manifest, catalog))[
        ("customers", "first_name")
    ]

    assert first_name.pii is True
    assert first_name.description == "Customer's first name."


def test_key_and_value_facts_come_from_dbt_tests(manifest, catalog):
    cols = _by_key(score_context.load_columns(manifest, catalog))

    assert "primary_key" in cols[("customers", "customer_id")].facts
    # not_null alone is not a primary key
    assert "primary_key" not in cols[("orders", "order_id")].facts
    assert "foreign_key" in cols[("orders", "customer_id")].facts
    assert "accepted_values_test" in cols[("orders", "status")].facts


def test_data_type_comes_from_the_built_table(manifest, catalog):
    cols = _by_key(score_context.load_columns(manifest, catalog))

    assert cols[("customers", "customer_lifetime_value")].data_type == (
        "double"
    )
    assert cols[("customers", "total_order_amount")].data_type is None


def test_columns_are_sorted_by_model_then_name(manifest, catalog):
    columns = score_context.load_columns(manifest, catalog)

    keys = [(c.model, c.name) for c in columns]
    assert keys == sorted(keys)


def test_tested_values_are_kept_so_the_rule_can_check_each_one(
    manifest, catalog
):
    cols = _by_key(score_context.load_columns(manifest, catalog))

    assert cols[("orders", "status")].accepted_values == (
        "placed",
        "shipped",
        "completed",
    )
    assert cols[("customers", "first_name")].accepted_values == ()
