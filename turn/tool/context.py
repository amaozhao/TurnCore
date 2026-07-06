"""Tool execution context."""

from __future__ import annotations

from dataclasses import dataclass

from turn.artifact import ArtifactStore
from turn.event.sink import EventSink
from turn.memory import SessionMemoryPort
from turn.policy import PolicyRuntime
from turn.run.cancel import CancellationToken
from turn.secret import SecretLeaseProvider
from turn.user import Principal


@dataclass(frozen=True)
class ToolContext:
    """Session-scoped handles available to contextual tools."""

    session_id: str
    turn_id: str
    run_id: str
    principal: Principal
    event_sink: EventSink
    artifact_store: ArtifactStore
    memory: SessionMemoryPort
    secrets: SecretLeaseProvider
    cancellation_token: CancellationToken
    policy: PolicyRuntime


__all__ = ["ToolContext"]
