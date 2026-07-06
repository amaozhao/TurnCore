"""Approval service."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone
from typing import Mapping

from turn.approval.request import ApprovalRequest, ApprovalStatus
from turn.approval.store import ApprovalRepository
from turn.error import UAFError
from turn.port.run import TurnRepository
from turn.run.model import Turn
from turn.session.auth import SessionAuthorizer
from turn.user import Principal


class ApprovalService:
    """Creates and resolves session-scoped approval requests."""

    def __init__(
        self,
        *,
        approvals: ApprovalRepository,
        turns: TurnRepository,
        authorizer: SessionAuthorizer,
    ) -> None:
        self.approvals = approvals
        self.turns = turns
        self.authorizer = authorizer

    async def request_approval(
        self,
        *,
        principal: Principal,
        session_id: str,
        turn_id: str,
        run_id: str | None,
        action: str,
        reason: str,
        metadata: Mapping[str, object] | None = None,
    ) -> ApprovalRequest:
        await self.authorizer.authorize_session(principal, session_id)
        turn = await _require_turn(self.turns, turn_id)
        if turn.session_id != session_id:
            raise UAFError(
                code="turn.session_mismatch",
                message="Turn does not belong to session",
                metadata={"session_id": session_id, "turn_id": turn_id},
            )
        request = ApprovalRequest(
            approval_id=f"approval_{uuid.uuid4().hex}",
            session_id=session_id,
            turn_id=turn_id,
            run_id=run_id,
            action=action,
            reason=reason,
            status="pending",
            requested_by_user_id=principal.user_id,
            metadata={} if metadata is None else dict(metadata),
            created_at=datetime.now(timezone.utc),
        )
        await self.approvals.create(request)
        await self.turns.update_turn(replace(turn, status="waiting_for_approval"))
        return request

    async def submit_approval(
        self,
        *,
        principal: Principal,
        turn_id: str,
        approval_id: str,
        status: ApprovalStatus,
    ) -> ApprovalRequest:
        turn = await self.authorizer.authorize_turn(principal, turn_id)
        if status == "pending":
            raise UAFError(
                code="approval.invalid_status",
                message="Approval decision must approve or reject",
            )
        request = await self.approvals.get(session_id=turn.session_id, approval_id=approval_id)
        if request is None:
            raise UAFError(
                code="approval.not_found",
                message="Approval request was not found",
                metadata={"approval_id": approval_id},
            )
        if request.turn_id != turn_id:
            raise UAFError(
                code="approval.turn_mismatch",
                message="Approval request does not belong to turn",
                metadata={"approval_id": approval_id, "turn_id": turn_id},
            )
        resolved = await self.approvals.resolve(
            session_id=turn.session_id,
            approval_id=approval_id,
            status=status,
            resolved_by_user_id=principal.user_id,
        )
        await self.turns.update_turn(replace(turn, status="running"))
        return resolved


async def _require_turn(turns: TurnRepository, turn_id: str) -> Turn:
    turn = await turns.get_turn(turn_id)
    if turn is None:
        raise UAFError(
            code="turn.not_found",
            message="Turn was not found",
            metadata={"turn_id": turn_id},
        )
    return turn


__all__ = ["ApprovalService"]
