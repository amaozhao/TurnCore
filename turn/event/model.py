"""Transport-independent event protocol models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping


EventType = Literal[
    "session",
    "stage_start",
    "stage_end",
    "thinking",
    "content",
    "tool_call",
    "tool_result",
    "progress",
    "sources",
    "artifact",
    "approval_required",
    "waiting_for_user",
    "error",
    "result",
    "done",
]


@dataclass(frozen=True)
class StreamEvent:
    """Ordered turn-scoped event."""

    event_id: str
    session_id: str
    turn_id: str
    seq: int
    type: EventType
    source: str
    stage: str
    content: str
    metadata: Mapping[str, object]
    created_at: datetime

    def __post_init__(self) -> None:
        if self.seq < 0:
            raise ValueError("event sequence must be non-negative")


__all__ = ["EventType", "StreamEvent"]
