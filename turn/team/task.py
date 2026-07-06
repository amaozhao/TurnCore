"""Team task models."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Mapping

from turn.wire.error import ErrorEnvelope

TeamTaskStatus = Literal["queued", "running", "completed", "failed", "cancelled"]


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class TeamTask:
    """Task node inside a team DAG."""

    task_id: str
    name: str
    depends_on: tuple[str, ...] = ()
    input: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id must be non-empty")
        if not self.name:
            raise ValueError("task name must be non-empty")
        if self.task_id in self.depends_on:
            raise ValueError("task cannot depend on itself")
        object.__setattr__(self, "input", _freeze_mapping(self.input))


@dataclass(frozen=True)
class TeamTaskResult:
    """Result for one team task."""

    task_id: str
    status: TeamTaskStatus
    output: Mapping[str, object] = field(default_factory=_empty_mapping)
    error: ErrorEnvelope | None = None

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task result task_id must be non-empty")
        object.__setattr__(self, "output", _freeze_mapping(self.output))


__all__ = ["TeamTask", "TeamTaskResult", "TeamTaskStatus"]
