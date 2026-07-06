"""Team DAG runtime."""

from __future__ import annotations

import asyncio
from typing import Mapping, Protocol

from turn.error import UAFError
from turn.run.cancel import CancellationToken
from turn.team.graph import TeamGraph
from turn.team.task import TeamTask, TeamTaskResult
from turn.wire.error import ErrorEnvelope


class TeamTaskHandler(Protocol):
    """Executes one team task."""

    async def run(
        self,
        task: TeamTask,
        results: Mapping[str, TeamTaskResult],
    ) -> TeamTaskResult: ...


class TeamRuntime:
    """Executes DAG task layers in dependency order."""

    async def run(
        self,
        graph: TeamGraph,
        handler: TeamTaskHandler,
        *,
        cancellation_token: CancellationToken | None = None,
    ) -> tuple[TeamTaskResult, ...]:
        results: dict[str, TeamTaskResult] = {}
        for layer in graph.layers():
            _raise_if_cancelled(cancellation_token)
            layer_results = await asyncio.gather(
                *(_run_task(task, handler, results) for task in layer)
            )
            for result in layer_results:
                results[result.task_id] = result
            failed = [result for result in layer_results if result.status != "completed"]
            if failed:
                return tuple(results.values())
        return tuple(results.values())


async def _run_task(
    task: TeamTask,
    handler: TeamTaskHandler,
    results: Mapping[str, TeamTaskResult],
) -> TeamTaskResult:
    try:
        return await handler.run(task, results)
    except UAFError as exc:
        return TeamTaskResult(task_id=task.task_id, status="failed", error=exc.to_envelope())
    except Exception:
        return TeamTaskResult(
            task_id=task.task_id,
            status="failed",
            error=ErrorEnvelope(
                code="team.task_failed",
                message="Team task failed",
                details={"task_id": task.task_id},
            ),
        )


def _raise_if_cancelled(cancellation_token: CancellationToken | None) -> None:
    if cancellation_token is not None:
        cancellation_token.raise_if_cancelled()


__all__ = ["TeamRuntime", "TeamTaskHandler"]
