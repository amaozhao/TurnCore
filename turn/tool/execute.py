"""Tool execution runtime."""

from __future__ import annotations

import asyncio
from typing import Mapping

from turn.error import UAFError
from turn.policy import DefaultPolicyRuntime, PolicyRuntime, ToolPolicyContext
from turn.run.cancel import CancellationToken
from turn.tool.base import BaseTool
from turn.tool.registry import ToolRegistrySnapshot
from turn.tool.result import ToolResult
from turn.tool.schema import ToolCall, ToolDefinition, ToolEffect
from turn.user import Principal
from turn.wire.error import ErrorEnvelope


class ToolRuntime:
    """Executes tool calls against a turn-scoped registry snapshot."""

    def __init__(
        self,
        *,
        tools: Mapping[str, BaseTool],
        default_timeout_seconds: float | None = 30,
        policy: PolicyRuntime | None = None,
    ) -> None:
        if default_timeout_seconds is not None and default_timeout_seconds <= 0:
            raise ValueError("default_timeout_seconds must be positive")
        self.tools = dict(tools)
        self.default_timeout_seconds = default_timeout_seconds
        self.policy = policy or DefaultPolicyRuntime()

    async def execute_batch(
        self,
        *,
        calls: tuple[ToolCall, ...],
        snapshot: ToolRegistrySnapshot,
        session_id: str = "",
        turn_id: str = "",
        principal: Principal | None = None,
        approved_call_ids: tuple[str, ...] = (),
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[ToolResult, ...]:
        results: list[ToolResult] = []
        index = 0
        while index < len(calls):
            self._raise_if_cancelled(cancellation_token)
            definition = snapshot.tools.get(calls[index].name)
            if definition is None:
                results.append(_error_result(calls[index], "tool.not_found", "Tool not found"))
                index += 1
                continue
            if definition.effect == ToolEffect.READONLY:
                end = _readonly_group_end(calls, snapshot, index)
                group = tuple(
                    self._execute_one(
                        call=call,
                        definition=snapshot.tools[call.name],
                        session_id=session_id or snapshot.session_id,
                        turn_id=turn_id or snapshot.turn_id,
                        principal=principal,
                        approved=call.call_id in approved_call_ids,
                        cancellation_token=cancellation_token,
                    )
                    for call in calls[index:end]
                )
                results.extend(await asyncio.gather(*group))
                index = end
                continue
            results.append(
                await self._execute_one(
                    call=calls[index],
                    definition=definition,
                    session_id=session_id or snapshot.session_id,
                    turn_id=turn_id or snapshot.turn_id,
                    principal=principal,
                    approved=calls[index].call_id in approved_call_ids,
                    cancellation_token=cancellation_token,
                )
            )
            index += 1
        return tuple(results)

    async def _execute_one(
        self,
        *,
        call: ToolCall,
        definition: ToolDefinition,
        session_id: str,
        turn_id: str,
        principal: Principal | None,
        approved: bool,
        cancellation_token: CancellationToken | None,
    ) -> ToolResult:
        self._raise_if_cancelled(cancellation_token)
        decision = self.policy.decide_tool(
            ToolPolicyContext(
                principal=principal,
                session_id=session_id,
                turn_id=turn_id,
                call=call,
                definition=definition,
                approved=approved,
            )
        )
        if decision.requires_approval:
            return _error_result(
                call,
                "tool.approval_required",
                decision.reason or "Tool requires approval",
            )
        if not decision.allowed:
            return _error_result(call, "tool.policy_denied", decision.reason or "Tool denied")
        tool = self.tools.get(call.name)
        if tool is None:
            return _error_result(call, "tool.not_found", "Tool not found")
        timeout = definition.timeout_seconds or self.default_timeout_seconds
        try:
            if timeout is None:
                result = await tool.execute(call)
            else:
                result = await asyncio.wait_for(tool.execute(call), timeout=timeout)
        except TimeoutError:
            return _error_result(call, "tool.timeout", "Tool timed out", retryable=True)
        except UAFError as exc:
            return ToolResult(
                call_id=call.call_id,
                tool_name=call.name,
                content="",
                success=False,
                error=exc.to_envelope(),
            )
        except Exception:
            return _error_result(call, "tool.execution_failed", "Tool execution failed")
        self._raise_if_cancelled(cancellation_token)
        return result

    def _raise_if_cancelled(self, cancellation_token: CancellationToken | None) -> None:
        if cancellation_token is not None:
            cancellation_token.raise_if_cancelled()


def _readonly_group_end(
    calls: tuple[ToolCall, ...],
    snapshot: ToolRegistrySnapshot,
    start: int,
) -> int:
    end = start
    while end < len(calls):
        definition = snapshot.tools.get(calls[end].name)
        if definition is None or definition.effect != ToolEffect.READONLY:
            break
        end += 1
    return end


def _error_result(
    call: ToolCall,
    code: str,
    message: str,
    *,
    retryable: bool = False,
) -> ToolResult:
    return ToolResult(
        call_id=call.call_id,
        tool_name=call.name,
        content="",
        success=False,
        error=ErrorEnvelope(
            code=code,
            message=message,
            retryable=retryable,
            details={"tool_name": call.name},
        ),
    )


__all__ = ["ToolRuntime"]
