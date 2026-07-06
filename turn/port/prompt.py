"""Prompt repository port protocols."""

from __future__ import annotations

from typing import Protocol

from turn.prompt.snapshot import PromptSnapshot


class PromptSnapshotStore(Protocol):
    """Port for turn-scoped prompt snapshots."""

    async def save(self, snapshot: PromptSnapshot) -> None: ...

    async def get_by_turn(
        self,
        *,
        session_id: str,
        turn_id: str,
    ) -> PromptSnapshot | None: ...


__all__ = ["PromptSnapshotStore"]
