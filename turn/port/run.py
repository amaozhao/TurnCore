"""Message, turn, and run repository port protocols."""

from __future__ import annotations

from typing import Protocol

from turn.port.model import Page
from turn.run.model import Message, Run, Turn


class MessageRepository(Protocol):
    """Port for session-scoped conversation messages."""

    async def append_message(self, message: Message) -> None: ...

    async def list_messages(
        self,
        *,
        session_id: str,
        limit: int,
        cursor: str | None = None,
    ) -> Page[Message]: ...


class TurnRepository(Protocol):
    """Port for turn lifecycle records."""

    async def create_turn(self, turn: Turn) -> None: ...

    async def get_turn(self, turn_id: str) -> Turn | None: ...

    async def update_turn(self, turn: Turn) -> None: ...


class RunRepository(Protocol):
    """Port for run lifecycle records."""

    async def create_run(self, run: Run) -> None: ...

    async def get_run(self, run_id: str) -> Run | None: ...

    async def list_runs_for_turn(self, turn_id: str) -> tuple[Run, ...]: ...

    async def update_run(self, run: Run) -> None: ...


__all__ = ["MessageRepository", "RunRepository", "TurnRepository"]
