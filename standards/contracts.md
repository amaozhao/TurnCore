# Contract Standard

## Scope

Use this standard when changing public protocol objects, command/event envelopes, error envelopes, pack manifests, tool/capability interfaces, repository ports, policy decisions, artifact envelopes, or transport binding behavior.

## Core Rules

- Core defines protocols, not fixed REST/SSE/WebSocket routes.
- Adapters translate external transport or infrastructure into TurnCore contracts.
- Contract changes must update models, docs, tests, and affected adapters together.
- Clients and packs must not pass `user_id` as the runtime ownership key; adapters resolve `Principal`, then core authorizes through `Session`.
- Do not leak concrete database, SDK, stack trace, path, token, or adapter internals through public contracts.

## Required Public Contracts

Keep these stable and explicit:

- `CommandEnvelope`
- `StreamEvent`
- `ErrorEnvelope`
- `Principal`
- `Session`, `Turn`, `Run`
- prompt, tool, memory, policy, artifact, and approval snapshots/envelopes
- `CapabilityPack` and `PackRegistrar`
- `BaseTool` and tool definitions/results
- `BaseCapability` and capability manifests/results
- port protocols under `turn/port/`

## Envelope Rules

- `CommandEnvelope` carries command identity, command type, optional session/turn IDs, payload, and idempotency key.
- Transport adapters resolve authentication into `Principal`; command payloads do not carry trusted identity.
- `StreamEvent` is ordered by a stable sequence within a turn.
- Event replay/subscription uses cursor semantics such as `after_seq`.
- `ErrorEnvelope` carries stable code, message, retryability, optional scope IDs, and safe details.
- Envelope fields must remain transport-independent.

## Session Scope

Every runtime resource access must authorize through:

```text
principal -> session_id -> session.owner_user_id -> resource.session_id
```

If a request starts from `turn_id`, `run_id`, `artifact_id`, or `approval_id`, resolve its `session_id` before authorizing.

## Pack Contracts

- Pack definitions are global and read-only.
- Pack enablement is session-scoped.
- A running turn uses a frozen tool/prompt/memory snapshot.
- Pack upgrades must not change an already running turn.
- Manifests must declare permissions, prompts, tools, capabilities, and entrypoints explicitly.

## Transport Binding Rules

- WebSocket, SSE, REST, CLI, and IM are bindings over the same command/event model.
- Binding-specific status codes, close codes, or stream formats belong in adapters.
- Adapters must not bypass core runtime to mutate sessions, turns, events, approvals, or artifacts.

## Tests

Contract tests should cover:

- command parsing and validation;
- session authorization path;
- event sequence and replay behavior;
- error envelope shape and stable codes;
- pack manifest validation;
- adapter mapping for any binding that exists.

## Review Checklist

- Did every affected protocol object and adapter change together?
- Are identity and ownership resolved through `Principal` and `Session`?
- Are envelope fields stable, typed, and transport-independent?
- Are error codes stable and safe to expose?
- Are pack/tool/capability permissions explicit?
- Are contract tests updated at the boundary?
