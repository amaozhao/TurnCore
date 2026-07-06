import asyncio

import pytest

from turn import Agent
from turn.capability import CapabilityContext, CapabilityManifest, CapabilityResult
from turn.error import UAFError
from turn.model import ModelRequest, ModelResponse, ModelToolCall
from turn.tool import ToolCall, ToolDefinition, ToolEffect, ToolResult
from turn.user import Principal


class QueueModel:
    def __init__(self, responses: tuple[ModelResponse, ...]) -> None:
        self.responses = list(responses)
        self.requests: list[ModelRequest] = []

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        return self.responses.pop(0)


class EchoTool:
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(name="echo", description="Echo", effect=ToolEffect.READONLY)

    async def execute(self, call: ToolCall) -> ToolResult:
        text = call.arguments.get("text")
        return ToolResult(
            call_id=call.call_id,
            tool_name=call.name,
            content=text if isinstance(text, str) else "",
            success=True,
        )


class SimpleCapability:
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(name="simple")

    async def run(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(status="completed", content=context.user_message)


def test_agent_run_creates_session_turn_snapshots_and_messages() -> None:
    model = QueueModel((ModelResponse(content="hello"),))
    agent = Agent(model=model, instructions="Be brief.", owner_user_id="user_1")

    result = agent.run("Hi")

    assert result.status == "completed"
    assert result.content == "hello"
    assert len(agent.sessions.sessions) == 1
    assert len(agent.turns.turns) == 1
    assert len(agent.runs.runs) == 1
    assert len(agent.prompts.snapshots) == 1
    assert len(agent.tool_snapshots.snapshots) == 1
    messages = agent.messages.messages
    assert tuple(message.role for message in messages) == ("user", "assistant")
    assert model.requests[0].messages[0].content == "Be brief."


def test_agent_arun_uses_bound_tool() -> None:
    asyncio.run(check_agent_arun_uses_bound_tool())


async def check_agent_arun_uses_bound_tool() -> None:
    model = QueueModel(
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
            ModelResponse(content="final"),
        )
    )
    agent = Agent(model=model, tools=(EchoTool(),), owner_user_id="user_1")

    result = await agent.arun("Use the tool")

    assert result.status == "completed"
    assert result.tool_results[0].content == "tool output"
    assert model.requests[0].tools[0].name == "echo"
    assert any(event.type == "tool_result" for event in agent.events.events)


def test_agent_registers_capabilities_without_running_runtime() -> None:
    capability = SimpleCapability()
    agent = Agent(
        model=QueueModel((ModelResponse(content="hello"),)),
        capabilities=(capability,),
    )

    assert agent.capabilities == {"simple": capability}


def test_agent_runs_registered_capability() -> None:
    asyncio.run(check_agent_runs_registered_capability())


async def check_agent_runs_registered_capability() -> None:
    agent = Agent(
        model=QueueModel((ModelResponse(content="unused"),)),
        capabilities=(SimpleCapability(),),
    )

    result = await agent.arun("from capability", capability="simple")

    assert result.status == "completed"
    assert result.content == "from capability"
    assert tuple(run.kind for run in agent.runs.runs.values()) == ("capability_stage",)
    assert tuple(event.type for event in agent.events.events) == ("stage_start", "stage_end")


def test_agent_rejects_cross_user_session_access() -> None:
    asyncio.run(check_agent_rejects_cross_user_session_access())


async def check_agent_rejects_cross_user_session_access() -> None:
    agent = Agent(model=QueueModel((ModelResponse(content="unused"),)), owner_user_id="user_1")
    session = await agent.create_session()

    with pytest.raises(UAFError) as error:
        await agent.arun("Hi", session=session, principal=Principal(user_id="user_2"))

    assert error.value.code == "session.access_denied"
