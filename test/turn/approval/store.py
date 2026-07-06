import asyncio

import pytest

from turn.approval import ApprovalRequest, MemoryApprovalRepository


def test_approval_repository_is_session_and_turn_scoped() -> None:
    asyncio.run(check_approval_repository_is_session_and_turn_scoped())


async def check_approval_repository_is_session_and_turn_scoped() -> None:
    repository = MemoryApprovalRepository()
    request = ApprovalRequest(
        approval_id="approval_1",
        session_id="sess_1",
        turn_id="turn_1",
        run_id="run_1",
        action="tool.call",
        reason="requires write access",
        status="pending",
        requested_by_user_id="user_1",
    )

    await repository.create(request)

    assert await repository.get(session_id="sess_1", approval_id="approval_1") == request
    assert await repository.get(session_id="sess_2", approval_id="approval_1") is None
    assert await repository.list_by_turn(session_id="sess_1", turn_id="turn_1") == (request,)
    assert await repository.list_by_turn(session_id="sess_1", turn_id="turn_2") == ()


def test_approval_can_be_resolved_once() -> None:
    asyncio.run(check_approval_can_be_resolved_once())


async def check_approval_can_be_resolved_once() -> None:
    repository = MemoryApprovalRepository()
    await repository.create(
        ApprovalRequest(
            approval_id="approval_1",
            session_id="sess_1",
            turn_id="turn_1",
            run_id=None,
            action="tool.call",
            reason="requires write access",
            status="pending",
            requested_by_user_id="user_1",
        )
    )

    resolved = await repository.resolve(
        session_id="sess_1",
        approval_id="approval_1",
        status="approved",
        resolved_by_user_id="user_2",
    )

    assert resolved.status == "approved"
    assert resolved.resolved_by_user_id == "user_2"
    assert resolved.resolved_at is not None

    with pytest.raises(ValueError, match="already resolved"):
        await repository.resolve(
            session_id="sess_1",
            approval_id="approval_1",
            status="rejected",
            resolved_by_user_id="user_2",
        )


def test_approval_resolution_cannot_stay_pending() -> None:
    asyncio.run(check_approval_resolution_cannot_stay_pending())


async def check_approval_resolution_cannot_stay_pending() -> None:
    repository = MemoryApprovalRepository()
    await repository.create(
        ApprovalRequest(
            approval_id="approval_1",
            session_id="sess_1",
            turn_id="turn_1",
            run_id=None,
            action="tool.call",
            reason="requires write access",
            status="pending",
            requested_by_user_id="user_1",
        )
    )

    with pytest.raises(ValueError, match="approved or rejected"):
        await repository.resolve(
            session_id="sess_1",
            approval_id="approval_1",
            status="pending",
            resolved_by_user_id="user_2",
        )
