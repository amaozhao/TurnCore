"""Audit record model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Literal, Mapping

AuditAction = Literal["pack", "run", "approval", "artifact", "secret", "team", "eval"]


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class AuditRecord:
    """Session-scoped audit event."""

    record_id: str
    session_id: str
    turn_id: str | None
    actor_user_id: str
    action: AuditAction
    summary: str
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("audit record_id must be non-empty")
        if not self.session_id:
            raise ValueError("audit session_id must be non-empty")
        if not self.actor_user_id:
            raise ValueError("audit actor_user_id must be non-empty")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


__all__ = ["AuditAction", "AuditRecord"]
