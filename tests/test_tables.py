"""Table descriptions are graded too (spec 002, User Story 3).

An agent picks a table before it picks a column. A table description
that does not say what one row is can send every later answer wrong, so
each model gets its own grades, and those grades never move a column
pass rate.
"""

import pytest

import score_context
from tests.conftest import FILLED_RUBRIC

SCHEMA = """version: 2

models:
  - name: customers
    description: One row per customer.
    columns:
      - name: customer_id
        description: Unique identifier for a customer

  - name: orders
    columns:
      - name: order_id
        description: Unique identifier for an order
"""

GOOD = (
    "One row per customer. Built from the staging models. "
    "Excludes customers with no orders."
)


def _table(description, model="customers"):
    status = "documented" if description.strip() else "undocumented"
    return score_context.Table(model, status, description.strip(), None)


def _outcomes(description):
    return {
        grade.part: (grade.outcome, grade.reason)
        for grade in score_context.grade_table(_table(description))
    }


@pytest.mark.parametrize(
    ("part", "passing", "failing"),
    [
        (
            "table_grain",
            "One row per customer.",
            "Basic information about a customer.",
        ),
        (
            "table_source",
            "Built from the staging models.",
            "Basic information about a customer.",
        ),
        (
            "table_scope",
            "Excludes customers with no orders.",
            "Basic information about a customer.",
        ),
    ],
)
def test_each_table_part_passes_on_its_phrase_and_fails_without_it(
    part, passing, failing
):
    assert _outcomes(passing)[part] == ("pass", "")
    outcome, reason = _outcomes(failing)[part]
    assert outcome == "fail"
    assert reason


def test_one_part_passing_does_not_pass_another():
    outcomes = _outcomes("One row per customer.")

    assert outcomes["table_source"][0] == "fail"
    assert outcomes["table_scope"][0] == "fail"


@pytest.fixture
def located(manifest):
    """Both models tied to SCHEMA. Only customers has a description."""
    for model, description in (("customers", GOOD), ("orders", "   ")):
        node = manifest["nodes"][f"model.jaffle_shop.{model}"]
        node["description"] = description
        node["patch_path"] = "jaffle_shop://models/schema.yml"
        node["original_file_path"] = f"models/{model}.sql"
    return manifest


@pytest.fixture
def inputs(located, catalog, filled_rubric):
    rubric = score_context.load_rubric(filled_rubric)
    columns = score_context.load_columns(located, catalog, lambda _: SCHEMA)
    tables = score_context.load_tables(located, lambda _: SCHEMA)
    return (
        ("abc1234", rubric, columns, score_context.grade_all(columns)),
        tables,
        score_context.grade_tables(tables),
    )


def test_tables_come_from_this_package_only_with_their_location(located):
    tables = score_context.load_tables(located, lambda _: SCHEMA)

    assert [(t.model, t.status) for t in tables] == [
        ("customers", "documented"),
        ("orders", "undocumented"),
    ]
    assert tables[0].location == score_context.Location(
        "jaffle-shop/models/schema.yml", 4
    )
    assert tables[1].location == score_context.Location(
        "jaffle-shop/models/schema.yml", 10
    )


def test_a_model_with_no_documentation_file_links_to_its_query(manifest):
    node = manifest["nodes"]["model.jaffle_shop.customers"]
    node["original_file_path"] = "models/customers.sql"

    tables = score_context.load_tables(manifest)

    assert tables[0].location == score_context.Location(
        "jaffle-shop/models/customers.sql"
    )


def test_an_undocumented_table_fails_every_part_and_joins_the_drift(inputs):
    args, tables, table_grades = inputs

    orders = [g for g in table_grades if g.model == "orders"]
    assert [(g.outcome, g.reason) for g in orders] == [
        ("fail", "no description")
    ] * 3

    result = score_context.build_result(
        *args, tables=tables, table_grades=table_grades
    )
    assert result["drift"]["undocumented_tables"] == ["orders"]
    report = score_context.render_report(
        *args, tables=tables, table_grades=table_grades
    )
    assert (
        "Undocumented tables (1): "
        "[`orders`](../jaffle-shop/models/schema.yml#L10)"
    ) in report
    assert "Table grain, Table source, Table scope: no description" in report


def test_an_unwritten_table_section_stops_the_run_and_is_named(tmp_path):
    path = tmp_path / "rubric.md"
    path.write_text(FILLED_RUBRIC.split("## Table scope")[0])

    with pytest.raises(score_context.RubricUnwritten) as stopped:
        score_context.load_rubric(path)

    assert stopped.value.sections == ("table_scope",)


def test_table_grades_never_move_a_column_pass_rate(inputs):
    args, tables, table_grades = inputs

    without = score_context.build_result(*args)
    with_tables = score_context.build_result(
        *args, tables=tables, table_grades=table_grades
    )

    assert (
        with_tables["pass_rates"]["by_part"]
        == (without["pass_rates"]["by_part"])
    )
    assert (
        with_tables["pass_rates"]["by_model"]
        == (without["pass_rates"]["by_model"])
    )
    assert with_tables["columns"] == without["columns"]
    assert with_tables["pass_rates"]["table_parts"] == [
        {"part": "table_grain", "passed": 1, "applicable": 2, "rate": 50},
        {"part": "table_source", "passed": 1, "applicable": 2, "rate": 50},
        {"part": "table_scope", "passed": 1, "applicable": 2, "rate": 50},
    ]


def test_the_data_file_and_the_report_hold_the_same_table_grades(inputs):
    args, tables, table_grades = inputs

    result = score_context.build_result(
        *args, tables=tables, table_grades=table_grades
    )
    report = score_context.render_report(
        *args, tables=tables, table_grades=table_grades
    )

    assert [t["model"] for t in result["tables"]] == ["customers", "orders"]
    customers = result["tables"][0]
    assert customers["description"] == GOOD
    assert customers["location"] == {
        "path": "jaffle-shop/models/schema.yml",
        "line": 4,
    }
    assert {g["outcome"] for g in customers["grades"].values()} == {"pass"}
    assert "## Pass rate by table part" in report
    assert (
        "|[customers](../jaffle-shop/models/schema.yml#L4)|pass|pass|pass||"
    ) in report
    assert report.index("## Tables") < report.index("## Columns")


def test_each_table_rule_prints_beside_its_sentence_marked_if_heuristic(
    inputs,
):
    args, tables, table_grades = inputs

    result = score_context.build_result(
        *args, tables=tables, table_grades=table_grades
    )
    report = score_context.render_report(
        *args, tables=tables, table_grades=table_grades
    )

    table_rows = [r for r in result["rubric"] if r["applies_to"] == "table"]
    assert [(r["part"], r["heuristic"]) for r in table_rows] == [
        ("table_grain", True),
        ("table_source", True),
        ("table_scope", True),
    ]
    for row in table_rows:
        assert row["sentence"] in report
        assert row["rule"] in report
    assert all(
        r["applies_to"] == "column"
        for r in result["rubric"]
        if r not in table_rows
    )
