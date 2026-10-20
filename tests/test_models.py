import pytest

from errors import ValidationError
from models import Assessment, parse_assessment, parse_mark, parse_number, parse_student


@pytest.mark.parametrize(
    ("value", "expected"),
    [("15", 15.0), (15, 15.0), ("2.5", 2.5)],
)
def test_accepted_numbers(value: object, expected: float) -> None:
    assert parse_number(value, "score") == expected


@pytest.mark.parametrize("value", ["abc", True, None, [], "nan", "inf"])
def test_rejected_numbers(value: object) -> None:
    with pytest.raises(ValidationError):
        parse_number(value, "score")


def test_zero_assessment_total_is_rejected() -> None:
    with pytest.raises(ValidationError, match="total"):
        parse_assessment(
            {"id": "A1", "title": "Quiz", "weight": "10", "total": "0"}
        )


def test_negative_mark_score_is_rejected() -> None:
    with pytest.raises(ValidationError, match="score"):
        parse_mark({"student": "S1", "assessment": "A1", "score": "-1"})


def test_missing_student_field_is_rejected() -> None:
    with pytest.raises(ValidationError, match="name"):
        parse_student({"id": "S1"})


def test_non_object_payload_is_rejected() -> None:
    with pytest.raises(ValidationError, match="payload"):
        parse_student(["S1", "Ayesha"])


def test_valid_assessment_is_parsed() -> None:
    assert parse_assessment(
        {"id": "A1", "title": "Quiz", "weight": "10", "total": "20"}
    ) == Assessment(id="A1", title="Quiz", weight=10.0, total=20.0)
