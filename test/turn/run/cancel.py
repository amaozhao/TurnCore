import asyncio

import pytest

from turn.error import UAFError
from turn.run.cancel import CancellationToken


def test_cancellation_token_marks_and_raises_cancelled_state() -> None:
    token = CancellationToken()

    assert not token.cancelled
    token.raise_if_cancelled()

    token.cancel()

    assert token.cancelled
    with pytest.raises(UAFError) as error:
        token.raise_if_cancelled()
    assert error.value.code == "turn.cancelled"


def test_cancellation_token_can_be_awaited() -> None:
    asyncio.run(check_cancellation_token_can_be_awaited())


async def check_cancellation_token_can_be_awaited() -> None:
    token = CancellationToken()

    async def cancel() -> None:
        token.cancel()

    await cancel()
    await token.wait()

    assert token.cancelled
