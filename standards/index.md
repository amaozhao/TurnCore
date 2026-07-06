# Engineering Standards Index

These standards are for TurnCore: a Python library for an agent kernel, session-scoped runtime resources, capability packs, and transport-independent command/event protocols. They are not a full-stack application template.

## Use Model

1. Read `AGENTS.md` first.
2. Identify the area touched by the task.
3. Read only the matching standard files.
4. Prefer `docs/spec.md` and `docs/structure.md` when a standard and the product spec disagree.
5. Report only changes and checks that actually happened.

## Selection Guide

| Task touches | Read |
| --- | --- |
| `turn/` module boundaries, runtimes, ports, adapters, packs, deep module shape | `modules.md` |
| command/event envelopes, pack manifests, tool/capability interfaces, public protocols | `contracts.md` |
| Python types, dataclasses, protocols, schemas, DTOs, untrusted payloads | `typing.md` |
| `UAFError`, `ErrorEnvelope`, cancellation, retries, fallbacks, logging errors | `errors.md` |
| tests, fixtures, mocks, mirrored `test/turn/` layout, verification commands | `testing.md` |
| principal/session isolation, prompt snapshots, tool policy, secrets, uploads, SSRF, paths | `security.md` |
| dependencies, `pyproject.toml`, optional adapter extras, env vars, logs, tracing, background work | `operations.md` |
| async throughput, event streams, snapshots, pack loading, payload size, storage-port costs | `performance.md` |
| code review, final self-review, diff scope, verification reporting | `review.md` |

There is no separate frontend standard. TurnCore does not contain a frontend.

There is no separate database standard. Core storage is defined as ports; concrete database rules belong to adapter code only when such an adapter exists.

## File Map

- `modules.md`: ownership of invariants, dependency direction, port/adapter boundaries, runtime boundaries.
- `contracts.md`: stable public protocol objects and extension contracts.
- `typing.md`: strict Python typing for domain models, ports, envelopes, and untrusted data.
- `errors.md`: domain exceptions, error envelopes, expected vs unexpected failures.
- `testing.md`: pytest layout and focused regression coverage.
- `security.md`: session-scoped authorization and runtime isolation.
- `operations.md`: package/dependency/config/observability rules.
- `performance.md`: non-blocking execution, bounded concurrency, payload and snapshot costs.
- `review.md`: final review and verification checklist.

## What Belongs Here

Put a rule in `standards/` only when it is durable, applies across multiple tasks, and is too detailed for `AGENTS.md`.

Do not put one-off product requirements, phase plans, runbooks, historical decisions, or tutorials here. Product requirements belong in `docs/spec.md`; layout requirements belong in `docs/structure.md`.

## Maintenance Rules

- Keep standards short and actionable.
- Delete implementation-specific standards that are not part of TurnCore's library scope.
- Do not add a new standard until an existing file is clearly too broad.
- Keep examples shaped like the spec: Python package code under `turn/`, tests under `test/turn/`, transport-independent protocols, and optional adapters.
