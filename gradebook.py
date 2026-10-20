import datetime
import http.server
import json
import logging
import sys
from collections.abc import Callable

from errors import ConflictError, GradebookError, NotFoundError, ValidationError
from models import parse_assessment, parse_mark, parse_student

DATA = "gradebook.json"
STATE = {"students": {}, "assessments": {}, "marks": []}
LOGGER = logging.getLogger(__name__)


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


def pct(sid: str) -> str:
    total = 0.0
    got = 0.0
    for mark in STATE["marks"]:
        if mark["student"] == sid:
            assessment = STATE["assessments"].get(mark["assessment"])
            if assessment is not None:
                got += (
                    float(mark["score"])
                    * float(assessment["weight"])
                    / float(assessment["total"])
                )
                total += float(assessment["weight"])
    if total == 0:
        return "0"
    return str(round(got, 2))


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
            student_record = {
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
            assessment_record = {
                "id": assessment.id,
                "title": assessment.title,
                "weight": payload["weight"],
                "total": payload["total"],
            }
            STATE["assessments"][assessment.id] = assessment_record
            save()
            return 200, assessment_record

        mark = parse_mark(payload)
        if mark.student not in STATE["students"]:
            raise NotFoundError("student not found")
        assessment_record = STATE["assessments"].get(mark.assessment)
        if assessment_record is None:
            raise NotFoundError("assessment not found")
        assessment = parse_assessment(assessment_record)
        if mark.score > assessment.total:
            raise ValidationError("score must not exceed total")
        STATE["marks"].append(
            {
                "student": mark.student,
                "assessment": mark.assessment,
                "score": mark.score,
                "at": str(datetime.datetime.now()),
            }
        )
        save()
        LOGGER.info("Recorded mark for %s with score %s", mark.student, mark.score)
        return 200, {"ok": True}

    def do_GET(self) -> None:
        self._respond(self._get)

    def do_POST(self) -> None:
        self._respond(self._post)


def main(argv: list[str] = sys.argv) -> None:
    load()
    port = 8000
    if len(argv) > 1:
        port = int(argv[1])
    logging.basicConfig(level=logging.INFO)
    LOGGER.info("gradebook on %s", port)
    http.server.HTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
