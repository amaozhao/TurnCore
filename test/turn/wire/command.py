import pytest

from turn.wire.command import CommandEnvelope


def test_command_envelope_carries_transport_independent_command() -> None:
    command = CommandEnvelope(
        command_id="cmd_1",
        type="start_turn",
        session_id="sess_1",
        turn_id=None,
        payload={"content": "hello"},
        idempotency_key="start-sess_1-1",
    )

    assert command.type == "start_turn"
    assert command.payload["content"] == "hello"
    assert command.idempotency_key == "start-sess_1-1"


def test_command_envelope_rejects_trusted_identity_in_payload() -> None:
    with pytest.raises(ValueError, match="user_id"):
        CommandEnvelope(
            command_id="cmd_1",
            type="start_turn",
            session_id="sess_1",
            turn_id=None,
            payload={"content": "hello", "user_id": "user_1"},
        )
