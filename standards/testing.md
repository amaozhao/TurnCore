# Testing Standard

## Scope

Use this standard when adding or changing tests, fixtures, mocks, test data, test layout, or verification commands.

## Core Rules

- Tests must be deterministic, isolated, and meaningful.
- Add the narrowest regression test that would have failed before a bug fix.
- Test the boundary that owns the invariant.
- Do not introduce a new test framework without an explicit reason.
- Do not hide failures with broad `try` blocks, arbitrary sleeps, broad mocks, or snapshots that do not assert behavior.

## Layout

TurnCore tests live under `test/` and mirror `turn/`.

```text
turn/agent/loop.py
test/turn/agent/loop.py
```

The project may configure pytest to collect `*.py` under `test/`, so do not assume `test_*.py` filenames are required.

Do not add application-style test trees or tier directories unless the spec changes.

## What To Test

- Session ownership and authorization paths.
- Turn locking, cancellation, resume, and event ordering.
- Prompt compilation and immutable snapshots.
- Tool registry snapshots, tool effect policy, timeout, and error handling.
- Pack manifest validation and registration.
- Artifact/workspace path isolation.
- Error code and `ErrorEnvelope` mapping.
- Adapter mapping when optional adapters exist.

## Unit Tests

Use unit tests for pure domain logic, dataclass/model behavior, mappers, compilers, policy decisions, and small runtime components.

Avoid real network calls, model providers, databases, clocks, or filesystem state outside temporary paths.

## Integration Tests

Use integration tests when behavior depends on collaboration across real internal boundaries, such as:

- session runtime plus turn repository port fake;
- agent loop plus tool runtime fake;
- prompt compiler plus pack prompt sources;
- transport binding helper plus command/event envelopes.

Mock only unstable external boundaries. Do not mock internal calls just to prove a call chain happened.

## Async Tests

- Use the project's configured async pytest support.
- Avoid arbitrary sleeps.
- Prefer explicit awaits, deterministic synchronization, cancellation tokens, fake clocks, or bounded polling helpers.
- Clean up tasks, streams, temporary workspaces, and in-memory stores.

## Fixtures

- Keep fixtures close to the tests that use them.
- Use wider `conftest.py` fixtures only when many modules share them.
- Prefer explicit small builders over large implicit fixture graphs.
- Test data must preserve session/turn/user ownership relationships.
- Do not use real credentials, tokens, personal data, or provider keys.

## Verification

Run the narrowest useful command first, then broaden when shared contracts or runtime behavior changed.

Common commands:

```bash
ruff format .
ruff check .
pyright
pytest
```

Targeted examples:

```bash
pytest test/turn/session/guard.py
pytest test/turn/wire/error.py
```

## Review Checklist

- Does the test mirror the owning `turn/` path?
- Would a regression test fail before the fix?
- Are mocks at unstable boundaries rather than internal implementation steps?
- Are async operations awaited deterministically?
- Are session, turn, run, and principal relationships realistic?
- Was verification run and read before completion was claimed?
