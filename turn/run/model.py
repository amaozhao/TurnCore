"""Turn, run, and message protocol models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping

from turn.wire.error import ErrorEnvelope


@dataclass(frozen=True)
class Message:
    """Session-scoped conversation message."""

    message_id: str
    session_id: str
    turn_id: str | None
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    artifact_ids: tuple[str, ...]
    created_at: datetime


@dataclass(frozen=True)
class Turn:
    """Execution boundary for one user request."""

    turn_id: str
    session_id: str
    parent_turn_id: str | None
    status: Literal[
        "queued",
        "running",
        "waiting_for_user",
        "waiting_for_approval",
        "completed",
        "failed",
        "cancelled",
    ]
    command_snapshot: Mapping[str, object]
    prompt_snapshot_id: str | None
    tool_registry_snapshot_id: str | None
    memory_snapshot_id: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


@dataclass(frozen=True)
class Run:
    """Concrete execution instance inside a turn."""

    run_id: str
    session_id: str
    turn_id: str
    kind: Literal["agent_loop", "capability_stage", "team_task", "tool_batch"]
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    input_summary: str
    output_summary: str | None
    error: ErrorEnvelope | None
    created_at: datetime
    completed_at: datetime | None


__all__ = ["Message", "Run", "Turn"]
