"""In-memory turn and run repositories."""

from __future__ import annotations

from turn.port.model import Page
from turn.run.model import Message, Run, Turn


class MemoryMessageStore:
    """Message repository backed by process memory."""

    def __init__(self) -> None:
        self.messages: list[Message] = []

    async def append_message(self, message: Message) -> None:
        self.messages.append(message)

    async def list_messages(
        self,
        *,
        session_id: str,
        limit: int,
        cursor: str | None = None,
    ) -> Page[Message]:
        if limit < 1:
            raise ValueError("limit must be positive")
        messages = [message for message in self.messages if message.session_id == session_id]
        start = int(cursor) if cursor is not None else 0
        items = tuple(messages[start : start + limit])
        next_index = start + len(items)
        next_cursor = str(next_index) if next_index < len(messages) else None
        return Page(items=items, next_cursor=next_cursor)


class MemoryTurnStore:
    """Turn repository backed by process memory."""

    def __init__(self) -> None:
        self.turns: dict[str, Turn] = {}

    async def create_turn(self, turn: Turn) -> None:
        if turn.turn_id in self.turns:
            raise KeyError(turn.turn_id)
        self.turns[turn.turn_id] = turn

    async def get_turn(self, turn_id: str) -> Turn | None:
        return self.turns.get(turn_id)

    async def update_turn(self, turn: Turn) -> None:
        if turn.turn_id not in self.turns:
            raise KeyError(turn.turn_id)
        self.turns[turn.turn_id] = turn


class MemoryRunStore:
    """Run repository backed by process memory."""

    def __init__(self) -> None:
        self.runs: dict[str, Run] = {}

    async def create_run(self, run: Run) -> None:
        if run.run_id in self.runs:
            raise KeyError(run.run_id)
        self.runs[run.run_id] = run

    async def get_run(self, run_id: str) -> Run | None:
        return self.runs.get(run_id)

    async def list_runs_for_turn(self, turn_id: str) -> tuple[Run, ...]:
        return tuple(run for run in self.runs.values() if run.turn_id == turn_id)

    async def update_run(self, run: Run) -> None:
        if run.run_id not in self.runs:
            raise KeyError(run.run_id)
        self.runs[run.run_id] = run


__all__ = ["MemoryMessageStore", "MemoryRunStore", "MemoryTurnStore"]
