import asyncio

import pytest

from turn.eval import EvalCase, EvalRunner, EvalSuite


class EchoSubject:
    async def run(self, input: str) -> str:
        return input.upper()


def test_eval_suite_rejects_duplicate_cases() -> None:
    with pytest.raises(ValueError, match="unique"):
        EvalSuite(
            suite_id="suite_1",
            cases=(
                EvalCase(case_id="case_1", input="a", expected="A"),
                EvalCase(case_id="case_1", input="b", expected="B"),
            ),
        )


def test_eval_runner_reports_pass_and_failure() -> None:
    asyncio.run(check_eval_runner_reports_pass_and_failure())


async def check_eval_runner_reports_pass_and_failure() -> None:
    suite = EvalSuite(
        suite_id="suite_1",
        cases=(
            EvalCase(case_id="case_1", input="a", expected="A"),
            EvalCase(case_id="case_2", input="b", expected="wrong"),
        ),
    )

    result = await EvalRunner().run(suite, EchoSubject())

    assert result.passed is False
    assert tuple(case.status for case in result.results) == ("passed", "failed")
