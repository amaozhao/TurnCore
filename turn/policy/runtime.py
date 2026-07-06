"""Policy runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from turn.policy.decision import PolicyDecision
from turn.tool.schema import ToolCall, ToolDefinition, ToolEffect
from turn.user import Principal


@dataclass(frozen=True)
class ToolPolicyContext:
    """Inputs for one tool policy decision."""

    principal: Principal | None
    session_id: str
    turn_id: str
    call: ToolCall
    definition: ToolDefinition
    approved: bool = False


class PolicyRuntime(Protocol):
    """Port for runtime policy checks."""

    def decide_tool(self, context: ToolPolicyContext) -> PolicyDecision: ...


class DefaultPolicyRuntime:
    """Minimal tool policy checker."""

    def decide_tool(self, context: ToolPolicyContext) -> PolicyDecision:
        if context.definition.effect == ToolEffect.READONLY:
            return PolicyDecision(status="allow")
        if context.approved:
            return PolicyDecision(status="allow")
        if context.definition.effect in {
            ToolEffect.IDEMPOTENT_WRITE,
            ToolEffect.WRITE,
            ToolEffect.DESTRUCTIVE,
        }:
            return PolicyDecision(
                status="approval_required",
                reason=f"{context.definition.effect.value} tool requires approval",
            )
        return PolicyDecision(status="deny", reason="Tool effect is not allowed")


__all__ = ["DefaultPolicyRuntime", "PolicyRuntime", "ToolPolicyContext"]
