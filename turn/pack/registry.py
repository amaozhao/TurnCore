"""Pack registration."""

from __future__ import annotations

from dataclasses import dataclass

from turn.artifact import ArtifactRenderer
from turn.capability import BaseCapability
from turn.error import UAFError
from turn.pack.base import CapabilityPack
from turn.pack.manifest import PackManifest, PromptSourceDefinition
from turn.policy import PolicyRuleDefinition
from turn.tool import BaseTool


@dataclass(frozen=True)
class PackRegistration:
    """Registered pack contributions."""

    manifest: PackManifest
    tools: tuple[type[BaseTool], ...]
    capabilities: tuple[type[BaseCapability], ...]
    prompt_sources: tuple[PromptSourceDefinition, ...]
    policy_rules: tuple[PolicyRuleDefinition, ...]
    artifact_renderers: tuple[type[ArtifactRenderer], ...]


class PackRegistry:
    """In-memory pack registry."""

    def __init__(self) -> None:
        self.registrations: dict[str, PackRegistration] = {}

    def register(self, pack: CapabilityPack) -> PackRegistration:
        manifest = pack.describe()
        if manifest.pack_id in self.registrations:
            raise UAFError(
                code="pack.duplicate",
                message="Pack is already registered",
                metadata={"pack_id": manifest.pack_id},
            )
        registrar = MemoryPackRegistrar()
        pack.register(registrar)
        registration = registrar.registration(manifest)
        self.registrations[manifest.pack_id] = registration
        return registration

    def get(self, pack_id: str) -> PackRegistration | None:
        return self.registrations.get(pack_id)


class MemoryPackRegistrar:
    """Collects pack contributions during registration."""

    def __init__(self) -> None:
        self.tools: list[type[BaseTool]] = []
        self.capabilities: list[type[BaseCapability]] = []
        self.prompt_sources: list[PromptSourceDefinition] = []
        self.policy_rules: list[PolicyRuleDefinition] = []
        self.artifact_renderers: list[type[ArtifactRenderer]] = []

    def add_tool(self, tool_cls: type[BaseTool]) -> None:
        self.tools.append(tool_cls)

    def add_capability(self, capability_cls: type[BaseCapability]) -> None:
        self.capabilities.append(capability_cls)

    def add_prompt_source(self, source: PromptSourceDefinition) -> None:
        self.prompt_sources.append(source)

    def add_policy_rule(self, rule: PolicyRuleDefinition) -> None:
        self.policy_rules.append(rule)

    def add_artifact_renderer(self, renderer_cls: type[ArtifactRenderer]) -> None:
        self.artifact_renderers.append(renderer_cls)

    def registration(self, manifest: PackManifest) -> PackRegistration:
        return PackRegistration(
            manifest=manifest,
            tools=tuple(self.tools),
            capabilities=tuple(self.capabilities),
            prompt_sources=tuple(self.prompt_sources),
            policy_rules=tuple(self.policy_rules),
            artifact_renderers=tuple(self.artifact_renderers),
        )


__all__ = ["MemoryPackRegistrar", "PackRegistration", "PackRegistry"]
