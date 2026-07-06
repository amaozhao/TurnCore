"""Domain exception base class."""

from __future__ import annotations

from typing import Mapping

from turn.wire.error import ErrorEnvelope


class UAFError(Exception):
    """Expected library error with a stable code."""

    code: str
    message: str
    retryable: bool
    metadata: Mapping[str, object]

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        if not code:
            raise ValueError("error code must be non-empty")
        self.code = code
        self.message = message
        self.retryable = retryable
        self.metadata = {} if metadata is None else metadata

    def to_envelope(
        self,
        *,
        session_id: str | None = None,
        turn_id: str | None = None,
        run_id: str | None = None,
    ) -> ErrorEnvelope:
        """Convert an expected library error for a cross-boundary result."""

        return ErrorEnvelope(
            code=self.code,
            message=self.message,
            retryable=self.retryable,
            session_id=session_id,
            turn_id=turn_id,
            run_id=run_id,
            details=self.metadata,
        )


__all__ = ["UAFError"]
