import asyncio

import pytest

from turn.error import UAFError
from turn.run.cancel import CancellationToken
from turn.tool import ToolCall, ToolDefinition, ToolEffect, ToolRegistry, ToolResult, ToolRuntime


class BlockingTool:
    def __init__(
        self,
        *,
        name: str,
        effect: ToolEffect,
        started: asyncio.Event,
        release: asyncio.Event,
        starts: list[str],
    ) -> None:
        self._definition = ToolDefinition(name=name, description=name, effect=effect)
        self.started = started
        self.release = release
        self.starts = starts

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    async def execute(self, call: ToolCall) -> ToolResult:
        self.starts.append(call.name)
        self.started.set()
        await self.release.wait()
        return ToolResult(
            call_id=call.call_id,
            tool_name=call.name,
            content=call.name,
            success=True,
        )


class CountingTool:
    def __init__(self, definition: ToolDefinition) -> None:
        self._definition = definition
        self.calls = 0

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    async def execute(self, call: ToolCall) -> ToolResult:
        self.calls += 1
        return ToolResult(
            call_id=call.call_id,
            tool_name=call.name,
            content="called",
            success=True,
        )


class WaitingTool:
    def __init__(self) -> None:
        self._definition = ToolDefinition(
            name="wait",
            description="Wait",
            effect=ToolEffect.READONLY,
            timeout_seconds=0.001,
        )

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    async def execute(self, call: ToolCall) -> ToolResult:
        await asyncio.Event().wait()
        return ToolResult(call_id=call.call_id, tool_name=call.name, content="", success=True)


class RaisingTool:
    def __init__(self) -> None:
        self._definition = ToolDefinition(
            name="raise",
            description="Raise",
            effect=ToolEffect.READONLY,
        )

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    async def execute(self, call: ToolCall) -> ToolResult:
        raise ValueError("tool failed")


def test_tool_runtime_runs_readonly_group_concurrently() -> None:
    asyncio.run(check_tool_runtime_runs_readonly_group_concurrently())


async def check_tool_runtime_runs_readonly_group_concurrently() -> None:
    first_started = asyncio.Event()
    second_started = asyncio.Event()
    release = asyncio.Event()
    starts: list[str] = []
    first = BlockingTool(
        name="first",
        effect=ToolEffect.READONLY,
        started=first_started,
        release=release,
        starts=starts,
    )
    second = BlockingTool(
        name="second",
        effect=ToolEffect.READONLY,
        started=second_started,
        release=release,
        starts=starts,
    )
    registry = ToolRegistry()
    registry.register(first)
    registry.register(second)
    snapshot = registry.build_snapshot(session_id="sess_1", turn_id="turn_1")
    runtime = ToolRuntime(tools={"first": first, "second": second}, default_timeout_seconds=None)

    task = asyncio.create_task(
        runtime.execute_batch(
            calls=(
                ToolCall(call_id="call_1", name="first"),
                ToolCall(call_id="call_2", name="second"),
            ),
            snapshot=snapshot,
        )
    )
    await first_started.wait()
    await second_started.wait()

    assert starts == ["first", "second"]
    assert not task.done()

    release.set()
    results = await task
    assert tuple(result.content for result in results) == ("first", "second")


def test_tool_runtime_requires_approval_for_write_tools() -> None:
    asyncio.run(check_tool_runtime_requires_approval_for_write_tools())


async def check_tool_runtime_requires_approval_for_write_tools() -> None:
    tool = CountingTool(
        ToolDefinition(
            name="write",
            description="Write",
            effect=ToolEffect.WRITE,
        )
    )
    registry = ToolRegistry()
    registry.register(tool)
    snapshot = registry.build_snapshot(session_id="sess_1", turn_id="turn_1")
    runtime = ToolRuntime(tools={"write": tool}, default_timeout_seconds=None)

    results = await runtime.execute_batch(
        calls=(ToolCall(call_id="call_1", name="write"),),
        snapshot=snapshot,
    )

    assert results[0].error is not None
    assert results[0].error.code == "tool.approval_required"
    assert tool.calls == 0


def test_tool_runtime_runs_approved_writes_serially() -> None:
    asyncio.run(check_tool_runtime_runs_approved_writes_serially())


async def check_tool_runtime_runs_approved_writes_serially() -> None:
    first_started = asyncio.Event()
    second_started = asyncio.Event()
    release = asyncio.Event()
    starts: list[str] = []
    first = BlockingTool(
        name="first",
        effect=ToolEffect.WRITE,
        started=first_started,
        release=release,
        starts=starts,
    )
    second = BlockingTool(
        name="second",
        effect=ToolEffect.WRITE,
        started=second_started,
        release=release,
        starts=starts,
    )
    registry = ToolRegistry()
    registry.register(first)
    registry.register(second)
    snapshot = registry.build_snapshot(session_id="sess_1", turn_id="turn_1")
    runtime = ToolRuntime(tools={"first": first, "second": second}, default_timeout_seconds=None)

    task = asyncio.create_task(
        runtime.execute_batch(
            calls=(
                ToolCall(call_id="call_1", name="first"),
                ToolCall(call_id="call_2", name="second"),
            ),
            snapshot=snapshot,
            approved_call_ids=("call_1", "call_2"),
        )
    )
    await first_started.wait()

    assert starts == ["first"]
    assert not second_started.is_set()

    release.set()
    results = await task
    assert tuple(result.content for result in results) == ("first", "second")


def test_tool_runtime_fails_closed_for_unknown_and_destructive_tools() -> None:
    asyncio.run(check_tool_runtime_fails_closed_for_unknown_and_destructive_tools())


async def check_tool_runtime_fails_closed_for_unknown_and_destructive_tools() -> None:
    destructive = CountingTool(
        ToolDefinition(
            name="destroy",
            description="Destroy",
            effect=ToolEffect.DESTRUCTIVE,
        )
    )
    registry = ToolRegistry()
    registry.register(destructive)
    snapshot = registry.build_snapshot(session_id="sess_1", turn_id="turn_1")
    runtime = ToolRuntime(tools={"destroy": destructive}, default_timeout_seconds=None)

    results = await runtime.execute_batch(
        calls=(
            ToolCall(call_id="call_1", name="missing"),
            ToolCall(call_id="call_2", name="destroy"),
        ),
        snapshot=snapshot,
    )

    assert results[0].error is not None
    assert results[0].error.code == "tool.not_found"
    assert results[1].error is not None
    assert results[1].error.code == "tool.approval_required"
    assert destructive.calls == 0


def test_tool_runtime_returns_timeout_result() -> None:
    asyncio.run(check_tool_runtime_returns_timeout_result())


async def check_tool_runtime_returns_timeout_result() -> None:
    tool = WaitingTool()
    registry = ToolRegistry()
    registry.register(tool)
    snapshot = registry.build_snapshot(session_id="sess_1", turn_id="turn_1")
    runtime = ToolRuntime(tools={"wait": tool}, default_timeout_seconds=None)

    (result,) = await runtime.execute_batch(
        calls=(ToolCall(call_id="call_1", name="wait"),),
        snapshot=snapshot,
    )

    assert result.error is not None
    assert result.error.code == "tool.timeout"


def test_tool_runtime_propagates_cancellation() -> None:
    asyncio.run(check_tool_runtime_propagates_cancellation())


async def check_tool_runtime_propagates_cancellation() -> None:
    tool = CountingTool(ToolDefinition(name="count", description="Count"))
    registry = ToolRegistry()
    registry.register(tool)
    snapshot = registry.build_snapshot(session_id="sess_1", turn_id="turn_1")
    runtime = ToolRuntime(tools={"count": tool}, default_timeout_seconds=None)
    token = CancellationToken()
    token.cancel()

    with pytest.raises(UAFError) as error:
        await runtime.execute_batch(
            calls=(ToolCall(call_id="call_1", name="count"),),
            snapshot=snapshot,
            cancellation_token=token,
        )
    assert error.value.code == "turn.cancelled"
    assert tool.calls == 0


def test_tool_runtime_returns_execution_error_result() -> None:
    asyncio.run(check_tool_runtime_returns_execution_error_result())


async def check_tool_runtime_returns_execution_error_result() -> None:
    tool = RaisingTool()
    registry = ToolRegistry()
    registry.register(tool)
    snapshot = registry.build_snapshot(session_id="sess_1", turn_id="turn_1")
    runtime = ToolRuntime(tools={"raise": tool}, default_timeout_seconds=None)

    (result,) = await runtime.execute_batch(
        calls=(ToolCall(call_id="call_1", name="raise"),),
        snapshot=snapshot,
    )

    assert result.error is not None
    assert result.error.code == "tool.execution_failed"
