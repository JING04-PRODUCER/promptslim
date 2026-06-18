# Contributing to PromptSlim

## Getting Started

```bash
git clone https://github.com/JING04-PRODUCER/promptslim.git
cd promptslim
pip install -e ".[dev]"
```

## Development

```bash
pytest tests/ -v          # Run tests
ruff check promptslim/    # Lint
ruff format promptslim/   # Format
```

## Adding Redundancy Patterns

- Chinese patterns: add regex to `ZH_REDUNDANCY_V2` in `promptslim/redundancy.py`
- English patterns: add regex to `EN_REDUNDANCY_V2` in `promptslim/redundancy.py`
- Each pattern must have a corresponding test in `tests/test_prompslim.py`
- Code protection: ensure `_is_code_like()` correctly excludes your test cases

## Pull Request

1. Update CHANGELOG.md
2. Ensure all tests pass
3. Describe what and why in the PR description
