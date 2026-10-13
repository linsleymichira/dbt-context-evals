"""Each column in the report links to where its description is written.

A grade is only useful if the reader can open the words that earned it
(spec 002, User Story 1). The link must land on the right model's
column, because two models often share a column name, and on the shared
block when the words live there and not in the schema file.
"""

from dataclasses import replace

import score_context
from conftest import CUSTOMERS, ORDERS
from score_context import Location

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
      - name: status
        description: '{{ doc("orders_status") }}'
"""

DOCS = """Some intro text.

{% docs orders_status %}

Orders can be one of the following statuses.

{% enddocs %}
"""


def _read(path):
    return {"models/schema.yml": SCHEMA, "models/docs.md": DOCS}[path]


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


def test_a_block_line_is_the_line_that_opens_the_block():
    assert score_context.find_block_line(DOCS, "orders_status") == 3
    assert score_context.find_block_line(DOCS, "orders") is None


def _with_paths(manifest):
    for model_id, name in ((CUSTOMERS, "customers"), (ORDERS, "orders")):
        node = manifest["nodes"][model_id]
        node["patch_path"] = "jaffle_shop://models/schema.yml"
        node["original_file_path"] = f"models/{name}.sql"
    return manifest


def _column(columns, model, name):
    return next(c for c in columns if (c.model, c.name) == (model, name))


def test_a_documented_column_points_at_its_schema_line(manifest, catalog):
    columns = score_context.load_columns(
        _with_paths(manifest), catalog, read=_read
    )
    assert _column(columns, "customers", "customer_id").location == Location(
        "jaffle-shop/models/schema.yml", 8
    )


def test_an_unreadable_schema_file_keeps_the_file_location_without_a_line(
    manifest, catalog
):
    def unreadable(_):
        raise OSError("schema file is unavailable")

    columns = score_context.load_columns(
        _with_paths(manifest), catalog, read=unreadable
    )
    assert _column(columns, "customers", "customer_id").location == Location(
        "jaffle-shop/models/schema.yml", None
    )


def test_a_column_with_no_schema_entry_points_at_the_model_sql(
    manifest, catalog
):
    # customer_lifetime_value is built by the SQL and absent from the
    # YAML, so the SQL file is the only place it is defined.
    columns = score_context.load_columns(
        _with_paths(manifest), catalog, read=_read
    )
    assert _column(
        columns, "customers", "customer_lifetime_value"
    ).location == Location("jaffle-shop/models/customers.sql", None)


def _with_status_block(manifest, blocks):
    manifest = _with_paths(manifest)
    manifest["nodes"][ORDERS]["columns"]["status"] = {
        "name": "status",
        "description": "Orders can be one of the following statuses.",
        "doc_blocks": blocks,
    }
    manifest["docs"] = {
        "doc.jaffle_shop.orders_status": {
            "name": "orders_status",
            "original_file_path": "models/docs.md",
        }
    }
    return manifest


def test_a_description_from_a_shared_block_points_at_the_block(
    manifest, catalog
):
    # The schema line holds only the reference. The reader wants the
    # words that were graded, and those are in the block (FR-002).
    columns = score_context.load_columns(
        _with_status_block(manifest, ["doc.jaffle_shop.orders_status"]),
        catalog,
        read=_read,
    )
    assert _column(columns, "orders", "status").location == Location(
        "jaffle-shop/models/docs.md", 3
    )


def test_a_table_description_from_a_shared_block_points_at_the_block(manifest):
    manifest = _with_paths(manifest)
    manifest["nodes"][CUSTOMERS]["description"] = "Customers in the model."
    manifest["nodes"][CUSTOMERS]["doc_blocks"] = [
        "doc.jaffle_shop.orders_status"
    ]
    manifest["docs"] = {
        "doc.jaffle_shop.orders_status": {
            "name": "orders_status",
            "original_file_path": "models/docs.md",
        }
    }

    tables = score_context.load_tables(manifest, read=_read)

    assert tables[0].location == Location("jaffle-shop/models/docs.md", 3)


def test_an_unreadable_docs_file_keeps_the_block_location_without_a_line(
    manifest, catalog
):
    # A link is for navigation. A docs file that cannot be read costs
    # the line number and never the run (FR-004).
    def unreadable(_):
        raise OSError("docs file is unavailable")

    columns = score_context.load_columns(
        _with_status_block(manifest, ["doc.jaffle_shop.orders_status"]),
        catalog,
        read=unreadable,
    )
    assert _column(columns, "orders", "status").location == Location(
        "jaffle-shop/models/docs.md", None
    )


def test_a_description_built_from_several_blocks_points_at_the_schema_line(
    manifest, catalog
):
    # No single block holds the words, so the schema line is the one
    # place that shows how they are put together.
    columns = score_context.load_columns(
        _with_status_block(
            manifest,
            ["doc.jaffle_shop.orders_status", "doc.jaffle_shop.other"],
        ),
        catalog,
        read=_read,
    )
    assert _column(columns, "orders", "status").location == Location(
        "jaffle-shop/models/schema.yml", 18
    )


def test_a_location_never_changes_a_grade(manifest, catalog):
    # Locations are for navigation only (FR-004).
    plain = score_context.load_columns(manifest, catalog)
    linked = score_context.load_columns(
        _with_paths(manifest), catalog, read=_read
    )
    assert score_context.grade_all(plain) == score_context.grade_all(linked)


def test_columns_load_without_paths_and_carry_no_location(manifest, catalog):
    columns = score_context.load_columns(manifest, catalog)
    assert {c.location for c in columns} == {None}


def _report(columns, rubric_path):
    rubric = score_context.load_rubric(rubric_path)
    return score_context.render_report(
        "abc1234", rubric, columns, score_context.grade_all(columns)
    )


def _relocated(columns, pick, location):
    return [replace(c, location=location) if pick(c) else c for c in columns]


def test_the_column_table_links_relative_to_the_results_folder(
    manifest, catalog, filled_rubric
):
    columns = _relocated(
        score_context.load_columns(manifest, catalog),
        lambda c: (c.model, c.name) == ("customers", "customer_id"),
        Location("jaffle-shop/models/schema.yml", 8),
    )
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
    columns = _relocated(
        score_context.load_columns(manifest, catalog),
        lambda c: c.status == "stale",
        Location("jaffle-shop/models/schema.yml", 20),
    )
    assert (
        "[`customers.total_order_amount`]"
        "(../jaffle-shop/models/schema.yml#L20)"
        in _report(columns, filled_rubric)
    )


def test_a_file_link_without_a_line_has_no_anchor(
    manifest, catalog, filled_rubric
):
    columns = _relocated(
        score_context.load_columns(manifest, catalog),
        lambda c: (
            (c.model, c.name) == ("customers", "customer_lifetime_value")
        ),
        Location("jaffle-shop/models/customers.sql"),
    )
    assert (
        "[customer_lifetime_value](../jaffle-shop/models/customers.sql)|"
        in _report(columns, filled_rubric)
    )


def test_a_stale_column_points_at_the_line_that_still_describes_it(
    manifest, catalog
):
    # total_order_amount is documented and no longer built. The schema
    # line is what the author has to delete.
    schema = (
        "models:\n"
        "  - name: customers\n"
        "    columns:\n"
        "      - name: customer_id\n"
        "      - name: total_order_amount\n"
    )
    columns = score_context.load_columns(
        _with_paths(manifest), catalog, read=lambda path: schema
    )
    stale = _column(columns, "customers", "total_order_amount")
    assert (stale.status, stale.location) == (
        "stale",
        Location("jaffle-shop/models/schema.yml", 5),
    )


def test_a_model_with_no_schema_file_points_at_its_sql(manifest, catalog):
    manifest["nodes"][ORDERS]["original_file_path"] = "models/orders.sql"
    columns = score_context.load_columns(manifest, catalog, read=_read)
    assert {c.location for c in columns if c.model == "orders"} == {
        Location("jaffle-shop/models/orders.sql")
    }


def test_an_unreadable_file_costs_the_line_and_not_the_run(manifest, catalog):
    # Links are for navigation. A missing schema file must never stop a
    # scorecard whose grades come from the manifest (FR-004).
    def unreadable(path):
        raise FileNotFoundError(path)

    columns = score_context.load_columns(
        _with_paths(manifest), catalog, read=unreadable
    )
    assert _column(columns, "customers", "customer_id").location == Location(
        "jaffle-shop/models/schema.yml", None
    )
