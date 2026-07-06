from datetime import datetime, timezone

import pytest

from turn.error import UAFError
from turn.event.sink import EventSink
from turn.event.store import MemoryEventStore
from turn.run.cancel import CancellationToken
from turn.run.turn import TurnExecution
from turn.user import Principal
from turn.wire import CommandEnvelope


def test_turn_execution_binds_runtime_objects_to_one_turn() -> None:
    execution = TurnExecution(
        session_id="sess_1",
        turn_id="turn_1",
        command=CommandEnvelope(
            command_id="cmd_1",
            type="start_turn",
            session_id="sess_1",
            turn_id="turn_1",
            payload={"content": "hello"},
        ),
        principal=Principal(user_id="user_1"),
        cancellation_token=CancellationToken(),
        event_sink=EventSink(store=MemoryEventStore(), session_id="sess_1", turn_id="turn_1"),
        started_at=datetime.now(timezone.utc),
    )

    assert execution.session_id == "sess_1"
    assert execution.command.session_id == "sess_1"
    assert execution.event_sink.turn_id == "turn_1"

    execution.cancellation_token.cancel()
    with pytest.raises(UAFError) as error:
        execution.raise_if_cancelled()
    assert error.value.code == "turn.cancelled"
