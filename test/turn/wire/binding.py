from datetime import datetime, timezone
from operator import setitem

import pytest

from turn.event import StreamEvent
from turn.wire import (
    CommandEnvelope,
    ErrorEnvelope,
    RestRequest,
    TextCommandInput,
    WireMessage,
    command_from_rest,
    command_from_text,
    command_to_wire,
    error_to_rest,
    error_to_sse,
    error_to_text,
    event_to_rest,
    event_to_sse,
    event_to_text,
    event_to_wire,
    wire_to_command,
)


def event() -> StreamEvent:
    return StreamEvent(
        event_id="evt_1",
        session_id="sess_1",
        turn_id="turn_1",
        seq=7,
        type="content",
        source="agent_loop",
        stage="answer",
        content="hello",
        metadata={"safe": True},
        created_at=datetime(2026, 7, 6, tzinfo=timezone.utc),
    )


def test_websocket_binding_maps_commands_events_errors_and_ping() -> None:
    command = CommandEnvelope(
        command_id="cmd_1",
        type="start_turn",
        session_id="sess_1",
        turn_id=None,
        payload={"content": "hello"},
        idempotency_key="idem_1",
    )
    wire = command_to_wire(command)

    assert wire.type == "command"
    assert wire_to_command(wire) == command
    assert wire_to_command(WireMessage(type="ping")) is None
    assert event_to_wire(event()).type == "event"
    assert error_to_text(ErrorEnvelope(code="x", message="bad")) == "x: bad"

    with pytest.raises(TypeError):
        setitem(wire.data, "type", "changed")


def test_sse_binding_maps_event_id_and_error_payload() -> None:
    sse = event_to_sse(event())
    error = error_to_sse(ErrorEnvelope(code="turn.cancelled", message="Cancelled"))

    assert sse.event == "content"
    assert sse.id == "7"
    assert sse.data["content"] == "hello"
    assert error.event == "error"
    assert error.data["code"] == "turn.cancelled"


def test_rest_binding_maps_request_and_responses() -> None:
    request = RestRequest(
        method="POST",
        path="/turns",
        body={
            "command_id": "cmd_1",
            "type": "start_turn",
            "session_id": "sess_1",
            "payload": {"content": "hello"},
        },
    )

    command = command_from_rest(request)
    response = event_to_rest(event())
    error = error_to_rest(ErrorEnvelope(code="bad.request", message="Bad"), status=422)

    assert command.type == "start_turn"
    assert command.payload["content"] == "hello"
    assert response.status == 200
    assert response.body["event_id"] == "evt_1"
    assert error.status == 422
    assert error.body["code"] == "bad.request"


def test_cli_binding_maps_text_to_command_and_event_to_text() -> None:
    command = command_from_text(
        TextCommandInput(text="hello", session_id="sess_1", command_id="cmd_1")
    )

    assert command.command_id == "cmd_1"
    assert command.type == "start_turn"
    assert command.payload == {"content": "hello"}
    assert event_to_text(event()) == "hello"


def test_im_binding_uses_same_text_mapping_without_transport_identity() -> None:
    command = command_from_text(TextCommandInput(text="hello"))
    same = command_from_text(TextCommandInput(text="hello"))

    assert command.session_id is None
    assert command.command_id == same.command_id
    assert command.payload == {"content": "hello"}
    with pytest.raises(ValueError):
        command_from_text(TextCommandInput(text=""))


def test_binding_rejects_user_id_payload() -> None:
    with pytest.raises(ValueError, match="user_id"):
        wire_to_command(
            WireMessage(
                type="command",
                data={
                    "command_id": "cmd_1",
                    "type": "start_turn",
                    "payload": {"user_id": "user_1"},
                },
            )
        )
