"""Each column in the report links to where it is defined.

A grade is only useful if the reader can open the description that
earned it. The link must land on the right model's column, because two
models often share a column name.
"""

from dataclasses import replace

import score_context
from conftest import CUSTOMERS

SCHEMA = """version: 2

models:
  - name: customers
    description: One row per customer

    columns:
      - name: customer_id
        description: Unique identifier for a customer
        tests:
          - unique

  - name: orders
    columns:
      - name: order_id
      - name: "customer_id"
        description: Foreign key to the customers table
"""


def test_a_shared_column_name_resolves_under_its_own_model():
    assert (
        score_context.find_column_line(SCHEMA, "customers", "customer_id") == 8
    )
    assert (
        score_context.find_column_line(SCHEMA, "orders", "customer_id") == 16
    )


def test_a_column_missing_from_the_file_has_no_line():
    assert score_context.find_column_line(SCHEMA, "orders", "amount") is None
    assert (
        score_context.find_column_line(SCHEMA, "payments", "order_id") is None
    )


def _with_paths(manifest):
    node = manifest["nodes"][CUSTOMERS]
    node["patch_path"] = "jaffle_shop://models/schema.yml"
    node["original_file_path"] = "models/customers.sql"
    return manifest


def test_a_documented_column_points_at_its_schema_line(manifest, catalog):
    columns = score_context.load_columns(
        _with_paths(manifest), catalog, read=lambda path: SCHEMA
    )
    col = next(
        c for c in columns if (c.model, c.name) == ("customers", "customer_id")
    )
    assert (col.path, col.line) == ("models/schema.yml", 8)


def test_a_column_with_no_schema_entry_points_at_the_model_sql(
    manifest, catalog
):
    # customer_lifetime_value is built by the SQL and absent from the
    # YAML, so the SQL file is the only place it is defined.
    columns = score_context.load_columns(
        _with_paths(manifest), catalog, read=lambda path: SCHEMA
    )
    col = next(
        c
        for c in columns
        if (c.model, c.name) == ("customers", "customer_lifetime_value")
    )
    assert (col.path, col.line) == ("models/customers.sql", None)


def test_columns_load_without_a_reader_and_carry_no_link(manifest, catalog):
    columns = score_context.load_columns(manifest, catalog)
    assert {(c.path, c.line) for c in columns} == {("", None)}


def _report(columns, rubric_path):
    rubric = score_context.load_rubric(rubric_path)
    return score_context.render_report(
        "abc1234", rubric, columns, score_context.grade_all(columns)
    )


def test_the_column_table_links_relative_to_the_results_folder(
    manifest, catalog, filled_rubric
):
    columns = [
        replace(c, path="models/schema.yml", line=8)
        if (c.model, c.name) == ("customers", "customer_id")
        else c
        for c in score_context.load_columns(manifest, catalog)
    ]
    report = _report(columns, filled_rubric)
    assert (
        "|customers|[customer_id](../jaffle-shop/models/schema.yml#L8)|"
        in report
    )
    # A column with no known file stays plain text, never a dead link.
    assert "|customers|first_name|" in report


def test_a_stale_column_is_linked_from_the_drift_list(
    manifest, catalog, filled_rubric
):
    # A stale column is not in the column table, so the drift list is
    # the only place a reader can jump to the line that needs deleting.
    columns = [
        replace(c, path="models/schema.yml", line=20)
        if c.status == "stale"
        else c
        for c in score_context.load_columns(manifest, catalog)
    ]
    assert (
        "[`customers.total_order_amount`]"
        "(../jaffle-shop/models/schema.yml#L20)"
        in _report(columns, filled_rubric)
    )


def test_a_file_link_without_a_line_has_no_anchor(
    manifest, catalog, filled_rubric
):
    columns = [
        replace(c, path="models/customers.sql")
        if (c.model, c.name) == ("customers", "customer_lifetime_value")
        else c
        for c in score_context.load_columns(manifest, catalog)
    ]
    assert (
        "[customer_lifetime_value](../jaffle-shop/models/customers.sql)|"
        in _report(columns, filled_rubric)
    )
