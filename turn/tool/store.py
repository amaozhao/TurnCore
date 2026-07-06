"""In-memory tool snapshot store."""

from __future__ import annotations

from turn.tool.registry import ToolRegistrySnapshot


class MemoryToolRegistrySnapshotStore:
    """Tool snapshot store backed by process memory."""

    def __init__(self) -> None:
        self.snapshots: dict[tuple[str, str], ToolRegistrySnapshot] = {}

    async def save(self, snapshot: ToolRegistrySnapshot) -> None:
        key = (snapshot.session_id, snapshot.turn_id)
        if key in self.snapshots:
            raise KeyError(f"{snapshot.session_id}:{snapshot.turn_id}")
        self.snapshots[key] = snapshot

    async def get_by_turn(
        self,
        *,
        session_id: str,
        turn_id: str,
    ) -> ToolRegistrySnapshot | None:
        return self.snapshots.get((session_id, turn_id))


__all__ = ["MemoryToolRegistrySnapshotStore"]
