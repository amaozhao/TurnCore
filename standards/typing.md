# Typing Standard

## Scope

Use this standard when changing Python type hints, dataclasses, protocols, schemas, DTOs, envelopes, pack manifests, port interfaces, untrusted payload parsing, or public models.

## Core Rules

- Types must describe real runtime values.
- Public contracts must be typed explicitly.
- Use `Protocol` for ports and extension contracts.
- Use frozen dataclasses or equivalent immutable models for snapshots and envelopes.
- Treat external input as untrusted until validated or narrowed.
- Do not lie to the type checker with broad casts or ignores.

## Boundary Models

Use explicit models for:

- command, event, error, artifact, approval, prompt, memory, and tool envelopes;
- session, turn, run, user, and principal models;
- pack manifests and capability/tool definitions;
- repository/store/model/policy ports;
- adapter input and output boundaries.

Prefer `Literal` or enums for finite protocol values such as command type, event type, tool effect, policy decision, and run status.

## `Any` And Untyped Payloads

`dict[str, Any]` is allowed only where the spec intentionally defines schema-less extension points, such as command payloads, metadata, capability config schemas, or provider-specific adapter data.

Rules:

- Keep `Any` at the boundary.
- Narrow or validate before using values for decisions, storage keys, paths, permissions, or side effects.
- Prefer typed dataclasses, `TypedDict`, or narrow dictionaries once the shape is known.
- Do not spread `Any` into core runtime state.

## Dataclasses And Protocols

- Use `@dataclass(frozen=True)` for immutable snapshots and envelopes.
- Use `Protocol` for ports, model adapters, stores, pack registrar surfaces, and extension points.
- Do not create a `Protocol` for every class mechanically.
- Keep protocol methods small and domain-oriented.

## Optionality

Use `T | None` only when absence is a real state the caller must handle.

Distinguish:

- missing field;
- explicit `None`;
- empty string;
- empty collection;
- default value.

This matters for command payloads, prompt layers, event content, artifact references, and approval state.

## Casts And Ignores

Avoid `cast()` and `# type: ignore`. If unavoidable, keep the scope tiny and explain the external limitation.

Do not use ignores to hide mismatches in public contracts, port signatures, snapshot shapes, or adapter mappings.

## Review Checklist

- Are public protocol objects explicitly typed?
- Are untrusted payloads validated before use?
- Is `Any` contained to intentional extension points?
- Are snapshots and envelopes immutable where the spec requires freezing?
- Do optional fields represent real runtime states?
- Did the change avoid unsafe casts and ignores?
