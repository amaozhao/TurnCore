"""Policy declaration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Mapping

PolicyEffect = Literal["allow", "deny", "approval_required"]


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


def _freeze_mapping(value: Mapping[str, object] | None) -> Mapping[str, object]:
    return MappingProxyType({} if value is None else dict(value))


@dataclass(frozen=True)
class PolicyRuleDefinition:
    """Declarative pack policy rule."""

    rule_id: str
    target: str
    effect: PolicyEffect
    reason: str = ""
    metadata: Mapping[str, object] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ValueError("policy rule_id must be non-empty")
        if not self.target:
            raise ValueError("policy target must be non-empty")
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


__all__ = ["PolicyEffect", "PolicyRuleDefinition"]
