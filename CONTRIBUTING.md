# Contributing to PromptSlim

## Getting Started

```bash
git clone https://github.com/JING04-PRODUCER/promptslim.git
cd promptslim
pip install -e .
```

## Development

```bash
pytest tests/ -v          # Run tests
ruff check promptslim/    # Lint
```

## Adding Compression Rules

- Add patterns to `compressor.py` using pre-compiled regex at module level
- Each pattern must have a corresponding test in `tests/test_prompslim.py`
- Code protection: ensure `looks_like_code()` correctly excludes your test cases

## Pull Request

1. Update CHANGELOG.md
2. Ensure all tests pass
3. Describe what and why in the PR description
