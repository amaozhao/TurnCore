"""Cross-boundary error envelope."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


def empty_details() -> Mapping[str, object]:
    return {}


@dataclass(frozen=True)
class ErrorEnvelope:
    """Safe error value for wire, event, and tool-result boundaries."""

    code: str
    message: str
    retryable: bool = False
    session_id: str | None = None
    turn_id: str | None = None
    run_id: str | None = None
    details: Mapping[str, object] = field(default_factory=empty_details)

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("error code must be non-empty")


__all__ = ["ErrorEnvelope"]
