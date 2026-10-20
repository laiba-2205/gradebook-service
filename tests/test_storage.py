import json

import pytest

import gradebook


@pytest.fixture
def gradebook_path(tmp_path, monkeypatch):
	path = tmp_path / "gradebook.json"
	monkeypatch.setattr(gradebook, "DATA", path)
	return path


def test_saved_gradebook_loads_back_unchanged(gradebook_path):
	sample = {
		"students": {"student-1": {"name": "Ada"}},
		"assessments": {"assessment-1": {"name": "Quiz"}},
		"marks": [{"student_id": "student-1", "assessment_id": "assessment-1", "mark": 95}],
	}
	gradebook.STATE = sample
	gradebook.save()

	gradebook.STATE = {"students": {}, "assessments": {}, "marks": []}
	gradebook.load()

	assert gradebook.STATE == sample


def test_missing_file_loads_empty_state(gradebook_path):
	assert not gradebook_path.exists()
	gradebook.load()

	assert gradebook.STATE == {"students": {}, "assessments": {}, "marks": []}


def test_invalid_json_raises_decode_error(gradebook_path):
	gradebook_path.write_text("{bad", encoding="utf-8")

	with pytest.raises(json.JSONDecodeError):
		gradebook.load()
