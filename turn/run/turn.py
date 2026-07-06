"""Turn execution object."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from turn.event.sink import EventSink
from turn.prompt.snapshot import PromptSnapshot
from turn.run.cancel import CancellationToken
from turn.tool.registry import ToolRegistrySnapshot
from turn.user import Principal
from turn.wire import CommandEnvelope


@dataclass
class TurnExecution:
    """Runtime object scoped to one turn."""

    session_id: str
    turn_id: str
    command: CommandEnvelope
    principal: Principal
    cancellation_token: CancellationToken
    event_sink: EventSink
    started_at: datetime
    prompt_snapshot: PromptSnapshot | None = None
    memory_snapshot: object | None = None
    tool_registry_snapshot: ToolRegistrySnapshot | None = None
    capability_snapshot: object | None = None
    workspace: object | None = None
    secret_lease: object | None = None

    def raise_if_cancelled(self) -> None:
        self.cancellation_token.raise_if_cancelled()


__all__ = ["TurnExecution"]
