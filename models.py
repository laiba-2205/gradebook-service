import math
from dataclasses import dataclass

from errors import ValidationError


def parse_number(raw: object, field: str) -> float:
    if isinstance(raw, bool):
        raise ValidationError(f"{field} must be a finite number")

    if isinstance(raw, (int, float)):
        try:
            number = float(raw)
        except OverflowError:
            raise ValidationError(f"{field} must be a finite number") from None
    elif isinstance(raw, str):
        try:
            number = float(raw)
        except ValueError:
            raise ValidationError(f"{field} must be a finite number") from None
    else:
        raise ValidationError(f"{field} must be a finite number")

    if not math.isfinite(number):
        raise ValidationError(f"{field} must be a finite number")
    return number


def parse_text(raw: object, field: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValidationError(f"{field} must be a non-blank string")
    return raw.strip()


def _payload_field(payload: object, field: str) -> object:
    if not isinstance(payload, dict):
        raise ValidationError("payload must be an object")
    if field not in payload:
        raise ValidationError(f"{field} is required")
    value: object = payload[field]
    return value


@dataclass(frozen=True)
class Student:
    id: str
    name: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("id must not be empty")
        if not self.name:
            raise ValidationError("name must not be empty")


@dataclass(frozen=True)
class Assessment:
    id: str
    title: str
    weight: float
    total: float

    def __post_init__(self) -> None:
        if not self.id:
            raise ValidationError("id must not be empty")
        if not self.title:
            raise ValidationError("title must not be empty")
        if not 0 <= self.weight <= 100:
            raise ValidationError("weight must be between 0 and 100")
        if self.total <= 0:
            raise ValidationError("total must be above 0")


@dataclass(frozen=True)
class Mark:
    student: str
    assessment: str
    score: float

    def __post_init__(self) -> None:
        if not self.student:
            raise ValidationError("student must not be empty")
        if not self.assessment:
            raise ValidationError("assessment must not be empty")
        if self.score < 0:
            raise ValidationError("score must not be negative")


def parse_student(payload: object) -> Student:
    return Student(
        id=parse_text(_payload_field(payload, "id"), "id"),
        name=parse_text(_payload_field(payload, "name"), "name"),
    )


def parse_assessment(payload: object) -> Assessment:
    return Assessment(
        id=parse_text(_payload_field(payload, "id"), "id"),
        title=parse_text(_payload_field(payload, "title"), "title"),
        weight=parse_number(_payload_field(payload, "weight"), "weight"),
        total=parse_number(_payload_field(payload, "total"), "total"),
    )


def parse_mark(payload: object) -> Mark:
    return Mark(
        student=parse_text(_payload_field(payload, "student"), "student"),
        assessment=parse_text(_payload_field(payload, "assessment"), "assessment"),
        score=parse_number(_payload_field(payload, "score"), "score"),
    )
