import asyncio

import pytest

from turn.tool import MemoryToolRegistrySnapshotStore, ToolDefinition, ToolRegistrySnapshot


def test_memory_tool_registry_snapshot_store_rejects_overwrite() -> None:
    asyncio.run(check_memory_tool_registry_snapshot_store_rejects_overwrite())


async def check_memory_tool_registry_snapshot_store_rejects_overwrite() -> None:
    store = MemoryToolRegistrySnapshotStore()
    first = ToolRegistrySnapshot(
        snapshot_id="tool_1",
        session_id="sess_1",
        turn_id="turn_1",
        tools={"echo": ToolDefinition(name="echo", description="Echo")},
    )
    second = ToolRegistrySnapshot(
        snapshot_id="tool_2",
        session_id="sess_1",
        turn_id="turn_1",
        tools={"other": ToolDefinition(name="other", description="Other")},
    )

    await store.save(first)

    with pytest.raises(KeyError):
        await store.save(second)
    assert await store.get_by_turn(session_id="sess_1", turn_id="turn_1") == first
    assert await store.get_by_turn(session_id="sess_1", turn_id="missing") is None
