from operator import setitem

import pytest

from turn.error import UAFError
from turn.tool import ToolCall, ToolDefinition, ToolEffect, ToolRegistry, ToolResult


class EchoTool:
    def __init__(self, name: str = "echo") -> None:
        self._definition = ToolDefinition(
            name=name,
            description="Echo text",
            parameters={"type": "object"},
            effect=ToolEffect.READONLY,
        )

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    async def execute(self, call: ToolCall) -> ToolResult:
        text = call.arguments.get("text")
        return ToolResult(
            call_id=call.call_id,
            tool_name=call.name,
            content="" if not isinstance(text, str) else text,
            success=True,
        )


def test_tool_registry_builds_turn_scoped_snapshot() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool("alpha"))
    registry.register(EchoTool("beta"))

    snapshot = registry.build_snapshot(
        session_id="sess_1",
        turn_id="turn_1",
        enabled_tool_names=("beta",),
        policy_summary={"scope": "session"},
    )

    assert snapshot.session_id == "sess_1"
    assert snapshot.turn_id == "turn_1"
    assert tuple(snapshot.tools) == ("beta",)
    assert snapshot.snapshot_id.startswith("tool_")
    assert snapshot.checksum
    with pytest.raises(TypeError):
        setitem(snapshot.tools, "alpha", EchoTool("alpha").definition)
    with pytest.raises(TypeError):
        setitem(snapshot.policy_summary, "scope", "changed")


def test_tool_registry_snapshot_checksum_includes_policy_summary() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool("echo"))

    first = registry.build_snapshot(
        session_id="sess_1",
        turn_id="turn_1",
        policy_summary={"network": "off"},
    )
    second = registry.build_snapshot(
        session_id="sess_1",
        turn_id="turn_1",
        policy_summary={"network": "on"},
    )

    assert first.checksum != second.checksum
    assert first.snapshot_id != second.snapshot_id


def test_tool_registry_rejects_duplicate_and_missing_tools() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool("echo"))

    with pytest.raises(KeyError):
        registry.register(EchoTool("echo"))

    with pytest.raises(UAFError) as error:
        registry.build_snapshot(
            session_id="sess_1",
            turn_id="turn_1",
            enabled_tool_names=("missing",),
        )
    assert error.value.code == "tool.not_found"
