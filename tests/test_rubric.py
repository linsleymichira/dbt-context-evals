"""The rubric is the user's standard (constitution Principle I).

Grading against a section nobody wrote would publish numbers for
criteria that do not exist, so an unwritten section must stop the run.
"""

import pytest

import score_context
from conftest import FILLED_RUBRIC

PLACEHOLDER = "<!-- YOU WRITE: one sentence on what passes. -->"


def test_filled_rubric_returns_each_part_sentence_keyed_by_part(
    filled_rubric,
):
    rubric = score_context.load_rubric(filled_rubric)

    assert rubric == {
        "business_meaning": "Says what the column means to the business.",
        "allowed_values": "Lists every value when the set is closed.",
        "interpretation_guidance": (
            "Names the unit, timezone, or caveat a reader needs."
        ),
        "default_filter": "Says which rows to exclude by default.",
        "not_applicable": (
            "Primary keys skip allowed values and default filter."
        ),
    }


def test_every_unwritten_section_is_named_so_the_user_knows_what_is_left(
    tmp_path,
):
    text = FILLED_RUBRIC.replace(
        "Lists every value when the set is closed.", PLACEHOLDER
    ).replace(
        "Primary keys skip allowed values and default filter.", PLACEHOLDER
    )
    path = tmp_path / "rubric.md"
    path.write_text(text)

    with pytest.raises(score_context.RubricUnwritten) as err:
        score_context.load_rubric(path)

    assert err.value.sections == ("allowed_values", "not_applicable")


def test_a_missing_section_counts_as_unwritten(tmp_path):
    text = FILLED_RUBRIC.split("## 4. Default filter")[0]
    path = tmp_path / "rubric.md"
    path.write_text(text)

    with pytest.raises(score_context.RubricUnwritten) as err:
        score_context.load_rubric(path)

    assert err.value.sections == ("default_filter", "not_applicable")


def test_the_real_unwritten_rubric_is_refused():
    with pytest.raises(score_context.RubricUnwritten):
        score_context.load_rubric(score_context.REPO_ROOT / "rubric.md")
