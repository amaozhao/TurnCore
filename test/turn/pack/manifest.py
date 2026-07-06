from operator import setitem

import pytest

from turn.pack import PackManifest, PromptSourceDefinition
from turn.policy import PolicyRuleDefinition


def test_pack_manifest_validates_required_fields() -> None:
    with pytest.raises(ValueError, match="pack_id"):
        PackManifest(pack_id="", name="Example", version="0.1.0", entrypoint="pack:Pack")


def test_pack_manifest_metadata_is_frozen_copy() -> None:
    metadata: dict[str, object] = {"domain": "research"}
    manifest = PackManifest(
        pack_id="com.example.research",
        name="Research",
        version="0.1.0",
        entrypoint="example.pack:ResearchPack",
        metadata=metadata,
        prompts=(
            PromptSourceDefinition(
                source_id="agents",
                file="prompts/AGENTS.md",
            ),
        ),
        policy_rules=(
            PolicyRuleDefinition(
                rule_id="network",
                target="network",
                effect="approval_required",
            ),
        ),
    )

    metadata["domain"] = "changed"

    assert manifest.metadata["domain"] == "research"
    assert manifest.prompts[0].source_type == "pack_builtin"
    with pytest.raises(TypeError):
        setitem(manifest.metadata, "domain", "changed")
