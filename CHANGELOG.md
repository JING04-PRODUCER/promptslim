# Changelog

## [0.4.1] - 2026-06-25

### Fixed
- Restored 40+ Chinese & English redundancy patterns lost in 0.4.0 merge
- Version unified across pyproject.toml and __init__.py
- Test file renamed: test_prompslim.py → test_promptslim.py
- README code examples fixed (report.slimmed → report.compressed, cost_per_call_saved → cost_saved)
- CI workflow fixed for promptslim repo structure

## [0.4.0] - 2026-06-19

### Changed
- Merged redundancy engine into compressor (`strip_text`)
- Replaced SlimReport with CompressReport dataclass
- Simplified tokenizer API: `count`, `count_batch`, `est_zh`, `cost`
- Renamed cache API: `analyze`/`CacheReport`
- Removed redundancy.py and reporter.py modules
- Pre-compiled regex patterns at module level

## [0.3.0] - 2026-06-17

### Added
- 40+ Chinese + English redundancy patterns (V2)
- Code block protection (`_is_code_like()` auto-detection)
- Anthropic Prompt Caching analysis module (`cache.py`)
- `--cache` CLI flag for cache breakpoint analysis
- `quick_slim()` cache_messages parameter for one-line cache savings estimate
- README_zh.md Chinese documentation
- Context-aware English filler removal (sentence-start only)

### Changed
- Refactored redundancy engine with context-aware rules
- More aggressive Chinese redundancy patterns while maintaining code safety
- Improved mixed Chinese-English text handling

## [0.2.0] - 2026-06-16

### Added
- Basic Chinese redundancy detection
- Multi-model token counting (GPT / Claude / DeepSeek / Qwen)
- CLI `count`, `slim`, `smart`, `compare` subcommands
- Python SDK public API exports

### Fixed
- Mixed Chinese-English redundancy detection
- Chinese whitespace removal edge cases
- Rich console encoding on Windows

## [0.1.0] - 2026-06-15

### Added
- Initial release
- English redundancy pattern detection
- Rule-based compression engine
- Token counting with tiktoken
- SlimReport with savings metrics
