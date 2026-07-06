"""Prompt compiler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Final, Iterable, Protocol

from turn.prompt.layer import PromptSource, PromptSourceType
from turn.prompt.profile import SessionPromptProfile
from turn.prompt.snapshot import PromptSnapshot

_SOURCE_ORDER: Final[dict[PromptSourceType, int]] = {
    "framework_builtin": 0,
    "capability_manifest": 1,
    "pack_builtin": 2,
    "tool_manifest": 3,
    "user_default": 4,
    "session_profile": 5,
    "memory_injection": 6,
    "knowledge_injection": 7,
    "turn_overlay": 8,
}
_MANIFEST_TYPES: Final[tuple[PromptSourceType, ...]] = (
    "tool_manifest",
    "capability_manifest",
)


@dataclass(frozen=True)
class PromptCompileCommand:
    """Inputs needed to freeze a turn prompt snapshot."""

    session_id: str
    turn_id: str
    sources: tuple[PromptSource, ...] = ()
    profile: SessionPromptProfile | None = None
    memory_injection: str | None = None
    knowledge_injection: str | None = None
    turn_overlay: str | None = None
    tool_manifest: str | None = None
    capability_manifest: str | None = None


class PromptCompiler(Protocol):
    """Port for compiling one turn's immutable prompt snapshot."""

    async def compile_for_turn(self, command: PromptCompileCommand) -> PromptSnapshot: ...


class DefaultPromptCompiler:
    """Deterministic prompt compiler for core runtime tests and adapters."""

    async def compile_for_turn(self, command: PromptCompileCommand) -> PromptSnapshot:
        if command.profile is not None and command.profile.session_id != command.session_id:
            raise ValueError("profile session_id must match command session_id")
        sources = _ordered_sources(
            (
                *command.sources,
                *_profile_sources(command.profile),
                *_optional_sources(command),
            )
        )
        system_prompt = _join(
            source.content for source in sources if source.source_type not in _MANIFEST_TYPES
        )
        tool_manifest = _join(
            source.content for source in sources if source.source_type == "tool_manifest"
        )
        capability_manifest = _join(
            source.content for source in sources if source.source_type == "capability_manifest"
        )
        checksum = _snapshot_checksum(
            session_id=command.session_id,
            turn_id=command.turn_id,
            sources=sources,
            system_prompt=system_prompt,
            developer_prompt=None,
            tool_manifest=tool_manifest,
            capability_manifest=capability_manifest,
        )
        return PromptSnapshot(
            snapshot_id=f"prompt_{checksum[:16]}",
            session_id=command.session_id,
            turn_id=command.turn_id,
            sources=sources,
            compiled_system_prompt=system_prompt,
            compiled_developer_prompt=None,
            compiled_tool_manifest=tool_manifest,
            compiled_capability_manifest=capability_manifest,
            checksum=checksum,
            created_at=datetime.now(timezone.utc),
        )


def _profile_sources(profile: SessionPromptProfile | None) -> tuple[PromptSource, ...]:
    if profile is None:
        return ()
    sections: tuple[tuple[str, int, str], ...] = (
        ("safety", 0, profile.safety_prompt),
        ("base", 10, profile.base_prompt),
        ("persona", 20, profile.persona_prompt),
        ("style", 30, profile.style_prompt),
    )
    return tuple(
        PromptSource.from_text(
            source_id=f"session_profile:{profile.profile_id}:{section}",
            source_type="session_profile",
            priority=priority,
            content=content,
            metadata={
                "profile_id": profile.profile_id,
                "session_id": profile.session_id,
                "section": section,
            },
        )
        for section, priority, content in sections
        if content
    )


def _optional_sources(command: PromptCompileCommand) -> tuple[PromptSource, ...]:
    specs: tuple[tuple[str, PromptSourceType, int, str | None], ...] = (
        ("capability_manifest", "capability_manifest", 0, command.capability_manifest),
        ("tool_manifest", "tool_manifest", 0, command.tool_manifest),
        ("memory", "memory_injection", 0, command.memory_injection),
        ("knowledge", "knowledge_injection", 0, command.knowledge_injection),
        ("turn_overlay", "turn_overlay", 0, command.turn_overlay),
    )
    return tuple(
        PromptSource.from_text(
            source_id=f"{name}:{command.session_id}:{command.turn_id}",
            source_type=source_type,
            priority=priority,
            content=content,
            metadata={"session_id": command.session_id, "turn_id": command.turn_id},
        )
        for name, source_type, priority, content in specs
        if content
    )


def _ordered_sources(sources: Iterable[PromptSource]) -> tuple[PromptSource, ...]:
    return tuple(
        sorted(
            sources,
            key=lambda source: (
                _SOURCE_ORDER[source.source_type],
                source.priority,
                source.source_id,
            ),
        )
    )


def _join(parts: Iterable[str]) -> str:
    return "\n\n".join(part for part in parts if part)


def _snapshot_checksum(
    *,
    session_id: str,
    turn_id: str,
    sources: tuple[PromptSource, ...],
    system_prompt: str,
    developer_prompt: str | None,
    tool_manifest: str,
    capability_manifest: str,
) -> str:
    digest = sha256()
    for part in (
        session_id,
        turn_id,
        system_prompt,
        developer_prompt or "",
        tool_manifest,
        capability_manifest,
    ):
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    for source in sources:
        for part in (
            source.source_id,
            source.source_type,
            str(source.priority),
            source.checksum,
            source.content,
        ):
            digest.update(part.encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


__all__ = ["DefaultPromptCompiler", "PromptCompileCommand", "PromptCompiler"]
