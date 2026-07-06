import asyncio
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from turn.run.model import Message, Run, Turn
from turn.run.store import MemoryMessageStore, MemoryRunStore, MemoryTurnStore


def test_memory_turn_store_manages_turn_lifecycle() -> None:
    asyncio.run(check_memory_turn_store_manages_turn_lifecycle())


async def check_memory_turn_store_manages_turn_lifecycle() -> None:
    store = MemoryTurnStore()
    now = datetime.now(timezone.utc)
    turn = Turn(
        turn_id="turn_1",
        session_id="sess_1",
        parent_turn_id=None,
        status="queued",
        command_snapshot={},
        prompt_snapshot_id=None,
        tool_registry_snapshot_id=None,
        memory_snapshot_id=None,
        created_at=now,
        started_at=None,
        completed_at=None,
    )

    await store.create_turn(turn)
    assert await store.get_turn("turn_1") == turn

    with pytest.raises(KeyError):
        await store.create_turn(turn)

    running = replace(turn, status="running", started_at=now)
    await store.update_turn(running)
    assert await store.get_turn("turn_1") == running


def test_memory_message_and_run_stores_are_session_and_turn_scoped() -> None:
    asyncio.run(check_memory_message_and_run_stores_are_session_and_turn_scoped())


async def check_memory_message_and_run_stores_are_session_and_turn_scoped() -> None:
    now = datetime.now(timezone.utc)
    message_store = MemoryMessageStore()
    run_store = MemoryRunStore()
    message = Message(
        message_id="msg_1",
        session_id="sess_1",
        turn_id="turn_1",
        role="user",
        content="hello",
        artifact_ids=(),
        created_at=now,
    )
    run = Run(
        run_id="run_1",
        session_id="sess_1",
        turn_id="turn_1",
        kind="agent_loop",
        status="queued",
        input_summary="input",
        output_summary=None,
        error=None,
        created_at=now,
        completed_at=None,
    )

    await message_store.append_message(message)
    await run_store.create_run(run)

    assert (await message_store.list_messages(session_id="sess_1", limit=10)).items == (message,)
    assert await run_store.list_runs_for_turn("turn_1") == (run,)
