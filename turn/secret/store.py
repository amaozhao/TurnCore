"""Secret lease provider."""

from __future__ import annotations

from typing import Protocol

from turn.error import UAFError
from turn.secret.lease import SecretLease, SecretValue


class SecretLeaseProvider(Protocol):
    """Port for session-bound secret leases."""

    async def get_secret(
        self,
        *,
        session_id: str,
        turn_id: str,
        name: str,
        required_scope: str,
    ) -> SecretValue: ...


class MemorySecretLeaseProvider:
    """Secret lease provider backed by process memory."""

    def __init__(self) -> None:
        self.leases: dict[tuple[str, str, str], SecretLease] = {}

    def add_lease(self, lease: SecretLease) -> None:
        self.leases[(lease.session_id, lease.turn_id, lease.name)] = lease

    async def get_secret(
        self,
        *,
        session_id: str,
        turn_id: str,
        name: str,
        required_scope: str,
    ) -> SecretValue:
        lease = self.leases.get((session_id, turn_id, name))
        if lease is None:
            raise UAFError(
                code="secret.not_found",
                message="Secret lease was not found",
                metadata={"secret_name": name},
            )
        if required_scope not in lease.scopes:
            raise UAFError(
                code="secret.scope_denied",
                message="Secret lease does not include required scope",
                metadata={"secret_name": name, "required_scope": required_scope},
            )
        return SecretValue(
            name=name,
            value=lease.value,
            scope=required_scope,
            session_id=session_id,
            turn_id=turn_id,
        )


__all__ = ["MemorySecretLeaseProvider", "SecretLeaseProvider"]
