"""Developer facade for running one agent."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import replace
from datetime import datetime, timezone

from turn.agent.loop import AgentLoop
from turn.agent.result import TurnResult
from turn.approval import ApprovalService, MemoryApprovalRepository
from turn.artifact import MemoryArtifactStore
from turn.capability import BaseCapability, CapabilityContext, CapabilityRuntime
from turn.error import UAFError
from turn.event.sink import EventSink
from turn.event.store import MemoryEventStore
from turn.memory import MemorySessionMemoryStore, MemorySnapshot
from turn.model import ModelPort
from turn.policy import DefaultPolicyRuntime
from turn.prompt import DefaultPromptCompiler, PromptCompileCommand, PromptSource, PromptSnapshot
from turn.prompt.store import MemoryPromptSnapshotStore
from turn.run.cancel import CancellationToken
from turn.run.model import Message, Run, Turn
from turn.run.store import MemoryMessageStore, MemoryRunStore, MemoryTurnStore
from turn.run.turn import TurnExecution
from turn.secret import MemorySecretLeaseProvider
from turn.session import Session
from turn.session.auth import SessionAuthorizer, authorize_session
from turn.session.guard import MemorySessionTurnLock
from turn.session.store import MemorySessionStore
from turn.tool import BaseTool, MemoryToolRegistrySnapshotStore, ToolRegistry, ToolRuntime
from turn.user import Principal
from turn.wire import CommandEnvelope


class Agent:
    """Small public entry point for a runnable agent."""

    def __init__(
        self,
        *,
        model: ModelPort,
        instructions: str = "",
        tools: tuple[BaseTool, ...] = (),
        capabilities: tuple[BaseCapability, ...] = (),
        owner_user_id: str = "local",
        title: str = "Agent",
        max_iterations: int = 4,
    ) -> None:
        self.model = model
        self.instructions = instructions
        self.owner_user_id = owner_user_id
        self.title = title
        self.sessions = MemorySessionStore()
        self.turns = MemoryTurnStore()
        self.runs = MemoryRunStore()
        self.messages = MemoryMessageStore()
        self.approvals = MemoryApprovalRepository()
        self.events = MemoryEventStore()
        self.artifacts = MemoryArtifactStore()
        self.secrets = MemorySecretLeaseProvider()
        self.policy = DefaultPolicyRuntime()
        self.memory = MemorySessionMemoryStore()
        self.prompts = MemoryPromptSnapshotStore()
        self.tool_snapshots = MemoryToolRegistrySnapshotStore()
        self.locks = MemorySessionTurnLock()
        self.authorizer = SessionAuthorizer(self.sessions, self.turns)
        self.approval = ApprovalService(
            approvals=self.approvals,
            turns=self.turns,
            authorizer=self.authorizer,
        )
        self.tools = ToolRegistry()
        self.capabilities: dict[str, BaseCapability] = {}
        for tool in tools:
            self.tools.register(tool)
        for capability in capabilities:
            self.add_capability(capability)
        tool_runtime = ToolRuntime(
            tools={tool.definition.name: tool for tool in tools},
            default_timeout_seconds=None,
        )
        self.loop = AgentLoop(
            model=model,
            tool_runtime=tool_runtime,
            max_iterations=max_iterations,
        )
        self.capability_runtime = CapabilityRuntime(self.runs)

    def add_tool(self, tool: BaseTool) -> None:
        self.tools.register(tool)
        self.loop.tool_runtime.tools[tool.definition.name] = tool

    def add_capability(self, capability: BaseCapability) -> None:
        name = capability.manifest.name
        if name in self.capabilities:
            raise KeyError(name)
        self.capabilities[name] = capability

    def run(
        self,
        message: str,
        *,
        session: Session | None = None,
        principal: Principal | None = None,
        capability: str | None = None,
    ) -> TurnResult:
        return asyncio.run(
            self.arun(message, session=session, principal=principal, capability=capability)
        )

    async def arun(
        self,
        message: str,
        *,
        session: Session | None = None,
        principal: Principal | None = None,
        capability: str | None = None,
    ) -> TurnResult:
        if not message:
            raise ValueError("message must be non-empty")
        active_session = session or await self.create_session()
        actor = principal or Principal(user_id=active_session.owner_user_id)
        authorize_session(actor, active_session)
        now = datetime.now(timezone.utc)
        turn_id = f"turn_{uuid.uuid4().hex}"
        command = CommandEnvelope(
            command_id=f"cmd_{uuid.uuid4().hex}",
            type="start_turn",
            session_id=active_session.session_id,
            turn_id=turn_id,
            payload={"content": message},
        )
        turn = Turn(
            turn_id=turn_id,
            session_id=active_session.session_id,
            parent_turn_id=None,
            status="queued",
            command_snapshot=dict(command.payload),
            prompt_snapshot_id=None,
            tool_registry_snapshot_id=None,
            memory_snapshot_id=None,
            created_at=now,
            started_at=None,
            completed_at=None,
        )
        await self.turns.create_turn(turn)
        await self.messages.append_message(
            Message(
                message_id=f"msg_{uuid.uuid4().hex}",
                session_id=active_session.session_id,
                turn_id=turn_id,
                role="user",
                content=message,
                artifact_ids=(),
                created_at=now,
            )
        )
        async with await self.locks.acquire_active_turn_lock(
            session_id=active_session.session_id,
            turn_id=turn_id,
            ttl_seconds=30,
        ):
            started = datetime.now(timezone.utc)
            prompt = await self._compile_prompt(active_session, turn_id)
            memory = await self.memory.build_snapshot(
                session_id=active_session.session_id,
                turn_id=turn_id,
            )
            tools = self.tools.build_snapshot(
                session_id=active_session.session_id,
                turn_id=turn_id,
            )
            await self.prompts.save(prompt)
            await self.tool_snapshots.save(tools)
            await self.turns.update_turn(
                replace(
                    turn,
                    status="running",
                    started_at=started,
                    prompt_snapshot_id=prompt.snapshot_id,
                    tool_registry_snapshot_id=tools.snapshot_id,
                    memory_snapshot_id=memory.snapshot_id,
                )
            )
            event_sink = EventSink(
                store=self.events,
                session_id=active_session.session_id,
                turn_id=turn_id,
            )
            token = CancellationToken()
            if capability is None:
                run = Run(
                    run_id=f"run_{uuid.uuid4().hex}",
                    session_id=active_session.session_id,
                    turn_id=turn_id,
                    kind="agent_loop",
                    status="running",
                    input_summary=message,
                    output_summary=None,
                    error=None,
                    created_at=started,
                    completed_at=None,
                )
                await self.runs.create_run(run)
                result = await self.loop.run(
                    TurnExecution(
                        session_id=active_session.session_id,
                        turn_id=turn_id,
                        command=command,
                        principal=actor,
                        cancellation_token=token,
                        event_sink=event_sink,
                        started_at=started,
                        prompt_snapshot=prompt,
                        memory_snapshot=memory,
                        tool_registry_snapshot=tools,
                    )
                )
                await self._update_run(run, result)
            else:
                result = await self._run_capability(
                    capability=capability,
                    session=active_session,
                    turn_id=turn_id,
                    principal=actor,
                    message=message,
                    prompt=prompt,
                    memory=memory,
                    event_sink=event_sink,
                    cancellation_token=token,
                )
            completed = datetime.now(timezone.utc)
            await self.turns.update_turn(
                replace(
                    await _require_turn(self.turns, turn_id),
                    status=result.status,
                    completed_at=completed,
                )
            )
            if result.content:
                await self.messages.append_message(
                    Message(
                        message_id=f"msg_{uuid.uuid4().hex}",
                        session_id=active_session.session_id,
                        turn_id=turn_id,
                        role="assistant",
                        content=result.content,
                        artifact_ids=(),
                        created_at=completed,
                    )
                )
            return result

    async def _update_run(self, run: Run, result: TurnResult) -> None:
        await self.runs.update_run(
            replace(
                run,
                status=result.status,
                output_summary=result.content,
                error=result.error,
                completed_at=datetime.now(timezone.utc),
            )
        )

    async def _run_capability(
        self,
        *,
        capability: str,
        session: Session,
        turn_id: str,
        principal: Principal,
        message: str,
        prompt: PromptSnapshot,
        memory: MemorySnapshot,
        event_sink: EventSink,
        cancellation_token: CancellationToken,
    ) -> TurnResult:
        item = self.capabilities.get(capability)
        if item is None:
            raise UAFError(
                code="capability.not_found",
                message="Capability was not registered",
                metadata={"capability": capability},
            )
        result = await self.capability_runtime.run(
            capability=item,
            context=CapabilityContext(
                session_id=session.session_id,
                turn_id=turn_id,
                principal=principal,
                user_message=message,
                prompt_snapshot=prompt,
                memory_snapshot=memory,
                tool_runtime=self.loop.tool_runtime,
                model=self.model,
                event_sink=event_sink,
                artifact_store=self.artifacts,
                memory=self.memory,
                secrets=self.secrets,
                policy=self.policy,
                cancellation_token=cancellation_token,
            ),
        )
        return TurnResult(
            session_id=session.session_id,
            turn_id=turn_id,
            status="completed" if result.status == "completed" else "failed",
            content=result.content,
            error=result.error,
        )

    async def create_session(self, *, title: str | None = None) -> Session:
        return await self.sessions.create_session(
            owner_user_id=self.owner_user_id,
            title=self.title if title is None else title,
        )

    async def _compile_prompt(self, session: Session, turn_id: str) -> PromptSnapshot:
        sources = _instruction_sources(self.instructions)
        memory = await self.memory.build_snapshot(session_id=session.session_id, turn_id=turn_id)
        return await DefaultPromptCompiler().compile_for_turn(
            PromptCompileCommand(
                session_id=session.session_id,
                turn_id=turn_id,
                sources=sources,
                memory_injection=_memory_text(memory),
            )
        )


def _instruction_sources(instructions: str) -> tuple[PromptSource, ...]:
    if not instructions:
        return ()
    return (
        PromptSource.from_text(
            source_id="agent:instructions",
            source_type="framework_builtin",
            priority=0,
            content=instructions,
        ),
    )


def _memory_text(snapshot: MemorySnapshot) -> str | None:
    parts = tuple(
        part
        for part in (snapshot.recent_summary, snapshot.profile_notes, snapshot.preferences)
        if part
    )
    return "\n\n".join(parts) if parts else None


async def _require_turn(turns: MemoryTurnStore, turn_id: str) -> Turn:
    turn = await turns.get_turn(turn_id)
    if turn is None:
        raise KeyError(turn_id)
    return turn


__all__ = ["Agent"]
