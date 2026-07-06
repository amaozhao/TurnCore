"""Tool snapshot store port protocols."""

from __future__ import annotations

from typing import Protocol

from turn.tool.registry import ToolRegistrySnapshot


class ToolRegistrySnapshotStore(Protocol):
    """Port for turn-scoped tool registry snapshots."""

    async def save(self, snapshot: ToolRegistrySnapshot) -> None: ...

    async def get_by_turn(
        self,
        *,
        session_id: str,
        turn_id: str,
    ) -> ToolRegistrySnapshot | None: ...


__all__ = ["ToolRegistrySnapshotStore"]
