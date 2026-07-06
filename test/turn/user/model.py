from dataclasses import FrozenInstanceError

import pytest

from turn.user.model import Principal


def test_principal_is_authenticated_actor_not_resource_owner() -> None:
    principal = Principal(user_id="user_1", roles=("admin",), scopes=("session.read",))

    assert principal.user_id == "user_1"
    assert principal.roles == ("admin",)
    assert principal.scopes == ("session.read",)

    with pytest.raises(FrozenInstanceError):
        principal.user_id = "user_2"  # type: ignore[misc]
