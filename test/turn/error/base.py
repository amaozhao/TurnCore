from turn.error.base import UAFError


def test_uaf_error_converts_to_safe_envelope() -> None:
    error = UAFError(
        code="prompt.compile_failed",
        message="Prompt compilation failed",
        retryable=False,
        metadata={"source": "pack_prompt"},
    )

    envelope = error.to_envelope(session_id="sess_1", turn_id="turn_1")

    assert str(error) == "Prompt compilation failed"
    assert envelope.code == "prompt.compile_failed"
    assert envelope.session_id == "sess_1"
    assert envelope.turn_id == "turn_1"
    assert envelope.details["source"] == "pack_prompt"
