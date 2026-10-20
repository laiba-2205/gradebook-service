import gradebook


def test_student_with_no_marks_has_zero_percentage(monkeypatch) -> None:
    state = {
        "students": {"S1": {"id": "S1", "name": "Ayesha", "joined": ""}},
        "assessments": {},
        "marks": [],
    }
    monkeypatch.setattr(gradebook, "STATE", state)

    result = gradebook.pct("S1")

    assert result == "0"


def test_mark_percentage_uses_assessment_weight(monkeypatch) -> None:
    state = {
        "students": {"S1": {"id": "S1", "name": "Ayesha", "joined": ""}},
        "assessments": {
            "A1": {"id": "A1", "title": "Quiz", "weight": 10, "total": 20}
        },
        "marks": [
            {"student": "S1", "assessment": "A1", "score": 15, "at": ""}
        ],
    }
    monkeypatch.setattr(gradebook, "STATE", state)

    result = gradebook.pct("S1")

    assert result == "7.5"


def test_mark_for_unknown_assessment_is_ignored(monkeypatch) -> None:
    state = {
        "students": {"S1": {"id": "S1", "name": "Ayesha", "joined": ""}},
        "assessments": {},
        "marks": [
            {"student": "S1", "assessment": "UNKNOWN", "score": 15, "at": ""}
        ],
    }
    monkeypatch.setattr(gradebook, "STATE", state)

    result = gradebook.pct("S1")

    assert result == "0"
