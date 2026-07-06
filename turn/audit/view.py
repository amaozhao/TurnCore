"""Audit viewer data."""

from __future__ import annotations

from dataclasses import dataclass

from turn.audit.record import AuditRecord
from turn.audit.store import AuditLogStore


@dataclass(frozen=True)
class AuditTrail:
    """Session-scoped audit viewer payload."""

    session_id: str
    records: tuple[AuditRecord, ...]


class AuditViewer:
    """Builds audit viewer payloads from an audit store."""

    def __init__(self, store: AuditLogStore) -> None:
        self.store = store

    async def list_session_records(
        self,
        *,
        session_id: str,
        limit: int = 100,
        cursor: str | None = None,
    ) -> AuditTrail:
        records = await self.store.list_by_session(
            session_id=session_id,
            limit=limit,
            cursor=cursor,
        )
        return AuditTrail(session_id=session_id, records=records)


__all__ = ["AuditTrail", "AuditViewer"]
