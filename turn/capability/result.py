"""Capability result model."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Mapping

from turn.wire.error import ErrorEnvelope

CapabilityStatus = Literal["completed", "failed", "waiting_for_user", "waiting_for_approval"]


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class CapabilityResult:
    """Result returned by a capability."""

    status: CapabilityStatus
    content: str = ""
    error: ErrorEnvelope | None = None
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


__all__ = ["CapabilityResult", "CapabilityStatus"]
