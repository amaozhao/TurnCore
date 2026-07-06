from datetime import datetime, timezone

from turn.run.model import Message, Run, Turn
from turn.wire.error import ErrorEnvelope


def test_message_turn_and_run_are_session_scoped() -> None:
    now = datetime.now(timezone.utc)

    message = Message(
        message_id="msg_1",
        session_id="sess_1",
        turn_id="turn_1",
        role="user",
        content="hello",
        artifact_ids=(),
        created_at=now,
    )
    turn = Turn(
        turn_id="turn_1",
        session_id=message.session_id,
        parent_turn_id=None,
        status="running",
        command_snapshot={"type": "start_turn"},
        prompt_snapshot_id="prompt_1",
        tool_registry_snapshot_id="tools_1",
        memory_snapshot_id="mem_1",
        created_at=now,
        started_at=now,
        completed_at=None,
    )
    error = ErrorEnvelope(code="model.provider_error", message="provider failed")
    run = Run(
        run_id="run_1",
        session_id=turn.session_id,
        turn_id=turn.turn_id,
        kind="agent_loop",
        status="failed",
        input_summary="input",
        output_summary=None,
        error=error,
        created_at=now,
        completed_at=now,
    )

    assert message.session_id == turn.session_id == run.session_id
    assert run.turn_id == turn.turn_id
    assert run.error is error
