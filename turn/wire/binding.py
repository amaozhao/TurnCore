"""Transport binding helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from types import MappingProxyType
from typing import Literal, Mapping, cast

from turn.event import StreamEvent
from turn.wire.command import CommandEnvelope, CommandType
from turn.wire.error import ErrorEnvelope

WireMessageType = Literal["command", "event", "error", "ping"]
RestMethod = Literal["GET", "POST"]

_COMMAND_TYPES: tuple[CommandType, ...] = (
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
)


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class WireMessage:
    """Transport-neutral message used by websocket-like bindings."""

    type: WireMessageType
    data: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", _freeze_mapping(self.data))


@dataclass(frozen=True)
class SseEvent:
    """SSE frame data without server implementation."""

    event: str
    data: Mapping[str, object]
    id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "data", _freeze_mapping(self.data))


@dataclass(frozen=True)
class RestRequest:
    """REST-style request mapped by adapters into a command."""

    method: RestMethod
    path: str
    body: Mapping[str, object] = field(default_factory=_empty_mapping)
    query: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "body", _freeze_mapping(self.body))
        object.__setattr__(self, "query", _freeze_mapping(self.query))


@dataclass(frozen=True)
class RestResponse:
    """REST-style response payload without HTTP status policy."""

    body: Mapping[str, object]
    status: int = 200

    def __post_init__(self) -> None:
        object.__setattr__(self, "body", _freeze_mapping(self.body))


@dataclass(frozen=True)
class TextCommandInput:
    """CLI or IM text command input."""

    text: str
    session_id: str | None = None
    turn_id: str | None = None
    command_id: str = ""


def command_to_wire(command: CommandEnvelope) -> WireMessage:
    return WireMessage(type="command", data=command_to_mapping(command))


def wire_to_command(message: WireMessage) -> CommandEnvelope | None:
    if message.type == "ping":
        return None
    if message.type != "command":
        raise ValueError("wire message must be command or ping")
    return command_from_mapping(message.data)


def event_to_wire(event: StreamEvent) -> WireMessage:
    return WireMessage(type="event", data=event_to_mapping(event))


def error_to_wire(error: ErrorEnvelope) -> WireMessage:
    return WireMessage(type="error", data=error_to_mapping(error))


def event_to_sse(event: StreamEvent) -> SseEvent:
    return SseEvent(event=event.type, data=event_to_mapping(event), id=str(event.seq))


def error_to_sse(error: ErrorEnvelope) -> SseEvent:
    return SseEvent(event="error", data=error_to_mapping(error))


def command_from_rest(request: RestRequest) -> CommandEnvelope:
    payload = request.body if request.method == "POST" else request.query
    return CommandEnvelope(
        command_id=_required_text(payload, "command_id"),
        type=_command_type(_required_text(payload, "type")),
        session_id=_optional_text(payload, "session_id"),
        turn_id=_optional_text(payload, "turn_id"),
        payload=_payload(payload),
        idempotency_key=_optional_text(payload, "idempotency_key"),
    )


def event_to_rest(event: StreamEvent) -> RestResponse:
    return RestResponse(body=event_to_mapping(event))


def error_to_rest(error: ErrorEnvelope, *, status: int = 400) -> RestResponse:
    return RestResponse(body=error_to_mapping(error), status=status)


def command_from_text(
    item: TextCommandInput,
    *,
    type: CommandType = "start_turn",
) -> CommandEnvelope:
    if not item.text:
        raise ValueError("text command must be non-empty")
    command_id = item.command_id or f"{type}:{_text_command_digest(item, type)}"
    return CommandEnvelope(
        command_id=command_id,
        type=type,
        session_id=item.session_id,
        turn_id=item.turn_id,
        payload={"content": item.text},
    )


def event_to_text(event: StreamEvent) -> str:
    return event.content or event.type


def error_to_text(error: ErrorEnvelope) -> str:
    return f"{error.code}: {error.message}"


def command_to_mapping(command: CommandEnvelope) -> Mapping[str, object]:
    data: dict[str, object] = {
        "command_id": command.command_id,
        "type": command.type,
        "session_id": "" if command.session_id is None else command.session_id,
        "turn_id": "" if command.turn_id is None else command.turn_id,
        "payload": dict(command.payload),
    }
    if command.idempotency_key is not None:
        data["idempotency_key"] = command.idempotency_key
    return MappingProxyType(data)


def command_from_mapping(data: Mapping[str, object]) -> CommandEnvelope:
    return CommandEnvelope(
        command_id=_required_text(data, "command_id"),
        type=_command_type(_required_text(data, "type")),
        session_id=_optional_text(data, "session_id"),
        turn_id=_optional_text(data, "turn_id"),
        payload=_payload(data),
        idempotency_key=_optional_text(data, "idempotency_key"),
    )


def event_to_mapping(event: StreamEvent) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "event_id": event.event_id,
            "session_id": event.session_id,
            "turn_id": event.turn_id,
            "seq": event.seq,
            "type": event.type,
            "source": event.source,
            "stage": event.stage,
            "content": event.content,
            "metadata": dict(event.metadata),
            "created_at": _datetime_text(event.created_at),
        }
    )


def error_to_mapping(error: ErrorEnvelope) -> Mapping[str, object]:
    data: dict[str, object] = {
        "code": error.code,
        "message": error.message,
        "retryable": error.retryable,
        "details": dict(error.details),
    }
    if error.session_id is not None:
        data["session_id"] = error.session_id
    if error.turn_id is not None:
        data["turn_id"] = error.turn_id
    if error.run_id is not None:
        data["run_id"] = error.run_id
    return MappingProxyType(data)


def _required_text(data: Mapping[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional_text(data: Mapping[str, object], key: str) -> str | None:
    value = data.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _payload(data: Mapping[str, object]) -> Mapping[str, object]:
    value = data.get("payload")
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("payload must be a mapping")
    raw = cast(dict[object, object], value)
    payload: dict[str, object] = {}
    for key, item in raw.items():
        if not isinstance(key, str):
            raise ValueError("payload keys must be strings")
        payload[key] = item
    return MappingProxyType(payload)


def _command_type(value: str) -> CommandType:
    if value not in _COMMAND_TYPES:
        raise ValueError("unknown command type")
    return value


def _datetime_text(value: datetime) -> str:
    return value.isoformat()


def _text_command_digest(item: TextCommandInput, type: CommandType) -> str:
    digest = sha256()
    for part in (type, item.session_id or "", item.turn_id or "", item.text):
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:16]


__all__ = [
    "RestRequest",
    "RestResponse",
    "SseEvent",
    "TextCommandInput",
    "WireMessage",
    "WireMessageType",
    "command_from_mapping",
    "command_from_rest",
    "command_from_text",
    "command_to_mapping",
    "command_to_wire",
    "error_to_mapping",
    "error_to_rest",
    "error_to_sse",
    "error_to_text",
    "error_to_wire",
    "event_to_mapping",
    "event_to_rest",
    "event_to_sse",
    "event_to_text",
    "event_to_wire",
    "wire_to_command",
]
