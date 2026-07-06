"""Model port contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Mapping, Protocol

from turn.tool.schema import ToolDefinition

ModelRole = Literal["system", "developer", "user", "assistant", "tool"]
ModelFinishReason = Literal["stop", "tool_calls", "length", "error"]


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    data: dict[str, object] = {} if value is None else dict(value)
    return MappingProxyType(data)


@dataclass(frozen=True)
class ModelMessage:
    """Message sent to or returned from a model adapter."""

    role: ModelRole
    content: str
    tool_call_id: str | None = None


@dataclass(frozen=True)
class ModelToolCall:
    """Tool call requested by a model response."""

    call_id: str
    tool_name: str
    arguments: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", _freeze_mapping(self.arguments))


@dataclass(frozen=True)
class ModelRequest:
    """Turn-scoped model request."""

    session_id: str
    turn_id: str
    messages: tuple[ModelMessage, ...]
    tools: tuple[ToolDefinition, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True)
class ModelResponse:
    """Provider-neutral model response."""

    content: str
    tool_calls: tuple[ModelToolCall, ...] = ()
    finish_reason: ModelFinishReason = "stop"
    usage: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "usage", _freeze_mapping(self.usage))


class ModelPort(Protocol):
    """Port implemented by concrete model adapters outside core."""

    async def complete(self, request: ModelRequest) -> ModelResponse: ...


__all__ = [
    "ModelFinishReason",
    "ModelMessage",
    "ModelPort",
    "ModelRequest",
    "ModelResponse",
    "ModelRole",
    "ModelToolCall",
]
