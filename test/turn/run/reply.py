import asyncio
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from turn.error import UAFError
from turn.run import Turn
from turn.run.reply import UserReplyService
from turn.run.store import MemoryTurnStore
from turn.session import SessionAuthorizer
from turn.session.store import MemorySessionStore
from turn.user import Principal


def test_user_reply_service_resumes_waiting_turn() -> None:
    asyncio.run(check_user_reply_service_resumes_waiting_turn())


async def check_user_reply_service_resumes_waiting_turn() -> None:
    sessions = MemorySessionStore()
    turns = MemoryTurnStore()
    session = await sessions.create_session(owner_user_id="user_1", title="One")
    now = datetime.now(timezone.utc)
    turn = Turn(
        turn_id="turn_1",
        session_id=session.session_id,
        parent_turn_id=None,
        status="waiting_for_user",
        command_snapshot={},
        prompt_snapshot_id=None,
        tool_registry_snapshot_id=None,
        memory_snapshot_id=None,
        created_at=now,
        started_at=now,
        completed_at=None,
    )
    await turns.create_turn(turn)
    service = UserReplyService(turns=turns, authorizer=SessionAuthorizer(sessions, turns))

    await service.submit_user_reply(
        principal=Principal(user_id="user_1"),
        turn_id="turn_1",
        content="reply",
    )

    assert await turns.get_turn("turn_1") == replace(turn, status="running")

    with pytest.raises(UAFError) as error:
        await service.submit_user_reply(
            principal=Principal(user_id="user_1"),
            turn_id="turn_1",
            content="reply again",
        )

    assert error.value.code == "turn.not_waiting_for_user"
