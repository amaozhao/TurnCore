"""Pack protocol."""

from __future__ import annotations

from typing import Protocol

from turn.pack.manifest import PackManifest, PromptSourceDefinition
from turn.policy import PolicyRuleDefinition
from turn.artifact import ArtifactRenderer
from turn.capability import BaseCapability
from turn.tool import BaseTool


class PackRegistrar(Protocol):
    """Registrar exposed to capability packs."""

    def add_tool(self, tool_cls: type[BaseTool]) -> None: ...

    def add_capability(self, capability_cls: type[BaseCapability]) -> None: ...

    def add_prompt_source(self, source: PromptSourceDefinition) -> None: ...

    def add_policy_rule(self, rule: PolicyRuleDefinition) -> None: ...

    def add_artifact_renderer(self, renderer_cls: type[ArtifactRenderer]) -> None: ...


class CapabilityPack(Protocol):
    """Protocol implemented by external packs."""

    def describe(self) -> PackManifest: ...

    def register(self, registrar: PackRegistrar) -> None: ...


__all__ = ["CapabilityPack", "PackRegistrar"]
