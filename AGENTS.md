# Project Agent Instructions

These instructions apply to the whole repository unless a deeper `AGENTS.md` overrides them for files under its directory.

## General

- Do not commit or push changes unless the user explicitly asks for it in the current task.
- Keep changes small, reviewable, and scoped to the user's request.
- Prefer existing project patterns over new abstractions.
- Inspect existing implementation, configuration, tests, and public contracts before changing architecture, dependencies, test layout, build tooling, or API behavior.
- Do not edit generated, vendored, cache, runtime, log, build, coverage, or dependency output unless the task explicitly targets it.
- Avoid unrelated formatting churn. Format only files affected by the task unless the user asks for broader cleanup.
- Keep specifications, tests, implementation, and documentation consistent.
- When fixing a bug, identify the owning invariant and root cause first. Do not hide the failure behind broad fallback logic.

## Standards

Read the relevant standard before changing affected code:

- `standards/modules.md`: `turn/` module boundaries, runtimes, ports, adapters, capability packs, registries, stores, compilers, policies, or shared models.
- `standards/testing.md`: tests, fixtures, mocks, test layout, test data, or verification strategy.
- `standards/typing.md`: Python typing, dataclasses, protocols, schemas, DTOs, envelopes, pack manifests, ports, or untrusted data.
- `standards/errors.md`: domain errors, `UAFError`-style exceptions, `ErrorEnvelope`, cancellation, logging, fallbacks, retries, or exception mapping.
- `standards/contracts.md`: command/event/error envelopes, pack manifests, tool/capability interfaces, repository ports, policy decisions, or transport bindings.
- `standards/security.md`: principals, session authorization, prompt snapshots, tool policy, pack permissions, secrets, uploads, artifacts, paths, SSRF, or sensitive logging.
- `standards/operations.md`: dependencies, package changes, `pyproject.toml`, optional adapter extras, environment variables, runtime configuration, logs, tracing, background work, or diagnostics.
- `standards/performance.md`: async execution, session locks, turn concurrency, event streams, snapshots, pack loading, payload size, or storage-port costs.
- `standards/review.md`: code review, final self-review, diff review, or change risk assessment.

If standards conflict, follow the more specific standard for the touched code. If a deeper `AGENTS.md` conflicts with these root rules, follow the deeper file for its subtree.

## Naming

- Project-owned file and directory names must be a single real word.
- Use lowercase ASCII words by default.
- Do not create fake compound words such as `loaddata`, `runagent`, `fetchreport`, or verb-plus-noun concatenations.
- Avoid new multiword names joined by hyphen, underscore, camelCase, or PascalCase.
- Python ecosystem filenames are allowed, for example `__init__.py`, `pyproject.toml`, and generated metadata files.
- Test files under `test/` should mirror `turn/` source paths. The project may configure pytest to collect `*.py`, so `test_*.py` names are not required.
- Existing generated files, dependency folders, and third-party conventions are exempt unless the task explicitly renames them.
- If a concept needs several words, place code in an existing appropriate single-word directory and use clear symbol names inside the file.

## Architecture

- Prefer deep modules at stable boundaries: small typed domain interfaces that hide non-trivial implementation.
- Avoid shallow wrappers that only rename, forward, re-export, or add indirection without owning an invariant, policy, type boundary, or useful abstraction.
- Public APIs should express domain operations and invariants, not implementation steps.
- Keep entry points thin. Put runtime rules, storage details, external SDK details, transport bindings, and cache keys behind project-owned boundaries.
- SOLID is a maintenance constraint, not a reason for speculative abstraction. Do not add layers, factories, registries, event buses, or plugin systems unless the task or existing project pattern justifies them.
- Deep modules are not god modules. Split code when responsibilities, dependencies, reasons to change, or test setup become unrelated.

## Error Handling

- Do not add `try` blocks merely to make a bug disappear.
- Keep each `try` block as narrow as possible and catch the most specific error type available.
- Do not use bare `except`, catch `BaseException`, use empty `catch` blocks, or silently ignore errors.
- Avoid broad `except Exception` unless it is at an adapter or host-application boundary and returns or raises a structured error.
- Do not return `None`, an empty collection, a default object, or a success response after an unexpected error unless that fallback is an explicit documented contract.
- Preserve causes when translating errors, for example `raise NewError(...) from exc` in Python.
- Tests must not hide assertion failures inside `try` blocks. Use `pytest.raises`.

## Python Library

- Library code lives under `turn/`.
- Do not add top-level `src/`, `app/`, `server/`, `api/`, `deploy/`, `infra/`, `adapter/`, or `pack/` directories unless the spec changes.
- Python imports must be at module top, after the module docstring and `from __future__` imports.
- Do not add imports inside functions, methods, or branches except for a documented cycle, optional dependency, or cold-path performance reason.
- Keep each source file focused and below 800 lines.
- Use pytest for tests, Ruff for formatting and lint-compatible style, and Pyright for type checking when configured.
- Type hints must describe real values. Do not silence type issues with incorrect annotations, unnecessary casts, or broad `Any`.
- Prefer dataclasses, typed dicts, protocols, literal types, or narrow dictionaries over unstructured payloads after boundary validation.
- Use async all the way through runtime, port, adapter, and storage paths that are asynchronous.
- Do not call blocking I/O, `time.sleep()`, or `asyncio.run()` from async library code.
- Do not leave fire-and-forget tasks unmanaged. Agent loops, streams, tool calls, and adapter tasks need ownership, error logging, cancellation behavior, and cleanup.
- Core must not depend on FastAPI, SQLAlchemy, Postgres, Redis, Qdrant, OpenAI SDK, or other concrete infrastructure. Put concrete integrations behind ports or optional adapters.
- Validate external input at adapter or protocol boundaries before it reaches core runtime logic.
- Do not leak adapter internals, stack traces, secrets, raw provider payloads, full paths, or implementation details in public envelopes.

### Tests

Tests live under `test/` and mirror `turn/`:

```text
turn/agent/loop.py
test/turn/agent/loop.py
```

The project may configure pytest to collect `*.py` under `test/`; do not assume `test_*.py` filenames are required. Bug fixes should include the narrowest test that would have failed before the fix.

### Verification

Run the narrowest useful verification, then broaden when shared behavior changes:

```bash
ruff format .
ruff check .
pyright
pytest
```

For targeted tests, prefer:

```bash
pytest test/turn/session/guard.py
```

## Configuration, Dependencies, Security

- Do not hardcode secrets, tokens, passwords, private keys, account IDs, or environment-specific credentials.
- Use existing configuration loading and validation patterns.
- Keep `.env.example` and sample environment files free of real secrets.
- Do not add a runtime dependency when the standard library, existing dependency, or small local helper is sufficient.
- When a dependency change is necessary, update the appropriate lockfile and report why the dependency was needed.
- Keep command/event/error envelopes, port protocols, docs, tests, and adapters synchronized when public contracts change.
- Enforce authentication and authorization before protected runtime resources are accessed.
- Do not trust client-provided identity, role, ownership, session scope, price, status, or permission fields.
- Validate and normalize external input before persistence or sensitive operations.
- Do not log secrets, credentials, session tokens, authorization headers, personal data, or large request bodies.
- Avoid SQL injection, command injection, path traversal, SSRF, XSS, open redirects, and unsafe deserialization.

## Documentation And Specs

- Keep specifications consistent with the current implementation baseline.
- Mark future phases clearly as future work.
- Do not mix first-phase requirements with later-phase ambitions in the same acceptance criteria.
- When replacing specs, delete superseded files only when the replacement preserves the original intent and clearly states what it replaces.
- Update relevant README, API notes, environment examples, or developer docs when behavior, setup, commands, or contracts change.

## Completion Expectations

- Before reporting completion, check the relevant git diff and verify no unrelated files were changed.
- Report what changed, what was verified, and any verification intentionally skipped.
- Do not claim a tool, test, type check, or build passed unless it was actually run and the output was checked.
- Mention known risks, follow-up work, or repository assumptions when they affect the result.
