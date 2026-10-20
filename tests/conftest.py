import pytest
import gradebook


@pytest.fixture
def state():
	return {
		"students": {
			"S1": {"id": "S1", "name": "Ayesha", "joined": ""}
		},
		"assessments": {
			"A1": {"id": "A1", "title": "Quiz 1", "weight": 10, "total": 20},
			"A2": {"id": "A2", "title": "Quiz 2", "weight": 30, "total": 50},
		},
		"marks": [],
	}


@pytest.fixture
def loaded(monkeypatch, state):
	monkeypatch.setattr(gradebook, "STATE", state)
	return state
