"""Event store port protocol."""

from __future__ import annotations

from typing import Protocol

from turn.event.model import StreamEvent


class EventStore(Protocol):
    """Port for ordered turn-scoped stream events."""

    async def append(self, event: StreamEvent) -> None: ...

    async def list_by_turn(
        self,
        *,
        turn_id: str,
        after_seq: int = 0,
        limit: int = 500,
    ) -> tuple[StreamEvent, ...]: ...

    async def latest_seq(self, turn_id: str) -> int: ...


__all__ = ["EventStore"]
