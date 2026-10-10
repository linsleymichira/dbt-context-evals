"""The report is what the user reads aloud and publishes (FR-003, FR-005,
FR-007, FR-008, FR-011, SC-004).

A pass rate that counts n/a grades, a fail with no reason, or output
that changes between runs would each make the published number
impossible to defend.
"""

import re

import score_context


def _report(manifest, catalog, rubric_path, label="abc1234"):
    rubric = score_context.load_rubric(rubric_path)
    columns = score_context.load_columns(manifest, catalog)
    grades = score_context.grade_all(columns)
    return score_context.render_report(label, rubric, columns, grades)


def _section(report, heading):
    match = re.search(
        rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)",
        report,
        flags=re.M | re.S,
    )
    assert match, f"missing section: {heading}"
    return match.group(1)


def _rows(section):
    return [
        [cell.strip() for cell in line.strip("|").split("|")]
        for line in section.splitlines()
        if line.startswith("|") and not line.startswith("|---")
    ][1:]


def test_pass_rate_by_part_leaves_not_applicable_out_of_the_denominator(
    manifest, catalog, filled_rubric
):
    rates = {
        row[0]: row
        for row in _rows(
            _section(
                _report(manifest, catalog, filled_rubric), "Pass rate by part"
            )
        )
    }

    # 7 graded columns. 2 are keys and 2 are free text, which leaves
    # customer_lifetime_value, order_id and status applicable.
    assert rates["Allowed values"][1:3] == ["1", "3"]
    # Keys skip the default filter, the other 5 columns do not.
    assert rates["Default filter"][1:3] == ["0", "5"]
    assert rates["Business meaning"][1:3] == ["1", "7"]


def test_pass_rate_by_model_counts_applicable_grades_only(
    manifest, catalog, filled_rubric
):
    rates = {
        row[0]: row
        for row in _rows(
            _section(
                _report(manifest, catalog, filled_rubric), "Pass rate by model"
            )
        )
    }

    # customers: 1 key (2 applicable) + 2 free text (3 each) + 1 numeric (4)
    assert rates["customers"][1:3] == ["0", "12"]
    # orders: 1 key (2) + order_id (4, not_null alone is no key) + status (4)
    assert rates["orders"][1:3] == ["2", "10"]


def test_every_fail_in_the_column_table_shows_its_reason(
    manifest, catalog, filled_rubric
):
    rows = _rows(
        _section(_report(manifest, catalog, filled_rubric), "Columns")
    )

    assert len(rows) == 7
    for row in rows:
        fails = row[3:7].count("fail")
        assert (fails > 0) == bool(row[7])


def test_a_pii_column_is_flagged_in_the_column_table(
    manifest, catalog, filled_rubric
):
    rows = {
        (row[0], row[1]): row
        for row in _rows(
            _section(_report(manifest, catalog, filled_rubric), "Columns")
        )
    }

    assert rows[("customers", "first_name")][2] == "PII"
    assert rows[("orders", "status")][2] == ""


def test_rows_sort_by_model_then_column(manifest, catalog, filled_rubric):
    rows = _rows(
        _section(_report(manifest, catalog, filled_rubric), "Columns")
    )

    keys = [(row[0], row[1]) for row in rows]
    assert keys == sorted(keys)


def test_the_rubric_table_puts_the_users_sentence_beside_the_rule(
    manifest, catalog, filled_rubric
):
    rows = _rows(_section(_report(manifest, catalog, filled_rubric), "Rubric"))

    by_part = {row[0]: row for row in rows}
    assert by_part["Business meaning"][1] == (
        "Says what the column means to the business."
    )
    assert (
        by_part["Business meaning"][2]
        == (score_context.RULE_SUMMARIES["business_meaning"])
    )
    assert by_part["Business meaning"][3] == "yes"
    assert by_part["Allowed values"][3] == "no"
    assert "Not applicable" in by_part


def test_the_heuristic_notice_is_always_present(
    manifest, catalog, filled_rubric
):
    report = _report(manifest, catalog, filled_rubric)

    assert "heuristic" in report.split("## Rubric")[0].lower()


def test_a_dirty_label_adds_a_warning_line(manifest, catalog, filled_rubric):
    clean = _report(manifest, catalog, filled_rubric)
    dirty = _report(manifest, catalog, filled_rubric, label="abc1234-dirty")

    assert "uncommitted" not in clean
    assert "uncommitted" in dirty


def test_output_is_identical_across_runs_and_carries_no_time_or_path(
    manifest, catalog, filled_rubric
):
    first = _report(manifest, catalog, filled_rubric)
    second = _report(manifest, catalog, filled_rubric)

    assert first == second
    assert str(filled_rubric.parent) not in first
    assert "/Users/" not in first
    assert not re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}:\d{2}", first)


# --- examples (FR-008) ----------------------------------------------------


def test_examples_are_3_to_5_columns_with_a_pass_and_a_fail(manifest, catalog):
    columns = score_context.load_columns(manifest, catalog)
    grades = score_context.grade_all(columns)

    examples = score_context.select_examples(columns, grades)

    assert 3 <= len(examples) <= 5
    picked = {(c.model, c.name) for c in examples}
    outcomes = {g.outcome for g in grades if (g.model, g.name) in picked}
    assert {"pass", "fail"} <= outcomes


def test_examples_are_the_same_picks_on_every_run(manifest, catalog):
    columns = score_context.load_columns(manifest, catalog)
    grades = score_context.grade_all(columns)

    first = score_context.select_examples(columns, grades)
    second = score_context.select_examples(
        tuple(reversed(columns)), tuple(reversed(grades))
    )

    assert first == second


def test_examples_appear_in_the_report(manifest, catalog, filled_rubric):
    rows = _rows(
        _section(_report(manifest, catalog, filled_rubric), "Examples")
    )

    assert 3 <= len(rows) <= 5
