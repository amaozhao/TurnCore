"""Session memory models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Literal, Mapping

MemoryTraceType = Literal["event", "preference"]


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class MemoryTraceEvent:
    """Session-scoped memory trace entry."""

    entry_id: str
    session_id: str
    turn_id: str
    type: MemoryTraceType
    text: str
    reason: str = ""
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.entry_id:
            raise ValueError("memory entry_id must be non-empty")
        if not self.session_id:
            raise ValueError("memory session_id must be non-empty")
        if not self.turn_id:
            raise ValueError("memory turn_id must be non-empty")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True)
class SessionMemoryDocument:
    """Current memory document for one session."""

    session_id: str
    recent_summary: str = ""
    profile_notes: str = ""
    preferences: str = ""
    entry_ids: tuple[str, ...] = ()


__all__ = ["MemoryTraceEvent", "MemoryTraceType", "SessionMemoryDocument"]
