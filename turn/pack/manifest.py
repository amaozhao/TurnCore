"""Pack manifest models."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from turn.policy import PolicyRuleDefinition
from turn.prompt import PromptSourceType


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class PackRuntime:
    """Runtime requirements declared by a pack manifest."""

    min_uaf_version: str = ""


@dataclass(frozen=True)
class PackPermissions:
    """Permission declaration from pack.yaml."""

    tools: tuple[str, ...] = ()
    network_hosts: tuple[str, ...] = ()
    filesystem_read: tuple[str, ...] = ()
    filesystem_write: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromptSourceDefinition:
    """Prompt source declared by a pack."""

    source_id: str
    file: str
    source_type: PromptSourceType = "pack_builtin"
    priority: int = 0
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("prompt source_id must be non-empty")
        if not self.file:
            raise ValueError("prompt file must be non-empty")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True)
class ToolReference:
    """Tool entry declared by pack.yaml."""

    name: str
    class_path: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("tool name must be non-empty")
        if not self.class_path:
            raise ValueError("tool class_path must be non-empty")


@dataclass(frozen=True)
class CapabilityReference:
    """Capability entry declared by pack.yaml."""

    name: str
    class_path: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("capability name must be non-empty")
        if not self.class_path:
            raise ValueError("capability class_path must be non-empty")


@dataclass(frozen=True)
class ArtifactRendererReference:
    """Artifact renderer entry declared by pack.yaml."""

    class_path: str
    artifact_type: str = ""

    def __post_init__(self) -> None:
        if not self.class_path:
            raise ValueError("artifact renderer class_path must be non-empty")


@dataclass(frozen=True)
class PackManifest:
    """Python representation of pack.yaml."""

    pack_id: str
    name: str
    version: str
    entrypoint: str
    runtime: PackRuntime = PackRuntime()
    permissions: PackPermissions = PackPermissions()
    prompts: tuple[PromptSourceDefinition, ...] = ()
    capabilities: tuple[CapabilityReference, ...] = ()
    tools: tuple[ToolReference, ...] = ()
    artifact_renderers: tuple[ArtifactRendererReference, ...] = ()
    policy_rules: tuple[PolicyRuleDefinition, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.pack_id:
            raise ValueError("pack_id must be non-empty")
        if not self.name:
            raise ValueError("pack name must be non-empty")
        if not self.version:
            raise ValueError("pack version must be non-empty")
        if not self.entrypoint:
            raise ValueError("pack entrypoint must be non-empty")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


__all__ = [
    "ArtifactRendererReference",
    "CapabilityReference",
    "PackManifest",
    "PackPermissions",
    "PackRuntime",
    "PromptSourceDefinition",
    "ToolReference",
]
