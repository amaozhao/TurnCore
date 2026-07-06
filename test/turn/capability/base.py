import asyncio
from operator import setitem

import pytest

from turn.capability import CapabilityContext
from turn.artifact import MemoryArtifactStore
from turn.event.sink import EventSink
from turn.event.store import MemoryEventStore
from turn.memory import MemorySessionMemoryStore
from turn.model import ModelRequest, ModelResponse
from turn.policy import DefaultPolicyRuntime
from turn.prompt import DefaultPromptCompiler, PromptCompileCommand
from turn.run.cancel import CancellationToken
from turn.secret import MemorySecretLeaseProvider
from turn.tool import ToolRuntime
from turn.user import Principal


class NoopPort:
    async def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(content="")


def test_capability_context_config_is_frozen_copy() -> None:
    context_config: dict[str, object] = {"depth": 1}
    prompt = asyncio.run(async_prompt())
    memory = MemorySessionMemoryStore()
    memory_snapshot = asyncio.run(memory.build_snapshot(session_id="sess_1", turn_id="turn_1"))
    context = CapabilityContext(
        session_id="sess_1",
        turn_id="turn_1",
        principal=Principal(user_id="user_1"),
        user_message="hello",
        prompt_snapshot=prompt,
        memory_snapshot=memory_snapshot,
        tool_runtime=ToolRuntime(tools={}, default_timeout_seconds=None),
        model=NoopPort(),
        event_sink=EventSink(store=MemoryEventStore(), session_id="sess_1", turn_id="turn_1"),
        artifact_store=MemoryArtifactStore(),
        memory=memory,
        secrets=MemorySecretLeaseProvider(),
        policy=DefaultPolicyRuntime(),
        cancellation_token=CancellationToken(),
        config=context_config,
    )

    context_config["depth"] = 2

    assert context.config["depth"] == 1
    with pytest.raises(TypeError):
        setitem(context.config, "depth", 2)


async def async_prompt():
    compiler = DefaultPromptCompiler()
    return await compiler.compile_for_turn(
        PromptCompileCommand(session_id="sess_1", turn_id="turn_1")
    )
