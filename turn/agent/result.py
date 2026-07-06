"""Agent loop result model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from turn.tool.result import ToolResult
from turn.wire.error import ErrorEnvelope

TurnResultStatus = Literal["completed", "failed", "cancelled"]


@dataclass(frozen=True)
class TurnResult:
    """Final result for one turn execution."""

    session_id: str
    turn_id: str
    status: TurnResultStatus
    content: str
    tool_results: tuple[ToolResult, ...] = ()
    error: ErrorEnvelope | None = None


__all__ = ["TurnResult", "TurnResultStatus"]
