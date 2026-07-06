"""Audit store."""

from __future__ import annotations

from typing import Protocol

from turn.audit.record import AuditRecord


class AuditLogStore(Protocol):
    """Port for session-scoped audit records."""

    async def append(self, record: AuditRecord) -> None: ...

    async def list_by_session(
        self,
        *,
        session_id: str,
        limit: int,
        cursor: str | None = None,
    ) -> tuple[AuditRecord, ...]: ...


class MemoryAuditLogStore:
    """Audit log store backed by process memory."""

    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    async def append(self, record: AuditRecord) -> None:
        self.records.append(record)

    async def list_by_session(
        self,
        *,
        session_id: str,
        limit: int,
        cursor: str | None = None,
    ) -> tuple[AuditRecord, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        records = [record for record in self.records if record.session_id == session_id]
        start = int(cursor) if cursor is not None else 0
        return tuple(records[start : start + limit])


__all__ = ["AuditLogStore", "MemoryAuditLogStore"]
