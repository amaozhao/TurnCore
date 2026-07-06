# Operations Standard

## Scope

Use this standard when changing dependencies, `pyproject.toml`, optional adapter extras, environment variables, runtime configuration, feature flags, logging, metrics, tracing, background work, packaging, or operational diagnostics.

## Core Rule

TurnCore is a library, not a deployed backend application. Keep core dependencies minimal, optional infrastructure isolated, and runtime behavior explicit.

## Dependencies

Core must not require concrete infrastructure dependencies such as web frameworks, database clients, queues, vector stores, object stores, or model provider SDKs.

Use this order:

1. Python standard library.
2. Existing dependency.
3. Optional adapter extra.
4. New dependency, only when it prevents more risk than it adds.

Rules:

- put optional infrastructure dependencies behind extras or adapter-specific installation paths;
- do not import optional dependencies from core modules;
- update package metadata when dependencies change;
- do not add lockfiles unless the project already uses them;
- do not vendor generated dependency output.

## Configuration

Configuration is untrusted input.

- Parse and validate config at adapter or startup boundaries.
- Expose typed config to core runtime code.
- Fail fast for missing required config.
- Use safe defaults only when absence is genuinely acceptable.
- Avoid ad hoc `os.environ` reads across core modules.
- Keep sample env values fake.

## Packaging

- Keep installable code under `turn/`.
- Keep tests under `test/`.
- Keep docs as Markdown.
- Keep adapter code inside `turn/adapter/` unless the spec changes.
- Do not add top-level deployment, app, server, API, infra, plugin, or pack directories.

## Logging, Metrics, And Tracing

Observability should help debug sessions, turns, runs, tools, packs, and adapters without leaking sensitive data.

- Use stable low-cardinality IDs where safe.
- Redact secrets, prompt bodies, uploaded contents, and raw provider payloads.
- Avoid duplicate exception logging at many layers.
- Keep event names, metric labels, and span names stable.
- Do not add high-cardinality labels such as raw user input, filenames, URLs, or emails.

## Background Work

Agent loops, stream publishers, tool calls, and adapter tasks need owned lifecycle, cancellation, error handling, and cleanup.

Do not create unmanaged fire-and-forget tasks. A task owner must know how to cancel, await, log, and release resources.

## Review Checklist

- Did core avoid new concrete infrastructure dependencies?
- Are optional dependencies isolated behind adapters or extras?
- Is configuration typed and validated at the boundary?
- Does package layout still match `docs/structure.md`?
- Are logs/traces useful without leaking sensitive data?
- Are background tasks supervised and cancellable?
