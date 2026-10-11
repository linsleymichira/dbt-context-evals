"""The scorecard's own sentences (spec 002, User Story 4).

The report is the first page a reader opens after the README, so the
text the scorecard writes on its own follows the same writing rules:
one term for one thing, short sentences, and a warning that gives a
command before its reason. Quoted rubric and sample text is exempt.
"""

import re

import score_context

MAX_WORDS = 25


def _report(manifest, catalog, filled_rubric, label="abc1234"):
    rubric = score_context.load_rubric(filled_rubric)
    columns = score_context.load_columns(manifest, catalog)
    grades = score_context.grade_all(columns)
    return score_context.render_report(label, rubric, columns, grades)


def _own_sentences(report):
    """Sentences outside tables and headings, which the scorecard wrote."""
    prose = [
        line
        for line in report.splitlines()
        if line and not line.startswith(("|", "#", "Undocumented", "Stale"))
    ]
    return [
        sentence
        for line in prose
        for sentence in re.split(r"(?<=[.:])\s+", line)
        if sentence
    ]


def test_the_notice_uses_one_word_for_what_the_scorecard_applies(
    manifest, catalog, filled_rubric
):
    notice = _report(manifest, catalog, filled_rubric).split("## Rubric")[0]

    assert "rule" in notice
    assert "check" not in notice


def test_the_dirty_warning_gives_a_command_and_then_the_reason(
    manifest, catalog, filled_rubric
):
    report = _report(manifest, catalog, filled_rubric, "abc1234-dirty")

    warning = report.splitlines()[2]
    assert warning.startswith("Warning: do not cite this report.")
    assert "uncommitted changes" in warning.split(". ", 1)[1]


def test_a_clean_report_has_no_warning(manifest, catalog, filled_rubric):
    assert "Warning" not in _report(manifest, catalog, filled_rubric)


def test_no_sentence_of_the_scorecard_passes_25_words(
    manifest, catalog, filled_rubric
):
    report = _report(manifest, catalog, filled_rubric, "abc1234-dirty")

    for sentence in _own_sentences(report):
        assert len(sentence.split()) <= MAX_WORDS, sentence


def test_every_rule_summary_sentence_is_25_words_at_most():
    for summary in score_context.RULE_SUMMARIES.values():
        for sentence in re.split(r"(?<=[.:])\s+", summary):
            assert len(sentence.split()) <= MAX_WORDS, sentence


def test_a_reason_shared_by_several_parts_is_written_once(
    manifest, catalog, filled_rubric
):
    # An undescribed column fails every part for one reason. Saying it
    # four times buries the rows that fail for different reasons.
    report = _report(manifest, catalog, filled_rubric)

    row = next(
        line
        for line in report.splitlines()
        if line.startswith("|customers|customer_lifetime_value|")
    )
    assert row.count("no description") == 1
    assert (
        "Business meaning, Allowed values, Interpretation guidance, "
        "Default filter: no description" in row
    )


def test_different_reasons_stay_separate(manifest, catalog, filled_rubric):
    report = _report(manifest, catalog, filled_rubric)

    row = next(
        line
        for line in report.splitlines()
        if line.startswith("|customers|customer_id|")
    )
    assert "Business meaning: key names no table it joins to" in row
    assert "Interpretation guidance: names no case" in row
