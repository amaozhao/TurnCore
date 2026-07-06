from turn.policy import DefaultPolicyRuntime, ToolPolicyContext
from turn.tool import ToolCall, ToolDefinition, ToolEffect
from turn.user import Principal


def test_policy_runtime_requires_approval_for_write_effects() -> None:
    runtime = DefaultPolicyRuntime()
    context = ToolPolicyContext(
        principal=Principal(user_id="user_1"),
        session_id="sess_1",
        turn_id="turn_1",
        call=ToolCall(call_id="call_1", name="write"),
        definition=ToolDefinition(name="write", description="Write", effect=ToolEffect.WRITE),
    )

    decision = runtime.decide_tool(context)
    approved = runtime.decide_tool(
        ToolPolicyContext(
            principal=context.principal,
            session_id=context.session_id,
            turn_id=context.turn_id,
            call=context.call,
            definition=context.definition,
            approved=True,
        )
    )

    assert decision.requires_approval
    assert approved.allowed
