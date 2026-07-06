"""Tool registry and snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

from turn.error import UAFError
from turn.tool.base import BaseTool
from turn.tool.schema import ToolDefinition


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_object_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    data: dict[str, object] = {} if value is None else dict(value)
    return MappingProxyType(data)


def _freeze_tool_mapping(value: Mapping[str, ToolDefinition]) -> Mapping[str, ToolDefinition]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class ToolRegistrySnapshot:
    """Turn-scoped tool definitions frozen before execution."""

    snapshot_id: str
    session_id: str
    turn_id: str
    tools: Mapping[str, ToolDefinition]
    policy_summary: Mapping[str, object] = field(default_factory=_empty_mapping)
    checksum: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "tools", _freeze_tool_mapping(self.tools))
        object.__setattr__(self, "policy_summary", _freeze_object_mapping(self.policy_summary))
        if not self.checksum:
            object.__setattr__(
                self,
                "checksum",
                tool_snapshot_checksum(self.tools, policy_summary=self.policy_summary),
            )


class ToolRegistry:
    """Process-local table for tool implementations."""

    def __init__(self) -> None:
        self.tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        name = tool.definition.name
        if name in self.tools:
            raise KeyError(name)
        self.tools[name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self.tools.get(name)

    def build_snapshot(
        self,
        *,
        session_id: str,
        turn_id: str,
        enabled_tool_names: tuple[str, ...] | None = None,
        policy_summary: Mapping[str, object] | None = None,
    ) -> ToolRegistrySnapshot:
        names = tuple(self.tools) if enabled_tool_names is None else enabled_tool_names
        definitions: dict[str, ToolDefinition] = {}
        for name in names:
            tool = self.tools.get(name)
            if tool is None:
                raise UAFError(
                    code="tool.not_found",
                    message="Tool is not registered",
                    retryable=False,
                    metadata={"tool_name": name},
                )
            definitions[name] = tool.definition
        frozen_policy = _freeze_object_mapping(policy_summary)
        checksum = tool_snapshot_checksum(definitions, policy_summary=frozen_policy)
        return ToolRegistrySnapshot(
            snapshot_id=f"tool_{checksum[:16]}",
            session_id=session_id,
            turn_id=turn_id,
            tools=definitions,
            policy_summary=frozen_policy,
            checksum=checksum,
        )


def tool_snapshot_checksum(
    tools: Mapping[str, ToolDefinition],
    *,
    policy_summary: Mapping[str, object] | None = None,
) -> str:
    digest = sha256()
    digest.update(_stable_text({} if policy_summary is None else policy_summary).encode("utf-8"))
    digest.update(b"\0")
    for name in sorted(tools):
        definition = tools[name]
        for part in (
            definition.name,
            definition.description,
            definition.effect.value,
            "" if definition.timeout_seconds is None else str(definition.timeout_seconds),
            _stable_text(definition.parameters),
            _stable_text(definition.metadata),
        ):
            digest.update(part.encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


def _stable_text(value: Mapping[str, object]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


__all__ = ["ToolRegistry", "ToolRegistrySnapshot", "tool_snapshot_checksum"]
