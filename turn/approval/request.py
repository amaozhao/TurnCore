"""Approval request models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Literal, Mapping

ApprovalStatus = Literal["pending", "approved", "rejected"]


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class ApprovalRequest:
    """Session/turn-scoped approval request."""

    approval_id: str
    session_id: str
    turn_id: str
    run_id: str | None
    action: str
    reason: str
    status: ApprovalStatus
    requested_by_user_id: str
    resolved_by_user_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.approval_id:
            raise ValueError("approval_id must be non-empty")
        if not self.session_id:
            raise ValueError("approval session_id must be non-empty")
        if not self.turn_id:
            raise ValueError("approval turn_id must be non-empty")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


__all__ = ["ApprovalRequest", "ApprovalStatus"]
