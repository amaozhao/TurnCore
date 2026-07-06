"""Session repository port protocols."""

from __future__ import annotations

from typing import Mapping, Protocol

from turn.port.model import Page
from turn.session.model import Session, SessionPackSelection


class SessionRepository(Protocol):
    """Port for session identity and lifecycle records."""

    async def create_session(
        self,
        *,
        owner_user_id: str,
        title: str,
        prompt_profile_id: str | None,
        pack_selection_id: str | None,
        default_capability: str,
        config: Mapping[str, object],
    ) -> Session: ...

    async def get_session(self, session_id: str) -> Session | None: ...

    async def list_sessions_for_user(
        self,
        *,
        owner_user_id: str,
        limit: int,
        cursor: str | None = None,
    ) -> Page[Session]: ...

    async def update_session(self, session: Session) -> None: ...

    async def archive_session(self, session_id: str) -> None: ...


class SessionPackSelectionRepository(Protocol):
    """Port for session-scoped pack enablement."""

    async def save_selection(self, selection: SessionPackSelection) -> None: ...

    async def get_selection(self, session_id: str) -> SessionPackSelection | None: ...


__all__ = ["SessionPackSelectionRepository", "SessionRepository"]
