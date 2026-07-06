import asyncio

import pytest

from turn.error import UAFError
from turn.run.store import MemoryTurnStore
from turn.session import SessionAuthorizer
from turn.session.store import MemorySessionStore
from turn.user import Principal


def test_session_authorizer_checks_owner() -> None:
    asyncio.run(check_session_authorizer_checks_owner())


async def check_session_authorizer_checks_owner() -> None:
    sessions = MemorySessionStore()
    turns = MemoryTurnStore()
    session = await sessions.create_session(owner_user_id="user_1", title="One")
    authorizer = SessionAuthorizer(sessions, turns)

    assert await authorizer.authorize_session(Principal(user_id="user_1"), session.session_id)

    with pytest.raises(UAFError) as error:
        await authorizer.authorize_session(Principal(user_id="user_2"), session.session_id)

    assert error.value.code == "session.access_denied"
