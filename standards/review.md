# Review Standard

## Scope

Use this standard for final self-review, requested code review, diff scope checks, and verification reporting.

## Core Rule

Review the actual diff, verify relevant behavior, and report only what changed and what was checked.

Do not claim lint, type check, tests, or build passed unless the command was run and the output was read.

## Review Workflow

### 1. Scope

Check for:

- changes outside the user's request;
- generated, cache, runtime, build, or dependency output;
- unrelated formatting churn;
- deleted standards or docs still referenced elsewhere.

### 2. Spec Alignment

Check against `docs/spec.md` and `docs/structure.md`:

- TurnCore remains a Python library, not an app template.
- Core is protocol-first and infrastructure-neutral.
- `Session` remains the runtime namespace.
- Transport is an adapter binding, not core API.
- Storage is a port, not a built-in database.

### 3. Modules

Apply `modules.md`:

- owning boundary enforces the invariant;
- no shallow wrappers;
- no core-to-adapter dependency;
- public interfaces are typed and domain-oriented.

### 4. Contracts

Apply `contracts.md` when public protocol behavior changes:

- command/event/error envelopes are stable;
- principal/session authorization path is preserved;
- adapters map to core contracts instead of bypassing them;
- pack/tool/capability contracts stay explicit.

### 5. Types

Apply `typing.md`:

- public models are typed;
- `Any` stays at intended extension boundaries;
- untrusted payloads are narrowed before use;
- optional values represent real states.

### 6. Errors

Apply `errors.md`:

- expected errors have stable codes;
- unexpected errors are not swallowed;
- cancellation, approval-required, and tool errors are distinct;
- error envelopes and logs are safe.

### 7. Security

Apply `security.md`:

- runtime resources are session-scoped;
- prompt/tool/memory snapshots are isolated;
- tool and pack permissions are checked;
- secrets, paths, uploads, external URLs, and logs are safe.

### 8. Operations And Performance

Apply `operations.md` and `performance.md`:

- core dependencies stay minimal;
- optional dependencies stay in adapters/extras;
- config is validated at boundaries;
- async work is bounded and cancellable;
- event streams, snapshots, and storage-port calls are bounded.

### 9. Tests

Apply `testing.md`:

- tests mirror `turn/` under `test/turn/`;
- regression tests target the owning boundary;
- mocks are at unstable boundaries;
- verification started narrow and broadened when needed.

## Completion Report

Use this structure when useful:

```text
Changed:
- ...

Verified:
- ...

Skipped:
- ... because ...

Notes:
- ...
```

Keep it factual and short.

## Review Findings Format

Findings first, ordered by severity:

- Critical: security, data loss, or build-breaking production risk.
- High: likely functional bug or broken public contract.
- Medium: maintainability, test, typing, or performance risk.
- Low: clarity or minor cleanup.

Each finding should include file/location, problem, impact, and recommended fix.

If there are no findings, say so and mention any verification gap.
