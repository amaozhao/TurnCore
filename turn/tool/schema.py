"""Tool schema models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class ToolEffect(str, Enum):
    """Side-effect class used by the tool runtime scheduler."""

    READONLY = "readonly"
    IDEMPOTENT_WRITE = "idempotent_write"
    WRITE = "write"
    DESTRUCTIVE = "destructive"


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    data: dict[str, object] = {} if value is None else dict(value)
    return MappingProxyType(data)


@dataclass(frozen=True)
class ToolDefinition:
    """Provider-neutral tool definition exposed to model adapters."""

    name: str
    description: str
    parameters: Mapping[str, object] = field(default_factory=_empty_mapping)
    effect: ToolEffect = ToolEffect.READONLY
    timeout_seconds: float | None = None
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("tool name must be non-empty")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        object.__setattr__(self, "parameters", _freeze_mapping(self.parameters))
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True)
class ToolCall:
    """One tool invocation requested for a turn."""

    call_id: str
    name: str
    arguments: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.call_id:
            raise ValueError("tool call_id must be non-empty")
        if not self.name:
            raise ValueError("tool name must be non-empty")
        object.__setattr__(self, "arguments", _freeze_mapping(self.arguments))


__all__ = ["ToolCall", "ToolDefinition", "ToolEffect"]
