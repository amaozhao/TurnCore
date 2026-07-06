"""In-memory event store."""

from __future__ import annotations

import asyncio

from turn.event.model import StreamEvent


class MemoryEventStore:
    """Ordered event store backed by process memory."""

    def __init__(self) -> None:
        self.events: list[StreamEvent] = []
        self.guard = asyncio.Lock()

    async def append(self, event: StreamEvent) -> None:
        async with self.guard:
            latest = await self.latest_seq(event.turn_id)
            if event.seq <= latest:
                raise ValueError("event sequence must increase within a turn")
            self.events.append(event)

    async def list_by_turn(
        self,
        *,
        turn_id: str,
        after_seq: int = 0,
        limit: int = 500,
    ) -> tuple[StreamEvent, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        events = [
            event for event in self.events if event.turn_id == turn_id and event.seq > after_seq
        ]
        events.sort(key=lambda event: event.seq)
        return tuple(events[:limit])

    async def latest_seq(self, turn_id: str) -> int:
        sequences = [event.seq for event in self.events if event.turn_id == turn_id]
        return max(sequences, default=0)


__all__ = ["MemoryEventStore"]
