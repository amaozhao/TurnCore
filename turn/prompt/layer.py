"""Prompt source layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Literal, Mapping, Self

PromptSourceType = Literal[
    "framework_builtin",
    "pack_builtin",
    "user_default",
    "session_profile",
    "turn_overlay",
    "memory_injection",
    "knowledge_injection",
    "tool_manifest",
    "capability_manifest",
]


def prompt_checksum(content: str) -> str:
    """Return the stable checksum used for prompt source content."""

    return sha256(content.encode("utf-8")).hexdigest()


def _empty_metadata() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if metadata is None else dict(metadata))


@dataclass(frozen=True)
class PromptSource:
    """One immutable prompt input captured before turn execution."""

    source_id: str
    source_type: PromptSourceType
    priority: int
    content: str
    checksum: str
    metadata: Mapping[str, object] = field(default_factory=_empty_metadata)

    @classmethod
    def from_text(
        cls,
        *,
        source_id: str,
        source_type: PromptSourceType,
        priority: int,
        content: str,
        metadata: Mapping[str, object] | None = None,
    ) -> Self:
        return cls(
            source_id=source_id,
            source_type=source_type,
            priority=priority,
            content=content,
            checksum=prompt_checksum(content),
            metadata=_freeze_metadata(metadata),
        )


__all__ = ["PromptSource", "PromptSourceType", "prompt_checksum"]
