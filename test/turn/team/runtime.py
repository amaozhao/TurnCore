import asyncio

import pytest

from turn.error import UAFError
from turn.team import TeamGraph, TeamRuntime, TeamTask, TeamTaskResult


class RecordingHandler:
    def __init__(self) -> None:
        self.started: list[str] = []
        self.wait = asyncio.Event()

    async def run(
        self,
        task: TeamTask,
        results: dict[str, TeamTaskResult],
    ) -> TeamTaskResult:
        self.started.append(task.task_id)
        if task.task_id in {"a", "b"}:
            await self.wait.wait()
        return TeamTaskResult(
            task_id=task.task_id,
            status="completed",
            output={"seen": tuple(results)},
        )


def test_team_graph_rejects_cycles() -> None:
    with pytest.raises(ValueError, match="acyclic"):
        TeamGraph(
            tasks=(
                TeamTask(task_id="a", name="A", depends_on=("b",)),
                TeamTask(task_id="b", name="B", depends_on=("a",)),
            )
        )


def test_team_runtime_runs_ready_tasks_together_then_dependents() -> None:
    asyncio.run(check_team_runtime_runs_ready_tasks_together_then_dependents())


async def check_team_runtime_runs_ready_tasks_together_then_dependents() -> None:
    graph = TeamGraph(
        tasks=(
            TeamTask(task_id="a", name="A"),
            TeamTask(task_id="b", name="B"),
            TeamTask(task_id="c", name="C", depends_on=("a", "b")),
        )
    )
    handler = RecordingHandler()
    runtime = TeamRuntime()

    task = asyncio.create_task(runtime.run(graph, handler))
    while set(handler.started) != {"a", "b"}:
        await asyncio.sleep(0)

    assert "c" not in handler.started

    handler.wait.set()
    results = await task

    assert tuple(result.task_id for result in results) == ("a", "b", "c")
    assert handler.started == ["a", "b", "c"]
    assert results[-1].output["seen"] == ("a", "b")


def test_team_runtime_stops_after_failed_layer() -> None:
    asyncio.run(check_team_runtime_stops_after_failed_layer())


class FailingHandler:
    async def run(
        self,
        task: TeamTask,
        results: dict[str, TeamTaskResult],
    ) -> TeamTaskResult:
        raise UAFError(code="task.nope", message="Nope")


async def check_team_runtime_stops_after_failed_layer() -> None:
    graph = TeamGraph(
        tasks=(
            TeamTask(task_id="a", name="A"),
            TeamTask(task_id="b", name="B", depends_on=("a",)),
        )
    )

    results = await TeamRuntime().run(graph, FailingHandler())

    assert len(results) == 1
    assert results[0].task_id == "a"
    assert results[0].status == "failed"
    assert results[0].error is not None
    assert results[0].error.code == "task.nope"
