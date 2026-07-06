# Performance Standard

## Scope

Use this standard when changing async execution, session locks, turn concurrency, event streams, snapshots, pack loading, tool execution, storage-port calls, external calls, payload size, or caching.

## Core Rule

Do not optimize blindly, but do not introduce obvious latency, memory, concurrency, or isolation regressions. Prefer the simplest bounded behavior that preserves correctness.

## Async Runtime

- Do not block the event loop with sync I/O, sleeps, provider calls, or heavy CPU work.
- Do not call `asyncio.run()` inside library runtime code.
- Bound parallel tool calls.
- Keep cancellation tokens checked in long-running loops.
- Clean up tasks, streams, workspaces, and adapter resources.

## Turn Concurrency

- Use session/turn locking to prevent conflicting writes.
- Allow read-only tool concurrency only when tool effects are classified and policy-checked.
- Serialize write tools unless a stronger owner proves safety.
- Do not let concurrent turns mix prompt snapshots, tool registries, memory snapshots, events, artifacts, or approvals.

## Agent Loop Limits

Agent loops need explicit limits:

- max iterations;
- tool timeout;
- model timeout;
- event emission bounds;
- cancellation checks;
- finalization behavior.

Do not add unbounded retry, reflection, or planning loops.

## Event Streams

- Event sequence numbers must be stable within a turn.
- Subscription/replay should use cursors instead of replaying unbounded history.
- Avoid large event payloads; store large artifacts separately and reference them.
- Keep metadata safe and bounded.

## Snapshots

Prompt, tool registry, memory, and policy snapshots are correctness boundaries. Avoid expensive deep copies in hot paths, but never trade away immutability or isolation.

Cache compiled or loaded data only when the cache key includes the inputs that affect behavior, such as session, turn, pack version, prompt source, policy, and checksum.

## External Calls

External calls belong behind ports or adapters and should have:

- timeouts;
- bounded retries when safe;
- cancellation behavior;
- rate/concurrency limits when looping;
- safe logging or metrics for failures and latency.

## Storage Ports

Core code should not assume a database, but it should still avoid expensive storage-port patterns:

- unbounded lists;
- missing deterministic ordering;
- repeated per-item fetches when a port can expose a batch operation;
- loading large artifacts through event payloads;
- hidden cross-session scans.

## Review Checklist

- Are async operations non-blocking and cancellable?
- Is concurrency bounded and separated by session/turn?
- Are write effects serialized or protected?
- Are event streams cursor-based and payloads bounded?
- Are snapshots immutable without excessive copying?
- Are external/storage calls bounded and behind ports?
