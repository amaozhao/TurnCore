# TurnCore 库目录结构说明

## 1. 目录设计原则

TurnCore 是一个可安装的 Python 库，不是一个完整后端应用，也不是部署模板仓库。因此仓库只保留库代码、测试、文档和打包元数据。

核心约束如下：

1. **所有库代码必须放在一个源码包目录下：`turn/`。**
2. **不设置 `source/`、`src/`、`app/`、`deploy/`、`server/` 等顶层代码目录。**
3. **不把 adapter、pack、api 等实现拆成多个顶层代码树。它们都是库的一部分，必须位于 `turn/` 内。**
4. **`test/` 目录必须镜像 `turn/` 代码目录结构。**
5. **自有目录名和自有 Python 文件名使用单个真实英文单词。**
6. **不使用缩写、伪单词、连字符、下划线、驼峰或复合式命名。**
7. **框架 core 不依赖 FastAPI、SQLAlchemy、Postgres、Redis、Qdrant、OpenAI SDK 等具体基础设施。所有具体实现通过 `turn/adapter/` 作为可选适配器提供。**
8. **SSE、WebSocket、REST 只是 transport binding 协议，不是 core 固定 API。库内只提供协议对象、事件对象和可选绑定工具。**
9. **User 只拥有 Session；运行态资源归属于 Session。**

唯一允许的非业务命名例外是 Python 生态强约束文件，例如 `pyproject.toml`。这是打包标准文件，不属于自有模块命名空间。

## 2. 顶层仓库结构

```text
turncore/
├── turn/
│   └── ...
├── test/
│   └── turn/
├── docs/
│   ├── index.md
│   ├── structure.md
│   ├── pack.md
│   ├── wire.md
│   ├── prompt.md
│   ├── error.md
│   └── test.md
├── standards/
│   └── ...
├── AGENTS.md
├── CLAUDE.md
├── pyproject.toml
├── readme.md
└── license
```

### 2.1 `turn/`

`turn/` 是唯一源码包目录。所有可被用户安装、导入和复用的代码都必须放在这里。

当前已实现到 Phase 11，保证 core protocol、session runtime、prompt runtime、ModelPort、AgentLoop、ToolRuntime、Capability Pack Protocol、CapabilityRuntime、transport-neutral binding helper、session memory、approval、artifact、secret lease port、TeamRuntime、control-plane data helpers、高层 `Agent(...)` facade、session authorization、policy runtime 和 approval runtime 可导入使用，例如：

```python
from turn import Agent
from turn.agent import AgentLoop
from turn.artifact import MemoryArtifactStore
from turn.capability import CapabilityRuntime
from turn.control import DashboardReader, PackManager
from turn.eval import EvalRunner
from turn.model import ModelPort
from turn.memory import MemorySessionMemoryStore
from turn.prompt import DefaultPromptCompiler, PromptCompileCommand, PromptSource
from turn.secret import MemorySecretLeaseProvider
from turn.policy import DefaultPolicyRuntime
from turn.session import SessionAuthorizer
from turn.session.store import MemorySessionStore
from turn.team import TeamRuntime
from turn.tool import ToolRegistry, ToolRuntime
```

高层入口是：

```python
from turn import Agent
```

Capability stage runtime 已接入 Agent facade；外部 pack loader 和 transport service 仍由后续 adapter 或应用层提供。

### 2.2 `test/`

`test/` 是测试目录，不是库代码。它必须完整镜像 `turn/` 的代码结构。

例如：

```text
turn/agent/loop.py
```

对应测试文件必须是：

```text
test/turn/agent/loop.py
```

为了让测试文件名保持单个单词，测试收集规则由 `pyproject.toml` 配置，而不是使用 `test_*.py` 命名。

### 2.3 `docs/`

`docs/` 只放 Markdown 文档，不放运行代码，不放部署脚本。

### 2.4 `standards/`

`standards/` 放工程标准和 agent 工作规则细化，不属于运行时代码。

### 2.5 `pyproject.toml`

`pyproject.toml` 是 Python 库打包入口。它定义包名、依赖、可选依赖、测试配置和构建后端。

TurnCore 的源码包来自 `turn/`，不使用 `src/` 布局。

### 2.6 不出现的顶层目录

以下目录不应出现在库仓库中：

```text
source/
src/
app/
apps/
server/
api/
deploy/
deployment/
infra/
plugin/
plugins/
plug/
adapter/
pack/
```

原因如下：

- `source/`、`src/`：用户已经明确要求不要使用。
- `app/`、`server/`、`api/`：TurnCore 是库，不是服务应用。
- `deploy/`、`infra/`：库不负责部署。
- `adapter/`、`pack/`：它们是库内部模块，应放在 `turn/` 内。
- `plug`：是缩写或不清晰命名，禁止使用。

## 3. `turn/` 完整目录结构

```text
turn/
├── __init__.py
├── agent/
│   ├── __init__.py
│   ├── loop.py
│   ├── step.py
│   ├── state.py
│   ├── plan.py
│   └── limit.py
├── session/
│   ├── __init__.py
│   ├── model.py
│   ├── store.py
│   ├── guard.py
│   └── branch.py
├── run/
│   ├── __init__.py
│   ├── turn.py
│   ├── task.py
│   ├── cancel.py
│   ├── resume.py
│   └── state.py
├── event/
│   ├── __init__.py
│   ├── type.py
│   ├── sink.py
│   ├── bus.py
│   └── store.py
├── wire/
│   ├── __init__.py
│   ├── command.py
│   ├── stream.py
│   ├── error.py
│   ├── route.py
│   └── socket.py
├── prompt/
│   ├── __init__.py
│   ├── profile.py
│   ├── layer.py
│   ├── compile.py
│   ├── snapshot.py
│   └── guard.py
├── context/
│   ├── __init__.py
│   ├── build.py
│   ├── compact.py
│   ├── collapse.py
│   ├── token.py
│   └── snapshot.py
├── memory/
│   ├── __init__.py
│   ├── store.py
│   ├── trace.py
│   ├── session.py
│   ├── snapshot.py
│   └── merge.py
├── tool/
│   ├── __init__.py
│   ├── base.py
│   ├── schema.py
│   ├── result.py
│   ├── registry.py
│   ├── execute.py
│   ├── batch.py
│   └── guard.py
├── capability/
│   ├── __init__.py
│   ├── base.py
│   ├── manifest.py
│   ├── registry.py
│   ├── flow.py
│   ├── stage.py
│   └── result.py
├── pack/
│   ├── __init__.py
│   ├── base.py
│   ├── manifest.py
│   ├── load.py
│   ├── check.py
│   └── registry.py
├── policy/
│   ├── __init__.py
│   ├── rule.py
│   ├── check.py
│   └── result.py
├── approval/
│   ├── __init__.py
│   ├── request.py
│   ├── store.py
│   └── service.py
├── artifact/
│   ├── __init__.py
│   ├── file.py
│   ├── store.py
│   └── view.py
├── model/
│   ├── __init__.py
│   ├── base.py
│   ├── route.py
│   ├── stream.py
│   └── usage.py
├── port/
│   ├── __init__.py
│   ├── session.py
│   ├── event.py
│   ├── artifact.py
│   ├── memory.py
│   ├── model.py
│   ├── lock.py
│   ├── secret.py
│   └── file.py
├── adapter/
│   ├── __init__.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   ├── event.py
│   │   ├── artifact.py
│   │   └── lock.py
│   ├── file/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   ├── event.py
│   │   ├── artifact.py
│   │   └── memory.py
│   ├── sqlite/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   ├── event.py
│   │   └── artifact.py
│   └── web/
│       ├── __init__.py
│       ├── route.py
│       ├── stream.py
│       └── socket.py
├── user/
│   ├── __init__.py
│   ├── auth.py
│   ├── grant.py
│   ├── profile.py
│   └── secret.py
├── error/
│   ├── __init__.py
│   ├── base.py
│   ├── code.py
│   └── envelope.py
├── trace/
│   ├── __init__.py
│   ├── span.py
│   ├── log.py
│   └── audit.py
└── shell/
    ├── __init__.py
    ├── main.py
    └── run.py
```

## 4. 模块职责说明

### 4.1 `turn/agent/`

`agent/` 是自研 Agent 内核模块。

职责：

- 管理 ReAct 风格主循环。
- 控制每轮模型调用、工具调用、上下文更新和最终回答。
- 支持工具调用后的继续推理。
- 支持到达轮次上限后的强制收尾。
- 支持取消信号、错误恢复和部分结果输出。

文件说明：

| 文件 | 职责 |
|---|---|
| `loop.py` | Agent 主循环。 |
| `result.py` | TurnResult。 |

后续上下文治理变复杂后再增加：

| 文件 | 职责 |
|---|---|
| `step.py` | 单轮执行步骤。 |
| `state.py` | AgentLoop 内部状态。 |
| `plan.py` | 计划与下一步动作抽象。 |
| `limit.py` | 轮次、工具次数、token 与时间预算限制。 |

禁止事项：

- 不直接依赖 Web 框架。
- 不直接读写数据库。
- 不直接读用户文件。
- 不直接拼接 SOUL.md、AGENTS.md 等提示词文件。
- 不直接创建全局工具表。

### 4.2 `turn/session/`

`session/` 是会话归属边界模块。

职责：

- 定义 Session 数据模型。
- 管理 Session 生命周期。
- 校验当前用户是否拥有目标 Session。
- 支持 Session 分支、编辑、重试和恢复。

文件说明：

| 文件 | 职责 |
|---|---|
| `model.py` | Session、Message 等数据结构。 |
| `store.py` | Session 存取接口的默认封装。 |
| `guard.py` | Session 访问控制。 |
| `branch.py` | Session 内消息分支与重试逻辑。 |

核心原则：

```text
User owns Session.
Session owns Turn.
Turn owns Run, Event, Artifact, Approval and Trace.
```

除身份、默认配置和授权外，运行态资源不应直接挂在 `user_id` 下。

### 4.3 `turn/run/`

`run/` 是 Turn 执行调度模块。

职责：

- 启动一个 Turn。
- 给每个 Turn 创建隔离执行对象。
- 绑定取消信号、事件输出、prompt 快照、memory 快照、tool 快照。
- 支持恢复、取消、重试和状态查询。

文件说明：

| 文件 | 职责 |
|---|---|
| `turn.py` | Turn 执行对象。 |
| `task.py` | 后台任务抽象。 |
| `cancel.py` | 取消信号。 |
| `resume.py` | 断线恢复与事件续传。 |
| `state.py` | Turn 状态机。 |

每个 Turn 必须拥有独立对象：

```text
TurnExecution
CancellationToken
EventSink
PromptSnapshot
MemorySnapshot
ToolRegistrySnapshot
```

### 4.4 `turn/event/`

`event/` 是事件协议模块。

职责：

- 定义统一事件类型。
- 管理事件发送、缓存、订阅和持久化。
- 支持不同 transport 绑定读取同一事件流。

文件说明：

| 文件 | 职责 |
|---|---|
| `type.py` | 事件类型枚举。 |
| `sink.py` | 事件写入接口。 |
| `bus.py` | 本地事件总线。 |
| `store.py` | 事件持久化接口。 |

事件必须 session scoped：

```text
session_id + turn_id + seq
```

不使用全局递增序号。

### 4.5 `turn/wire/`

`wire/` 是传输绑定协议模块，不是真实服务实现。

职责：

- 定义客户端如何表达命令。
- 定义事件如何被映射到 WebSocket、SSE、REST、CLI 或 IM。
- 不绑定 FastAPI、Django、Flask 或任何具体框架。

文件说明：

| 文件 | 职责 |
|---|---|
| `command.py` | 统一命令协议。 |
| `stream.py` | 流式事件协议。 |
| `error.py` | 传输层错误协议。 |
| `route.py` | HTTP 风格路由绑定辅助。 |
| `socket.py` | WebSocket 风格绑定辅助。 |

核心命令：

```text
start
subscribe
resume
cancel
reply
approve
reject
upload
```

这些只是协议动作，不要求库本身启动 HTTP 服务。

### 4.6 `turn/prompt/`

`prompt/` 管理 PromptProfile 与 PromptSnapshot。

职责：

- 统一吸收类似 SOUL.md、AGENTS.md、pack prompt、session prompt、turn prompt 的提示词来源。
- 编译成每个 Turn 独立冻结的 PromptSnapshot。
- 保证同一用户多个 session 之间提示词隔离。
- 保证同一 session 多个 turn 之间提示词快照不串扰。

文件说明：

| 文件 | 职责 |
|---|---|
| `profile.py` | PromptProfile 数据结构。 |
| `layer.py` | 提示词层级。 |
| `compile.py` | 提示词编译器。 |
| `snapshot.py` | Turn 级冻结提示词快照。 |
| `guard.py` | 提示词安全校验与注入防护。 |

推荐提示词层级：

```text
system
pack
user
session
turn
memory
knowledge
```

其中 `user` 层只作为默认来源；最终注入必须发生在 `session` 和 `turn` 边界。

### 4.7 `turn/context/`

`context/` 管理上下文构造与压缩。

职责：

- 从 session 消息、memory 快照、knowledge 快照、工具结果和当前输入构造模型上下文。
- 执行上下文压缩、折叠、摘要和 token 预算控制。
- 维护可追溯的上下文快照。

文件说明：

| 文件 | 职责 |
|---|---|
| `build.py` | 构造上下文。 |
| `compact.py` | LLM 摘要压缩。 |
| `collapse.py` | 无模型调用的文本折叠。 |
| `token.py` | token 估算与预算。 |
| `snapshot.py` | 上下文快照。 |

### 4.8 `turn/memory/`

`memory/` 管理 session scoped memory。

职责：

- 不把运行态记忆直接挂到 user 下。
- 每个 session 拥有自己的 session memory。
- 用户级偏好只作为 session 创建时的默认来源。
- Turn 启动时读取并冻结 MemorySnapshot。

文件说明：

| 文件 | 职责 |
|---|---|
| `store.py` | 记忆存取接口。 |
| `trace.py` | 原始事件记忆。 |
| `session.py` | Session 级记忆。 |
| `snapshot.py` | Turn 级记忆快照。 |
| `merge.py` | 记忆合并策略。 |

### 4.9 `turn/tool/`

`tool/` 是工具协议模块。

职责：

- 定义 BaseTool。
- 定义 ToolResult。
- 定义工具 schema。
- 管理工具注册、筛选、执行、批处理和安全校验。

文件说明：

| 文件 | 职责 |
|---|---|
| `base.py` | BaseTool 协议。 |
| `schema.py` | 工具参数 schema。 |
| `result.py` | 工具执行结果。 |
| `registry.py` | 工具注册表。 |
| `execute.py` | 单个工具执行。 |
| `store.py` | ToolRegistrySnapshot 存储。 |

Phase 4 的批处理规则由 `execute.py` 内的 ToolRuntime 负责。独立的 `batch.py`、`guard.py` 等到 policy / approval 规则变复杂后再拆。

工具执行规则：

- readonly 工具可以并发。
- write 工具必须串行。
- unknown 工具必须 fail closed。
- 工具错误默认返回 ToolResult，不直接击穿整个 Turn。
- destructive 工具必须经过 policy 或 approval。

### 4.10 `turn/capability/`

`capability/` 是多阶段能力协议模块。

职责：

- 定义 BaseCapability。
- 支持一个 capability 接管整个 Turn。
- 支持阶段化执行、进度事件、工具使用和最终结果输出。

文件说明：

| 文件 | 职责 |
|---|---|
| `base.py` | BaseCapability 协议。 |
| `manifest.py` | Capability 元数据。 |
| `result.py` | Capability 执行结果。 |

后续 capability runtime 变复杂后再增加：

| 文件 | 职责 |
|---|---|
| `registry.py` | Capability 注册表。 |
| `flow.py` | 阶段流程编排。 |
| `stage.py` | 阶段状态。 |

Capability 与 Tool 的区别：

```text
Tool: 单次函数调用。
Capability: 多阶段 Turn 控制器。
```

### 4.11 `turn/pack/`

`pack/` 是能力包协议模块，不是内置业务能力集合。

职责：

- 定义第三方能力包如何声明、安装、验证和注册。
- 支持用户接入自己的 tool、capability、prompt、policy、memory hook、artifact view。
- 不限定能力包属于金融、教育、办公或数据分析。

文件说明：

| 文件 | 职责 |
|---|---|
| `base.py` | CapabilityPack 协议。 |
| `manifest.py` | pack manifest 结构。 |
| `registry.py` | 注册 pack。 |

Phase 5 不解析 YAML、不动态导入 entrypoint、不安装依赖。需要从文件加载 pack 时再增加：

| 文件 | 职责 |
|---|---|
| `load.py` | 加载 pack。 |
| `check.py` | 校验 pack。 |

外部能力包示意：

```text
mypack/
├── pack.yaml
├── tool/
├── capability/
├── prompt/
└── test/
```

外部能力包不要求放进 TurnCore 仓库。TurnCore 只负责定义接入协议。

### 4.12 `turn/policy/`

`policy/` 管理权限与安全策略。

职责：

- 校验工具能否执行。
- 校验 capability 能否启用。
- 校验 pack 能否加载。
- 决定是否需要 approval。

文件说明：

| 文件 | 职责 |
|---|---|
| `rule.py` | 策略规则。 |
| `check.py` | 策略检查器。 |
| `result.py` | 策略结果。 |

### 4.13 `turn/approval/`

`approval/` 管理人工审批。

职责：

- 创建审批请求。
- 暂停 Turn。
- 接收 approve 或 reject。
- 恢复 Turn。
- 写入 audit。

文件说明：

| 文件 | 职责 |
|---|---|
| `request.py` | 审批请求模型。 |
| `store.py` | 审批持久化。 |
| `service.py` | 审批流程服务。 |

### 4.14 `turn/artifact/`

`artifact/` 管理运行产物。

职责：

- 存储工具、capability 或模型生成的文件。
- 给 transport binding 提供可展示的 artifact 元信息。
- 保证 artifact 归属于 session 和 turn。

文件说明：

| 文件 | 职责 |
|---|---|
| `file.py` | Artifact 文件模型。 |
| `store.py` | Artifact 存取接口。 |
| `view.py` | Artifact 展示元数据。 |

### 4.15 `turn/model/`

`model/` 是模型调用抽象层。

职责：

- 定义模型端口。
- 屏蔽具体模型 SDK。

文件说明：

| 文件 | 职责 |
|---|---|
| `base.py` | 模型端口协议。 |

后续需要多 provider、流式输出或成本统计时再增加：

| 文件 | 职责 |
|---|---|
| `route.py` | 模型路由。 |
| `stream.py` | 流式输出抽象。 |
| `usage.py` | token 与费用统计。 |

### 4.16 `turn/port/`

`port/` 是核心依赖接口层。

职责：

- core 只能依赖 port。
- adapter 实现 port。
- 上层应用注入 port 实现。

文件说明：

| 文件 | 职责 |
|---|---|
| `session.py` | Session 存储端口。 |
| `event.py` | Event 存储端口。 |
| `artifact.py` | Artifact 存储端口。 |
| `memory.py` | Memory 端口。 |
| `model.py` | Model 端口。 |
| `lock.py` | Lock 端口。 |
| `secret.py` | Secret 端口。 |
| `file.py` | File 端口。 |

### 4.17 `turn/team/`

`team/` 是 TeamRuntime 的 DAG task runtime。

职责：

- 定义 team task DAG。
- 按依赖层顺序执行。
- 同层 ready task 并发执行。
- 不启动后台队列或工作进程。

文件说明：

| 文件 | 职责 |
|---|---|
| `task.py` | Team task 和执行结果模型。 |
| `graph.py` | DAG 校验与分层。 |
| `runtime.py` | TeamRuntime 执行器。 |

### 4.18 `turn/control/`

`control/` 是 transport-neutral control-plane data helper，不是 Web 服务。

职责：

- 管理 session-scoped pack selection。
- 读取 run dashboard data。
- 不定义 REST 路由、WebSocket 或 UI。

文件说明：

| 文件 | 职责 |
|---|---|
| `pack.py` | PackManager。 |
| `dashboard.py` | Run dashboard data reader。 |

### 4.19 `turn/eval/`

`eval/` 管理最小 evaluation suite 协议。

职责：

- 定义 deterministic eval case / suite / result。
- 提供最小 eval runner。
- 不接入模型服务或外部评测平台。

文件说明：

| 文件 | 职责 |
|---|---|
| `suite.py` | Eval suite 模型和 runner。 |

### 4.20 `turn/audit/`

`audit/` 管理 session-scoped audit viewer data。

职责：

- 记录 session-scoped audit records。
- 提供 audit viewer payload。
- 不记录 secrets、raw prompt、provider payload 或 artifact content。

文件说明：

| 文件 | 职责 |
|---|---|
| `record.py` | Audit record 模型。 |
| `store.py` | Audit log store port 和内存实现。 |
| `view.py` | Audit viewer payload。 |

### 4.21 `turn/adapter/`

`adapter/` 是可选适配器实现层。它仍然位于 `turn/` 内，所以所有库代码都在一个目录下。

职责：

- 给 port 提供默认或可选实现。
- 不让 core 依赖具体基础设施。
- 允许用户替换为自己的实现。

子目录说明：

| 目录 | 职责 |
|---|---|
| `memory/` | 进程内适配器，适合测试。 |
| `file/` | 文件系统适配器。 |
| `sqlite/` | SQLite 适配器。 |
| `web/` | Web 绑定辅助，不绑定具体框架。 |

`turn/adapter/web/` 不应导入 FastAPI。若需要 FastAPI，可由用户在自己的应用中实现绑定，或通过额外包提供。

### 4.22 `turn/user/`

`user/` 只处理身份、默认配置、授权和凭据引用。

职责：

- 验证用户身份。
- 判断用户是否拥有目标 session。
- 提供用户默认 profile。
- 提供用户默认 grant。
- 提供 secret 引用，不直接把 secret 注入 AgentLoop。

文件说明：

| 文件 | 职责 |
|---|---|
| `auth.py` | 身份认证。 |
| `grant.py` | 用户授权。 |
| `profile.py` | 用户默认 profile。 |
| `secret.py` | 用户 secret 引用。 |

### 4.23 `turn/error/`

`error/` 定义统一异常与错误协议。

职责：

- 定义 UAFError 基类。
- 定义错误码。
- 构造跨 wire / tool / event 边界使用的 ErrorEnvelope。
- 保留异常 cause，由调用方或 adapter 决定日志和 transport 映射。
- 避免泄露内部路径、密钥、堆栈和用户私有内容。
- 不直接生成 HTTP response、WebSocket close、SSE event 或宿主应用日志。

文件说明：

| 文件 | 职责 |
|---|---|
| `base.py` | 异常基类。 |
| `code.py` | 错误码。 |
| `envelope.py` | 安全 ErrorEnvelope 构造。 |

### 4.24 `turn/trace/`

`trace/` 管理观测和审计。

职责：

- 记录模型调用、工具调用、capability 阶段和 approval。
- 支持调试与回放。
- 区分 trace、log 和 audit。

文件说明：

| 文件 | 职责 |
|---|---|
| `span.py` | Trace span。 |
| `log.py` | 运行日志。 |
| `audit.py` | 审计日志。 |

### 4.25 `turn/shell/`

`shell/` 是命令行入口。

职责：

- 提供本地调试入口。
- 不作为后端服务。
- 不启动 Web 服务。

文件说明：

| 文件 | 职责 |
|---|---|
| `main.py` | 命令行入口。 |
| `run.py` | 本地执行命令。 |

## 5. `test/` 完整镜像结构

`test/` 必须完整镜像 `turn/`。

```text
test/
└── turn/
    ├── agent/
    │   ├── loop.py
    │   ├── step.py
    │   ├── state.py
    │   ├── plan.py
    │   └── limit.py
    ├── session/
    │   ├── model.py
    │   ├── store.py
    │   ├── guard.py
    │   └── branch.py
    ├── run/
    │   ├── turn.py
    │   ├── task.py
    │   ├── cancel.py
    │   ├── resume.py
    │   └── state.py
    ├── event/
    │   ├── type.py
    │   ├── sink.py
    │   ├── bus.py
    │   └── store.py
    ├── wire/
    │   ├── command.py
    │   ├── stream.py
    │   ├── error.py
    │   ├── route.py
    │   └── socket.py
    ├── prompt/
    │   ├── profile.py
    │   ├── layer.py
    │   ├── compile.py
    │   ├── snapshot.py
    │   └── guard.py
    ├── context/
    │   ├── build.py
    │   ├── compact.py
    │   ├── collapse.py
    │   ├── token.py
    │   └── snapshot.py
    ├── memory/
    │   ├── store.py
    │   ├── trace.py
    │   ├── session.py
    │   ├── snapshot.py
    │   └── merge.py
    ├── tool/
    │   ├── base.py
    │   ├── schema.py
    │   ├── result.py
    │   ├── registry.py
    │   ├── execute.py
    │   ├── batch.py
    │   └── guard.py
    ├── capability/
    │   ├── base.py
    │   ├── manifest.py
    │   ├── registry.py
    │   ├── flow.py
    │   ├── stage.py
    │   └── result.py
    ├── pack/
    │   ├── base.py
    │   ├── manifest.py
    │   ├── load.py
    │   ├── check.py
    │   └── registry.py
    ├── policy/
    │   ├── rule.py
    │   ├── check.py
    │   └── result.py
    ├── approval/
    │   ├── request.py
    │   ├── store.py
    │   └── service.py
    ├── artifact/
    │   ├── file.py
    │   ├── store.py
    │   └── view.py
    ├── model/
    │   ├── base.py
    │   ├── route.py
    │   ├── stream.py
    │   └── usage.py
    ├── port/
    │   ├── session.py
    │   ├── event.py
    │   ├── artifact.py
    │   ├── memory.py
    │   ├── model.py
    │   ├── lock.py
    │   ├── secret.py
    │   └── file.py
    ├── adapter/
    │   ├── memory/
    │   │   ├── session.py
    │   │   ├── event.py
    │   │   ├── artifact.py
    │   │   └── lock.py
    │   ├── file/
    │   │   ├── session.py
    │   │   ├── event.py
    │   │   ├── artifact.py
    │   │   └── memory.py
    │   ├── sqlite/
    │   │   ├── session.py
    │   │   ├── event.py
    │   │   └── artifact.py
    │   └── web/
    │       ├── route.py
    │       ├── stream.py
    │       └── socket.py
    ├── user/
    │   ├── auth.py
    │   ├── grant.py
    │   ├── profile.py
    │   └── secret.py
    ├── error/
    │   ├── base.py
    │   ├── code.py
    │   └── envelope.py
    ├── trace/
    │   ├── span.py
    │   ├── log.py
    │   └── audit.py
    └── shell/
        ├── main.py
        └── run.py
```

## 6. 依赖方向

依赖方向必须保持单向。

```text
agent
  -> context
  -> prompt
  -> memory
  -> tool
  -> capability
  -> policy
  -> approval
  -> event
  -> model
  -> port

adapter
  -> port

wire
  -> event
  -> error

session
  -> port
  -> user

pack
  -> tool
  -> capability
  -> prompt
  -> policy
```

禁止方向：

```text
core -> adapter concrete dependency
agent -> web framework
tool -> socket
tool -> route
prompt -> adapter
memory -> adapter
port -> adapter
```

## 7. Session scoped 资源模型

TurnCore 的资源归属模型如下：

```text
User
└── Session
    ├── Message
    ├── Turn
    │   ├── Run
    │   ├── Event
    │   ├── Tool
    │   ├── Artifact
    │   ├── Approval
    │   └── Trace
    ├── Memory
    ├── Prompt
    ├── Pack
    └── Secret
```

说明：

- `User` 是身份主体。
- `Session` 是隔离边界。
- `Turn` 是执行边界。
- `Run` 是一次执行实例。
- `Event`、`Artifact`、`Approval`、`Trace` 都通过 `session_id` 和 `turn_id` 关联。
- 用户默认提示词、偏好、权限和凭据引用可以来自 user，但注入时必须冻结到 session 或 turn。

## 8. Prompt 文件与快照规则

外部系统可能提供类似下面的提示词文件：

```text
SOUL.md
AGENTS.md
```

TurnCore 不直接让 AgentLoop 读取这些文件，而是通过 `turn/prompt/` 统一转换为 PromptProfile。

流程如下：

```text
external file
  -> PromptProfile
  -> PromptLayer
  -> PromptSnapshot
  -> AgentLoop
```

规则：

1. PromptSnapshot 在 Turn 启动前生成。
2. PromptSnapshot 生成后不可变。
3. 同一 session 的不同 turn 使用不同快照。
4. 同一用户的不同 session 不共享运行态快照。
5. pack prompt 只能通过 pack manifest 声明进入快照。
6. user prompt 默认值不能越过 session 权限边界。

## 9. Capability Pack 接入方式

TurnCore 是库，用户的能力包不需要放在 TurnCore 仓库内。

能力包通过协议接入：

```python
from turn.pack.base import CapabilityPack

class MyPack(CapabilityPack):
    def tools(self):
        return []

    def capabilities(self):
        return []

    def prompts(self):
        return []

    def policies(self):
        return []
```

能力包 manifest 使用 `pack.yaml`：

```yaml
name: math
version: 1.0.0
entry: mypack:MyPack
```

库内 `turn/pack/` 只负责加载、验证和注册，不内置具体领域假设。

## 10. Transport binding 规则

TurnCore 不固定提供真实 API。

它只定义协议：

```text
CommandEnvelope
StreamEvent
ErrorEnvelope
ArtifactEnvelope
ApprovalEnvelope
```

任何服务框架都可以做绑定：

```text
WebSocket -> command -> core -> event -> WebSocket
SSE       -> event subscription
REST      -> command submission
CLI       -> command submission and event print
IM        -> command submission and event reply
```

库内 `turn/wire/` 只提供协议对象和绑定辅助，不启动服务。

Phase 6 当前实现的绑定辅助集中在 `turn/wire/binding.py`：

```text
WebSocket-like: WireMessage, command_to_wire, wire_to_command, event_to_wire, error_to_wire
SSE: SseEvent, event_to_sse, error_to_sse
REST: RestRequest, RestResponse, command_from_rest, event_to_rest, error_to_rest
CLI / IM: TextCommandInput, command_from_text, event_to_text, error_to_text
```

这些 helper 不负责认证、路由、HTTP status 策略、WebSocket/SSE 服务端或 IM webhook。

## 11. 打包配置建议

`pyproject.toml` 建议：

```toml
[project]
name = "turncore"
version = "0.1.0"
readme = "readme.md"
requires-python = ">=3.11"

[tool.setuptools]
packages = ["turn"]

[tool.pytest.ini_options]
testpaths = ["test"]
python_files = ["*.py"]
```

说明：

- 分发名可以是 `turncore`。
- 导入包名必须是 `turn`。
- 库代码只来自 `turn/`。
- 测试文件不使用 `test_` 前缀，由 pytest 配置控制。

## 12. 目标最小可启动目录

完整 MVP 可以先实现以下最小目录。它是阶段目标清单，不表示这些目录需要在同一阶段一次性全部完成：

```text
turn/
├── __init__.py
├── agent/
│   ├── __init__.py
│   └── loop.py
├── session/
│   ├── __init__.py
│   └── model.py
├── run/
│   ├── __init__.py
│   └── turn.py
├── event/
│   ├── __init__.py
│   ├── type.py
│   └── sink.py
├── prompt/
│   ├── __init__.py
│   └── snapshot.py
├── tool/
│   ├── __init__.py
│   ├── base.py
│   ├── result.py
│   └── registry.py
├── capability/
│   ├── __init__.py
│   └── base.py
├── pack/
│   ├── __init__.py
│   └── base.py
├── port/
│   ├── __init__.py
│   └── model.py
└── error/
    ├── __init__.py
    └── base.py
```

对应测试：

```text
test/
└── turn/
    ├── agent/
    │   └── loop.py
    ├── session/
    │   └── model.py
    ├── run/
    │   └── turn.py
    ├── event/
    │   ├── type.py
    │   └── sink.py
    ├── prompt/
    │   └── snapshot.py
    ├── tool/
    │   ├── base.py
    │   ├── result.py
    │   └── registry.py
    ├── capability/
    │   └── base.py
    ├── pack/
    │   └── base.py
    ├── port/
    │   └── model.py
    └── error/
        └── base.py
```

## 13. 命名检查清单

提交前检查：

- 顶层是否只有 `turn/` 一个源码包目录。
- 是否出现了 `source/`、`src/`、`deploy/`、`app/`、`server/`。
- 是否出现了 `plug`、`impl`、`cfg`、`svc`、`repo` 等缩写。
- 是否出现了连字符文件名。
- 是否出现了下划线文件名。
- 是否出现了驼峰文件名。
- 测试目录是否完整镜像代码目录。
- 代码是否从 `turn/adapter/` 反向污染 core。
- core 是否导入具体 Web 框架。
- core 是否导入具体数据库客户端。
