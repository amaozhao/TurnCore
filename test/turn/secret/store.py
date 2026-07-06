import asyncio

import pytest

from turn.error import UAFError
from turn.secret import MemorySecretLeaseProvider, SecretLease


def test_secret_provider_requires_session_bound_lease() -> None:
    asyncio.run(check_secret_provider_requires_session_bound_lease())


async def check_secret_provider_requires_session_bound_lease() -> None:
    provider = MemorySecretLeaseProvider()
    provider.add_lease(
        SecretLease(
            session_id="sess_1",
            turn_id="turn_1",
            name="github",
            value="token",
            scopes=("repo:read",),
        )
    )

    secret = await provider.get_secret(
        session_id="sess_1",
        turn_id="turn_1",
        name="github",
        required_scope="repo:read",
    )

    assert secret.value == "token"
    assert secret.session_id == "sess_1"
    assert secret.turn_id == "turn_1"

    with pytest.raises(UAFError) as missing:
        await provider.get_secret(
            session_id="sess_2",
            turn_id="turn_1",
            name="github",
            required_scope="repo:read",
        )
    assert missing.value.code == "secret.not_found"


def test_secret_provider_rejects_missing_scope() -> None:
    asyncio.run(check_secret_provider_rejects_missing_scope())


async def check_secret_provider_rejects_missing_scope() -> None:
    provider = MemorySecretLeaseProvider()
    provider.add_lease(
        SecretLease(
            session_id="sess_1",
            turn_id="turn_1",
            name="github",
            value="token",
            scopes=("repo:read",),
        )
    )

    with pytest.raises(UAFError) as denied:
        await provider.get_secret(
            session_id="sess_1",
            turn_id="turn_1",
            name="github",
            required_scope="repo:write",
        )
    assert denied.value.code == "secret.scope_denied"
