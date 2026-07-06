"""Shared port value models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    """Cursor page returned by list ports."""

    items: tuple[T, ...]
    next_cursor: str | None = None


__all__ = ["Page"]
