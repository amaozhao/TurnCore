"""In-memory session repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Mapping

from turn.port.model import Page
from turn.session.model import Session, SessionPackSelection


class MemorySessionStore:
    """Session and pack-selection repository backed by process memory."""

    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self.selections: dict[str, SessionPackSelection] = {}

    async def create_session(
        self,
        *,
        owner_user_id: str,
        title: str,
        prompt_profile_id: str | None = None,
        pack_selection_id: str | None = None,
        default_capability: str = "",
        config: Mapping[str, object] | None = None,
    ) -> Session:
        now = datetime.now(timezone.utc)
        session = Session(
            session_id=f"sess_{uuid.uuid4().hex}",
            owner_user_id=owner_user_id,
            title=title,
            status="active",
            prompt_profile_id=prompt_profile_id,
            pack_selection_id=pack_selection_id,
            default_capability=default_capability,
            config={} if config is None else dict(config),
            created_at=now,
            updated_at=now,
        )
        self.sessions[session.session_id] = session
        return session

    async def get_session(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    async def list_sessions_for_user(
        self,
        *,
        owner_user_id: str,
        limit: int,
        cursor: str | None = None,
    ) -> Page[Session]:
        if limit < 1:
            raise ValueError("limit must be positive")
        sessions = [
            session
            for session in self.sessions.values()
            if session.owner_user_id == owner_user_id and session.status != "deleted"
        ]
        sessions.sort(key=lambda session: (session.created_at, session.session_id))
        start = int(cursor) if cursor is not None else 0
        items = tuple(sessions[start : start + limit])
        next_index = start + len(items)
        next_cursor = str(next_index) if next_index < len(sessions) else None
        return Page(items=items, next_cursor=next_cursor)

    async def update_session(self, session: Session) -> None:
        if session.session_id not in self.sessions:
            raise KeyError(session.session_id)
        self.sessions[session.session_id] = session

    async def archive_session(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        self.sessions[session_id] = Session(
            session_id=session.session_id,
            owner_user_id=session.owner_user_id,
            title=session.title,
            status="archived",
            prompt_profile_id=session.prompt_profile_id,
            pack_selection_id=session.pack_selection_id,
            default_capability=session.default_capability,
            config=session.config,
            created_at=session.created_at,
            updated_at=datetime.now(timezone.utc),
        )

    async def save_selection(self, selection: SessionPackSelection) -> None:
        self.selections[selection.session_id] = selection

    async def get_selection(self, session_id: str) -> SessionPackSelection | None:
        return self.selections.get(session_id)


__all__ = ["MemorySessionStore"]
