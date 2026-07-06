"""User reply submission."""

from __future__ import annotations

from dataclasses import replace

from turn.error import UAFError
from turn.port.run import TurnRepository
from turn.session.auth import SessionAuthorizer
from turn.user import Principal


class UserReplyService:
    """Resumes turns waiting for user input."""

    def __init__(self, *, turns: TurnRepository, authorizer: SessionAuthorizer) -> None:
        self.turns = turns
        self.authorizer = authorizer

    async def submit_user_reply(
        self,
        *,
        principal: Principal,
        turn_id: str,
        content: str,
    ) -> None:
        if not content:
            raise ValueError("reply content must be non-empty")
        turn = await self.authorizer.authorize_turn(principal, turn_id)
        if turn.status != "waiting_for_user":
            raise UAFError(
                code="turn.not_waiting_for_user",
                message="Turn is not waiting for user input",
                metadata={"turn_id": turn_id},
            )
        await self.turns.update_turn(replace(turn, status="running"))


__all__ = ["UserReplyService"]
