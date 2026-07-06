import asyncio

import pytest

from turn.error import UAFError
from turn.session.guard import MemorySessionTurnLock, SessionTurnLock


def test_session_turn_lock_allows_only_one_active_turn_per_session() -> None:
    asyncio.run(check_session_turn_lock_allows_only_one_active_turn_per_session())


async def check_session_turn_lock_allows_only_one_active_turn_per_session() -> None:
    lock: SessionTurnLock = MemorySessionTurnLock()

    async with await lock.acquire_active_turn_lock(
        session_id="sess_1",
        turn_id="turn_1",
        ttl_seconds=30,
    ):
        with pytest.raises(UAFError) as error:
            await lock.acquire_active_turn_lock(
                session_id="sess_1",
                turn_id="turn_2",
                ttl_seconds=30,
            )
        assert error.value.code == "session.active_turn_exists"

        async with await lock.acquire_active_turn_lock(
            session_id="sess_2",
            turn_id="turn_3",
            ttl_seconds=30,
        ):
            pass

    async with await lock.acquire_active_turn_lock(
        session_id="sess_1",
        turn_id="turn_2",
        ttl_seconds=30,
    ):
        pass
