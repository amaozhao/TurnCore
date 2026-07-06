"""Policy decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PolicyDecisionStatus = Literal["allow", "deny", "approval_required"]


@dataclass(frozen=True)
class PolicyDecision:
    """Decision for one tool or runtime action."""

    status: PolicyDecisionStatus
    reason: str = ""

    @property
    def allowed(self) -> bool:
        return self.status == "allow"

    @property
    def requires_approval(self) -> bool:
        return self.status == "approval_required"


__all__ = ["PolicyDecision", "PolicyDecisionStatus"]
