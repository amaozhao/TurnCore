"""Transport-independent command envelope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping


CommandType = Literal[
    "create_session",
    "start_turn",
    "subscribe_turn",
    "resume_turn",
    "cancel_turn",
    "submit_user_reply",
    "submit_approval",
    "list_sessions",
    "list_messages",
    "list_events",
    "upload_file",
]


@dataclass(frozen=True)
class CommandEnvelope:
    """Command submitted through any adapter binding."""

    command_id: str
    type: CommandType
    session_id: str | None
    turn_id: str | None
    payload: Mapping[str, object]
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if "user_id" in self.payload:
            raise ValueError("command payload must not carry trusted user_id")


__all__ = ["CommandEnvelope", "CommandType"]
