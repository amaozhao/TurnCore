import asyncio

from turn.event.sink import EventSink
from turn.event.store import MemoryEventStore


def test_event_sink_writes_ordered_events_for_bound_turn() -> None:
    asyncio.run(check_event_sink_writes_ordered_events_for_bound_turn())


async def check_event_sink_writes_ordered_events_for_bound_turn() -> None:
    store = MemoryEventStore()
    sink = EventSink(store=store, session_id="sess_1", turn_id="turn_1")

    first = await sink.emit(
        type="stage_start",
        source="runtime",
        stage="start",
        event_id="evt_1",
    )
    second = await sink.emit(
        type="content",
        source="runtime",
        stage="answer",
        content="hello",
        metadata={"chunk": 1},
        event_id="evt_2",
    )

    assert first.seq == 1
    assert second.seq == 2
    assert first.session_id == second.session_id == "sess_1"
    assert first.turn_id == second.turn_id == "turn_1"
    assert await store.list_by_turn(turn_id="turn_1") == (first, second)
