"""Exit codes and the no-file-on-failure rule (contracts/cli.md).

A report written from an unwritten rubric or a failed dbt run would
publish a number with nothing behind it, so both must stop before any
file exists.
"""

import pytest

import score_context
from tests.conftest import FILLED_RUBRIC


@pytest.fixture
def results(tmp_path, monkeypatch):
    path = tmp_path / "results"
    monkeypatch.setattr(score_context, "RESULTS_DIR", path)
    return path


def test_an_unwritten_rubric_exits_2_names_the_section_and_writes_nothing(
    tmp_path, monkeypatch, results, capsys
):
    rubric = tmp_path / "rubric.md"
    rubric.write_text(
        FILLED_RUBRIC.replace(
            "Says which rows to exclude by default.",
            "<!-- YOU WRITE: one sentence -->",
        )
    )
    monkeypatch.setattr(score_context, "RUBRIC_PATH", rubric)

    assert score_context.main() == 2
    assert "default_filter" in capsys.readouterr().err
    assert not results.exists()


def test_a_failed_dbt_refresh_exits_3_and_writes_nothing(
    filled_rubric, monkeypatch, results, capsys
):
    def fail():
        raise score_context.RefreshFailed("dbt build failed:\nboom")

    monkeypatch.setattr(score_context, "RUBRIC_PATH", filled_rubric)
    monkeypatch.setattr(score_context, "refresh_dbt", fail)

    assert score_context.main() == 3
    assert "boom" in capsys.readouterr().err
    assert not results.exists()
