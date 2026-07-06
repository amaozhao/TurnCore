"""Session-scoped protocol models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping


@dataclass(frozen=True)
class Session:
    """Agent runtime namespace owned by one user."""

    session_id: str
    owner_user_id: str
    title: str
    status: Literal["active", "archived", "deleted"]
    prompt_profile_id: str | None
    pack_selection_id: str | None
    default_capability: str
    config: Mapping[str, object]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class SessionPackSelection:
    """Session-owned pack and tool enablement."""

    selection_id: str
    session_id: str
    enabled_pack_ids: tuple[str, ...]
    enabled_tool_names: tuple[str, ...]
    revision: int
    checksum: str


__all__ = ["Session", "SessionPackSelection"]
