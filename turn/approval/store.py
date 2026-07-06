"""Approval repository."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Protocol

from turn.approval.request import ApprovalRequest, ApprovalStatus


class ApprovalRepository(Protocol):
    """Port for session-scoped approval requests."""

    async def create(self, request: ApprovalRequest) -> None: ...

    async def get(self, *, session_id: str, approval_id: str) -> ApprovalRequest | None: ...

    async def list_by_turn(
        self, *, session_id: str, turn_id: str
    ) -> tuple[ApprovalRequest, ...]: ...

    async def resolve(
        self,
        *,
        session_id: str,
        approval_id: str,
        status: ApprovalStatus,
        resolved_by_user_id: str,
    ) -> ApprovalRequest: ...


class MemoryApprovalRepository:
    """Approval repository backed by process memory."""

    def __init__(self) -> None:
        self.requests: dict[tuple[str, str], ApprovalRequest] = {}

    async def create(self, request: ApprovalRequest) -> None:
        key = (request.session_id, request.approval_id)
        if key in self.requests:
            raise KeyError(request.approval_id)
        self.requests[key] = request

    async def get(self, *, session_id: str, approval_id: str) -> ApprovalRequest | None:
        return self.requests.get((session_id, approval_id))

    async def list_by_turn(self, *, session_id: str, turn_id: str) -> tuple[ApprovalRequest, ...]:
        return tuple(
            request
            for request in self.requests.values()
            if request.session_id == session_id and request.turn_id == turn_id
        )

    async def resolve(
        self,
        *,
        session_id: str,
        approval_id: str,
        status: ApprovalStatus,
        resolved_by_user_id: str,
    ) -> ApprovalRequest:
        key = (session_id, approval_id)
        request = self.requests.get(key)
        if request is None:
            raise KeyError(approval_id)
        if request.status != "pending":
            raise ValueError("approval request is already resolved")
        if status == "pending":
            raise ValueError("approval resolution must be approved or rejected")
        resolved = replace(
            request,
            status=status,
            resolved_by_user_id=resolved_by_user_id,
            resolved_at=datetime.now(timezone.utc),
        )
        self.requests[key] = resolved
        return resolved


__all__ = ["ApprovalRepository", "MemoryApprovalRepository"]
