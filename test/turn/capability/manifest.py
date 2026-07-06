from operator import setitem

import pytest

from turn.capability import CapabilityManifest, CapabilityStage


def test_capability_manifest_validates_name_and_freezes_metadata() -> None:
    metadata: dict[str, object] = {"mode": "linear"}
    manifest = CapabilityManifest(
        name="research",
        stages=(CapabilityStage(name="collect"),),
        metadata=metadata,
    )

    metadata["mode"] = "changed"

    assert manifest.metadata["mode"] == "linear"
    assert manifest.stages[0].name == "collect"
    with pytest.raises(TypeError):
        setitem(manifest.metadata, "mode", "changed")

    with pytest.raises(ValueError, match="capability name"):
        CapabilityManifest(name="")
