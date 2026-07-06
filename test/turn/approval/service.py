import asyncio
from dataclasses import replace
from datetime import datetime, timezone

from turn.approval import ApprovalService, MemoryApprovalRepository
from turn.run import Turn
from turn.run.store import MemoryTurnStore
from turn.session import SessionAuthorizer
from turn.session.store import MemorySessionStore
from turn.user import Principal


def test_approval_service_requests_and_submits_approval() -> None:
    asyncio.run(check_approval_service_requests_and_submits_approval())


async def check_approval_service_requests_and_submits_approval() -> None:
    sessions = MemorySessionStore()
    turns = MemoryTurnStore()
    approvals = MemoryApprovalRepository()
    session = await sessions.create_session(owner_user_id="user_1", title="One")
    now = datetime.now(timezone.utc)
    turn = Turn(
        turn_id="turn_1",
        session_id=session.session_id,
        parent_turn_id=None,
        status="running",
        command_snapshot={},
        prompt_snapshot_id=None,
        tool_registry_snapshot_id=None,
        memory_snapshot_id=None,
        created_at=now,
        started_at=now,
        completed_at=None,
    )
    await turns.create_turn(turn)
    service = ApprovalService(
        approvals=approvals,
        turns=turns,
        authorizer=SessionAuthorizer(sessions, turns),
    )

    request = await service.request_approval(
        principal=Principal(user_id="user_1"),
        session_id=session.session_id,
        turn_id="turn_1",
        run_id=None,
        action="tool.write",
        reason="write tool requires approval",
    )

    waiting = await turns.get_turn("turn_1")
    assert waiting is not None
    assert waiting.status == "waiting_for_approval"

    resolved = await service.submit_approval(
        principal=Principal(user_id="user_1"),
        turn_id="turn_1",
        approval_id=request.approval_id,
        status="approved",
    )

    assert resolved.status == "approved"
    assert resolved.resolved_by_user_id == "user_1"
    current = await turns.get_turn("turn_1")
    assert current == replace(waiting, status="running")
