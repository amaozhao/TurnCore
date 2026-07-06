from hashlib import sha256
from operator import setitem

import pytest

from turn.prompt import PromptSource


def test_prompt_source_from_text_adds_content_checksum() -> None:
    source = PromptSource.from_text(
        source_id="framework",
        source_type="framework_builtin",
        priority=0,
        content="kernel",
    )

    assert source.checksum == sha256(b"kernel").hexdigest()
    assert source.metadata == {}


def test_prompt_source_metadata_is_frozen_copy() -> None:
    metadata: dict[str, object] = {"scope": "initial"}
    source = PromptSource.from_text(
        source_id="framework",
        source_type="framework_builtin",
        priority=0,
        content="kernel",
        metadata=metadata,
    )

    metadata["scope"] = "changed"

    assert source.metadata["scope"] == "initial"
    with pytest.raises(TypeError):
        setitem(source.metadata, "scope", "changed")
