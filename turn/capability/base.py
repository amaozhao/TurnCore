"""Capability protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol

from turn.artifact import ArtifactStore
from turn.event.sink import EventSink
from turn.memory import MemorySnapshot, SessionMemoryPort
from turn.model import ModelPort
from turn.policy import PolicyRuntime
from turn.prompt import PromptSnapshot
from turn.run.cancel import CancellationToken
from turn.secret import SecretLeaseProvider
from turn.tool import ToolRuntime
from turn.user import Principal
from turn.capability.manifest import CapabilityManifest
from turn.capability.result import CapabilityResult


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class CapabilityContext:
    """Turn-scoped context passed to capabilities."""

    session_id: str
    turn_id: str
    principal: Principal
    user_message: str
    prompt_snapshot: PromptSnapshot
    memory_snapshot: MemorySnapshot
    tool_runtime: ToolRuntime
    model: ModelPort
    event_sink: EventSink
    artifact_store: ArtifactStore
    memory: SessionMemoryPort
    secrets: SecretLeaseProvider
    policy: PolicyRuntime
    cancellation_token: CancellationToken
    config: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "config", _freeze_mapping(self.config))


class BaseCapability(Protocol):
    """Protocol implemented by pack capabilities."""

    @property
    def manifest(self) -> CapabilityManifest: ...

    async def run(self, context: CapabilityContext) -> CapabilityResult: ...


__all__ = ["BaseCapability", "CapabilityContext"]
