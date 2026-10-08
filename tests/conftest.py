"""Fixture builders shaped like dbt's manifest.json and catalog.json.

The fixture mirrors the real drift in jaffle-shop: a documented column
that is no longer built (stale), built columns with no description
(undocumented), a PII-flagged name, and test-derived key facts.
"""

import pytest

FILLED_RUBRIC = """# Context rubric

Intro text that is not a section.

## 1. Business meaning

Says what the column means to the business.

## 2. Allowed values

Lists every value when the set is closed.

## 3. Interpretation guidance

Names the unit, timezone, or caveat a reader needs.

## 4. Default filter

Says which rows to exclude by default.

## Not applicable

Primary keys skip allowed values and default filter.
"""


def _model(name, columns, package="jaffle_shop"):
    return {
        "resource_type": "model",
        "package_name": package,
        "name": name,
        "columns": {
            col: {"name": col, "description": desc}
            for col, desc in columns.items()
        },
    }


def _test(test_name, model_id, column):
    return {
        "resource_type": "test",
        "test_metadata": {"name": test_name, "kwargs": {}},
        "attached_node": model_id,
        "column_name": column,
    }


CUSTOMERS = "model.jaffle_shop.customers"
ORDERS = "model.jaffle_shop.orders"


@pytest.fixture
def manifest():
    return {
        "nodes": {
            CUSTOMERS: _model(
                "customers",
                {
                    "customer_id": "Unique identifier for a customer",
                    "first_name": "Customer's first name. PII.",
                    "total_order_amount": "Total value of orders",
                    "blank_col": "   ",
                },
            ),
            ORDERS: _model(
                "orders",
                {
                    "order_id": "Unique identifier for an order",
                    "status": "One of placed, shipped, completed",
                    "customer_id": "",
                },
            ),
            "model.other_pkg.thing": _model(
                "thing", {"x": "From another package"}, "other_pkg"
            ),
            "test.u1": _test("unique", CUSTOMERS, "customer_id"),
            "test.n1": _test("not_null", CUSTOMERS, "customer_id"),
            "test.n2": _test("not_null", ORDERS, "order_id"),
            "test.r1": _test("relationships", ORDERS, "customer_id"),
            "test.a1": _test("accepted_values", ORDERS, "status"),
        }
    }


@pytest.fixture
def catalog():
    def cols(spec):
        return {name: {"name": name, "type": t} for name, t in spec.items()}

    return {
        "nodes": {
            CUSTOMERS: {
                "columns": cols(
                    {
                        "customer_id": "INTEGER",
                        "first_name": "VARCHAR",
                        "blank_col": "VARCHAR",
                        "customer_lifetime_value": "DOUBLE",
                    }
                )
            },
            ORDERS: {
                "columns": cols(
                    {
                        "ORDER_ID": "INTEGER",
                        "status": "VARCHAR",
                        "customer_id": "INTEGER",
                    }
                )
            },
        }
    }


@pytest.fixture
def filled_rubric(tmp_path):
    path = tmp_path / "rubric.md"
    path.write_text(FILLED_RUBRIC)
    return path
