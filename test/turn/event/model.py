from datetime import datetime, timezone

import pytest

from turn.event.model import StreamEvent


def test_stream_event_is_turn_scoped_and_ordered() -> None:
    event = StreamEvent(
        event_id="evt_1",
        session_id="sess_1",
        turn_id="turn_1",
        seq=1,
        type="content",
        source="agent_loop",
        stage="answering",
        content="hello",
        metadata={"chunk": 1},
        created_at=datetime.now(timezone.utc),
    )

    assert event.session_id == "sess_1"
    assert event.turn_id == "turn_1"
    assert event.seq == 1


def test_stream_event_rejects_negative_sequence() -> None:
    with pytest.raises(ValueError, match="sequence"):
        StreamEvent(
            event_id="evt_1",
            session_id="sess_1",
            turn_id="turn_1",
            seq=-1,
            type="content",
            source="agent_loop",
            stage="answering",
            content="hello",
            metadata={},
            created_at=datetime.now(timezone.utc),
        )
