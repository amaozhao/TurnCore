import asyncio
from datetime import datetime, timezone

from turn.control import DashboardReader
from turn.event import StreamEvent
from turn.event.store import MemoryEventStore
from turn.run import Run, Turn
from turn.run.store import MemoryRunStore, MemoryTurnStore


def test_dashboard_reader_returns_session_scoped_turn_data() -> None:
    asyncio.run(check_dashboard_reader_returns_session_scoped_turn_data())


async def check_dashboard_reader_returns_session_scoped_turn_data() -> None:
    now = datetime.now(timezone.utc)
    turns = MemoryTurnStore()
    runs = MemoryRunStore()
    events = MemoryEventStore()
    turn = Turn(
        turn_id="turn_1",
        session_id="sess_1",
        parent_turn_id=None,
        status="running",
        command_snapshot={},
        prompt_snapshot_id=None,
        tool_registry_snapshot_id=None,
        memory_snapshot_id=None,
        created_at=now,
        started_at=now,
        completed_at=None,
    )
    run = Run(
        run_id="run_1",
        session_id="sess_1",
        turn_id="turn_1",
        kind="team_task",
        status="running",
        input_summary="input",
        output_summary=None,
        error=None,
        created_at=now,
        completed_at=None,
    )
    event = StreamEvent(
        event_id="event_1",
        session_id="sess_1",
        turn_id="turn_1",
        seq=1,
        type="progress",
        source="team",
        stage="task",
        content="started",
        metadata={},
        created_at=now,
    )
    leaked = StreamEvent(
        event_id="event_2",
        session_id="sess_2",
        turn_id="turn_1",
        seq=2,
        type="progress",
        source="team",
        stage="task",
        content="leaked",
        metadata={},
        created_at=now,
    )

    await turns.create_turn(turn)
    await runs.create_run(run)
    await events.append(event)
    await events.append(leaked)

    reader = DashboardReader(turns=turns, runs=runs, events=events)
    dashboard = await reader.get_turn_dashboard(session_id="sess_1", turn_id="turn_1")

    assert dashboard is not None
    assert dashboard.turn == turn
    assert dashboard.runs == (run,)
    assert dashboard.latest_events == (event,)
    assert dashboard.latest_seq == 2
    assert await reader.get_turn_dashboard(session_id="sess_2", turn_id="turn_1") is None
