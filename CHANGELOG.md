# Changelog

## [0.4.0] - 2026-06-19

### Changed
- Simplified ToolRegistry with inspect-based auto-registration
- Replaced plugin decorator pattern with builtin.py functions
- Streamlined main.py with lifespan and RAGMemory
- Removed workflow engine and multi-agent orchestration
- Simplified API surface (agents, health endpoints only)

## [0.3.0] - 2026-06-17

### Added
- Web Search tool (DuckDuckGo, free, no API key)
- RAG memory system with cosine similarity search
- Memory API endpoints (`/api/memory/init`, `/remember`, `/recall`, `/recall-context`)
- README_zh.md Chinese documentation

### Changed
- Auto-registration for web_search tool on startup

## [0.2.0] - 2026-06-16

### Added
- Comprehensive README with architecture diagram
- Badge optimization and English keywords
- Repository structure documentation

### Fixed
- Clone URL in README

## [0.1.0] - 2026-06-15

### Added
- Initial release
- LLM Agent core (OpenAI-compatible protocol)
- Function Calling with tool registry
- Plugin-based tool system (read_file, execute_sql, list_tables)
- Multi-agent workflow engine (sequential/parallel/DAG)
- Async tool execution with timeout and retry
- Spring Boot admin backend with JPA
- Docker Compose deployment
