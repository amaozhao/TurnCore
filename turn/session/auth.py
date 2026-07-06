"""Session authorization helpers."""

from __future__ import annotations

from turn.error import UAFError
from turn.port.run import TurnRepository
from turn.port.session import SessionRepository
from turn.run.model import Turn
from turn.session.model import Session
from turn.user import Principal


def authorize_session(principal: Principal, session: Session) -> None:
    if principal.user_id != session.owner_user_id:
        raise UAFError(
            code="session.access_denied",
            message="Session access denied",
            metadata={"session_id": session.session_id},
        )


class SessionAuthorizer:
    """Authorizes runtime access through session ownership."""

    def __init__(self, sessions: SessionRepository, turns: TurnRepository) -> None:
        self.sessions = sessions
        self.turns = turns

    async def authorize_session(self, principal: Principal, session_id: str) -> Session:
        session = await self.sessions.get_session(session_id)
        if session is None:
            raise UAFError(
                code="session.not_found",
                message="Session was not found",
                metadata={"session_id": session_id},
            )
        authorize_session(principal, session)
        return session

    async def authorize_turn(self, principal: Principal, turn_id: str) -> Turn:
        turn = await self.turns.get_turn(turn_id)
        if turn is None:
            raise UAFError(
                code="turn.not_found",
                message="Turn was not found",
                metadata={"turn_id": turn_id},
            )
        await self.authorize_session(principal, turn.session_id)
        return turn


__all__ = ["SessionAuthorizer", "authorize_session"]
