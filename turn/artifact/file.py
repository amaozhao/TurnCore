"""Artifact models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Artifact:
    """Session/turn-scoped artifact metadata."""

    artifact_id: str
    session_id: str
    turn_id: str
    run_id: str | None
    filename: str
    mime_type: str
    uri: str
    size_bytes: int
    checksum: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("artifact_id must be non-empty")
        if not self.session_id:
            raise ValueError("artifact session_id must be non-empty")
        if not self.turn_id:
            raise ValueError("artifact turn_id must be non-empty")


__all__ = ["Artifact"]
