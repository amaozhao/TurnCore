"""Artifact renderer protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class ArtifactRenderInput:
    """Artifact data passed to a renderer."""

    artifact_id: str
    session_id: str
    turn_id: str
    content_type: str
    content: bytes
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True)
class ArtifactRenderResult:
    """Renderer output for transport adapters."""

    content_type: str
    content: str
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


class ArtifactRenderer(Protocol):
    """Protocol implemented by pack artifact renderers."""

    @property
    def artifact_type(self) -> str: ...

    def render(self, item: ArtifactRenderInput) -> ArtifactRenderResult: ...


__all__ = ["ArtifactRenderInput", "ArtifactRenderResult", "ArtifactRenderer"]
