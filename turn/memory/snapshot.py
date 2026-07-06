"""Memory snapshot models."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class MemorySnapshot:
    """Turn-scoped frozen memory view."""

    snapshot_id: str
    session_id: str
    turn_id: str
    recent_summary: str
    profile_notes: str
    preferences: str
    scope: str
    source_entry_ids: tuple[str, ...]
    checksum: str


def memory_checksum(
    *,
    recent_summary: str,
    profile_notes: str,
    preferences: str,
    scope: str,
    source_entry_ids: tuple[str, ...],
) -> str:
    digest = sha256()
    for part in (recent_summary, profile_notes, preferences, scope, *source_entry_ids):
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


__all__ = ["MemorySnapshot", "memory_checksum"]
