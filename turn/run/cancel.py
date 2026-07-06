"""Turn cancellation token."""

from __future__ import annotations

import asyncio

from turn.error import UAFError


class CancellationToken:
    """Cooperative cancellation signal for one turn."""

    def __init__(self) -> None:
        self.event = asyncio.Event()

    @property
    def cancelled(self) -> bool:
        return self.event.is_set()

    def cancel(self) -> None:
        self.event.set()

    async def wait(self) -> None:
        await self.event.wait()

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise UAFError(
                code="turn.cancelled",
                message="Turn was cancelled",
                retryable=False,
            )


__all__ = ["CancellationToken"]
