"""Every report names the commit it scored (Principle II, SC-005).

Descriptions, the rubric, and the scorecard code all change grades, so a
report produced with any of them uncommitted must not carry a clean
hash. Only new reports in results/ are exempt, since writing one is the
point of the run.
"""

import subprocess

import pytest

import score_context


def _fake_git(status_lines):
    def run(cmd, **kwargs):
        out = "abc1234\n" if "rev-parse" in cmd else "\n".join(status_lines)
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")

    return run


@pytest.mark.parametrize(
    "status_lines, expected",
    [
        ([], "abc1234"),
        (["?? results/abc1234.md"], "abc1234"),
        ([" M results/old.md"], "abc1234"),
        ([" M jaffle-shop/models/schema.yml"], "abc1234-dirty"),
        ([" M rubric.md"], "abc1234-dirty"),
        ([" M score_context.py"], "abc1234-dirty"),
        (["?? tests/test_new.py"], "abc1234-dirty"),
    ],
)
def test_label_is_dirty_for_any_change_outside_results(
    monkeypatch, status_lines, expected
):
    monkeypatch.setattr(
        score_context.subprocess, "run", _fake_git(status_lines)
    )

    assert score_context.commit_label() == expected
