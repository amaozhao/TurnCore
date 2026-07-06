"""Turn prompt snapshot model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from turn.prompt.layer import PromptSource


@dataclass(frozen=True)
class PromptSnapshot:
    """Prompt inputs compiled and frozen for one turn."""

    snapshot_id: str
    session_id: str
    turn_id: str
    sources: tuple[PromptSource, ...]
    compiled_system_prompt: str
    compiled_developer_prompt: str | None
    compiled_tool_manifest: str
    compiled_capability_manifest: str
    checksum: str
    created_at: datetime


__all__ = ["PromptSnapshot"]
