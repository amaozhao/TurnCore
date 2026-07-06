import asyncio
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from turn.event.model import StreamEvent
from turn.event.store import MemoryEventStore


def test_memory_event_store_lists_by_turn_with_cursor() -> None:
    asyncio.run(check_memory_event_store_lists_by_turn_with_cursor())


async def check_memory_event_store_lists_by_turn_with_cursor() -> None:
    store = MemoryEventStore()
    now = datetime.now(timezone.utc)
    first = StreamEvent(
        event_id="evt_1",
        session_id="sess_1",
        turn_id="turn_1",
        seq=1,
        type="content",
        source="agent_loop",
        stage="answer",
        content="one",
        metadata={},
        created_at=now,
    )
    second = replace(first, event_id="evt_2", seq=2, content="two")
    other = replace(first, event_id="evt_3", turn_id="turn_2")

    await store.append(first)
    await store.append(second)
    await store.append(other)

    assert await store.latest_seq("turn_1") == 2
    assert await store.list_by_turn(turn_id="turn_1", after_seq=1, limit=10) == (second,)
    assert await store.list_by_turn(turn_id="turn_2") == (other,)

    with pytest.raises(ValueError, match="increase"):
        await store.append(replace(first, event_id="evt_4"))
