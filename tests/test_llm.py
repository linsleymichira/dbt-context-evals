"""The optional model grader (spec User Story 3, research.md R8).

The published numbers are the rule grades. The model is a second opinion
shown beside them, so it must stay off unless asked for, must stop before
any file exists when it cannot run, and must never move a pass rate.
"""

import json
import sys
from types import SimpleNamespace

import pytest

import score_context

JUDGMENT_PARTS = {"business_meaning", "interpretation_guidance"}


class FakeAnthropic:
    """Stands in for the anthropic module and records every request."""

    def __init__(self):
        self.api_keys = []
        self.requests = []
        self.messages = SimpleNamespace(create=self._create)

    def Anthropic(self, api_key):
        self.api_keys.append(api_key)
        return self

    def _create(self, **request):
        self.requests.append(request)
        reply = json.dumps({"grade": "fail", "reason": "Restates the name."})
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=reply)]
        )


@pytest.fixture
def project(tmp_path, monkeypatch, filled_rubric, manifest, catalog):
    """A scoreable project with dbt and git patched out."""
    target = tmp_path / "jaffle-shop" / "target"
    target.mkdir(parents=True)
    (target / "manifest.json").write_text(json.dumps(manifest))
    (target / "catalog.json").write_text(json.dumps(catalog))
    monkeypatch.setattr(score_context, "PROJECT_DIR", tmp_path / "jaffle-shop")
    monkeypatch.setattr(score_context, "RUBRIC_PATH", filled_rubric)
    monkeypatch.setattr(score_context, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(score_context, "ENV_PATH", tmp_path / ".env")
    monkeypatch.setattr(score_context, "refresh_dbt", lambda: None)
    monkeypatch.setattr(score_context, "commit_label", lambda: "abc1234")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("SCORECARD_MODEL", raising=False)
    return tmp_path


@pytest.fixture
def fake_anthropic(monkeypatch):
    fake = FakeAnthropic()
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    return fake


def _report(project, name="abc1234.md"):
    return (project / "results" / name).read_text()


def _section(report, heading):
    return report.split(f"## {heading}\n")[1].split("\n## ")[0]


def test_the_default_run_never_imports_the_model_package(project, monkeypatch):
    # None in sys.modules makes any `import anthropic` raise, so a
    # default run that reached for the package would crash here.
    monkeypatch.setitem(sys.modules, "anthropic", None)

    assert score_context.main([]) == 0
    assert "Model grade" not in _report(project)


def test_llm_without_the_package_exits_4_names_it_and_writes_nothing(
    project, monkeypatch, capsys
):
    monkeypatch.setitem(sys.modules, "anthropic", None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    assert score_context.main(["--llm"]) == 4
    assert "anthropic" in capsys.readouterr().err
    assert not (project / "results").exists()


def test_llm_without_a_key_exits_4_names_it_and_writes_nothing(
    project, fake_anthropic, capsys
):
    assert score_context.main(["--llm"]) == 4
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err
    assert not (project / "results").exists()
    assert fake_anthropic.requests == []


def test_the_key_can_come_from_the_gitignored_env_file(
    project, fake_anthropic
):
    (project / ".env").write_text("ANTHROPIC_API_KEY=sk-from-file\n")

    assert score_context.main(["--llm"]) == 0
    assert fake_anthropic.api_keys == ["sk-from-file"]


def test_an_empty_key_in_the_env_file_counts_as_missing(
    project, fake_anthropic
):
    # .env.example ships as `ANTHROPIC_API_KEY=`, and copying it
    # unedited must not look like a configured key.
    (project / ".env").write_text("ANTHROPIC_API_KEY=\n")

    assert score_context.main(["--llm"]) == 4


def test_the_model_grades_only_the_two_judgment_parts(
    filled_rubric, manifest, catalog, fake_anthropic
):
    rubric = score_context.load_rubric(filled_rubric)
    columns = score_context.load_columns(manifest, catalog)
    grades = score_context.grade_all(columns)

    model_grades = score_context.grade_with_model(
        fake_anthropic, rubric, columns, grades
    )

    assert {g.part for g in model_grades} == JUDGMENT_PARTS
    assert {g.grader for g in model_grades} == {"model"}
    assert all(g.reason for g in model_grades)


def test_the_model_is_not_asked_about_columns_with_no_description(
    filled_rubric, manifest, catalog, fake_anthropic
):
    # An undocumented column already fails with "no description". A
    # model opinion on empty text would be invented.
    rubric = score_context.load_rubric(filled_rubric)
    columns = score_context.load_columns(manifest, catalog)

    model_grades = score_context.grade_with_model(
        fake_anthropic, rubric, columns, score_context.grade_all(columns)
    )

    documented = {
        (c.model, c.name) for c in columns if c.status == "documented"
    }
    assert {(g.model, g.name) for g in model_grades} == documented


def test_the_prompt_carries_the_rubric_sentence_and_the_description(
    filled_rubric, manifest, catalog, fake_anthropic
):
    rubric = score_context.load_rubric(filled_rubric)
    columns = score_context.load_columns(manifest, catalog)

    score_context.grade_with_model(
        fake_anthropic, rubric, columns, score_context.grade_all(columns)
    )

    prompts = [r["messages"][0]["content"] for r in fake_anthropic.requests]
    assert any(
        "Says what the column means to the business." in prompt
        and "One of placed, shipped, completed" in prompt
        for prompt in prompts
    )


def test_model_grades_never_change_a_rule_grade_or_a_pass_rate(
    project, fake_anthropic, monkeypatch
):
    assert score_context.main([]) == 0
    without = _report(project)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert score_context.main(["--llm"]) == 0
    with_llm = _report(project, "abc1234-llm.md")

    for heading in ("Pass rate by part", "Pass rate by model", "Drift"):
        assert _section(with_llm, heading) == _section(without, heading)
    assert "Model grade" in _section(with_llm, "Columns")
    assert "Restates the name." in _section(with_llm, "Columns")

    def rule_cells(report):
        return [
            line.split("|")[1:9]
            for line in _section(report, "Columns").splitlines()[2:]
        ]

    assert rule_cells(with_llm) == rule_cells(without)


def test_a_model_run_never_overwrites_the_committed_report(
    project, fake_anthropic, monkeypatch
):
    # The report for a commit is byte-identical on every run. Model
    # wording changes run to run, so it goes to its own file.
    assert score_context.main([]) == 0
    committed = _report(project)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    assert score_context.main(["--llm"]) == 0

    assert _report(project) == committed
    assert "Model grade" in _report(project, "abc1234-llm.md")


def test_the_model_id_defaults_and_can_be_overridden(
    project, fake_anthropic, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    score_context.main(["--llm"])
    assert {r["model"] for r in fake_anthropic.requests} == {
        "claude-sonnet-5-5"
    }

    fake_anthropic.requests.clear()
    monkeypatch.setenv("SCORECARD_MODEL", "claude-haiku-5-5")
    score_context.main(["--llm"])
    assert {r["model"] for r in fake_anthropic.requests} == {
        "claude-haiku-5-5"
    }


def test_a_reply_that_is_not_the_expected_json_is_shown_as_unreadable(
    filled_rubric, manifest, catalog, fake_anthropic
):
    # A malformed reply must not be read as a pass or a fail.
    fake_anthropic.messages = SimpleNamespace(
        create=lambda **request: SimpleNamespace(
            content=[SimpleNamespace(type="text", text="Looks fine to me")]
        )
    )
    rubric = score_context.load_rubric(filled_rubric)
    columns = score_context.load_columns(manifest, catalog)

    model_grades = score_context.grade_with_model(
        fake_anthropic, rubric, columns, score_context.grade_all(columns)
    )

    assert {g.outcome for g in model_grades} == {"unreadable"}
