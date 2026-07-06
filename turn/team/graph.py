"""Team task DAG."""

from __future__ import annotations

from dataclasses import dataclass

from turn.team.task import TeamTask


@dataclass(frozen=True)
class TeamGraph:
    """Acyclic graph of team tasks."""

    tasks: tuple[TeamTask, ...]

    def __post_init__(self) -> None:
        ids = [task.task_id for task in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("team task ids must be unique")
        task_ids = set(ids)
        for task in self.tasks:
            missing = [task_id for task_id in task.depends_on if task_id not in task_ids]
            if missing:
                raise ValueError("team task dependency must exist")
        _layers(self.tasks)

    def layers(self) -> tuple[tuple[TeamTask, ...], ...]:
        return _layers(self.tasks)


def _layers(tasks: tuple[TeamTask, ...]) -> tuple[tuple[TeamTask, ...], ...]:
    remaining = {task.task_id: task for task in tasks}
    completed: set[str] = set()
    layers: list[tuple[TeamTask, ...]] = []
    while remaining:
        ready = tuple(
            task
            for task in remaining.values()
            if all(task_id in completed for task_id in task.depends_on)
        )
        if not ready:
            raise ValueError("team task graph must be acyclic")
        layers.append(ready)
        for task in ready:
            completed.add(task.task_id)
            del remaining[task.task_id]
    return tuple(layers)


__all__ = ["TeamGraph"]
