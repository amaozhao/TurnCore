# TurnCore / UAF 后端 Agent Kernel 与 Session-Scoped Capability Pack 协议规格

## 1. 项目定位

TurnCore 是 Universal Agent Fabric（UAF）协议的 Python 库实现。下文用 UAF 指代协议与架构边界，用 TurnCore 指代本仓库实现。

UAF 定位为一个**后端优先、自研 Agent Kernel、协议优先的 Agent 基座框架**。它不以适配外部 Agent 框架为核心，也不绑定某个 Web 框架、数据库、消息队列、向量库或模型 SDK。

开发者体验目标是最终提供类似 Agno 的少量代码入口，用于创建 agent、绑定 tool / capability、启动 session 和运行 turn。这个入口属于 AgentLoop、ToolRuntime、Capability Pack Protocol 完成后的上层 facade；Phase 1 到 Phase 3 只落地可复用的协议模型、session runtime 和 prompt runtime，不暴露可运行的 Agent 对象。

UAF 的核心目标是：

1. 提供一个自研 Agent 执行内核：AgentLoop、ToolRuntime、CapabilityRuntime、TeamRuntime、MemoryRuntime、PolicyRuntime、ApprovalRuntime、EventRuntime。
2. 提供一套公共 Capability Pack 扩展协议，让业务方可以快速接入自己的能力包。
3. 提供统一客户端接入协议，而不是固定某个 API 实现。
4. 提供多用户环境下的 session 级隔离、运行时并发隔离、提示词隔离、工具权限隔离和事件流隔离。
5. 提供工程化规范：命名、目录、异常、错误码、日志、审计、测试、Pack 发布、兼容性。

核心判断：**User 是身份主体；Session 是运行命名空间；Turn / Run / Event / Artifact / Memory / Approval 等运行态资源都应归属于 Session，而不是直接归属于 User。**

## 2. 核心边界

### 2.1 不做什么

UAF 不做以下事情：

- 不把 LangGraph、CrewAI、AutoGen、Agno 等作为必须适配的 AgentAdapter 主路径。
- 不把 REST、SSE、WebSocket 路由写死在 core 中。
- 不绑定 FastAPI、Django、Starlette、Flask、gRPC 或任意 Web 框架。
- 不绑定 Postgres、SQLite、MongoDB、Redis、Qdrant、Milvus、S3 或任意存储系统。
- 不让 tool / capability 直接操作 HTTP request、WebSocket、数据库连接或模型 SDK。
- 不把 user_id 扩散到所有运行态对象中作为所有权字段。

### 2.2 要做什么

UAF 要提供：

- Agent Kernel：自研 ReAct / tool-calling loop。
- Capability Runtime：多阶段能力管线。
- Capability Pack Protocol：能力包声明、注册、加载、验证、运行接口。
- Session Runtime：会话、回合、运行、事件、artifact 的生命周期管理。
- Prompt Runtime：类似 SOUL.md / AGENTS.md / Pack prompt / Session instruction 的统一编译和快照机制。
- Tool Runtime：工具注册、权限、超时、错误、并发、审计。
- Memory Runtime：session-scoped memory 与可选 user default profile 的快照注入。
- Policy Runtime：能力、工具、文件、网络、MCP、代码执行、审批策略。
- Transport Binding Protocol：WebSocket / SSE / REST / CLI / IM 对统一 command / event 协议的绑定规范。
- Port / Adapter 机制：所有基础设施都通过接口注入。

## 3. 概念模型

### 3.1 User 与 Session 的正确关系

多用户系统中，`User` 的职责是：

- 身份认证主体。
- Session 的拥有者。
- 默认配置的来源，例如默认 PromptProfile、默认模型选择、默认能力包授权、默认 secret 引用。
- 访问控制判断的 principal。
- 审计中的 actor。

`Principal` 是认证层解析出的当前调用者，不是运行态资源所有权模型：

```python
@dataclass(frozen=True)
class Principal:
    user_id: str
    roles: list[str]
    scopes: list[str]
```

`Principal.user_id` 只用于认证、授权和审计。运行态资源访问仍必须先落到 session，再校验 `Session.owner_user_id`。

`Session` 的职责是：

- Agent 运行命名空间。
- 对话上下文边界。
- PromptProfile 快照边界。
- Memory 边界。
- ToolRegistrySnapshot 边界。
- Event 流边界。
- Artifact / upload / generated file 边界。
- Approval / run / turn / trace 边界。

因此运行态对象应按如下方式关联：

```text
User
 └── owns Session
      ├── Message
      ├── Turn
      │    ├── Run
      │    ├── StreamEvent
      │    ├── ToolCall
      │    ├── ApprovalRequest
      │    ├── Artifact
      │    └── TraceSpan
      ├── SessionMemory
      ├── SessionPromptProfile
      ├── SessionPackSelection
      └── SessionConnectionProfile
```

不推荐：

```text
User
 ├── Turn
 ├── Run
 ├── StreamEvent
 ├── Artifact
 ├── ToolCall
 ├── ApprovalRequest
 └── TraceSpan
```

因为这样会导致：

- 访问控制路径混乱。
- 同一用户多个 session 之间难以隔离。
- 删除 session 时无法完整回收运行态资源。
- 并发执行时容易串事件、串 prompt、串 artifact。
- 后续如果支持 session 分享或迁移，重构成本很高。

### 3.2 哪些资源可以直接关联 User

可以直接关联 `user_id` 的资源仅限身份层和默认配置层：

| 资源 | 是否直接 user-scoped | 说明 |
|---|---:|---|
| User | 是 | 身份主体。 |
| Session | 是 | `sessions.owner_user_id` 是核心访问控制字段。 |
| UserDefaultPromptProfile | 是 | 类似用户默认 SOUL.md，但只作为创建 session 或编译 prompt 的输入。 |
| UserModelPreference | 是 | 默认模型偏好，可被 session 覆盖。 |
| UserPackGrant | 是 | 用户被允许启用哪些 pack。真正运行时由 session 选择并冻结。 |
| UserSecretRef | 是 | 用户凭据引用。工具运行时只能通过 session-bound secret lease 使用。 |
| AuditLog.actor_user_id | 是 | 表示谁执行了某个动作，不表示资源所有权。 |
| Artifact | 否 | 应归属于 session/turn/run。 |
| Event | 否 | 应归属于 turn，间接归属于 session。 |
| MemoryEntry | 默认否 | 运行态 memory 应归属于 session。若有跨 session 用户记忆，应作为 user default profile 或显式 user memory extension，不进入默认核心模型。 |
| ToolCall | 否 | 应归属于 run/turn。 |
| ApprovalRequest | 否 | 应归属于 session/turn/run，审批 actor 记录为 user。 |
| MCPTokenCache | 受控例外 | 凭据属于 user，但使用必须经 session-bound lease。 |

### 3.3 为什么 Session 是隔离边界

Agent 产品中真正需要隔离的是“某一次对话/任务上下文”，而不是整个用户。

同一个用户可以同时开多个 session：

- 一个用于金融研究。
- 一个用于教育答疑。
- 一个用于企业知识库问答。
- 一个用于代码分析。

这些 session 之间不应该共享：

- 当前 prompt 快照。
- 当前记忆快照。
- 工具调用历史。
- event stream。
- artifact。
- pending approval。
- cancellation token。
- workspace。
- MCP tool registry snapshot。

它们可以共享的只是用户默认配置，例如默认语言、默认模型、默认 persona、默认已授权能力包、用户凭据引用。但共享必须发生在 session 创建或 turn 启动时的快照编译阶段，而不是运行中直接读取可变 user state。

## 4. 资源归属模型

### 4.1 标准资源树

```text
Principal(user_id)
  └── Session(owner_user_id=user_id)
        ├── SessionConfig
        ├── SessionPromptProfile
        ├── SessionMemory
        ├── SessionPackSelection
        ├── Message[]
        ├── Turn[]
        │     ├── PromptSnapshot
        │     ├── ToolRegistrySnapshot
        │     ├── MemorySnapshot
        │     ├── Run[]
        │     │     ├── ToolCall[]
        │     │     ├── TraceSpan[]
        │     │     └── UsageRecord[]
        │     ├── StreamEvent[]
        │     ├── ApprovalRequest[]
        │     └── Artifact[]
        └── Upload[]
```

### 4.2 访问控制路径

所有运行态访问都必须走：

```text
principal.user_id
  -> session_id
  -> Session.owner_user_id == principal.user_id
  -> resource.session_id == session_id
```

对于只拿到 `turn_id`、`run_id`、`artifact_id`、`approval_id` 的请求，必须先反查其 `session_id`，再校验 session owner。

```python
async def authorize_turn_access(principal: Principal, turn_id: str) -> Turn:
    turn = await turn_repo.get_turn(turn_id)
    if turn is None:
        raise NotFoundError("turn.not_found")
    session = await session_repo.get_session(turn.session_id)
    if session is None:
        raise NotFoundError("session.not_found")
    if session.owner_user_id != principal.user_id:
        raise PermissionDeniedError("session.access_denied")
    return turn
```

禁止：

```python
# 不推荐：直接通过 user_id 查 event / artifact / tool_call
await event_store.list_events(user_id=user_id)
await artifact_store.get_artifact(user_id=user_id, artifact_id=artifact_id)
```

推荐：

```python
await event_store.list_events(turn_id=turn_id)
await artifact_store.get_artifact(session_id=session_id, artifact_id=artifact_id)
```

### 4.3 允许冗余 user_id 吗

可以为了查询性能在运行态表中冗余 `owner_user_id`，但它必须满足以下规则：

1. 该字段由 `Session.owner_user_id` 派生。
2. 不作为唯一访问控制依据。
3. 不能由 client 或 pack 直接写入。
4. 更新 session ownership 或迁移 session 时必须同步修复。
5. 安全校验仍以 session owner 为准。

推荐字段名使用：

```text
owner_user_id_cache
```

不要命名为：

```text
user_id
```

否则开发者容易误以为资源本身是 user-scoped。

## 5. PromptProfile 与 SOUL.md / AGENTS.md 隔离设计

### 5.1 问题

类似 `SOUL.md`、`AGENTS.md`、persona、系统提示词、能力包内置提示词这类内容，在多用户、多 session、多并发 turn 环境下最容易出现串扰。

常见错误做法：

```python
# 错误：AgentLoop 运行中直接读用户可变文件
system_prompt = read_file(f"users/{user_id}/SOUL.md")
```

问题：

- 用户修改 SOUL.md 会影响正在运行的 turn。
- 同一用户多个 session 无法独立维护提示词。
- pack 提示词和用户提示词合并顺序不稳定。
- 并发 turn 可能读到不一致状态。
- 难以审计“这次回答到底用了哪些提示词”。

### 5.2 正确抽象：PromptSource -> SessionPromptProfile -> PromptSnapshot

UAF 将所有提示词统一抽象为 `PromptSource`：

```python
@dataclass(frozen=True)
class PromptSource:
    source_id: str
    source_type: Literal[
        "framework_builtin",
        "pack_builtin",
        "user_default",
        "session_profile",
        "turn_overlay",
        "memory_injection",
        "knowledge_injection",
        "tool_manifest",
        "capability_manifest",
    ]
    priority: int
    content: str
    checksum: str
    metadata: Mapping[str, object]
```

其中：

- `framework_builtin`：框架内置基础系统提示词。
- `pack_builtin`：能力包内置提示词，例如 pack 内的 `AGENTS.md`、`SKILL.md`、`SOUL.md` 等。
- `user_default`：用户默认个性提示词，只作为 session 初始化或 turn 编译输入。
- `session_profile`：session 级提示词，是运行隔离的主提示词。
- `turn_overlay`：当前 turn 的临时附加指令。
- `memory_injection`：session memory 编译后的摘要。
- `knowledge_injection`：当前 turn 检索到的知识注入。
- `tool_manifest`：当前 tool snapshot 的工具说明。
- `capability_manifest`：当前 capability 的阶段和行为说明。

### 5.3 SessionPromptProfile

Session 创建时，系统从用户默认提示词和请求参数生成 `SessionPromptProfile`。

```python
@dataclass(frozen=True)
class SessionPromptProfile:
    profile_id: str
    session_id: str
    base_prompt: str
    persona_prompt: str
    style_prompt: str
    safety_prompt: str
    pack_prompt_refs: tuple[str, ...]
    created_from_user_default_id: str | None
    revision: int
    checksum: str
```

关键规则：

1. SessionPromptProfile 归属于 session。
2. 用户默认 SOUL.md / persona 只是 profile 的来源之一。
3. 用户后续修改默认 SOUL.md，不影响已存在 session，除非显式刷新 session profile。
4. 每个 turn 都基于当前 SessionPromptProfile 编译独立 PromptSnapshot。

### 5.4 PromptSnapshot

Turn 启动前必须冻结 PromptSnapshot。

```python
@dataclass(frozen=True)
class PromptSnapshot:
    snapshot_id: str
    session_id: str
    turn_id: str
    sources: tuple[PromptSource, ...]
    compiled_system_prompt: str
    compiled_developer_prompt: str | None
    compiled_tool_manifest: str
    compiled_capability_manifest: str
    checksum: str
    created_at: datetime
```

AgentLoop 运行时只能读取 `PromptSnapshot`，不能再读取可变文件、用户默认配置或 pack 原始 prompt。

```python
@dataclass(frozen=True)
class PromptCompileCommand:
    session_id: str
    turn_id: str
    sources: tuple[PromptSource, ...]
    profile: SessionPromptProfile | None
    memory_injection: str | None
    knowledge_injection: str | None
    turn_overlay: str | None
    tool_manifest: str | None
    capability_manifest: str | None


class PromptCompiler(Protocol):
    async def compile_for_turn(
        self,
        command: PromptCompileCommand,
    ) -> PromptSnapshot:
        ...
```

```python
class PromptSnapshotStore(Protocol):
    async def save(self, snapshot: PromptSnapshot) -> None:
        ...

    async def get_by_turn(
        self,
        *,
        session_id: str,
        turn_id: str,
    ) -> PromptSnapshot | None:
        ...
```

`save()` 是冻结操作。同一个 `session_id` + `turn_id` 已存在 snapshot 时，store 必须拒绝覆盖，保证一次 turn 的 prompt 证据不会被后续写入改写。

### 5.5 Prompt 合并顺序

推荐合并顺序：

```text
1. Framework Kernel Prompt
2. Safety / Policy Prompt
3. Capability Runtime Prompt
4. Pack Builtin Prompt
5. Tool Manifest Prompt
6. SessionPromptProfile
7. SessionMemory Injection
8. Knowledge Injection
9. Turn Overlay
10. User Message
```

Pack prompt 不能覆盖框架安全边界；用户 prompt 不能覆盖 tool 权限；turn overlay 不能覆盖 approval policy。

### 5.6 Prompt 文件命名建议

能力包可以提供以下提示词文件，但它们只是 `PromptSource` 的来源，不是运行时直接读取的对象：

```text
packs/<pack>/prompts/AGENTS.md
packs/<pack>/prompts/SOUL.md
packs/<pack>/prompts/SYSTEM.md
packs/<pack>/prompts/TOOLS.md
packs/<pack>/prompts/CAPABILITY.md
```

这些路径表示外部能力包自己的资源布局，不要求放进 TurnCore 仓库。

用户默认提示词可以命名为：

```text
default.md
soul.md
persona.md
```

Session 级提示词建议命名为：

```text
profile.md
persona.md
constraint.md
```

但无论底层文件怎么命名，core 只消费 `PromptSource` 和 `PromptSnapshot`。

## 6. Session Runtime

### 6.1 Session 对象

```python
@dataclass(frozen=True)
class Session:
    session_id: str
    owner_user_id: str
    title: str
    status: Literal["active", "archived", "deleted"]
    prompt_profile_id: str | None
    pack_selection_id: str | None
    default_capability: str
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime
```

Session 只引用当前 pack selection。具体启用哪些 pack 由 `SessionPackSelection` 拥有，避免 Session 对象和 selection 记录形成双重事实来源。

```python
@dataclass(frozen=True)
class SessionPackSelection:
    selection_id: str
    session_id: str
    enabled_pack_ids: list[str]
    enabled_tool_names: list[str]
    revision: int
    checksum: str
```

### 6.2 SessionRepository

```python
class SessionRepository(Protocol):
    async def create_session(
        self,
        *,
        owner_user_id: str,
        title: str,
        prompt_profile_id: str | None,
        pack_selection_id: str | None,
        default_capability: str,
        config: dict[str, Any],
    ) -> Session:
        ...

    async def get_session(self, session_id: str) -> Session | None:
        ...

    async def list_sessions_for_user(
        self,
        *,
        owner_user_id: str,
        limit: int,
        cursor: str | None = None,
    ) -> Page[Session]:
        ...

    async def update_session(self, session: Session) -> None:
        ...

    async def archive_session(self, session_id: str) -> None:
        ...
```

注意：只有 `SessionRepository` 直接按 user_id 查询。其他运行态 repository 应该优先按 session_id / turn_id / run_id 查询。

### 6.3 Session 级锁

默认策略：一个 session 同时只允许一个 active turn。

```python
class SessionTurnLock(Protocol):
    async def acquire_active_turn_lock(
        self,
        *,
        session_id: str,
        turn_id: str,
        ttl_seconds: int,
    ) -> AsyncContextManager[None]:
        ...
```

用户可以同时运行多个 session；这通过 user-level quota 控制，而不是通过 user-level runtime lock 控制。

```text
允许：user_1 同时运行 session_A 和 session_B
默认禁止：session_A 同时运行 turn_1 和 turn_2
```

对于需要后台长任务的 capability，可以使用 run-level 并发策略：

```text
session_A
 ├── foreground turn: one active
 └── background runs: controlled by capability policy
```

## 7. Turn / Run / Event 模型

### 7.1 Message

`Message` 是 session-scoped 对话消息，可选择关联到某个 turn。

```python
@dataclass(frozen=True)
class Message:
    message_id: str
    session_id: str
    turn_id: str | None
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    artifact_ids: list[str]
    created_at: datetime
```

### 7.2 Turn

```python
@dataclass(frozen=True)
class Turn:
    turn_id: str
    session_id: str
    parent_turn_id: str | None
    status: Literal[
        "queued",
        "running",
        "waiting_for_user",
        "waiting_for_approval",
        "completed",
        "failed",
        "cancelled",
    ]
    command_snapshot: dict[str, Any]
    prompt_snapshot_id: str | None
    tool_registry_snapshot_id: str | None
    memory_snapshot_id: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
```

### 7.3 Run

`Run` 是一次 AgentLoop / Capability stage / Team task 的执行实例。一个 turn 可以包含多个 run。

```python
@dataclass(frozen=True)
class Run:
    run_id: str
    session_id: str
    turn_id: str
    kind: Literal["agent_loop", "capability_stage", "team_task", "tool_batch"]
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    input_summary: str
    output_summary: str | None
    error: ErrorEnvelope | None
    created_at: datetime
    completed_at: datetime | None
```

`run.session_id` 是冗余字段，便于查询；其值必须由 turn.session_id 派生。

### 7.4 StreamEvent

核心事件协议不属于 WebSocket 或 SSE；它是 transport-independent 的事件对象。

```python
@dataclass(frozen=True)
class StreamEvent:
    event_id: str
    session_id: str
    turn_id: str
    seq: int
    type: Literal[
        "session",
        "stage_start",
        "stage_end",
        "thinking",
        "content",
        "tool_call",
        "tool_result",
        "progress",
        "sources",
        "artifact",
        "approval_required",
        "waiting_for_user",
        "error",
        "result",
        "done",
    ]
    source: str
    stage: str
    content: str
    metadata: dict[str, Any]
    created_at: datetime
```

事件访问控制通过 `session_id` 完成。

### 7.5 EventStore

```python
class EventStore(Protocol):
    async def append(self, event: StreamEvent) -> None:
        ...

    async def list_by_turn(
        self,
        *,
        turn_id: str,
        after_seq: int = 0,
        limit: int = 500,
    ) -> tuple[StreamEvent, ...]:
        ...

    async def latest_seq(self, turn_id: str) -> int:
        ...
```

Transport adapter 可以实现：

```text
WebSocket subscribe_turn(turn_id, after_seq)
SSE subscribe_turn(turn_id, after_seq)
REST poll_turn_events(turn_id, after_seq)
```

但 core 不关心具体路由。

## 8. TurnExecution 并发隔离

### 8.1 每个 Turn 的独立运行时对象

```python
@dataclass
class TurnExecution:
    session_id: str
    turn_id: str
    command: CommandEnvelope
    principal: Principal
    cancellation_token: CancellationToken
    event_sink: EventSink
    prompt_snapshot: PromptSnapshot
    memory_snapshot: MemorySnapshot
    tool_registry_snapshot: ToolRegistrySnapshot
    capability_snapshot: CapabilitySnapshot | None
    workspace: WorkspaceHandle
    secret_lease: SecretLease | None
    started_at: datetime
```

TurnExecution 必须满足：

- 不能被其他 turn 复用。
- 不能持有全局可变 PromptProfile。
- 不能持有全局可变 ToolRegistry。
- 不能把 event 写入其他 turn。
- 不能把 artifact 写入其他 session workspace。
- 取消只能取消当前 turn。

### 8.2 RuntimeRegistry 与 Snapshot

Pack / Tool / Capability 的 registry 可以是进程级只读定义表，但每个 turn 必须创建自己的 snapshot。

```python
@dataclass(frozen=True)
class ToolRegistrySnapshot:
    snapshot_id: str
    session_id: str
    turn_id: str
    tools: Mapping[str, ToolDefinition]
    policy_summary: Mapping[str, object]
    checksum: str
```

```python
class ToolRegistrySnapshotStore(Protocol):
    async def save(self, snapshot: ToolRegistrySnapshot) -> None:
        ...

    async def get_by_turn(
        self,
        *,
        session_id: str,
        turn_id: str,
    ) -> ToolRegistrySnapshot | None:
        ...
```

`ToolRegistrySnapshotStore.save()` 与 `PromptSnapshotStore.save()` 一样是冻结操作，同一个 `session_id` + `turn_id` 已存在 snapshot 时必须拒绝覆盖。

原因：

- 用户 A 的 session 可能启用了 Pack X。
- 用户 B 的 session 可能没有权限启用 Pack X。
- 同一用户不同 session 也可能选择不同 pack / tool。
- Pack 运行中升级不应影响正在执行的 turn。

### 8.3 并发策略

默认并发策略：

| 层级 | 并发策略 |
|---|---|
| User | 可同时运行多个 session，受 quota 限制。 |
| Session | 默认一个 foreground active turn。 |
| Turn | 内部可以运行多个只读 tool，但写 tool 串行。 |
| Tool batch | readonly 并发，write 串行。 |
| Capability | stage 可声明串行/并行。 |
| TeamRuntime | DAG 同层并发，不同层按依赖顺序。 |

### 8.4 只读工具并发与写工具串行

工具定义必须声明 side effect：

```python
class ToolEffect(str, Enum):
    READONLY = "readonly"
    IDEMPOTENT_WRITE = "idempotent_write"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
```

执行策略：

```text
readonly tools: same batch parallel
write tools: serial
idempotent_write: serial unless policy explicitly allows parallel
destructive: approval required by default
```

参考 Vibe-Trading 的工具批处理思路：只读工具并发，写工具串行；这能避免模型一次发出多个有副作用工具调用时造成不可恢复的状态污染。

## 9. Agent Kernel

### 9.1 AgentLoop 职责

AgentLoop 负责：

1. 接收 TurnExecution。
2. 构造模型消息。
3. 调用 ModelPort。
4. 解析模型文本与 tool calls。
5. 调用 ToolRuntime。
6. 追加 tool result。
7. 执行上下文治理。
8. 处理 ask_user / approval / cancel / timeout。
9. 生成最终 answer。
10. 写入事件、trace、usage、artifact。

### 9.2 ModelPort 与 AgentLoop 接口

Phase 4 只定义模型适配协议，不提供内置模型实现：

```python
@dataclass(frozen=True)
class ModelMessage:
    role: Literal["system", "developer", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None


@dataclass(frozen=True)
class ModelToolCall:
    call_id: str
    tool_name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True)
class ModelRequest:
    session_id: str
    turn_id: str
    messages: tuple[ModelMessage, ...]
    tools: tuple[ToolDefinition, ...]


@dataclass(frozen=True)
class ModelResponse:
    content: str
    tool_calls: tuple[ModelToolCall, ...]
    finish_reason: Literal["stop", "tool_calls", "length", "error"]


class ModelPort(Protocol):
    async def complete(self, request: ModelRequest) -> ModelResponse:
        ...
```

Phase 4 最小 `AgentLoop` 只接收注入的 `ModelPort` 和 `ToolRuntime`。上下文压缩、PolicyEngine、approval service、artifact service 属于后续阶段接入点，不在 Phase 4 内创建空壳。

```python
class AgentLoop:
    def __init__(
        self,
        *,
        model: ModelPort,
        tool_runtime: ToolRuntime,
        max_iterations: int = 4,
    ) -> None:
        ...

    async def run(self, execution: TurnExecution) -> TurnResult:
        ...
```

### 9.3 上下文治理

UAF 将“上下文治理”和“长期记忆”分开。

上下文治理用于处理当前 turn/run 的上下文窗口压力：

```text
C1 microcompact       清理旧工具结果的大块内容
C2 context_collapse   对长文本保留 head/tail，中间折叠
C3 auto_compact       超阈值时生成结构化摘要
C4 compact_tool       模型显式请求压缩
C5 iterative_update   多次压缩时更新旧摘要，减少信息衰减
```

长期记忆则属于 Memory Runtime，默认以 session 为边界。

### 9.4 强制收尾

当达到最大迭代次数、模型连续失败、上下文无法继续压缩或工具失败过多时，AgentLoop 必须触发强制收尾策略：

```text
- 禁用工具
- 注入 finish instruction
- 要求模型基于已获得的信息输出最终答复
- 如果模型仍失败，输出结构化错误或部分结果
```

用户取消不走强制收尾。取消是独立状态：停止当前 turn、发出取消事件、释放 runtime 资源，并把 turn 标记为 `cancelled`。

### 9.5 Tool error 不应默认杀死 Turn

Tool error 应作为 tool_result 返回给模型，除非错误属于 fatal：

```python
@dataclass(frozen=True)
class ToolResult:
    call_id: str
    tool_name: str
    content: str
    success: bool
    error: ErrorEnvelope | None = None
    metadata: Mapping[str, object]
```

Artifact、pause_for_user、approval payload 会在对应 runtime 阶段扩展，不在 Phase 4 的最小 ToolResult 中提前占位。

## 10. Capability Pack 公共协议

### 10.1 Capability Pack 是什么

Capability Pack 是业务能力扩展包。它不是金融、教育、代码、办公等固定能力合集，而是一套公共协议，允许任何业务方接入自己的能力。

一个 pack 可以提供：

- tools
- capabilities
- prompt sources
- policies
- memory hooks
- artifact renderers
- eval suites
- schemas
- migrations
- example commands

`migrations` 是 pack 或 adapter 自己声明的可选资源；core 可以暴露元数据，但不执行数据库迁移，也不假设某个存储系统存在。

### 10.2 pack.yaml

Phase 5 定义 `PackManifest` 等 Python 模型来表示 `pack.yaml`。core 不引入 YAML 解析依赖、不执行动态 import、不安装 pack 依赖；具体读取文件和加载 entrypoint 由后续 loader 或外部 adapter 完成。

```yaml
id: com.example.research
name: Example Research Pack
version: 0.1.0
entrypoint: example_research.pack:ResearchPack
runtime:
  min_uaf_version: ">=0.1.0"
permissions:
  tools:
    - web.read
    - file.read
  network:
    allowed_hosts:
      - api.example.com
  filesystem:
    read:
      - session_uploads
    write:
      - session_artifacts
prompts:
  - id: research_agents
    file: prompts/AGENTS.md
    source_type: pack_builtin
  - id: research_soul
    file: prompts/SOUL.md
    source_type: pack_builtin
capabilities:
  - name: deep_research
    class: example_research.capabilities:DeepResearchCapability
tools:
  - name: search_example_api
    class: example_research.tools:SearchExampleApiTool
artifacts:
  renderers:
    - class: example_research.renderers:ResearchReportRenderer
```

### 10.3 Pack 接口

```python
class CapabilityPack(Protocol):
    def describe(self) -> PackManifest:
        ...

    def register(self, registrar: PackRegistrar) -> None:
        ...
```

```python
class PackRegistrar(Protocol):
    def add_tool(self, tool_cls: type[BaseTool]) -> None:
        ...

    def add_capability(self, capability_cls: type[BaseCapability]) -> None:
        ...

    def add_prompt_source(self, source: PromptSourceDefinition) -> None:
        ...

    def add_policy_rule(self, rule: PolicyRuleDefinition) -> None:
        ...

    def add_artifact_renderer(self, renderer_cls: type[ArtifactRenderer]) -> None:
        ...
```

### 10.4 Tool 接口

Pack 注册的 tool 使用 Phase 4 已定义的 `BaseTool` 协议：提供 `definition: ToolDefinition`，并通过 `execute(call: ToolCall) -> ToolResult` 执行。

ToolContext 是 session-scoped：

`ToolContext` 属于后续阶段扩展，用于在工具需要 artifact、memory、secret 或 policy 访问时提供 session-scoped 句柄。Phase 5 不提前实现这个上下文对象。

```python
@dataclass(frozen=True)
class ToolContext:
    session_id: str
    turn_id: str
    run_id: str
    principal: Principal
    event_sink: EventSink
    artifact_store: ArtifactStore
    memory: SessionMemoryPort
    knowledge: KnowledgePort
    secrets: SecretLeaseProvider
    workspace: WorkspaceHandle
    cancellation_token: CancellationToken
    policy: PolicyDecisionSnapshot
```

Tool 可以读取 `principal` 做审计或权限判断，但不能以 `user_id` 作为资源存储命名空间。

禁止：

```python
await context.memory.write_user_memory(user_id=context.principal.user_id, ...)
```

推荐：

```python
await context.memory.write_session_memory(session_id=context.session_id, ...)
```

### 10.5 Capability 接口

```python
class BaseCapability(ABC):
    manifest: CapabilityManifest

    @abstractmethod
    async def run(self, context: CapabilityContext) -> CapabilityResult:
        ...
```

```python
@dataclass(frozen=True)
class CapabilityContext:
    session_id: str
    turn_id: str
    principal: Principal
    user_message: str
    prompt_snapshot: PromptSnapshot
    memory_snapshot: MemorySnapshot
    tool_runtime: ToolRuntime
    model_router: ModelRouter
    event_sink: EventSink
    artifact_store: ArtifactStore
    cancellation_token: CancellationToken
    config: dict[str, Any]
```

Capability 的阶段必须在 manifest 中声明：

```python
@dataclass(frozen=True)
class CapabilityManifest:
    name: str
    description: str
    stages: list[str]
    owned_tools: list[str]
    required_scopes: list[str]
    config_schema: dict[str, Any]
    output_schema: dict[str, Any] | None
```

### 10.6 Capability Pack 与 Session 的关系

Pack 的定义是全局的；Pack 的启用是 session-scoped 的。

```text
PackDefinition: global readonly
UserPackGrant: user can enable which packs
SessionPackSelection: this session enabled which packs
Turn ToolRegistrySnapshot: this turn actually sees which tools
```

因此：

- 同一个用户不同 session 可以启用不同 pack。
- 不同用户可以拥有不同 pack grant。
- Pack 升级不影响正在运行的 turn，因为 turn 使用的是 snapshot。
- ToolRegistrySnapshot 必须记录 pack id、pack version、tool checksum。

## 11. Transport Binding 协议

### 11.1 Core 不提供固定 API

UAF core 只定义 command 和 event。具体使用 WebSocket、SSE、REST、CLI、IM 由 adapter 决定。

Phase 6 只提供 transport-neutral binding helper：把外部输入映射为 `CommandEnvelope`，把 `StreamEvent` / `ErrorEnvelope` 映射为可发送的 payload。core 不启动 WebSocket/SSE/HTTP 服务，不决定 HTTP status、WebSocket close code、认证方式或具体路由。

### 11.2 CommandEnvelope

```python
@dataclass(frozen=True)
class CommandEnvelope:
    command_id: str
    type: Literal[
        "create_session",
        "start_turn",
        "subscribe_turn",
        "resume_turn",
        "cancel_turn",
        "submit_user_reply",
        "submit_approval",
        "list_sessions",
        "list_messages",
        "list_events",
        "upload_file",
    ]
    session_id: str | None
    turn_id: str | None
    payload: dict[str, Any]
    idempotency_key: str | None
```

客户端不传 `user_id`。Transport adapter 从认证层解析 principal。

### 11.3 start_turn CommandEnvelope 示例

```json
{
  "command_id": "cmd_001",
  "type": "start_turn",
  "session_id": "sess_123",
  "turn_id": null,
  "payload": {
    "content": "请分析这个文件并生成报告",
    "capability": "deep_research",
    "enabled_packs": ["com.example.research"],
    "enabled_tools": ["web_search", "read_document"],
    "attachments": [
      {
        "attachment_id": "att_1",
        "filename": "report.pdf",
        "mime_type": "application/pdf"
      }
    ],
    "config": {
      "max_iterations": 20
    },
    "parent_message_id": null
  },
  "idempotency_key": "start-sess_123-001"
}
```

### 11.4 Event 输出协议

所有 transport 输出同一 StreamEvent：

```json
{
  "event_id": "evt_001",
  "session_id": "sess_123",
  "turn_id": "turn_456",
  "seq": 12,
  "type": "tool_call",
  "source": "agent_loop",
  "stage": "researching",
  "content": "",
  "metadata": {
    "tool_name": "web_search",
    "arguments_preview": {"query": "..."}
  },
  "created_at": "2026-07-01T10:00:00Z"
}
```

### 11.5 WebSocket Binding 示例

WebSocket adapter 可以支持：

```text
client -> server: CommandEnvelope
server -> client: StreamEvent | ErrorEnvelope
```

推荐消息类型：

```text
create_session
start_turn
subscribe_turn
resume_turn
cancel_turn
submit_user_reply
submit_approval
ping
```

其中 `ping` 是 transport keepalive，可以不进入 core `CommandEnvelope`。

库内 helper 只提供 `WireMessage`、`command_to_wire()`、`wire_to_command()`、`event_to_wire()` 和 `error_to_wire()` 这类转换。

### 11.6 SSE Binding 示例

SSE adapter 可以支持：

```text
start_turn: ordinary request / command bus
subscribe_turn: event stream with cursor
resume: after_seq cursor
```

库内 helper 只提供 `SseEvent`、`event_to_sse()` 和 `error_to_sse()`，不实现 EventSource 服务端。

SSE 只是 binding，不是 core API。

### 11.7 REST Binding 示例

REST adapter 可以支持：

```text
create_session
start_turn
cancel_turn
submit_user_reply
submit_approval
list_sessions
list_messages
list_events
upload_file
```

这些接口必须映射到 CommandEnvelope 和 StreamEvent，不应直接绕过 core runtime。

库内 helper 只提供 `RestRequest`、`RestResponse`、`command_from_rest()`、`event_to_rest()` 和 `error_to_rest()`。HTTP method、status code、认证和路由由 adapter 决定。

### 11.8 CLI / IM Binding 示例

CLI 和 IM adapter 都可以把纯文本输入映射为 `start_turn` 命令：

```text
text -> CommandEnvelope(type="start_turn", payload={"content": text})
StreamEvent -> printable/reply text
ErrorEnvelope -> safe error text
```

库内 helper 只提供 `TextCommandInput`、`command_from_text()`、`event_to_text()` 和 `error_to_text()`。CLI 参数解析、IM 平台 webhook、用户身份解析和消息发送由 adapter 决定。

## 12. Memory 架构

### 12.1 SessionMemory 是默认模型

默认 memory 归属于 session：

```text
SessionMemory
 ├── L1 Event Trace
 ├── L2 Session Surface Summary
 └── L3 Session Long-Term Notes
```

这里的 L3 不是 user-level 全局记忆，而是 session 内长期信息，例如：

- 当前 session 的用户偏好。
- 当前 session 的研究目标。
- 当前 session 的知识范围。
- 当前 session 的阶段性结论。

### 12.2 User Default Profile 是 Memory 的输入，不是 Runtime Memory

用户级 profile 可以存在，但它不是运行态 memory：

```text
UserDefaultProfile
 └── used to initialize / refresh SessionPromptProfile
```

如果产品需要跨 session 用户记忆，应作为可选 extension：

```text
UserMemoryExtension
 └── read only during PromptSnapshot compilation
```

默认 core 不要求启用全局用户记忆。

### 12.3 MemorySnapshot

每个 turn 启动前冻结：

```python
@dataclass(frozen=True)
class MemorySnapshot:
    snapshot_id: str
    session_id: str
    turn_id: str
    recent_summary: str
    profile_notes: str
    preferences: str
    scope: str
    source_entry_ids: tuple[str, ...]
    checksum: str
```

AgentLoop 只能读 MemorySnapshot，不直接读 MemoryStore。

### 12.4 MemoryStore Port

```python
class SessionMemoryPort(Protocol):
    async def append_trace(
        self,
        *,
        session_id: str,
        turn_id: str,
        event: MemoryTraceEvent,
    ) -> None:
        ...

    async def read_session_memory(
        self,
        *,
        session_id: str,
    ) -> SessionMemoryDocument:
        ...

    async def write_session_preference(
        self,
        *,
        session_id: str,
        turn_id: str,
        text: str,
        reason: str,
    ) -> None:
        ...

    async def build_snapshot(
        self,
        *,
        session_id: str,
        turn_id: str,
    ) -> MemorySnapshot:
        ...
```

## 13. Secret 与外部连接隔离

### 13.1 Secret 属于用户，但使用绑定到 Session

凭据天然属于用户账户，但 Agent 运行时不能直接按 user_id 读取 secret。正确模型是：

```text
UserSecretRef
  -> SessionConnectionProfile
      -> SecretLease(session_id, turn_id, scopes)
```

Tool 只能通过 `SecretLeaseProvider` 获取当前 session 授权范围内的 secret。

```python
class SecretLeaseProvider(Protocol):
    async def get_secret(
        self,
        *,
        session_id: str,
        turn_id: str,
        name: str,
        required_scope: str,
    ) -> SecretValue:
        ...
```

### 13.2 MCP token cache

MCP token cache 可以物理上按 user 存储，但逻辑使用必须绑定 session：

```text
mcp token: user-owned credential
mcp tool call: session-scoped execution
mcp event/artifact/result: session-scoped output
```

## 14. Artifact / Upload / Workspace 隔离

### 14.1 Artifact 归属于 Session

```python
@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    session_id: str
    turn_id: str
    run_id: str | None
    filename: str
    mime_type: str
    uri: str
    size_bytes: int
    checksum: str
    created_at: datetime
```

### 14.2 Workspace 命名

推荐逻辑路径：

```text
workspace://sessions/{session_id}/turns/{turn_id}/...
artifact://sessions/{session_id}/turns/{turn_id}/{artifact_id}
```

不要使用：

```text
workspace://users/{user_id}/...
artifact://users/{user_id}/...
```

### 14.3 ArtifactStore Port

```python
class ArtifactStore(Protocol):
    async def save(
        self,
        *,
        session_id: str,
        turn_id: str,
        run_id: str | None,
        filename: str,
        mime_type: str,
        content: bytes | AsyncIterator[bytes],
    ) -> Artifact:
        ...

    async def get(
        self,
        *,
        session_id: str,
        artifact_id: str,
    ) -> Artifact | None:
        ...
```

## 15. Approval 与 ask_user

### 15.1 ask_user

`ask_user` 是 turn 内暂停，不是创建新 session，也不是结束 turn。

```python
@dataclass(frozen=True)
class AskUserPayload:
    questions: list[Question]
    resume_token: str
```

状态变化：

```text
running -> waiting_for_user -> running -> completed
```

`submit_user_reply` 必须携带 `turn_id`，系统反查 session 做访问控制。

### 15.2 Approval

ApprovalRequest 归属于 session/turn/run：

```python
@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    session_id: str
    turn_id: str
    run_id: str | None
    action: str
    reason: str
    status: Literal["pending", "approved", "rejected"]
    requested_by_user_id: str
    resolved_by_user_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
```

审批人记录为 actor：

```python
@dataclass(frozen=True)
class ApprovalDecision:
    approval_id: str
    actor_user_id: str
    decision: Literal["approved", "rejected"]
    comment: str | None
    decided_at: datetime
```

注意：`actor_user_id` 是审计字段，不是资源归属字段。

## 16. Policy 架构

### 16.1 Policy 输入

```python
@dataclass(frozen=True)
class PolicyContext:
    principal: Principal
    session: Session
    turn: Turn
    pack_ids: list[str]
    tool_name: str | None
    capability_name: str | None
    action: str
    resource: dict[str, Any]
```

### 16.2 Policy 决策

```python
@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str
    scopes: list[str]
    audit_level: Literal["none", "normal", "high", "critical"]
```

Policy 只能允许当前 session 范围内的动作。即使用户有全局 secret，也必须通过 session connection profile 显式启用。

## 17. 存储 Port 协议

### 17.1 Core 只依赖 Port

UAF core 不依赖具体数据库。所有存储通过 port 接口注入。

```python
@dataclass(frozen=True)
class StoragePorts:
    users: UserRepository
    sessions: SessionRepository
    pack_selections: SessionPackSelectionRepository
    turns: TurnRepository
    runs: RunRepository
    events: EventStore
    messages: MessageRepository
    artifacts: ArtifactStore
    memory: SessionMemoryPort
    prompts: PromptProfileRepository
    prompt_snapshots: PromptSnapshotStore
    tool_snapshots: ToolRegistrySnapshotStore
    approvals: ApprovalRepository
    audit: AuditLogStore
    locks: LockManager
```

### 17.2 关系型存储参考模型

下面只是关系型 adapter 的参考模型，不是 core 的内置数据库要求。

```text
users
  id PK

sessions
  id PK
  owner_user_id FK users.id

session_pack_selections
  id PK
  session_id FK sessions.id
  enabled_pack_ids json/text
  enabled_tool_names json/text
  revision int
  checksum str

messages
  id PK
  session_id FK sessions.id
  turn_id nullable FK turns.id

turns
  id PK
  session_id FK sessions.id

runs
  id PK
  session_id FK sessions.id  -- derived/cache
  turn_id FK turns.id

events
  id PK
  turn_id FK turns.id
  seq int

artifacts
  id PK
  session_id FK sessions.id
  turn_id FK turns.id
  run_id nullable FK runs.id

approvals
  id PK
  session_id FK sessions.id
  turn_id FK turns.id
  run_id nullable FK runs.id

session_memory_entries
  id PK
  session_id FK sessions.id

prompt_snapshots
  id PK
  session_id FK sessions.id
  turn_id FK turns.id

tool_registry_snapshots
  id PK
  session_id FK sessions.id
  turn_id FK turns.id

user_default_prompt_profiles
  id PK
  user_id FK users.id
```

### 17.3 删除语义

删除 session 时应删除或归档：

- turns
- runs
- events
- messages
- artifacts
- approvals
- session memory
- session pack selections
- prompt snapshots
- tool snapshots
- workspaces

不应删除：

- user account
- user default prompt profile
- user secret refs
- user pack grants

## 18. 错误与异常协议

### 18.1 库级错误边界

UAF 是库，不是应用服务，因此 core 不负责：

- 决定 HTTP status code。
- 关闭 WebSocket。
- 写入宿主应用日志。
- 返回 FastAPI / Django / Flask response。
- 把未知异常包装成成功结果。

Core 只负责定义稳定错误语义：

- 在库内部用 `UAFError` 或其子类表达可预期失败。
- 在需要跨 wire / tool / event 边界时，把错误转换为 `ErrorEnvelope`。
- 未预期异常应保留原始异常链，交给调用方或 adapter 处理。
- Tool error 默认是 `ToolResult.error`，不是整个 Turn 的 fatal error。
- Cancellation 是独立状态，不等同于普通失败。

责任边界：

| 层 | 职责 |
|---|---|
| core runtime | 抛出 `UAFError`、记录错误码、保留异常 cause。 |
| wire / tool result | 使用 `ErrorEnvelope` 承载安全错误信息。 |
| transport adapter | 把 `ErrorEnvelope` 映射为 HTTP status、WebSocket error event、SSE event、CLI 输出等。 |
| host application | 决定日志、告警、监控、用户展示和进程级异常处理。 |

### 18.2 UAFError

```python
class UAFError(Exception):
    code: str
    message: str
    retryable: bool
    metadata: dict[str, Any]

    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...
```

常见错误码：

```text
session.not_found
session.access_denied
session.active_turn_exists
turn.not_found
turn.cancelled
turn.not_waiting_for_user
tool.not_found
tool.timeout
tool.policy_denied
tool.approval_required
model.provider_error
model.empty_response
prompt.compile_failed
memory.snapshot_failed
artifact.not_found
pack.not_found
pack.permission_denied
```

`metadata` 只能放安全、结构化、可选的调试上下文。不得放密钥、完整 prompt、用户上传内容、内部路径、provider 原始响应或堆栈。

### 18.3 ErrorEnvelope

```python
@dataclass(frozen=True)
class ErrorEnvelope:
    code: str
    message: str
    retryable: bool
    session_id: str | None
    turn_id: str | None
    run_id: str | None
    details: dict[str, Any]
```

`ErrorEnvelope` 是跨边界错误值，不是 Python 异常的替代品。

使用场景：

- `Run.error`
- `ToolResult.error`
- `StreamEvent(type="error")`
- transport binding 输出

规则：

- `code` 必须稳定，可被调用方匹配。
- `message` 必须安全，不暴露内部实现。
- `retryable` 表示调用方是否可以重试同一语义操作。
- `details` 只能包含安全、低敏、结构化字段。
- core 不把未知异常默认转换为 `ErrorEnvelope` 后继续成功执行。

Transport adapter 可以把 `ErrorEnvelope` 映射为 HTTP status、WebSocket error event 或 SSE error event，但 core 只产出协议对象。

### 18.4 不推荐做法

```python
# 错误：库代码直接返回 HTTP response
raise HTTPException(status_code=404, detail="session not found")

# 错误：吞掉未知异常并返回空结果
try:
    snapshot = await build_snapshot(...)
except Exception:
    return PromptSnapshot.empty()

# 错误：把内部异常细节暴露到 wire
return ErrorEnvelope(
    code="internal.error",
    message=str(exc),
    details={"traceback": traceback.format_exc()},
)
```

推荐：

```python
try:
    snapshot = await build_snapshot(command)
except PromptSourceError as exc:
    raise UAFError(
        code="prompt.compile_failed",
        message="Prompt compilation failed",
        retryable=False,
        metadata={"source": exc.source_id},
    ) from exc
```

## 19. 工程命名规范

### 19.1 文件命名

自有 Python 文件名使用单个真实英文单词，保持 lowercase ASCII。

推荐：

```text
base.py
model.py
store.py
port.py
guard.py
compile.py
snapshot.py
envelope.py
```

允许的生态例外：

```text
__init__.py
pyproject.toml
```

不要用：

```text
session_runtime.py
tool_repository.py
api_router.py
prompt_compiler.py
```

如果概念需要多个词，用目录表达边界，用文件内符号表达具体含义。

### 19.2 类命名

```text
AgentLoop
ToolRuntime
CapabilityRuntime
TeamRuntime
SessionRuntime
TurnRuntime
PromptCompiler
PromptSnapshotStore
ToolRegistrySnapshot
SessionMemoryStore
PolicyEngine
ApprovalService
ArtifactStore
EventStore
```

### 19.3 方法命名

```text
create_session
get_session
list_sessions_for_user
start_turn
cancel_turn
resume_turn
submit_user_reply
submit_approval
compile_for_turn
build_snapshot
execute_tool
run_capability
append_event
save_artifact
```

避免：

```text
run(user_id=...)
save_user_artifact(...)
list_user_events(...)
execute_with_global_context(...)
```

## 20. 参考项目代码位置

### 20.1 Vibe-Trading

| 模块 | 参考文件 | 可借鉴点 |
|---|---|---|
| AgentLoop | `HKUDS/Vibe-Trading/agent/src/agent/loop.py` | ReAct loop、五层上下文治理、工具批处理、取消、trace、强制收尾。 |
| Tool 基类 | `HKUDS/Vibe-Trading/agent/src/agent/tools.py` | `BaseTool`、`ToolRegistry`、JSON Schema tool definition。 |
| Tool 注册 | `HKUDS/Vibe-Trading/agent/src/tools/__init__.py` | 自动发现、本地工具与 MCP 工具组合、shell tool policy。 |
| MCP 适配 | `HKUDS/Vibe-Trading/agent/src/tools/mcp.py` | MCP tool wrapper、schema normalize、OAuth token cache、远程工具命名。 |
| Session 服务 | `HKUDS/Vibe-Trading/agent/src/session/service.py` | session -> attempt -> AgentLoop 的调度、SSE event bridge。 |
| API binding | `HKUDS/Vibe-Trading/agent/api_server.py` | Session API、SSE event stream、upload、swarm API，作为 transport binding 参考。 |
| Swarm | `HKUDS/Vibe-Trading/agent/src/swarm/models.py`、`agent/src/swarm/runtime.py` | DAG task、agent spec、run status、同层并发。 |
| Memory | `HKUDS/Vibe-Trading/agent/src/agent/memory.py`、`agent/src/memory/persistent.py` | workspace memory 与 persistent memory 的区别。 |

### 20.2 DeepTutor

| 模块 | 参考文件 | 可借鉴点 |
|---|---|---|
| 架构说明 | `HKUDS/DeepTutor/AGENTS.md` | Tools / Capabilities 双层插件模型。 |
| UnifiedContext | `HKUDS/DeepTutor/deeptutor/core/context.py` | 单个 turn 的统一上下文对象。 |
| Tool 协议 | `HKUDS/DeepTutor/deeptutor/core/tool_protocol.py` | `BaseTool`、`ToolDefinition`、`ToolResult`、pause_for_user。 |
| Capability 协议 | `HKUDS/DeepTutor/deeptutor/core/capability_protocol.py` | `CapabilityManifest`、`BaseCapability.run(context, stream)`。 |
| StreamEvent | `HKUDS/DeepTutor/deeptutor/core/stream.py` | 统一事件类型与 payload。 |
| Orchestrator | `HKUDS/DeepTutor/deeptutor/runtime/orchestrator.py` | 统一入口，按 capability 路由。 |
| Agentic loop | `HKUDS/DeepTutor/deeptutor/agents/chat/agent_loop.py` | 单 turn 多轮 LLM + tool loop，ask_user pause/resume。 |
| WebSocket | `HKUDS/DeepTutor/deeptutor/api/routers/unified_ws.py` | start_turn、subscribe、resume、cancel、submit_user_reply 协议参考。 |
| 客户端协议 | `HKUDS/DeepTutor/web/lib/unified-ws.ts` | typed client、heartbeat、resume、seq。 |
| Memory | `HKUDS/DeepTutor/deeptutor/services/memory/store.py` | 三层持久 memory subsystem，可改为 session-scoped。 |
| Turn runtime | `HKUDS/DeepTutor/deeptutor/services/session/turn_runtime.py` | turn 级运行时、event multiplex、reply queue、stale turn 恢复。 |

### 20.3 Agno

| 模块 | 参考文件 | 可借鉴点 |
|---|---|---|
| Agent 对象 | `agno-agi/agno/libs/agno/agno/agent/agent.py` | Agent 的 session、memory、knowledge、tools、hooks、checkpoint 配置。 |
| Run 生命周期 | `agno-agi/agno/libs/agno/agno/agent/_run.py` | session 初始化、pre/post hooks、tool 解析、model call、pause、store、cleanup。 |
| Tool 解析 | `agno-agi/agno/libs/agno/agno/agent/_tools.py` | tools、knowledge、memory、skills 的运行时组合。 |
| Team | `agno-agi/agno/libs/agno/agno/team/team.py` | Team 对象、members、mode、tools、knowledge、memory。 |
| TeamMode | `agno-agi/agno/libs/agno/agno/team/mode.py` | coordinate、route、broadcast、tasks。 |
| AgentOS | `agno-agi/agno/libs/agno/agno/os/app.py` | agents、teams、workflows、knowledge、authorization、MCP、scheduler、tracing、registry。 |
| Agent router | `agno-agi/agno/libs/agno/agno/os/routers/agents/router.py` | SSE、resume、background run、cancel、approval resolved 等 transport binding 参考。 |

## 21. 多用户隔离验收标准

### 21.1 Prompt 隔离

- 用户 A 的 session 不能读取用户 B 的 SessionPromptProfile。
- 用户修改默认 SOUL.md 不影响已运行 turn。
- 同一用户两个 session 的 PromptSnapshot 可以不同。
- PromptSnapshot 必须可追溯 source checksum。

### 21.2 Runtime 隔离

- 不同 session 的 event stream 不能互相订阅。
- 不同 session 的 artifact 不能互相读取。
- 取消 turn 只能取消指定 turn。
- 同一 session 默认不能同时启动两个 foreground turn。
- 同一用户可以并发运行多个 session。

### 21.3 Tool 隔离

- Tool 只能使用 ToolContext 中的 session_id / turn_id / run_id。
- Tool 不能直接写 user-scoped runtime resource。
- ToolRegistrySnapshot 按 turn 冻结。
- Secret 使用必须通过 session-bound lease。

### 21.4 Storage 隔离

- 运行态表必须能通过 session_id 完整回收。
- 访问 artifact / event / turn / approval 必须反查 session owner。
- user_id 只作为 session owner、默认配置、secret ref、audit actor。

### 21.5 Pack 隔离

- Pack definition 是全局只读。
- Pack enablement 是 session-scoped。
- UserPackGrant 只决定用户能否在 session 中启用 pack。
- Pack upgrade 不影响 running turn。

## 22. 最小落地顺序

### 阶段 1：Core Protocol

- Principal
- Session
- Turn
- Run
- StreamEvent
- CommandEnvelope
- ErrorEnvelope
- Port interfaces

### 阶段 2：Session Runtime

- SessionRepository
- TurnRepository
- EventStore
- SessionTurnLock
- TurnExecution
- cancellation
- event sink

### 阶段 3：Prompt Runtime

- PromptSource
- SessionPromptProfile
- PromptCompiler
- PromptSnapshot
- prompt snapshot store

### 阶段 4：AgentLoop 与 ToolRuntime

- ModelPort
- BaseTool
- ToolRegistry
- ToolRegistrySnapshot
- readonly/write batching
- timeout/cancel/error

### 阶段 5：Capability Pack Protocol

- pack.yaml
- CapabilityPack
- PackRegistrar
- BaseCapability
- policy declarations
- prompt sources
- artifact renderer

### 阶段 6：Transport Binding

- transport-neutral binding helper
- WebSocket / SSE / REST / CLI / IM adapter payload mapping rules

### 阶段 7：Memory / Approval / Artifact

- SessionMemoryPort
- MemorySnapshot
- ApprovalRepository
- ArtifactStore
- SecretLeaseProvider

### 阶段 8：TeamRuntime 与 Control Plane

- DAG task runtime
- pack management
- run dashboard data
- eval suites
- audit viewer

Phase 8 当前实现为库内 transport-neutral helper：`turn.team` 提供 DAG task runtime，`turn.control` 提供 pack selection 与 dashboard data reader，`turn.eval` 提供 deterministic eval suite runner，`turn.audit` 提供 session-scoped audit viewer data。core 不启动 Web 服务、不提供 dashboard UI、不接数据库队列、不执行外部 eval 平台。

### 阶段 9：Developer Facade + Turn Orchestrator

- `Agent(...)` 高层入口
- 简单绑定 tool / capability
- 创建 session
- `run()` / `arun()` 启动 turn
- 自动编译 PromptSnapshot
- 自动构建 ToolRegistrySnapshot
- 自动构建 MemorySnapshot
- 调用 AgentLoop
- README 最小可运行示例

Phase 9 只解决“用户几行代码能跑 agent”的开发者入口。Policy / approval / authorization runtime 和 capability stage runtime 不塞进 Phase 9。

### 阶段 10：Policy / Approval / Authorization Runtime

- session authorization service
- policy checker / runtime
- tool permission decision
- approval service / runtime
- `submit_approval`
- `submit_user_reply`
- destructive / write tool 审批流

Phase 10 当前实现为库内 authorization / policy / approval helper：`turn.session.SessionAuthorizer` 通过 session owner 授权，`turn.policy.DefaultPolicyRuntime` 对 tool effect 做 allow / approval_required 决策，`turn.approval.ApprovalService` 创建并提交审批，`turn.run.UserReplyService` 恢复等待用户输入的 turn，`ToolRuntime` 对 write / destructive tool 默认要求审批。core 不提供审批 UI、不启动 transport 服务。

### 阶段 11：Capability Runtime + Context Completion

- CapabilityRuntime
- 多阶段 capability flow
- ToolContext
- CapabilityContext 补齐 memory / artifact / secret / policy
- capability stage event / run 记录
- capability 与 Agent facade 集成

Phase 11 当前实现为库内 capability runtime：`turn.capability.CapabilityRuntime` 负责执行 capability、写入 stage event 和 capability_stage run；`ToolContext` 提供 session-scoped tool 句柄；`CapabilityContext` 已补齐 memory / artifact / secret / policy；`Agent.arun(..., capability="name")` 可运行已注册 capability。core 不加载外部 pack 文件、不启动 transport service。

## 23. 关键设计原则

1. **User 是身份主体，不是运行命名空间。**
2. **Session 是运行命名空间。**
3. **Turn 是一次用户请求的执行边界。**
4. **Run 是执行实例。**
5. **Event 是 turn-scoped。**
6. **Artifact 是 session/turn-scoped。**
7. **Prompt 必须编译成 turn-scoped snapshot。**
8. **ToolRegistry 必须编译成 turn-scoped snapshot。**
9. **Memory 默认 session-scoped。**
10. **User default 只能作为初始化输入，不能作为运行中可变依赖。**
11. **Transport 是 adapter，不是 core。**
12. **数据库是 port，不是框架内置依赖。**
13. **Capability Pack 是公共扩展协议，不是固定领域能力合集。**
14. **所有运行态访问必须从 session 授权。**
