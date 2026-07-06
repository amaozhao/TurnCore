"""Session memory port and in-memory implementation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol

from turn.memory.session import MemoryTraceEvent, SessionMemoryDocument
from turn.memory.snapshot import MemorySnapshot, memory_checksum


class SessionMemoryPort(Protocol):
    """Port for session-scoped runtime memory."""

    async def append_trace(
        self, *, session_id: str, turn_id: str, event: MemoryTraceEvent
    ) -> None: ...

    async def read_session_memory(self, *, session_id: str) -> SessionMemoryDocument: ...

    async def write_session_preference(
        self,
        *,
        session_id: str,
        turn_id: str,
        text: str,
        reason: str,
    ) -> None: ...

    async def build_snapshot(self, *, session_id: str, turn_id: str) -> MemorySnapshot: ...


class MemorySessionMemoryStore:
    """Session memory store backed by process memory."""

    def __init__(self) -> None:
        self.events: list[MemoryTraceEvent] = []

    async def append_trace(self, *, session_id: str, turn_id: str, event: MemoryTraceEvent) -> None:
        if event.session_id != session_id or event.turn_id != turn_id:
            raise ValueError("memory event scope must match append scope")
        self.events.append(event)

    async def read_session_memory(self, *, session_id: str) -> SessionMemoryDocument:
        events = [event for event in self.events if event.session_id == session_id]
        preferences = "\n".join(event.text for event in events if event.type == "preference")
        recent = "\n".join(event.text for event in events if event.type == "event")
        return SessionMemoryDocument(
            session_id=session_id,
            recent_summary=recent,
            preferences=preferences,
            entry_ids=tuple(event.entry_id for event in events),
        )

    async def write_session_preference(
        self,
        *,
        session_id: str,
        turn_id: str,
        text: str,
        reason: str,
    ) -> None:
        event = MemoryTraceEvent(
            entry_id=f"mem_{len(self.events) + 1}",
            session_id=session_id,
            turn_id=turn_id,
            type="preference",
            text=text,
            reason=reason,
            created_at=datetime.now(timezone.utc),
        )
        await self.append_trace(session_id=session_id, turn_id=turn_id, event=event)

    async def build_snapshot(self, *, session_id: str, turn_id: str) -> MemorySnapshot:
        document = await self.read_session_memory(session_id=session_id)
        checksum = memory_checksum(
            recent_summary=document.recent_summary,
            profile_notes=document.profile_notes,
            preferences=document.preferences,
            scope="session",
            source_entry_ids=document.entry_ids,
        )
        return MemorySnapshot(
            snapshot_id=f"memory_{checksum[:16]}",
            session_id=session_id,
            turn_id=turn_id,
            recent_summary=document.recent_summary,
            profile_notes=document.profile_notes,
            preferences=document.preferences,
            scope="session",
            source_entry_ids=document.entry_ids,
            checksum=checksum,
        )


__all__ = ["MemorySessionMemoryStore", "SessionMemoryPort"]
