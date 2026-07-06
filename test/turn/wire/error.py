import pytest

from turn.wire.error import ErrorEnvelope


def test_error_envelope_is_safe_cross_boundary_value() -> None:
    error = ErrorEnvelope(
        code="session.not_found",
        message="Session not found",
        retryable=False,
        session_id="sess_1",
        details={"kind": "missing"},
    )

    assert error.code == "session.not_found"
    assert error.session_id == "sess_1"
    assert error.details["kind"] == "missing"


def test_error_envelope_requires_code() -> None:
    with pytest.raises(ValueError, match="code"):
        ErrorEnvelope(code="", message="broken")
