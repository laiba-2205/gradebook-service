import gradebook
import pytest


@pytest.mark.parametrize(
    ("marks", "expected"),
    [
        ([], "0"),
        ([{"student": "S1", "assessment": "A1", "score": 15, "at": ""}], "7.5"),
        ([{"student": "S1", "assessment": "A1", "score": 20, "at": ""}], "10.0"),
        ([{"student": "S1", "assessment": "A1", "score": 0, "at": ""}], "0.0"),
        (
            [
                {"student": "S1", "assessment": "A1", "score": 15, "at": ""},
                {"student": "S1", "assessment": "A2", "score": 40, "at": ""},
            ],
            "31.5",
        ),
    ],
    ids=["no-marks", "A1-score-15", "A1-score-20", "A1-score-0", "A1-and-A2"],
)
def test_percentage_for_marks(loaded, marks: list[dict], expected: str) -> None:
    loaded["marks"].extend(marks)

    result = gradebook.pct("S1")

    assert result == expected


def test_mark_for_unknown_assessment_is_ignored(loaded) -> None:
    loaded["marks"].append(
        {"student": "S1", "assessment": "UNKNOWN", "score": 15, "at": ""}
    )

    result = gradebook.pct("S1")

    assert result == "0"
