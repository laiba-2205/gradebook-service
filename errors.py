class GradebookError(Exception):
    """Base exception for gradebook service errors."""


class ValidationError(GradebookError):
    """Raised when input validation fails."""


class NotFoundError(GradebookError):
    """Raised when a requested resource does not exist."""


class ConflictError(GradebookError):
    """Raised when a request conflicts with existing data."""
