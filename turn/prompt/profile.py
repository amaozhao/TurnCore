"""Session prompt profile model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionPromptProfile:
    """Session-owned prompt profile frozen away from user defaults."""

    profile_id: str
    session_id: str
    base_prompt: str
    persona_prompt: str
    style_prompt: str
    safety_prompt: str
    pack_prompt_refs: tuple[str, ...]
    created_from_user_default_id: str | None
    revision: int
    checksum: str


__all__ = ["SessionPromptProfile"]
