# Module Standard

## Scope

Use this standard when changing `turn/` package boundaries, runtimes, ports, adapters, capability packs, registries, stores, compilers, policies, or shared domain models.

## Core Rule

Prefer deep modules that own a real invariant and expose a small typed interface. Delete shallow wrappers that only rename, forward, re-export, or add future-proofing.

TurnCore core must stay protocol-first and infrastructure-neutral. Web frameworks, databases, model SDKs, queues, vector stores, and object stores belong behind ports or optional adapters, not in core runtime modules.

## Boundary Rules

- `turn/` is the only source package.
- Core modules may depend on domain models, ports, and protocols.
- Core modules must not depend on concrete adapters.
- `turn/adapter/` may depend on ports and external libraries.
- `turn/wire/` defines command/event/error envelopes and binding helpers, not a running API server.
- `turn/pack/` loads and validates pack definitions; it must not bake in one business domain.
- Runtime resources belong to `Session`/`Turn`/`Run`, not directly to `User`.

Forbidden directions:

```text
core -> adapter concrete dependency
agent -> web framework
tool -> socket or route
prompt -> adapter
memory -> adapter
port -> adapter
```

## Invariant Owners

Put a rule where every caller naturally passes through it:

- Session ownership and access checks: session or policy boundary.
- Turn locking and cancellation: session/turn runtime boundary.
- Event sequence and cursor behavior: event store/sink boundary.
- Prompt layering and freezing: prompt compiler/snapshot boundary.
- Tool permissions, effect type, timeout, and audit: tool runtime/policy boundary.
- Pack manifest validation: pack loader/registrar boundary.
- Artifact path and workspace isolation: artifact/workspace boundary.

Bug fixes should strengthen the owning boundary instead of adding checks to each caller.

## Public Interfaces

Public interfaces should name domain operations, not implementation steps.

Prefer:

```python
class SessionRepository(Protocol):
    async def get(self, session_id: str) -> Session | None:
        ...

class PromptCompiler(Protocol):
    async def compile_for_turn(self, command: PromptCompileCommand) -> PromptSnapshot:
        ...
```

Avoid option bags that leak internal switches:

```python
async def run(user_id: str, prompt_file: str, db: object, websocket: object) -> None:
    ...
```

## Adapter Rules

Adapters translate concrete infrastructure into TurnCore protocols.

- A WebSocket/SSE/REST binding maps transport input to `CommandEnvelope` and output to `StreamEvent` or `ErrorEnvelope`.
- A storage adapter implements repository/store ports; core code does not import its database client.
- A model adapter implements the model port; core code does not import a provider SDK.
- Adapter-specific setup stays optional and isolated.

## Review Checklist

- Does the module own a clear invariant?
- Is the interface smaller and more stable than the implementation?
- Is `Session` the runtime namespace?
- Are concrete web, database, model, queue, file, or network dependencies kept behind ports/adapters?
- Did the change avoid adding a shallow wrapper, factory, registry, or plugin layer without a real need?
- Are tests placed at the boundary that owns the behavior?
