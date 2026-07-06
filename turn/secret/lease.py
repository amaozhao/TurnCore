"""Secret lease models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecretValue:
    """Session-bound secret value returned by a lease provider."""

    name: str
    value: str
    scope: str
    session_id: str
    turn_id: str


@dataclass(frozen=True)
class SecretLease:
    """Secret reference authorized for a session and turn."""

    session_id: str
    turn_id: str
    name: str
    value: str
    scopes: tuple[str, ...]


__all__ = ["SecretLease", "SecretValue"]
