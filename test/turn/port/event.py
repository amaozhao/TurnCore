import asyncio
from datetime import datetime, timezone

from turn.event.model import StreamEvent
from turn.port.event import EventStore


class MemoryEventStore:
    def __init__(self) -> None:
        self.events: list[StreamEvent] = []

    async def append(self, event: StreamEvent) -> None:
        self.events.append(event)

    async def list_by_turn(
        self,
        *,
        turn_id: str,
        after_seq: int = 0,
        limit: int = 500,
    ) -> tuple[StreamEvent, ...]:
        events = [
            event for event in self.events if event.turn_id == turn_id and event.seq > after_seq
        ]
        return tuple(events[:limit])

    async def latest_seq(self, turn_id: str) -> int:
        sequences = [event.seq for event in self.events if event.turn_id == turn_id]
        return max(sequences, default=0)


def test_event_store_protocol_shape_supports_replay() -> None:
    asyncio.run(check_event_store_protocol_shape_supports_replay())


async def check_event_store_protocol_shape_supports_replay() -> None:
    store: EventStore = MemoryEventStore()
    event = StreamEvent(
        event_id="evt_1",
        session_id="sess_1",
        turn_id="turn_1",
        seq=1,
        type="content",
        source="agent_loop",
        stage="answering",
        content="hello",
        metadata={},
        created_at=datetime.now(timezone.utc),
    )

    await store.append(event)

    assert await store.latest_seq("turn_1") == 1
    assert await store.list_by_turn(turn_id="turn_1", after_seq=0) == (event,)
    assert await store.list_by_turn(turn_id="turn_1", after_seq=1) == ()
