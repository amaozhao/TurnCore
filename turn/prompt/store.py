"""In-memory prompt snapshot store."""

from __future__ import annotations

from turn.prompt.snapshot import PromptSnapshot


class MemoryPromptSnapshotStore:
    """Prompt snapshot store backed by process memory."""

    def __init__(self) -> None:
        self.snapshots: dict[tuple[str, str], PromptSnapshot] = {}

    async def save(self, snapshot: PromptSnapshot) -> None:
        key = (snapshot.session_id, snapshot.turn_id)
        if key in self.snapshots:
            raise KeyError(f"{snapshot.session_id}:{snapshot.turn_id}")
        self.snapshots[key] = snapshot

    async def get_by_turn(
        self,
        *,
        session_id: str,
        turn_id: str,
    ) -> PromptSnapshot | None:
        return self.snapshots.get((session_id, turn_id))


__all__ = ["MemoryPromptSnapshotStore"]
