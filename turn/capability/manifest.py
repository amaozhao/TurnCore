"""Capability manifest models."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class CapabilityStage:
    """Declared stage in a capability flow."""

    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("capability stage name must be non-empty")


@dataclass(frozen=True)
class CapabilityManifest:
    """Capability metadata declared by a pack."""

    name: str
    description: str = ""
    stages: tuple[CapabilityStage, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("capability name must be non-empty")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


__all__ = ["CapabilityManifest", "CapabilityStage"]
