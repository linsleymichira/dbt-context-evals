"""The data file beside the report (spec 002, User Story 2).

A later tool drafts a fix from a failing grade. It needs the item, the
reason and the location as fields, and it must never see a number the
Markdown report does not show.
"""

import json

import pytest

import score_context

SCHEMA = """version: 2

models:
  - name: customers
    description: Basic facts about a customer.
    columns:
      - name: customer_id
        description: Unique identifier for a customer
      - name: first_name
        description: Customer's first name. PII.
      - name: total_order_amount
        description: Total value of orders
      - name: blank_col
        description: "   "

  - name: orders
    columns:
      - name: order_id
        description: Unique identifier for an order
      - name: status
        description: One of placed, shipped, completed
      - name: customer_id
"""


@pytest.fixture
def located(manifest):
    """The fixture manifest with each model tied to SCHEMA."""
    for model in ("customers", "orders"):
        node = manifest["nodes"][f"model.jaffle_shop.{model}"]
        node["patch_path"] = "jaffle_shop://models/schema.yml"
        node["original_file_path"] = f"models/{model}.sql"
    return manifest


@pytest.fixture
def inputs(located, catalog, filled_rubric):
    rubric = score_context.load_rubric(filled_rubric)
    columns = score_context.load_columns(located, catalog, lambda _: SCHEMA)
    return "abc1234", rubric, columns, score_context.grade_all(columns)


def _column(result, model, name):
    return next(
        c
        for c in result["columns"]
        if (c["model"], c["column"]) == (model, name)
    )


def test_the_result_names_the_commit_and_the_schema(inputs):
    result = score_context.build_result(*inputs)

    assert result["schema_version"] == 1
    assert result["commit"] == "abc1234"
    assert result["dirty"] is False
    assert score_context.build_result("abc1234-dirty", *inputs[1:])["dirty"]


def test_each_rubric_part_carries_its_sentence_and_its_rule(inputs):
    result = score_context.build_result(*inputs)

    assert result["rubric"][0] == {
        "part": "business_meaning",
        "applies_to": "column",
        "sentence": "Says what the column means to the business.",
        "rule": score_context.RULE_SUMMARIES["business_meaning"],
        "heuristic": True,
    }
    assert [r["part"] for r in result["rubric"]] == list(
        score_context.RUBRIC_SECTIONS
    )


def test_a_failing_column_carries_its_reason_and_its_location(inputs):
    column = _column(
        score_context.build_result(*inputs), "customers", "customer_id"
    )

    assert column["status"] == "documented"
    assert column["location"] == {
        "path": "jaffle-shop/models/schema.yml",
        "line": 7,
    }
    assert column["grades"]["business_meaning"] == {
        "outcome": "fail",
        "reason": "key names no table it joins to",
    }
    assert column["grades"]["default_filter"]["outcome"] == "n/a"


def test_a_column_with_no_location_says_so(manifest, catalog, filled_rubric):
    rubric = score_context.load_rubric(filled_rubric)
    columns = score_context.load_columns(manifest, catalog)

    result = score_context.build_result(
        "abc1234", rubric, columns, score_context.grade_all(columns)
    )

    assert {c["location"] for c in result["columns"]} == {None}


def test_a_stale_column_is_listed_with_no_grades(inputs):
    result = score_context.build_result(*inputs)

    stale = [c for c in result["columns"] if c["status"] == "stale"]
    assert [c["column"] for c in stale] == ["total_order_amount"]
    assert stale[0]["grades"] == {}
    assert result["drift"]["stale_columns"] == ["customers.total_order_amount"]
    assert len(result["drift"]["undocumented_columns"]) == 3


def test_a_part_with_nothing_applicable_has_no_rate(inputs):
    label, rubric, columns, grades = inputs
    skipped = tuple(g for g in grades if g.outcome == "n/a")

    result = score_context.build_result(label, rubric, columns, skipped)

    assert {r["rate"] for r in result["pass_rates"]["by_part"]} == {None}


def test_the_json_text_is_identical_on_every_render(inputs):
    first = score_context.render_json(score_context.build_result(*inputs))
    second = score_context.render_json(score_context.build_result(*inputs))

    assert first == second
    assert first.endswith("}\n")
    assert json.loads(first)["commit"] == "abc1234"


def test_the_data_file_and_the_report_agree(inputs):
    # Two files that can disagree are worse than one.
    result = score_context.build_result(*inputs)
    report = score_context.render_report(*inputs)

    for rate in result["pass_rates"]["by_part"]:
        title = score_context.PART_TITLES[rate["part"]]
        assert (
            f"|{title}|{rate['passed']}|{rate['applicable']}|{rate['rate']}%|"
            in report
        )
    for rate in result["pass_rates"]["by_model"]:
        assert (
            f"|{rate['model']}|{rate['passed']}|{rate['applicable']}|"
            f"{rate['rate']}%|" in report
        )
    rows = report.split("## Columns\n")[1].split("\n## ")[0].splitlines()
    graded = [c for c in result["columns"] if c["status"] != "stale"]
    assert len(rows) - 3 == len(graded)
    for column in graded:
        model, name = column["model"], column["column"]
        row = next(
            line
            for line in rows
            if line.startswith((f"|{model}|[{name}](", f"|{model}|{name}|"))
        )
        outcomes = [g["outcome"] for g in column["grades"].values()]
        assert "|" + "|".join(outcomes) + "|" in row
        for grade in column["grades"].values():
            assert grade["reason"] in row
        assert column["location"]["path"] in row


def test_a_default_run_writes_the_report_and_the_data_file(
    located, catalog, filled_rubric, tmp_path, monkeypatch
):
    project = tmp_path / "jaffle-shop"
    (project / "target").mkdir(parents=True)
    (project / "models").mkdir()
    (project / "models" / "schema.yml").write_text(SCHEMA)
    (project / "target" / "manifest.json").write_text(json.dumps(located))
    (project / "target" / "catalog.json").write_text(json.dumps(catalog))
    monkeypatch.setattr(score_context, "PROJECT_DIR", project)
    monkeypatch.setattr(score_context, "RUBRIC_PATH", filled_rubric)
    monkeypatch.setattr(score_context, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(score_context, "refresh_dbt", lambda: None)
    monkeypatch.setattr(score_context, "commit_label", lambda: "abc1234")

    assert score_context.main([]) == 0

    names = sorted(p.name for p in (tmp_path / "results").iterdir())
    assert names == ["abc1234.json", "abc1234.md"]
    data = json.loads((tmp_path / "results" / "abc1234.json").read_text())
    assert _column(data, "customers", "blank_col")["location"]["line"] == 13
    assert str(tmp_path) not in json.dumps(data)
