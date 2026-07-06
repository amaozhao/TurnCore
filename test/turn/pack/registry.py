import pytest

from turn.artifact import ArtifactRenderInput, ArtifactRenderResult
from turn.capability import CapabilityContext, CapabilityManifest, CapabilityResult
from turn.error import UAFError
from turn.pack import MemoryPackRegistrar, PackManifest, PackRegistry, PromptSourceDefinition
from turn.policy import PolicyRuleDefinition
from turn.tool import ToolCall, ToolDefinition, ToolResult


class SearchTool:
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(name="search", description="Search")

    async def execute(self, call: ToolCall) -> ToolResult:
        return ToolResult(
            call_id=call.call_id,
            tool_name=call.name,
            content="",
            success=True,
        )


class ResearchCapability:
    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(name="research")

    async def run(self, context: CapabilityContext) -> CapabilityResult:
        return CapabilityResult(status="completed")


class MarkdownRenderer:
    @property
    def artifact_type(self) -> str:
        return "markdown"

    def render(self, item: ArtifactRenderInput) -> ArtifactRenderResult:
        return ArtifactRenderResult(content_type="text/markdown", content="")


class ResearchPack:
    def describe(self) -> PackManifest:
        return PackManifest(
            pack_id="com.example.research",
            name="Research",
            version="0.1.0",
            entrypoint="example.pack:ResearchPack",
        )

    def register(self, registrar: MemoryPackRegistrar) -> None:
        registrar.add_tool(SearchTool)
        registrar.add_capability(ResearchCapability)
        registrar.add_prompt_source(
            PromptSourceDefinition(source_id="agents", file="prompts/AGENTS.md")
        )
        registrar.add_policy_rule(
            PolicyRuleDefinition(
                rule_id="network",
                target="network",
                effect="approval_required",
            )
        )
        registrar.add_artifact_renderer(MarkdownRenderer)


def test_pack_registry_collects_pack_contributions() -> None:
    registry = PackRegistry()

    registration = registry.register(ResearchPack())

    assert registration.manifest.pack_id == "com.example.research"
    assert registration.tools == (SearchTool,)
    assert registration.capabilities == (ResearchCapability,)
    assert registration.prompt_sources[0].source_id == "agents"
    assert registration.policy_rules[0].effect == "approval_required"
    assert registration.artifact_renderers == (MarkdownRenderer,)
    assert registry.get("com.example.research") == registration


def test_pack_registry_rejects_duplicate_pack() -> None:
    registry = PackRegistry()
    registry.register(ResearchPack())

    with pytest.raises(UAFError) as error:
        registry.register(ResearchPack())
    assert error.value.code == "pack.duplicate"
