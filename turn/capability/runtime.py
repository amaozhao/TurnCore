"""Capability runtime."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone

from turn.capability.base import BaseCapability, CapabilityContext
from turn.capability.result import CapabilityResult
from turn.error import UAFError
from turn.port.run import RunRepository
from turn.run.model import Run
from turn.wire.error import ErrorEnvelope


class CapabilityRuntime:
    """Runs one capability and records capability-stage events/runs."""

    def __init__(self, runs: RunRepository) -> None:
        self.runs = runs

    async def run(
        self,
        *,
        capability: BaseCapability,
        context: CapabilityContext,
    ) -> CapabilityResult:
        run = Run(
            run_id=f"run_{uuid.uuid4().hex}",
            session_id=context.session_id,
            turn_id=context.turn_id,
            kind="capability_stage",
            status="running",
            input_summary=capability.manifest.name,
            output_summary=None,
            error=None,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )
        await self.runs.create_run(run)
        await context.event_sink.emit(
            type="stage_start",
            source="capability",
            stage=capability.manifest.name,
        )
        try:
            result = await capability.run(context)
        except UAFError as exc:
            result = CapabilityResult(status="failed", error=exc.to_envelope())
        except Exception:
            result = CapabilityResult(
                status="failed",
                error=ErrorEnvelope(
                    code="capability.failed",
                    message="Capability failed",
                    session_id=context.session_id,
                    turn_id=context.turn_id,
                ),
            )
        await context.event_sink.emit(
            type="stage_end",
            source="capability",
            stage=capability.manifest.name,
            content=result.content,
            metadata={"status": result.status},
        )
        await self.runs.update_run(
            replace(
                run,
                status="completed" if result.status == "completed" else "failed",
                output_summary=result.content,
                error=result.error,
                completed_at=datetime.now(timezone.utc),
            )
        )
        return result


__all__ = ["CapabilityRuntime"]
