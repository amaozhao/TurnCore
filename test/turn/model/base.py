from operator import setitem

import pytest

from turn.model import ModelRequest, ModelToolCall


def test_model_tool_call_arguments_are_frozen() -> None:
    arguments: dict[str, object] = {"query": "initial"}
    call = ModelToolCall(call_id="call_1", tool_name="search", arguments=arguments)

    arguments["query"] = "changed"

    assert call.arguments["query"] == "initial"
    with pytest.raises(TypeError):
        setitem(call.arguments, "query", "changed")


def test_model_request_metadata_is_frozen() -> None:
    metadata: dict[str, object] = {"trace": "one"}
    request = ModelRequest(
        session_id="sess_1",
        turn_id="turn_1",
        messages=(),
        metadata=metadata,
    )

    metadata["trace"] = "two"

    assert request.metadata["trace"] == "one"
    with pytest.raises(TypeError):
        setitem(request.metadata, "trace", "two")
