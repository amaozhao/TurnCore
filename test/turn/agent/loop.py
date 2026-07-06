import asyncio
from datetime import datetime, timezone

from turn.agent import AgentLoop
from turn.event.store import MemoryEventStore
from turn.event.sink import EventSink
from turn.model import ModelRequest, ModelResponse, ModelToolCall
from turn.prompt import DefaultPromptCompiler, PromptCompileCommand, PromptSource
from turn.run.cancel import CancellationToken
from turn.run.turn import TurnExecution
from turn.tool import ToolCall, ToolDefinition, ToolEffect, ToolRegistry, ToolResult, ToolRuntime
from turn.user import Principal
from turn.wire import CommandEnvelope


class QueuedPort:
    def __init__(self, responses: tuple[ModelResponse, ...]) -> None:
        self.responses = list(responses)
        self.requests: list[ModelRequest] = []

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return self.responses.pop(0)


class EchoTool:
    def __init__(self) -> None:
        self._definition = ToolDefinition(
            name="echo",
            description="Echo text",
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


def test_agent_loop_uses_injected_model_port_and_tool_runtime() -> None:
    asyncio.run(check_agent_loop_uses_injected_model_port_and_tool_runtime())


async def check_agent_loop_uses_injected_model_port_and_tool_runtime() -> None:
    compiler = DefaultPromptCompiler()
    prompt = await compiler.compile_for_turn(
        PromptCompileCommand(
            session_id="sess_1",
            turn_id="turn_1",
            sources=(
                PromptSource.from_text(
                    source_id="kernel",
                    source_type="framework_builtin",
                    priority=0,
                    content="system prompt",
                ),
            ),
        )
    )
    tool = EchoTool()
    registry = ToolRegistry()
    registry.register(tool)
    tool_snapshot = registry.build_snapshot(session_id="sess_1", turn_id="turn_1")
    model = QueuedPort(
        (
            ModelResponse(
                content="",
                tool_calls=(
                    ModelToolCall(
                        call_id="call_1",
                        tool_name="echo",
                        arguments={"text": "tool output"},
                    ),
                ),
                finish_reason="tool_calls",
            ),
            ModelResponse(content="final answer"),
        )
    )
    event_store = MemoryEventStore()
    execution = TurnExecution(
        session_id="sess_1",
        turn_id="turn_1",
        command=CommandEnvelope(
            command_id="cmd_1",
            type="start_turn",
            session_id="sess_1",
            turn_id="turn_1",
            payload={"content": "hello"},
        ),
        principal=Principal(user_id="user_1"),
        cancellation_token=CancellationToken(),
        event_sink=EventSink(store=event_store, session_id="sess_1", turn_id="turn_1"),
        started_at=datetime.now(timezone.utc),
        prompt_snapshot=prompt,
        tool_registry_snapshot=tool_snapshot,
    )
    loop = AgentLoop(
        model=model,
        tool_runtime=ToolRuntime(tools={"echo": tool}, default_timeout_seconds=None),
    )

    result = await loop.run(execution)

    assert result.status == "completed"
    assert result.content == "final answer"
    assert len(model.requests) == 2
    assert model.requests[0].messages[0].content == "system prompt"
    assert model.requests[0].messages[1].content == "hello"
    assert any(
        message.role == "tool" and message.content == "tool output"
        for message in model.requests[1].messages
    )
    events = await event_store.list_by_turn(turn_id="turn_1")
    assert tuple(event.type for event in events) == (
        "stage_start",
        "tool_call",
        "tool_result",
        "content",
        "done",
    )


def test_agent_loop_returns_failed_result_at_iteration_limit() -> None:
    asyncio.run(check_agent_loop_returns_failed_result_at_iteration_limit())


async def check_agent_loop_returns_failed_result_at_iteration_limit() -> None:
    compiler = DefaultPromptCompiler()
    prompt = await compiler.compile_for_turn(
        PromptCompileCommand(session_id="sess_1", turn_id="turn_1")
    )
    tool = EchoTool()
    registry = ToolRegistry()
    registry.register(tool)
    tool_snapshot = registry.build_snapshot(session_id="sess_1", turn_id="turn_1")
    model = QueuedPort(
        (
            ModelResponse(
                content="",
                tool_calls=(
                    ModelToolCall(
                        call_id="call_1",
                        tool_name="echo",
                        arguments={"text": "tool output"},
                    ),
                ),
                finish_reason="tool_calls",
            ),
        )
    )
    event_store = MemoryEventStore()
    execution = TurnExecution(
        session_id="sess_1",
        turn_id="turn_1",
        command=CommandEnvelope(
            command_id="cmd_1",
            type="start_turn",
            session_id="sess_1",
            turn_id="turn_1",
            payload={"content": "hello"},
        ),
        principal=Principal(user_id="user_1"),
        cancellation_token=CancellationToken(),
        event_sink=EventSink(store=event_store, session_id="sess_1", turn_id="turn_1"),
        started_at=datetime.now(timezone.utc),
        prompt_snapshot=prompt,
        tool_registry_snapshot=tool_snapshot,
    )
    loop = AgentLoop(
        model=model,
        tool_runtime=ToolRuntime(tools={"echo": tool}, default_timeout_seconds=None),
        max_iterations=1,
    )

    result = await loop.run(execution)

    assert result.status == "failed"
    assert result.error is not None
    assert result.error.code == "agent.iteration_limit"
