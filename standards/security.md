# Security Standard

## Scope

Use this standard when changing principals, session authorization, prompt snapshots, tool policy, pack permissions, secrets, uploads, artifacts, workspace paths, external network access, logging, or untrusted input.

## Core Rule

`User` is the identity subject. `Session` is the runtime namespace. Runtime resources must be authorized through the session, not by scattering `user_id` across turns, runs, events, artifacts, approvals, memory, or tool calls.

## Authorization Path

All protected runtime access must follow:

```text
principal.user_id
  -> session_id
  -> session.owner_user_id
  -> resource.session_id
```

When a request starts from a child ID, resolve the session first.

Do not add APIs or ports shaped like:

```python
list_events(user_id=...)
get_artifact(user_id=..., artifact_id=...)
write_user_memory(user_id=...)
```

Prefer session-scoped operations.

## Prompt Isolation

- Agent runtime reads prompt snapshots, not mutable prompt files.
- User defaults may seed a session or turn snapshot, but runtime must not read mutable user prompt state mid-turn.
- Pack prompts enter the snapshot only through declared pack sources.
- Different sessions must not share runtime prompt snapshots.

## Tool And Pack Policy

- Tool permissions, network scope, filesystem scope, and effect type must be declared and checked before execution.
- Read-only tools may run concurrently only when their effect classification is trustworthy.
- Write tools must be serialized or otherwise protected by the owning runtime.
- Pack definitions are global read-only; pack enablement is session-scoped.
- User pack grants only authorize what a session may enable.

## Secrets

Secrets belong to the user, but use is session-bound through a lease or equivalent checked handle.

Rules:

- do not expose raw secrets to tools when a scoped handle is enough;
- do not log tokens, keys, cookies, auth headers, session IDs, or provider credentials;
- do not store secrets in prompt snapshots, events, artifacts, or error details;
- validate required secrets at adapter/config boundaries.

## Artifacts, Uploads, And Workspace

- Artifacts and uploads are session/turn-scoped.
- Normalize and constrain paths.
- Prevent path traversal.
- Do not trust original filenames or client-provided content types alone.
- Enforce size and type limits at the adapter or artifact boundary.
- Session deletion must delete or archive session runtime resources according to the spec.

## Network And SSRF

Server-side tools and adapters must not fetch arbitrary user-provided URLs without policy checks.

Check protocol, host, redirects, private network access, timeout, and response size. Use pack or session policy allowlists when possible.

## Logging

Log stable IDs and safe context. Do not log raw prompts, tool arguments, provider payloads, uploaded contents, secrets, or large request bodies unless a documented debug mode safely redacts them.

## Review Checklist

- Is every runtime resource scoped through session?
- Does the change avoid direct `user_id` ownership for turns, events, artifacts, approvals, memory, and tool calls?
- Are prompt, tool registry, and memory snapshots frozen for the turn?
- Are tool and pack permissions checked before execution?
- Are secrets accessed through scoped leases and redacted from outputs?
- Are paths, uploads, and external URLs constrained?
- Are security-critical paths tested?
