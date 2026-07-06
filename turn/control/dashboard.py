"""Run dashboard data."""

from __future__ import annotations

from dataclasses import dataclass

from turn.event.model import StreamEvent
from turn.port.event import EventStore
from turn.port.run import RunRepository, TurnRepository
from turn.run import Run, Turn


@dataclass(frozen=True)
class RunDashboard:
    """Transport-neutral dashboard data for one turn."""

    session_id: str
    turn: Turn
    runs: tuple[Run, ...]
    latest_events: tuple[StreamEvent, ...]
    latest_seq: int


class DashboardReader:
    """Builds run dashboard snapshots from existing ports."""

    def __init__(
        self,
        *,
        turns: TurnRepository,
        runs: RunRepository,
        events: EventStore,
    ) -> None:
        self.turns = turns
        self.runs = runs
        self.events = events

    async def get_turn_dashboard(
        self,
        *,
        session_id: str,
        turn_id: str,
        event_limit: int = 50,
    ) -> RunDashboard | None:
        if event_limit < 1:
            raise ValueError("event_limit must be positive")
        turn = await self.turns.get_turn(turn_id)
        if turn is None or turn.session_id != session_id:
            return None
        runs = tuple(
            run
            for run in await self.runs.list_runs_for_turn(turn_id)
            if run.session_id == session_id
        )
        latest_seq = await self.events.latest_seq(turn_id)
        events = await self.events.list_by_turn(
            turn_id=turn_id,
            after_seq=max(0, latest_seq - event_limit),
            limit=event_limit,
        )
        scoped_events = tuple(event for event in events if event.session_id == session_id)
        return RunDashboard(
            session_id=session_id,
            turn=turn,
            runs=runs,
            latest_events=scoped_events,
            latest_seq=latest_seq,
        )


__all__ = ["DashboardReader", "RunDashboard"]
