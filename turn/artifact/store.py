"""Artifact store."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import AsyncIterator, Protocol

from turn.artifact.file import Artifact


class ArtifactStore(Protocol):
    """Port for session-scoped artifacts."""

    async def save(
        self,
        *,
        session_id: str,
        turn_id: str,
        run_id: str | None,
        filename: str,
        mime_type: str,
        content: bytes | AsyncIterator[bytes],
    ) -> Artifact: ...

    async def get(self, *, session_id: str, artifact_id: str) -> Artifact | None: ...


class MemoryArtifactStore:
    """Artifact store backed by process memory."""

    def __init__(self) -> None:
        self.artifacts: dict[tuple[str, str], Artifact] = {}
        self.content: dict[tuple[str, str], bytes] = {}

    async def save(
        self,
        *,
        session_id: str,
        turn_id: str,
        run_id: str | None,
        filename: str,
        mime_type: str,
        content: bytes | AsyncIterator[bytes],
    ) -> Artifact:
        data = content if isinstance(content, bytes) else await _collect(content)
        checksum = sha256(data).hexdigest()
        artifact_id = f"art_{checksum[:16]}"
        artifact = Artifact(
            artifact_id=artifact_id,
            session_id=session_id,
            turn_id=turn_id,
            run_id=run_id,
            filename=filename,
            mime_type=mime_type,
            uri=f"artifact://sessions/{session_id}/turns/{turn_id}/{artifact_id}",
            size_bytes=len(data),
            checksum=checksum,
            created_at=datetime.now(timezone.utc),
        )
        self.artifacts[(session_id, artifact_id)] = artifact
        self.content[(session_id, artifact_id)] = data
        return artifact

    async def get(self, *, session_id: str, artifact_id: str) -> Artifact | None:
        return self.artifacts.get((session_id, artifact_id))

    async def read_content(self, *, session_id: str, artifact_id: str) -> bytes | None:
        return self.content.get((session_id, artifact_id))


async def _collect(content: AsyncIterator[bytes]) -> bytes:
    chunks: list[bytes] = []
    async for chunk in content:
        chunks.append(chunk)
    return b"".join(chunks)


__all__ = ["ArtifactStore", "MemoryArtifactStore"]
