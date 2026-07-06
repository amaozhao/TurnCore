"""Agent loop."""

from __future__ import annotations

from turn.error import UAFError
from turn.model import ModelMessage, ModelPort, ModelRequest, ModelToolCall
from turn.run.turn import TurnExecution
from turn.agent.result import TurnResult
from turn.tool import ToolCall, ToolResult, ToolRuntime
from turn.wire.error import ErrorEnvelope


class AgentLoop:
    """Minimal model/tool loop for one turn."""

    def __init__(
        self,
        *,
        model: ModelPort,
        tool_runtime: ToolRuntime,
        max_iterations: int = 4,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be positive")
        self.model = model
        self.tool_runtime = tool_runtime
        self.max_iterations = max_iterations

    async def run(self, execution: TurnExecution) -> TurnResult:
        prompt_snapshot = execution.prompt_snapshot
        tool_snapshot = execution.tool_registry_snapshot
        if prompt_snapshot is None:
            raise UAFError("agent.prompt_snapshot_missing", "Prompt snapshot is required")
        if tool_snapshot is None:
            raise UAFError("agent.tool_snapshot_missing", "Tool registry snapshot is required")

        messages = _initial_messages(execution)
        tool_results: list[ToolResult] = []
        await execution.event_sink.emit(
            type="stage_start",
            source="agent_loop",
            stage="agent",
        )

        for _ in range(self.max_iterations):
            execution.raise_if_cancelled()
            response = await self.model.complete(
                ModelRequest(
                    session_id=execution.session_id,
                    turn_id=execution.turn_id,
                    messages=tuple(messages),
                    tools=tuple(tool_snapshot.tools.values()),
                )
            )
            if response.content:
                messages.append(ModelMessage(role="assistant", content=response.content))
                await execution.event_sink.emit(
                    type="content",
                    source="agent_loop",
                    stage="model",
                    content=response.content,
                )
            if not response.tool_calls:
                if not response.content:
                    return _failed_result(
                        execution,
                        code="model.empty_response",
                        message="Model returned no content",
                        tool_results=tuple(tool_results),
                    )
                await execution.event_sink.emit(
                    type="done",
                    source="agent_loop",
                    stage="agent",
                )
                return TurnResult(
                    session_id=execution.session_id,
                    turn_id=execution.turn_id,
                    status="completed",
                    content=response.content,
                    tool_results=tuple(tool_results),
                )

            calls = tuple(_tool_call(call) for call in response.tool_calls)
            for call in calls:
                await execution.event_sink.emit(
                    type="tool_call",
                    source="agent_loop",
                    stage="tool",
                    content=call.name,
                    metadata={"call_id": call.call_id},
                )
            batch_results = await self.tool_runtime.execute_batch(
                calls=calls,
                snapshot=tool_snapshot,
                cancellation_token=execution.cancellation_token,
            )
            tool_results.extend(batch_results)
            await _append_tool_results(execution, messages, batch_results)

        return _failed_result(
            execution,
            code="agent.iteration_limit",
            message="Agent loop reached iteration limit",
            tool_results=tuple(tool_results),
        )


def _initial_messages(execution: TurnExecution) -> list[ModelMessage]:
    prompt_snapshot = execution.prompt_snapshot
    if prompt_snapshot is None:
        raise UAFError("agent.prompt_snapshot_missing", "Prompt snapshot is required")
    content = execution.command.payload.get("content")
    if not isinstance(content, str) or not content:
        raise UAFError("agent.user_message_missing", "User message content is required")
    messages = [
        ModelMessage(role="system", content=prompt_snapshot.compiled_system_prompt),
        ModelMessage(role="user", content=content),
    ]
    if prompt_snapshot.compiled_developer_prompt:
        messages.insert(
            1,
            ModelMessage(role="developer", content=prompt_snapshot.compiled_developer_prompt),
        )
    return messages


def _tool_call(call: ModelToolCall) -> ToolCall:
    return ToolCall(call_id=call.call_id, name=call.tool_name, arguments=call.arguments)


async def _append_tool_results(
    execution: TurnExecution,
    messages: list[ModelMessage],
    results: tuple[ToolResult, ...],
) -> None:
    for result in results:
        messages.append(
            ModelMessage(
                role="tool",
                content=result.content if result.success else _tool_error_content(result),
                tool_call_id=result.call_id,
            )
        )
        await execution.event_sink.emit(
            type="tool_result",
            source="agent_loop",
            stage="tool",
            content=result.content,
            metadata={
                "call_id": result.call_id,
                "tool_name": result.tool_name,
                "success": result.success,
                "error_code": "" if result.error is None else result.error.code,
            },
        )


def _tool_error_content(result: ToolResult) -> str:
    if result.error is None:
        return "Tool failed"
    return f"{result.error.code}: {result.error.message}"


def _failed_result(
    execution: TurnExecution,
    *,
    code: str,
    message: str,
    tool_results: tuple[ToolResult, ...],
) -> TurnResult:
    return TurnResult(
        session_id=execution.session_id,
        turn_id=execution.turn_id,
        status="failed",
        content="",
        tool_results=tool_results,
        error=ErrorEnvelope(
            code=code,
            message=message,
            session_id=execution.session_id,
            turn_id=execution.turn_id,
        ),
    )


__all__ = ["AgentLoop"]
