"""Error types for qfire. Raised only at load time, never from evaluate() (fail-closed instead)."""

from __future__ import annotations


class QfireError(Exception):
    """Base class for all qfire errors."""


class RuleValidationError(QfireError):
    def __init__(self, file: str, field: str, message: str):
        self.file = file
        self.field = field
        super().__init__(f"{file}: invalid field {field!r}: {message}")


class ChainValidationError(QfireError):
    def __init__(self, file: str, field: str, message: str):
        self.file = file
        self.field = field
        super().__init__(f"{file}: invalid field {field!r}: {message}")
