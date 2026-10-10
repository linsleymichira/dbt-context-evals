"""Drift between what dbt built and what the docs describe (User Story 2).

An undocumented column gives an agent nothing, so it must count against
coverage. A stale entry describes a column that no longer exists, so it
must be listed and must not be graded.
"""

import re

import score_context


def _graded(manifest, catalog):
    columns = score_context.load_columns(manifest, catalog)
    return columns, score_context.grade_all(columns)


def test_an_undocumented_column_fails_every_applicable_part(manifest, catalog):
    _, grades = _graded(manifest, catalog)

    lifetime_value = [g for g in grades if g.name == "customer_lifetime_value"]
    assert [g.outcome for g in lifetime_value] == ["fail"] * 4
    assert all("no description" in g.reason for g in lifetime_value)


def test_an_undocumented_key_still_skips_its_not_applicable_parts(
    manifest, catalog
):
    _, grades = _graded(manifest, catalog)

    outcomes = {
        g.part: g.outcome
        for g in grades
        if (g.model, g.name) == ("orders", "customer_id")
    }
    assert outcomes == {
        "business_meaning": "fail",
        "allowed_values": "n/a",
        "interpretation_guidance": "fail",
        "default_filter": "n/a",
    }


def test_a_stale_column_is_listed_but_never_graded(
    manifest, catalog, filled_rubric
):
    columns, grades = _graded(manifest, catalog)
    report = score_context.render_report(
        "abc1234", score_context.load_rubric(filled_rubric), columns, grades
    )
    drift = re.search(
        r"^## Drift\n(.*?)(?=^## )", report, flags=re.M | re.S
    ).group(1)

    assert not [g for g in grades if g.name == "total_order_amount"]
    assert "Stale (1): `customers.total_order_amount`" in drift
    assert "Undocumented (3)" in drift
    assert "`customers.customer_lifetime_value`" in drift
