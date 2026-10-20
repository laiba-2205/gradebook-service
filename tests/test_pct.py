import gradebook


def test_student_with_no_marks_has_zero_percentage(loaded) -> None:
    result = gradebook.pct("S1")

    assert result == "0"


def test_mark_percentage_uses_assessment_weight(loaded) -> None:
    loaded["marks"].append(
        {"student": "S1", "assessment": "A1", "score": 15, "at": ""}
    )

    result = gradebook.pct("S1")

    assert result == "7.5"


def test_mark_for_unknown_assessment_is_ignored(loaded) -> None:
    loaded["marks"].append(
        {"student": "S1", "assessment": "UNKNOWN", "score": 15, "at": ""}
    )

    result = gradebook.pct("S1")

    assert result == "0"
