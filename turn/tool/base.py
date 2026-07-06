"""Tool protocol."""

from __future__ import annotations

from typing import Protocol

from turn.tool.result import ToolResult
from turn.tool.schema import ToolCall, ToolDefinition


class BaseTool(Protocol):
    """Protocol implemented by concrete tools."""

    @property
    def definition(self) -> ToolDefinition: ...

    async def execute(self, call: ToolCall) -> ToolResult: ...


__all__ = ["BaseTool"]
