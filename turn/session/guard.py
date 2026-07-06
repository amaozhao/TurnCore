"""Session-scoped active-turn guard."""

from __future__ import annotations

import asyncio
from types import TracebackType
from typing import AsyncContextManager, Protocol

from turn.error import UAFError


class SessionTurnLock(Protocol):
    """Port for one active foreground turn per session."""

    async def acquire_active_turn_lock(
        self,
        *,
        session_id: str,
        turn_id: str,
        ttl_seconds: int,
    ) -> AsyncContextManager[None]: ...


class MemorySessionTurnLock:
    """Process-local foreground turn lock keyed by session."""

    def __init__(self) -> None:
        self.active: dict[str, str] = {}
        self.guard = asyncio.Lock()

    async def acquire_active_turn_lock(
        self,
        *,
        session_id: str,
        turn_id: str,
        ttl_seconds: int,
    ) -> ActiveTurnLock:
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        async with self.guard:
            active_turn_id = self.active.get(session_id)
            if active_turn_id is not None:
                raise UAFError(
                    code="session.active_turn_exists",
                    message="Session already has an active turn",
                    retryable=True,
                    metadata={"session_id": session_id, "turn_id": active_turn_id},
                )
            self.active[session_id] = turn_id
        return ActiveTurnLock(self, session_id, turn_id)

    async def release(self, session_id: str, turn_id: str) -> None:
        async with self.guard:
            if self.active.get(session_id) == turn_id:
                del self.active[session_id]


class ActiveTurnLock:
    """Acquired active-turn lock handle."""

    def __init__(self, owner: MemorySessionTurnLock, session_id: str, turn_id: str) -> None:
        self.owner = owner
        self.session_id = session_id
        self.turn_id = turn_id

    async def __aenter__(self) -> ActiveTurnLock:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.owner.release(self.session_id, self.turn_id)


__all__ = ["ActiveTurnLock", "MemorySessionTurnLock", "SessionTurnLock"]
