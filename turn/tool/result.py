"""Tool execution result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from turn.wire.error import ErrorEnvelope


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    data: dict[str, object] = {} if value is None else dict(value)
    return MappingProxyType(data)


@dataclass(frozen=True)
class ToolResult:
    """Safe result returned from a tool invocation."""

    call_id: str
    tool_name: str
    content: str
    success: bool
    error: ErrorEnvelope | None = None
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


__all__ = ["ToolResult"]
