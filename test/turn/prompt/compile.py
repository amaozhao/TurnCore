import asyncio

import pytest

from turn.prompt import DefaultPromptCompiler, PromptCompileCommand, PromptSource
from turn.prompt.profile import SessionPromptProfile


def test_prompt_compiler_freezes_ordered_snapshot() -> None:
    asyncio.run(check_prompt_compiler_freezes_ordered_snapshot())


async def check_prompt_compiler_freezes_ordered_snapshot() -> None:
    compiler = DefaultPromptCompiler()
    profile = SessionPromptProfile(
        profile_id="profile_1",
        session_id="sess_1",
        base_prompt="session base",
        persona_prompt="",
        style_prompt="",
        safety_prompt="session safety",
        pack_prompt_refs=("pack_1",),
        created_from_user_default_id="default_1",
        revision=1,
        checksum="profile_checksum",
    )

    snapshot = await compiler.compile_for_turn(
        PromptCompileCommand(
            session_id="sess_1",
            turn_id="turn_1",
            sources=(
                PromptSource.from_text(
                    source_id="pack_1",
                    source_type="pack_builtin",
                    priority=0,
                    content="pack prompt",
                ),
                PromptSource.from_text(
                    source_id="default_1",
                    source_type="user_default",
                    priority=0,
                    content="user default",
                ),
                PromptSource.from_text(
                    source_id="kernel",
                    source_type="framework_builtin",
                    priority=0,
                    content="framework kernel",
                ),
            ),
            profile=profile,
            memory_injection="memory summary",
            knowledge_injection="knowledge result",
            turn_overlay="turn overlay",
            tool_manifest="tool manifest",
            capability_manifest="capability manifest",
        )
    )

    assert snapshot.session_id == "sess_1"
    assert snapshot.turn_id == "turn_1"
    assert [source.source_id for source in snapshot.sources] == [
        "kernel",
        "capability_manifest:sess_1:turn_1",
        "pack_1",
        "tool_manifest:sess_1:turn_1",
        "default_1",
        "session_profile:profile_1:safety",
        "session_profile:profile_1:base",
        "memory:sess_1:turn_1",
        "knowledge:sess_1:turn_1",
        "turn_overlay:sess_1:turn_1",
    ]
    assert snapshot.compiled_system_prompt == "\n\n".join(
        (
            "framework kernel",
            "pack prompt",
            "user default",
            "session safety",
            "session base",
            "memory summary",
            "knowledge result",
            "turn overlay",
        )
    )
    assert snapshot.compiled_tool_manifest == "tool manifest"
    assert snapshot.compiled_capability_manifest == "capability manifest"
    assert snapshot.compiled_developer_prompt is None


def test_prompt_snapshot_checksum_changes_with_turn_inputs() -> None:
    asyncio.run(check_prompt_snapshot_checksum_changes_with_turn_inputs())


async def check_prompt_snapshot_checksum_changes_with_turn_inputs() -> None:
    compiler = DefaultPromptCompiler()
    first = await compiler.compile_for_turn(
        PromptCompileCommand(session_id="sess_1", turn_id="turn_1", turn_overlay="one")
    )
    second = await compiler.compile_for_turn(
        PromptCompileCommand(session_id="sess_1", turn_id="turn_1", turn_overlay="two")
    )

    assert first.checksum != second.checksum
    assert first.snapshot_id != second.snapshot_id


def test_prompt_compiler_rejects_cross_session_profile() -> None:
    asyncio.run(check_prompt_compiler_rejects_cross_session_profile())


async def check_prompt_compiler_rejects_cross_session_profile() -> None:
    compiler = DefaultPromptCompiler()
    profile = SessionPromptProfile(
        profile_id="profile_1",
        session_id="sess_2",
        base_prompt="base",
        persona_prompt="",
        style_prompt="",
        safety_prompt="",
        pack_prompt_refs=(),
        created_from_user_default_id=None,
        revision=1,
        checksum="checksum",
    )

    with pytest.raises(ValueError, match="profile session_id"):
        await compiler.compile_for_turn(
            PromptCompileCommand(session_id="sess_1", turn_id="turn_1", profile=profile)
        )
