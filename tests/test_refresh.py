"""Every run refreshes dbt output first (FR-012, research R1).

Grading old artifacts would put stale numbers into a committed report,
and a failed build means the descriptions are not valid (Principle III),
so a dbt failure must stop the run with dbt's own output.
"""

import subprocess

import pytest

import score_context


class FakeRun:
    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on

    def __call__(self, cmd, **kwargs):
        self.calls.append((cmd, kwargs))
        code = 1 if self.fail_on and self.fail_on in cmd else 0
        return subprocess.CompletedProcess(
            cmd, code, stdout=f"out of {cmd[1]}", stderr="boom"
        )


def test_build_runs_before_docs_generate_inside_the_project(monkeypatch):
    fake = FakeRun()
    monkeypatch.setattr(score_context.subprocess, "run", fake)

    score_context.refresh_dbt()

    commands = [cmd[1:] for cmd, _ in fake.calls]
    assert commands == [["build"], ["docs", "generate"]]
    for cmd, kwargs in fake.calls:
        assert cmd[0].endswith("dbt")
        # profiles.yml uses a relative DuckDB path, so dbt must run with
        # the project as its working directory.
        assert kwargs["cwd"] == score_context.PROJECT_DIR


@pytest.mark.parametrize("failing", ["build", "generate"])
def test_a_failing_dbt_step_stops_the_run_with_its_output(
    monkeypatch, failing
):
    fake = FakeRun(fail_on=failing)
    monkeypatch.setattr(score_context.subprocess, "run", fake)

    with pytest.raises(score_context.RefreshFailed) as err:
        score_context.refresh_dbt()

    assert "boom" in str(err.value)


def test_docs_generate_is_skipped_when_build_fails(monkeypatch):
    fake = FakeRun(fail_on="build")
    monkeypatch.setattr(score_context.subprocess, "run", fake)

    with pytest.raises(score_context.RefreshFailed):
        score_context.refresh_dbt()

    assert len(fake.calls) == 1
