from dataclasses import dataclass

from errors import ValidationError


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
