"""Session pack management."""

from __future__ import annotations

from hashlib import sha256

from turn.error import UAFError
from turn.pack import PackRegistry
from turn.session.model import SessionPackSelection


class PackManager:
    """Creates session-scoped pack selections from registered packs."""

    def __init__(self, registry: PackRegistry) -> None:
        self.registry = registry

    def select(
        self,
        *,
        session_id: str,
        pack_ids: tuple[str, ...],
        tool_names: tuple[str, ...] = (),
        revision: int = 1,
    ) -> SessionPackSelection:
        if revision < 1:
            raise ValueError("pack selection revision must be positive")
        missing = [pack_id for pack_id in pack_ids if self.registry.get(pack_id) is None]
        if missing:
            raise UAFError(
                code="pack.not_found",
                message="Pack is not registered",
                metadata={"pack_id": missing[0]},
            )
        enabled_tools = tool_names or _tools_for_pack_ids(self.registry, pack_ids)
        checksum = _selection_checksum(
            pack_ids=pack_ids, tool_names=enabled_tools, revision=revision
        )
        return SessionPackSelection(
            selection_id=f"sel_{checksum[:16]}",
            session_id=session_id,
            enabled_pack_ids=pack_ids,
            enabled_tool_names=enabled_tools,
            revision=revision,
            checksum=checksum,
        )


def _tools_for_pack_ids(registry: PackRegistry, pack_ids: tuple[str, ...]) -> tuple[str, ...]:
    names: list[str] = []
    for pack_id in pack_ids:
        registration = registry.get(pack_id)
        if registration is None:
            continue
        names.extend(tool.name for tool in registration.manifest.tools)
    return tuple(names)


def _selection_checksum(
    *,
    pack_ids: tuple[str, ...],
    tool_names: tuple[str, ...],
    revision: int,
) -> str:
    digest = sha256()
    for part in (*pack_ids, *tool_names, str(revision)):
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


__all__ = ["PackManager"]
