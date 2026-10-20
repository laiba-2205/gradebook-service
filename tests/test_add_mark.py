import pytest
from unittest.mock import Mock

from errors import NotFoundError, ValidationError
from models import Mark
from gradebook import add_mark


def fixed_clock():
	return "2026-10-12 09:00:00"


def test_add_mark_stores_mark(state):
	save = Mock()
	mark = Mark("S1", "A1", 15.0)

	add_mark(state, mark, fixed_clock, save)

	assert state["marks"] == [
		{
			"student": "S1",
			"assessment": "A1",
			"score": 15.0,
			"at": "2026-10-12 09:00:00",
		}
	]


def test_add_mark_calls_save(state):
	save = Mock()
	mark = Mark("S1", "A1", 15.0)

	add_mark(state, mark, fixed_clock, save)

	save.assert_called_once_with()


@pytest.mark.parametrize(
	("mark", "expected_error"),
	[
		(Mark("S2", "A1", 10), NotFoundError),
		(Mark("S1", "A3", 10), NotFoundError),
		(Mark("S1", "A1", 21), ValidationError),
	],
)
def test_add_mark_rejects_invalid_mark(state, mark, expected_error):
	save = Mock()

	with pytest.raises(expected_error):
		add_mark(state, mark, fixed_clock, save)

	assert state["marks"] == []
	save.assert_not_called()

