"""User-facing identity protocol models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    """Authenticated actor resolved by an adapter."""

    user_id: str
    roles: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ()


__all__ = ["Principal"]
