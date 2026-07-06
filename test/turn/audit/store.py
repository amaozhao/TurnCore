import asyncio
from datetime import datetime, timezone

from turn.audit import AuditRecord, AuditViewer, MemoryAuditLogStore


def test_audit_viewer_lists_session_scoped_records() -> None:
    asyncio.run(check_audit_viewer_lists_session_scoped_records())


async def check_audit_viewer_lists_session_scoped_records() -> None:
    store = MemoryAuditLogStore()
    first = AuditRecord(
        record_id="audit_1",
        session_id="sess_1",
        turn_id="turn_1",
        actor_user_id="user_1",
        action="team",
        summary="ran team task",
        created_at=datetime.now(timezone.utc),
    )
    other = AuditRecord(
        record_id="audit_2",
        session_id="sess_2",
        turn_id="turn_2",
        actor_user_id="user_2",
        action="team",
        summary="other session",
        created_at=datetime.now(timezone.utc),
    )
    await store.append(first)
    await store.append(other)

    trail = await AuditViewer(store).list_session_records(session_id="sess_1")

    assert trail.session_id == "sess_1"
    assert trail.records == (first,)
