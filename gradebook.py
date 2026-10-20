import datetime
import http.server
import json
import logging
import sys
from collections.abc import Callable
from typing import TypedDict

from errors import ConflictError, GradebookError, NotFoundError, ValidationError
from models import Mark, parse_assessment, parse_mark, parse_student

DATA = "gradebook.json"


class StudentRecord(TypedDict):
    id: str
    name: str
    joined: str


class AssessmentRecord(TypedDict):
    id: str
    title: str
    weight: object
    total: object


class MarkRecord(TypedDict):
    student: str
    assessment: str
    score: object
    at: str


class GradebookState(TypedDict):
    students: dict[str, StudentRecord]
    assessments: dict[str, AssessmentRecord]
    marks: list[MarkRecord]


STATE: GradebookState = {"students": {}, "assessments": {}, "marks": []}
LOGGER = logging.getLogger(__name__)


def _stored_number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise TypeError("invalid numeric value in gradebook data")
    return float(value)


def load() -> None:
    global STATE
    try:
        with open(DATA, encoding="utf-8") as data_file:
            STATE = json.load(data_file)
    except FileNotFoundError:
        STATE = {"students": {}, "assessments": {}, "marks": []}


def save() -> None:
    with open(DATA, "w", encoding="utf-8") as data_file:
        json.dump(STATE, data_file)


def now() -> str:
    return str(datetime.datetime.now())


def pct(sid: str) -> str:
    total = 0.0
    got = 0.0
    for mark in STATE["marks"]:
        if mark["student"] == sid:
            assessment = STATE["assessments"].get(mark["assessment"])
            if assessment is not None:
                weight = _stored_number(assessment["weight"])
                got += (
                    _stored_number(mark["score"])
                    * weight
                    / _stored_number(assessment["total"])
                )
                total += weight
    if total == 0:
        return "0"
    return str(round(got, 2))


def add_mark(
    state: GradebookState,
    mark: Mark,
    now: Callable[[], str],
    save: Callable[[], None],
) -> None:
    if mark.student not in state["students"]:
        raise NotFoundError("student not found")
    stored_assessment = state["assessments"].get(mark.assessment)
    if stored_assessment is None:
        raise NotFoundError("assessment not found")
    assessment = parse_assessment(stored_assessment)
    if mark.score > assessment.total:
        raise ValidationError("score must not exceed total")

    mark_record: MarkRecord = {
        "student": mark.student,
        "assessment": mark.assessment,
        "score": mark.score,
        "at": now(),
    }
    state["marks"].append(mark_record)
    save()


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def _send(self, code: int, body_object: object) -> None:
        body = json.dumps(body_object).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond(self, handler: Callable[[], tuple[int, object]]) -> None:
        try:
            status, body = handler()
        except ValidationError as error:
            self._send(400, {"error": str(error)})
        except ConflictError as error:
            self._send(409, {"error": str(error)})
        except NotFoundError as error:
            self._send(404, {"error": str(error)})
        except GradebookError as error:
            LOGGER.exception("Unexpected gradebook error")
            self._send(500, {"error": str(error)})
        except Exception:
            LOGGER.exception("Unexpected error while handling request")
            self._send(500, {"error": "internal error"})
        else:
            self._send(status, body)

    def _read_payload(self) -> dict[str, object]:
        content_length = self.headers.get("Content-Length")
        if content_length is None:
            raise ValidationError("Content-Length is required")
        try:
            length = int(content_length)
        except ValueError:
            raise ValidationError("Content-Length must be a number") from None
        if length < 0:
            raise ValidationError("Content-Length must not be negative")

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValidationError("request body must be valid JSON") from None
        if not isinstance(payload, dict):
            raise ValidationError("request body must be a JSON object")
        return payload

    def _get(self) -> tuple[int, object]:
        if self.path == "/students":
            return 200, list(STATE["students"].values())
        if self.path.startswith("/students/"):
            path_parts = self.path.split("/")
            if len(path_parts) != 3 or not path_parts[2]:
                raise NotFoundError("unknown route")
            student_id = path_parts[2]
            student = STATE["students"].get(student_id)
            if student is None:
                raise NotFoundError("student not found")
            student_response = dict(student)
            student_response["percentage"] = pct(student_id)
            return 200, student_response
        if self.path == "/assessments":
            return 200, list(STATE["assessments"].values())
        if self.path == "/report":
            report = [
                {"id": student_id, "name": student["name"], "pct": pct(student_id)}
                for student_id, student in STATE["students"].items()
            ]
            return 200, report
        raise NotFoundError("unknown route")

    def _post(self) -> tuple[int, object]:
        if self.path not in {"/students", "/assessments", "/marks"}:
            raise NotFoundError("unknown route")

        payload = self._read_payload()
        if self.path == "/students":
            student = parse_student(payload)
            if student.id in STATE["students"]:
                raise ConflictError("student already exists")
            student_record: StudentRecord = {
                "id": student.id,
                "name": student.name,
                "joined": str(datetime.datetime.now()),
            }
            STATE["students"][student.id] = student_record
            save()
            return 200, student_record

        if self.path == "/assessments":
            assessment = parse_assessment(payload)
            if assessment.id in STATE["assessments"]:
                raise ConflictError("assessment already exists")
            new_assessment_record: AssessmentRecord = {
                "id": assessment.id,
                "title": assessment.title,
                "weight": payload["weight"],
                "total": payload["total"],
            }
            STATE["assessments"][assessment.id] = new_assessment_record
            save()
            return 200, new_assessment_record

        mark = parse_mark(payload)
        add_mark(STATE, mark, now, save)
        LOGGER.info("Recorded mark for %s with score %s", mark.student, mark.score)
        return 200, {"ok": True}

    def do_GET(self) -> None:
        self._respond(self._get)

    def do_POST(self) -> None:
        self._respond(self._post)


def main(argv: list[str] = sys.argv) -> None:
    port = 8000
    if len(argv) > 1:
        try:
            port = int(argv[1])
        except ValueError:
            raise SystemExit("port must be a whole number from 1 to 65535") from None
    if not 1 <= port <= 65535:
        raise SystemExit("port must be a whole number from 1 to 65535")

    load()
    logging.basicConfig(level=logging.INFO)
    LOGGER.info("gradebook on %s", port)
    http.server.HTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
