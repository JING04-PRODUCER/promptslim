# Contributing to AgentOrchestrator

## Getting Started

```bash
git clone https://github.com/JING04-PRODUCER/agent-orchestrator.git
cd agent-orchestrator

# Agent Core (Python)
cd agent-core
pip install -r requirements.txt

# Admin Server (Java)
cd admin-server
./mvnw spring-boot:run
```

## Development

```bash
# Agent core tests
cd agent-core && pytest tests/ -v

# Admin server tests
cd admin-server && ./mvnw test
```

## Adding Custom Tools

1. Create a tool class in `agent-core/tools/`
2. Register it in the plugin registry with `@tool` decorator
3. Add tests

```python
from tools.registry import tool

@tool(name="my_tool", category="custom", description="My custom tool")
async def my_tool(param: str) -> str:
    return f"Result: {param}"
```

## Pull Request

1. Update CHANGELOG.md
2. Ensure all tests pass
3. Describe what and why in the PR description
