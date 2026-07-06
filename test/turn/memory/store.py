import asyncio

import pytest

from turn.memory import MemorySessionMemoryStore, MemoryTraceEvent


def test_memory_snapshot_is_session_scoped() -> None:
    asyncio.run(check_memory_snapshot_is_session_scoped())


async def check_memory_snapshot_is_session_scoped() -> None:
    store = MemorySessionMemoryStore()

    await store.append_trace(
        session_id="sess_1",
        turn_id="turn_1",
        event=MemoryTraceEvent(
            entry_id="mem_1",
            session_id="sess_1",
            turn_id="turn_1",
            type="event",
            text="project goal",
        ),
    )
    await store.write_session_preference(
        session_id="sess_1",
        turn_id="turn_1",
        text="prefer concise answers",
        reason="user preference",
    )
    await store.write_session_preference(
        session_id="sess_2",
        turn_id="turn_2",
        text="other session preference",
        reason="other user",
    )

    snapshot = await store.build_snapshot(session_id="sess_1", turn_id="turn_3")

    assert snapshot.session_id == "sess_1"
    assert snapshot.turn_id == "turn_3"
    assert snapshot.scope == "session"
    assert snapshot.recent_summary == "project goal"
    assert snapshot.preferences == "prefer concise answers"
    assert snapshot.source_entry_ids == ("mem_1", "mem_2")
    assert "other session" not in snapshot.preferences


def test_append_trace_rejects_mismatched_scope() -> None:
    asyncio.run(check_append_trace_rejects_mismatched_scope())


async def check_append_trace_rejects_mismatched_scope() -> None:
    store = MemorySessionMemoryStore()

    with pytest.raises(ValueError, match="scope"):
        await store.append_trace(
            session_id="sess_1",
            turn_id="turn_1",
            event=MemoryTraceEvent(
                entry_id="mem_1",
                session_id="sess_2",
                turn_id="turn_1",
                type="event",
                text="wrong session",
            ),
        )
