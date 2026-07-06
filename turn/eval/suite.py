"""Evaluation suite models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

EvalStatus = Literal["passed", "failed"]


@dataclass(frozen=True)
class EvalCase:
    """One deterministic evaluation case."""

    case_id: str
    input: str
    expected: str

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("eval case_id must be non-empty")


@dataclass(frozen=True)
class EvalCaseResult:
    """Result for one evaluation case."""

    case_id: str
    status: EvalStatus
    actual: str
    expected: str


@dataclass(frozen=True)
class EvalSuite:
    """A named group of evaluation cases."""

    suite_id: str
    cases: tuple[EvalCase, ...]

    def __post_init__(self) -> None:
        if not self.suite_id:
            raise ValueError("eval suite_id must be non-empty")
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("eval case ids must be unique")


@dataclass(frozen=True)
class EvalSuiteResult:
    """Result for a full evaluation suite."""

    suite_id: str
    results: tuple[EvalCaseResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.status == "passed" for result in self.results)


class EvalSubject(Protocol):
    """Callable subject evaluated by an eval suite."""

    async def run(self, input: str) -> str: ...


class EvalRunner:
    """Runs deterministic string-match evaluation suites."""

    async def run(self, suite: EvalSuite, subject: EvalSubject) -> EvalSuiteResult:
        results: list[EvalCaseResult] = []
        for case in suite.cases:
            actual = await subject.run(case.input)
            status: EvalStatus = "passed" if actual == case.expected else "failed"
            results.append(
                EvalCaseResult(
                    case_id=case.case_id,
                    status=status,
                    actual=actual,
                    expected=case.expected,
                )
            )
        return EvalSuiteResult(suite_id=suite.suite_id, results=tuple(results))


__all__ = [
    "EvalCase",
    "EvalCaseResult",
    "EvalRunner",
    "EvalStatus",
    "EvalSubject",
    "EvalSuite",
    "EvalSuiteResult",
]
