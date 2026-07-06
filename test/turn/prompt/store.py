import asyncio

import pytest

from turn.prompt import DefaultPromptCompiler, MemoryPromptSnapshotStore, PromptCompileCommand


def test_memory_prompt_snapshot_store_is_session_and_turn_scoped() -> None:
    asyncio.run(check_memory_prompt_snapshot_store_is_session_and_turn_scoped())


async def check_memory_prompt_snapshot_store_is_session_and_turn_scoped() -> None:
    compiler = DefaultPromptCompiler()
    first = await compiler.compile_for_turn(
        PromptCompileCommand(session_id="sess_1", turn_id="turn_1", turn_overlay="one")
    )
    second = await compiler.compile_for_turn(
        PromptCompileCommand(session_id="sess_2", turn_id="turn_1", turn_overlay="two")
    )
    store = MemoryPromptSnapshotStore()

    await store.save(first)
    await store.save(second)

    assert await store.get_by_turn(session_id="sess_1", turn_id="turn_1") == first
    assert await store.get_by_turn(session_id="sess_2", turn_id="turn_1") == second
    assert await store.get_by_turn(session_id="sess_1", turn_id="missing") is None


def test_memory_prompt_snapshot_store_rejects_overwrite() -> None:
    asyncio.run(check_memory_prompt_snapshot_store_rejects_overwrite())


async def check_memory_prompt_snapshot_store_rejects_overwrite() -> None:
    compiler = DefaultPromptCompiler()
    first = await compiler.compile_for_turn(
        PromptCompileCommand(session_id="sess_1", turn_id="turn_1", turn_overlay="one")
    )
    second = await compiler.compile_for_turn(
        PromptCompileCommand(session_id="sess_1", turn_id="turn_1", turn_overlay="two")
    )
    store = MemoryPromptSnapshotStore()

    await store.save(first)

    with pytest.raises(KeyError):
        await store.save(second)
    assert await store.get_by_turn(session_id="sess_1", turn_id="turn_1") == first
