# Error Standard

## Scope

Use this standard when changing domain exceptions, `UAFError`-style errors, `ErrorEnvelope`, cancellation, retries, fallbacks, adapter error mapping, tool errors, or error tests.

## Core Rules

- Expected failures become stable domain errors inside core and safe error envelopes at wire/tool/event boundaries.
- Unexpected failures must not be converted into success.
- Keep protected blocks narrow and catch specific errors.
- Preserve causes when translating errors.
- Tool errors do not automatically kill a turn unless policy or runtime state requires it.
- Cancellation is a first-class state, not a generic failure.
- Library code must not return HTTP responses, close sockets, write host-application logs, or choose user-facing presentation.

## Expected Failures

Expected failures include:

- session not found or access denied;
- active turn conflict;
- turn cancelled or not waiting for user;
- tool not found, timeout, policy denial, or approval required;
- model provider error or empty response;
- prompt compile failure;
- memory snapshot failure;
- artifact not found;
- pack not found or permission denied.

Use stable codes shaped like the spec, for example `session.not_found` and `tool.policy_denied`.

## Unexpected Failures

Unexpected failures include impossible state, missing required config, programmer error, malformed internal data, and unhandled infrastructure failures.

Let them surface to the caller with their cause preserved. Adapters or host applications decide logging and process-level handling. Do not return empty events, empty artifacts, default snapshots, or successful envelopes after unexpected errors.

## Python Rules

Prefer:

```python
try:
    snapshot = await compiler.compile_for_turn(command)
except PromptCompileError as exc:
    raise UAFError(
        code="prompt.compile_failed",
        message="Prompt compilation failed",
        retryable=False,
        metadata={"source": exc.source_id},
    ) from exc
```

Avoid:

```python
try:
    ...
except Exception:
    return None
```

Rules:

- Do not use bare `except`.
- Do not catch `BaseException`, `KeyboardInterrupt`, or `SystemExit`.
- Avoid broad `except Exception` outside adapter or host-application boundaries.
- Use `raise ... from exc` when translating errors.
- Use `finally` only for cleanup and do not suppress the original error.

## ErrorEnvelope Rules

`ErrorEnvelope` is a cross-boundary error value, not a replacement for Python exceptions inside core.

It must contain a stable code, safe message, retryability, optional session/turn/run scope, and safe details.

Do not include stack traces, secrets, raw provider payloads, file contents, full paths, database errors, or internal exception names.

Transport adapters may map an `ErrorEnvelope` to HTTP status, WebSocket message, SSE event, CLI output, or IM response. Core only produces the envelope.

Do not create an `ErrorEnvelope` merely to keep executing after an unexpected core bug.

## Retries And Fallbacks

Retries belong at the boundary that owns the external call. They require limits, timeout behavior, and cancellation awareness.

Fallbacks are allowed only when the contract says continuing is safe. A fallback must define what failed, what users or callers observe, and how the failure is logged or surfaced.

## Review Checklist

- Is the caught error specific?
- Are expected errors mapped to stable codes?
- Are unexpected errors allowed to fail visibly?
- Are tool errors, approval-required states, and cancellation handled distinctly?
- Are causes preserved when errors are translated?
- Did core avoid transport responses and host logging decisions?
- Are sensitive details excluded from envelopes and logs?
- Do tests prove expected error behavior?
