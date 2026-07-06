import asyncio

from turn.artifact import MemoryArtifactStore
from turn.capability import (
    CapabilityContext,
    CapabilityManifest,
    CapabilityResult,
    CapabilityRuntime,
)
from turn.event.sink import EventSink
from turn.event.store import MemoryEventStore
from turn.memory import MemorySessionMemoryStore
from turn.model import ModelRequest, ModelResponse
from turn.policy import DefaultPolicyRuntime
from turn.prompt import DefaultPromptCompiler, PromptCompileCommand
from turn.run.cancel import CancellationToken
from turn.run.store import MemoryRunStore
from turn.secret import MemorySecretLeaseProvider
from turn.tool import ToolRuntime
from turn.user import Principal


class Model:
    async def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(content="")


class Capability:
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(name="research")

    async def run(self, context: CapabilityContext) -> CapabilityResult:
        await context.memory.write_session_preference(
            session_id=context.session_id,
            turn_id=context.turn_id,
            text="remember",
            reason="test",
        )
        artifact = await context.artifact_store.save(
            session_id=context.session_id,
            turn_id=context.turn_id,
            run_id=None,
            filename="result.txt",
            mime_type="text/plain",
            content=b"artifact",
        )
        return CapabilityResult(status="completed", content=artifact.artifact_id)


def test_capability_runtime_records_stage_events_and_run() -> None:
    asyncio.run(check_capability_runtime_records_stage_events_and_run())


async def check_capability_runtime_records_stage_events_and_run() -> None:
    runs = MemoryRunStore()
    events = MemoryEventStore()
    memory = MemorySessionMemoryStore()
    prompt = await DefaultPromptCompiler().compile_for_turn(
        PromptCompileCommand(session_id="sess_1", turn_id="turn_1")
    )
    context = CapabilityContext(
        session_id="sess_1",
        turn_id="turn_1",
        principal=Principal(user_id="user_1"),
        user_message="hello",
        prompt_snapshot=prompt,
        memory_snapshot=await memory.build_snapshot(session_id="sess_1", turn_id="turn_1"),
        tool_runtime=ToolRuntime(tools={}, default_timeout_seconds=None),
        model=Model(),
        event_sink=EventSink(store=events, session_id="sess_1", turn_id="turn_1"),
        artifact_store=MemoryArtifactStore(),
        memory=memory,
        secrets=MemorySecretLeaseProvider(),
        policy=DefaultPolicyRuntime(),
        cancellation_token=CancellationToken(),
    )

    result = await CapabilityRuntime(runs).run(capability=Capability(), context=context)

    assert result.status == "completed"
    assert result.content.startswith("art_")
    assert tuple(event.type for event in await events.list_by_turn(turn_id="turn_1")) == (
        "stage_start",
        "stage_end",
    )
    recorded = await runs.list_runs_for_turn("turn_1")
    assert len(recorded) == 1
    assert recorded[0].kind == "capability_stage"
    assert recorded[0].status == "completed"
