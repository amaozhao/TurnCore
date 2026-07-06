# TurnCore
A session-scoped backend Agent Kernel for capability packs.

## Minimal use

```python
from turn import Agent
from turn.model import ModelRequest, ModelResponse


class MyModel:
    async def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(content="Hello")


agent = Agent(model=MyModel(), instructions="Answer briefly.")
result = agent.run("Say hello")

print(result.content)
```

TurnCore does not ship a model provider. Applications pass their own `ModelPort`
implementation.
