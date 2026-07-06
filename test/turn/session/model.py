from datetime import datetime, timezone

from turn.session.model import Session, SessionPackSelection


def test_session_references_pack_selection_without_owning_enabled_packs() -> None:
    now = datetime.now(timezone.utc)

    session = Session(
        session_id="sess_1",
        owner_user_id="user_1",
        title="Research",
        status="active",
        prompt_profile_id="profile_1",
        pack_selection_id="sel_1",
        default_capability="chat",
        config={"max_iterations": 4},
        created_at=now,
        updated_at=now,
    )
    selection = SessionPackSelection(
        selection_id="sel_1",
        session_id=session.session_id,
        enabled_pack_ids=("com.example.research",),
        enabled_tool_names=("web.read",),
        revision=1,
        checksum="abc123",
    )

    assert session.owner_user_id == "user_1"
    assert session.pack_selection_id == selection.selection_id
    assert selection.session_id == session.session_id
