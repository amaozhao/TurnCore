import asyncio
from collections.abc import AsyncIterator

from turn.artifact import MemoryArtifactStore


async def chunks() -> AsyncIterator[bytes]:
    yield b"hel"
    yield b"lo"


def test_artifact_store_uses_session_turn_uri() -> None:
    asyncio.run(check_artifact_store_uses_session_turn_uri())


async def check_artifact_store_uses_session_turn_uri() -> None:
    store = MemoryArtifactStore()

    artifact = await store.save(
        session_id="sess_1",
        turn_id="turn_1",
        run_id="run_1",
        filename="report.txt",
        mime_type="text/plain",
        content=b"hello",
    )

    assert artifact.uri == f"artifact://sessions/sess_1/turns/turn_1/{artifact.artifact_id}"
    assert artifact.size_bytes == 5
    assert await store.get(session_id="sess_1", artifact_id=artifact.artifact_id) == artifact
    assert await store.get(session_id="sess_2", artifact_id=artifact.artifact_id) is None
    assert (
        await store.read_content(session_id="sess_1", artifact_id=artifact.artifact_id) == b"hello"
    )


def test_artifact_store_accepts_async_content() -> None:
    asyncio.run(check_artifact_store_accepts_async_content())


async def check_artifact_store_accepts_async_content() -> None:
    store = MemoryArtifactStore()

    artifact = await store.save(
        session_id="sess_1",
        turn_id="turn_1",
        run_id=None,
        filename="report.txt",
        mime_type="text/plain",
        content=chunks(),
    )

    assert artifact.size_bytes == 5
    assert (
        await store.read_content(session_id="sess_1", artifact_id=artifact.artifact_id) == b"hello"
    )
