"""Bound event sink for one turn."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Mapping

from turn.event.model import EventType, StreamEvent
from turn.port.event import EventStore


class EventSink:
    """Writes ordered events for one session and turn."""

    def __init__(self, *, store: EventStore, session_id: str, turn_id: str) -> None:
        self.store = store
        self.session_id = session_id
        self.turn_id = turn_id
        self.guard = asyncio.Lock()

    async def emit(
        self,
        *,
        type: EventType,
        source: str,
        stage: str,
        content: str = "",
        metadata: Mapping[str, object] | None = None,
        event_id: str | None = None,
    ) -> StreamEvent:
        async with self.guard:
            seq = await self.store.latest_seq(self.turn_id) + 1
            event = StreamEvent(
                event_id=event_id if event_id is not None else f"evt_{uuid.uuid4().hex}",
                session_id=self.session_id,
                turn_id=self.turn_id,
                seq=seq,
                type=type,
                source=source,
                stage=stage,
                content=content,
                metadata={} if metadata is None else dict(metadata),
                created_at=datetime.now(timezone.utc),
            )
            await self.store.append(event)
            return event


__all__ = ["EventSink"]
