import pytest

from turn.control import PackManager
from turn.error import UAFError
from turn.pack import PackManifest, PackRegistry, ToolReference


class ToolPack:
    def describe(self) -> PackManifest:
        return PackManifest(
            pack_id="pack_1",
            name="Pack",
            version="0.1.0",
            entrypoint="example:Pack",
            tools=(ToolReference(name="search", class_path="example:Search"),),
        )

    def register(self, registrar: object) -> None:
        return None


def test_pack_manager_creates_session_scoped_selection() -> None:
    registry = PackRegistry()
    registry.register(ToolPack())
    manager = PackManager(registry)

    selection = manager.select(session_id="sess_1", pack_ids=("pack_1",))

    assert selection.session_id == "sess_1"
    assert selection.enabled_pack_ids == ("pack_1",)
    assert selection.enabled_tool_names == ("search",)
    assert selection.revision == 1
    assert selection.selection_id.startswith("sel_")


def test_pack_manager_rejects_unregistered_pack() -> None:
    manager = PackManager(PackRegistry())

    with pytest.raises(UAFError) as error:
        manager.select(session_id="sess_1", pack_ids=("missing",))

    assert error.value.code == "pack.not_found"
