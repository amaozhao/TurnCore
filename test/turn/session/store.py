import asyncio
from dataclasses import replace

from turn.session.model import SessionPackSelection
from turn.session.store import MemorySessionStore


def test_memory_session_store_manages_session_lifecycle() -> None:
    asyncio.run(check_memory_session_store_manages_session_lifecycle())


async def check_memory_session_store_manages_session_lifecycle() -> None:
    store = MemorySessionStore()

    first = await store.create_session(owner_user_id="user_1", title="First")
    second = await store.create_session(owner_user_id="user_1", title="Second")
    other = await store.create_session(owner_user_id="user_2", title="Other")

    assert await store.get_session(first.session_id) == first
    page = await store.list_sessions_for_user(owner_user_id="user_1", limit=1)
    assert page.items == (first,)
    assert page.next_cursor == "1"

    next_page = await store.list_sessions_for_user(
        owner_user_id="user_1",
        limit=5,
        cursor=page.next_cursor,
    )
    assert next_page.items == (second,)
    assert other not in page.items + next_page.items

    renamed = replace(first, title="Renamed")
    await store.update_session(renamed)
    assert (await store.get_session(first.session_id)).title == "Renamed"  # type: ignore[union-attr]

    await store.archive_session(first.session_id)
    archived = await store.get_session(first.session_id)
    assert archived is not None
    assert archived.status == "archived"


def test_memory_session_store_manages_pack_selection() -> None:
    asyncio.run(check_memory_session_store_manages_pack_selection())


async def check_memory_session_store_manages_pack_selection() -> None:
    store = MemorySessionStore()
    selection = SessionPackSelection(
        selection_id="sel_1",
        session_id="sess_1",
        enabled_pack_ids=("pack_1",),
        enabled_tool_names=("tool_1",),
        revision=1,
        checksum="checksum",
    )

    await store.save_selection(selection)

    assert await store.get_selection("sess_1") == selection
    assert await store.get_selection("sess_missing") is None
